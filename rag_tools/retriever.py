"""Public retrieval wrappers over the run-local BM25 index."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .initializer import retrieve_document_context as _document_search
from .initializer import retrieve_evidence as _combined_search


def retrieve_evidence(query: str, run_directory: str, top_k: int = 5) -> dict[str, Any]:
    """Return source-backed SQL/document matches, with line references."""
    return _combined_search(Path(run_directory), query, top_k)


def retrieve_document_context(query: str, run_directory: str, top_k: int = 3) -> dict[str, Any]:
    """Return only Markdown context matches, with line references."""
    return _document_search(Path(run_directory), query, top_k)
