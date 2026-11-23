"""Small, reproducible evaluation against developer-authored synthetic SQL cases.

This is a transparent structural PROXY, not expert review, semantic accuracy, or
an LLM-as-judge score. It never upgrades research or verification statuses.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_verifier.primary_anchors import atoms


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def _candidate(run: Path, task_id: str) -> tuple[dict[str, Any] | None, str]:
    verified = run/'research'/'verifications'/f'{task_id}.json'
    if verified.exists():
        doc = _read(verified)
        return doc.get('candidate'), doc.get('status', 'unknown')
    files = sorted((run/'research'/'agent_runs').glob(f'{task_id}_*.json'))
    if not files:
        return None, 'missing'
    raw = _read(files[-1])
    return raw.get('decision'), 'unverified_'+str(raw.get('status', 'unknown'))


def evaluate_pilot(run_directory: Path, reference_file: Path) -> dict[str, Any]:
    """Calculate condition/effect/classification proxies for synthetic fixtures.

    Source-atom precision measures only SQL predicates in conditions[]; prose
    assertions and causal validity are NOT covered. A result can be internally
    technically evidenced and nevertheless fail this independent fixture check.
    """
    run = run_directory.resolve()
    ref = _read(reference_file)
    cases = ref.get('cases') or []
    if not cases:
        raise ValueError('Synthetic pilot reference has no cases')
    results = []
    predicate_supported = predicate_total = expected_found = expected_total = 0
    classification_match = completed = full_match = 0
    for case in cases:
        task_id = case['task_id']
        source_file = run / case['source_file']
        if not source_file.is_file():
            raise FileNotFoundError(f'Synthetic reference source is missing: {source_file}')
        sql = source_file.read_text(encoding='utf-8-sig')
        sql_atoms = atoms(sql)
        expected = set()
        for condition in case['expected_predicates']:
            clause = atoms(condition)
            if not clause or not clause.issubset(sql_atoms):
                raise ValueError(f'Reference predicate is not in synthetic SQL: {task_id}: {condition}')
            expected |= clause
        candidate, status = _candidate(run, task_id)
        observed = set()
        if isinstance(candidate, dict):
            for condition in candidate.get('conditions') or []:
                if isinstance(condition, str):
                    observed |= atoms(condition)
        matched = observed & expected
        unexpected = observed - sql_atoms
        predicate_total += len(observed)
        predicate_supported += len(observed & sql_atoms)
        expected_total += len(expected)
        expected_found += len(matched)
        text = ' '.join(str(candidate.get(k) or '') for k in
                        ('observed_behavior', 'effect', 'candidate_rule')) if isinstance(candidate,dict) else ''
        missing_effects = [term for term in case['expected_effect_terms']
                           if term.casefold() not in text.casefold()]
        # These anchors must be grounded in the real source by design.
        for anchor in case['source_effect_anchors']:
            if anchor.casefold() not in sql.casefold():
                raise ValueError(f'Reference effect anchor absent from SQL: {task_id}: {anchor}')
        right_class = bool(isinstance(candidate,dict) and
                           candidate.get('classification') == case['expected_classification'])
        if right_class:
            classification_match += 1
        if isinstance(candidate, dict):
            completed += 1
        exact = bool(candidate and right_class and not unexpected and
                     expected.issubset(observed) and not missing_effects)
        full_match += int(exact)
        results.append({
            'task_id': task_id, 'object': case['object'], 'status': status,
            'expected_classification': case['expected_classification'],
            'classification_match': right_class,
            'expected_predicates_found': len(matched),
            'expected_predicates_total': len(expected),
            'asserted_sql_predicates_supported': len(observed & sql_atoms),
            'asserted_sql_predicates_total': len(observed),
            'unexpected_sql_predicates': [list(a) for a in sorted(unexpected)],
            'missing_expected_predicates': [list(a) for a in sorted(expected-observed)],
            'missing_effect_terms': missing_effects,
            'synthetic_structural_correct': exact,
            'reference_source': case['source_file'],
        })
    total = len(cases)
    observed_escalations = sum(1 for x in results if x['status'] in
                               ('pending_human_review','incomplete_research'))
    has_verifier = any((run/'research'/'verifications').glob('TASK-*.json'))
    return {
        'schema_version': '2.0', 'evaluation_type': 'developer_authored_synthetic_pilot',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'reference_file': str(reference_file), 'reference_cases': total,
        'proposals_available': completed,
        'pilot_structural_correctness': round(full_match/total,4),
        'pilot_groundedness_sql_predicate_precision':
            round(predicate_supported/predicate_total,4) if predicate_total else 0.0,
        'pilot_classification_accuracy': round(classification_match/total,4),
        'expected_predicate_recall': round(expected_found/expected_total,4) if expected_total else None,
        'observed_escalation_rate': round(observed_escalations/total,4) if has_verifier else None,
        'verified_results_available': bool(has_verifier),
        'case_details': results,
        'limitations': [
            'Synthetic reference authored from the fixture SQL, not external domain-expert adjudication.',
            'Correctness counts exact SQL predicate coverage, expected effect terms, classification, and no unsupported predicates; it is a structural proxy, not full semantic accuracy.',
            'Groundedness checks only source predicate alignment in conditions[], not every natural-language claim.',
            'Escalation rate is a frequency, not escalation sensitivity/precision; unverified stages report null.',
            'Do not describe these metrics as validated performance on production systems.',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-directory', type=Path, required=True)
    parser.add_argument('--references',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=evaluate_pilot(args.run_directory,args.references)
    output=args.output or args.run_directory/'research'/'evaluation_metrics.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'[pilot_evaluation] cases={result["reference_cases"]} structural_correctness={result["pilot_structural_correctness"]} '
          f'predicate_grounding={result["pilot_groundedness_sql_predicate_precision"]} '
          f'classification={result["pilot_classification_accuracy"]} output={output}',flush=True)


if __name__=='__main__':
    main()
