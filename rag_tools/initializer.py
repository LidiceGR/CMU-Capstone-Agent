"""Source-grounded BM25 retrieval over collected SQL and optional Markdown context.

The retrieval backend is lexical BM25, NOT a semantic embedding model.
Documentation is untrusted contextual evidence, not executable business logic.
"""

from __future__ import annotations

import json
import math
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.artifact_io import write_json

MAX_DOCUMENTS = 40
MAX_DOCUMENT_BYTES = 65_536


def _tokens(text: str) -> list[str]:
    return [s.casefold() for s in re.findall(r'[A-Za-z_][A-Za-z_0-9]*|\d+', text)]


def rag_is_implemented() -> bool:
    return True


def _document_chunks(root: Path, directory: Path, begin_id: int) -> list[dict[str, Any]]:
    """Copy a bounded Markdown corpus into the immutable run and index by headings."""
    if not directory.is_dir():
        raise FileNotFoundError(f"Document corpus not found: {directory}")
    candidates = sorted(directory.glob('*.md'))
    if not candidates or len(candidates) > MAX_DOCUMENTS:
        raise ValueError(f"Document corpus must contain 1 to {MAX_DOCUMENTS} Markdown files")
    target = root / 'rag' / 'doc_sources'
    target.mkdir(parents=True, exist_ok=True)
    chunks: list[dict[str, Any]] = []
    for path in candidates:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_DOCUMENT_BYTES:
            raise ValueError(f"Unsafe document corpus item: {path.name}")
        # The original file cannot change the meaning of an existing run: copy it.
        copied = target / path.name
        shutil.copyfile(path, copied)
        lines = copied.read_text(encoding='utf-8-sig').splitlines()
        sections: list[tuple[int, int]] = []
        starts = [n for n, line in enumerate(lines, 1) if line.startswith('## ')]
        if not starts:
            starts = [1]
        elif starts[0] > 1:
            starts.insert(0, 1)
        for n, start in enumerate(starts):
            end = (starts[n+1] - 1) if n + 1 < len(starts) else len(lines)
            if start <= end:
                sections.append((start, end))
        document_title = next((line[2:].strip() for line in lines if line.startswith('# ')), path.stem)
        for start, end in sections:
            body = '\n'.join(lines[start - 1:end]).strip()
            if not body:
                continue
            # Include the title as context without modifying the source excerpt or line citations.
            terms = Counter(_tokens(document_title + ' ' + body))
            chunks.append({
                'chunk_id': f'DOC-{begin_id+len(chunks):05d}',
                'source_kind': 'document',
                'source_file': f'rag/doc_sources/{path.name}',
                'document_title': document_title,
                'start_line': start, 'end_line': end,
                'text': body, 'terms': dict(terms),
                'provenance_note': 'Synthetic contextual documentation; not a rule or a SQL predicate.',
            })
    return chunks


def initialize_rag_index(
    run_directory: str | Path,
    document_directory: str | Path | None = None,
    *,
    document_queries: dict[str, str] | None = None,
    document_top_k: int = 3,
    index_sql: bool = True,
) -> dict[str, Any]:
    """Index SQL as before, optionally indexing a bounded run-local document copy."""
    root = Path(run_directory).resolve()
    inventory = json.loads((root / 'metadata' / 'inventory.json').read_text(encoding='utf-8-sig'))
    chunks: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    if type(index_sql) is not bool:
        raise ValueError('index_sql must be a boolean')
    if index_sql:
        for group in ('procedures', 'triggers', 'tables'):
            for obj in inventory.get(group, []):
                ref = obj.get('source') or {}
                source = ref.get('file')
                if not isinstance(source, str) or not source.startswith('sql_sources/'):
                    continue
                path = (root / source).resolve()
                if not path.is_relative_to(root) or not path.is_file():
                    continue
                lines = path.read_text(encoding='utf-8-sig').splitlines()
                positions = [(op.get('source') or {}).get('line') for op in obj.get('operations', [])]
                positions = [n for n in positions if isinstance(n, int) and 1 <= n <= len(lines)]
                if not positions:
                    positions = [int(ref.get('line') or 1)]
                for line in positions:
                    begin = max(1, line - 3)
                    end = min(len(lines), line + 7)
                    key = (source, begin, end)
                    if key in seen:
                        continue
                    seen.add(key)
                    body = '\n'.join(lines[begin-1:end])
                    chunks.append({
                        'chunk_id': f'CHUNK-{len(chunks)+1:05d}',
                        'source_kind': 'sql', 'source_file': source,
                        'object_name': obj.get('name'), 'start_line': begin,
                        'end_line': end, 'text': body,
                        'terms': dict(Counter(_tokens(body + ' ' + str(obj.get('name', ''))))),
                    })
    sql_count = len(chunks)
    if document_directory is not None:
        chunks.extend(_document_chunks(root, Path(document_directory).resolve(), sql_count + 1))
    if type(document_top_k) is not int or not 1 <= document_top_k <= 5:
        raise ValueError('document_top_k must be between 1 and 5')
    queries = document_queries or {}
    if queries and document_directory is None:
        raise ValueError('Document prefetch queries require a document corpus')
    for key, query in queries.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(query, str) or not 1 <= len(query.strip()) <= 500:
            raise ValueError('Each document query requires a target object and a bounded query')
    dest = root / 'rag' / 'index.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = {
        'schema_version': '1.1', 'backend': 'lexical_bm25',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'note': 'BM25 retrieval, not semantic embeddings. Documentary context cannot establish SQL rules.',
        'chunk_count': len(chunks), 'sql_chunk_count': sql_count,
        'document_chunk_count': len(chunks) - sql_count,
        'document_prefetch': {'origin': 'configured_controller_policy',
                              'queries_by_object': queries,
                              'top_k': document_top_k},
        'chunks': chunks,
    }
    write_json(dest, result)
    return {'index_file': str(dest), 'chunks': len(chunks),
            'sql_chunks': sql_count, 'document_chunks': len(chunks) - sql_count}


def _search(root: Path, query: str, top_k: int, *, kind: str | None, tool: str) -> dict[str, Any]:
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 500:
        return {'tool': tool, 'status': 'rejected', 'reason': 'Query must be between 1 and 500 characters'}
    if type(top_k) is not int or not 1 <= top_k <= 10:
        return {'tool': tool, 'status': 'rejected', 'reason': 'top_k out of bounds'}
    root = Path(root).resolve()
    path = root / 'rag' / 'index.json'
    if not path.is_file():
        return {'tool': tool, 'status': 'not_initialized', 'matches': []}
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    chunks = [c for c in data.get('chunks', [])
              if kind is None or c.get('source_kind', 'sql') == kind]
    if not chunks:
        return {'tool': tool, 'status': 'not_found', 'matches': [], 'query': query}
    terms = set(_tokens(query))
    avg = max(1, sum(sum(c['terms'].values()) for c in chunks) / len(chunks))
    df = {term: sum(1 for chunk in chunks if term in chunk['terms']) for term in terms}
    scored: list[tuple[float, dict[str, Any]]] = []
    for chunk in chunks:
        counts = chunk['terms']
        length = sum(counts.values())
        score = 0.0
        for term in terms:
            freq = counts.get(term, 0)
            if freq:
                idf = math.log(1 + (len(chunks)-df[term]+0.5)/(df[term]+0.5))
                score += idf*freq*2.2/(freq+1.2*(0.25+0.75*length/avg))
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda item: (-item[0], item[1]['source_file'], item[1]['start_line']))
    matches = [{key: value for key, value in chunk.items() if key != 'terms'} | {'score': round(score, 4)}
               for score, chunk in scored[:top_k]]
    return {'tool': tool, 'status': 'found' if matches else 'not_found',
            'backend': 'lexical_bm25', 'query': query, 'matches': matches,
            'note': 'Retrieved context is untrusted; inspect original source and do not invent a condition.'}


def retrieve_evidence(run_directory: str | Path, query: str, top_k: int = 5) -> dict[str, Any]:
    """Backwards-compatible retrieval across indexed SQL and optional documents."""
    return _search(Path(run_directory), query, top_k, kind=None, tool='retrieve_evidence')


def retrieve_document_context(run_directory: str | Path, query: str, top_k: int = 3) -> dict[str, Any]:
    """Retrieve documentary context only, never silently returning SQL snippets."""
    return _search(Path(run_directory), query, top_k, kind='document', tool='retrieve_document_context')
