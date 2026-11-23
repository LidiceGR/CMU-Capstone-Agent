# Legacy Business Rule Research Assistant — Capstone v0.8

## Purpose and implemented scope

This repository contains a **proof-of-concept** assistant that investigates candidate business rules from legacy T-SQL source files. It combines a read-only source collector, SQLFluff AST parsing, an object/dependency inventory, workflow task generation, a Qwen-based Research Agent with a ReAct loop, controlled retrieval tools, an Evidence Verifier, a programmatic coordinator, a BM25 documentary index, and run-local evidence records. No automatically generated candidate is a domain-approved rule.

The included sample system is synthetic (`mock_sql_examples/dummy_system1`). Source files and catalogs are copied into separate run directories. The implementation does **not** execute SQL statements against a database. ODBC source extraction and Java analysis are **not supported** in this distribution.

## Project structure

| Path | Current role |
| --- | --- |
| `capstone_app/` | Pipeline entry point, configuration, orchestration and stage status |
| `source_extractor/` | Copies local `.sql` and `.catalog.json` input; creates a provenance manifest |
| `sql_ast_parsers/` | Parses T-SQL using SQLFluff; writes AST artifacts |
| `inventory_builder/` | Builds SQL object inventory, relationships and catalog metadata |
| `task_initializer/` | Creates source-backed workflow research tasks |
| `research_agent/` | Researcher, two-phase ReAct controller, tool dispatch, traces and task queue |
| `resource_acquisition/` | Read-only acquisition abstraction for research operations |
| `evidence_verifier/` | Verification, deterministic evidence checks, catalog grounding and feedback coordination |
| `rag_tools/` | Local BM25 indexing and retrieval for SQL or Markdown evidence |
| `llm/` and `prompts/` | Local Qwen inference and active model prompts |
| `evaluation/` | Five-case synthetic pilot references and metrics; optional reviewed-reference comparator |
| `mock_sql_examples/dummy_system1/` | Seven SQL files, two catalogs and five Markdown business-context sources |
| `config/` | The five complete/demo run configurations and local source configuration |
| `workspace/` | Five saved, **real** example executions, with full analysis artifacts |
| `*.html` | Four offline viewers: technical workspace, raw artifacts, business review and four-stage comparison |

The Markdown files under `mock_sql_examples/dummy_system1/rag_documents/` are **RAG input data**, not obsolete README files; keep them with the project.

## Five executable runs

Run these commands from the project root using the `cmu-llm` Conda environment. See [INSTALLATION.md](INSTALLATION.md) for setup.

**1. Full end-to-end run** — SQL extraction, AST, inventory, tasks, ReAct, catalog evidence, documentary BM25, verifier, findings, pending cases and synthetic-pilot evaluation:

```powershell
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run --no-capture-output -n cmu-llm python -m capstone_app --config config\capstone_pipeline.capstone_full_v08.json
```

**2. Stage 1 — SQL-only baseline** (no research tools, verifier or RAG):

```powershell
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run --no-capture-output -n cmu-llm python -m capstone_app --config config\capstone_pipeline.demo_01_sql_only.json
```

**3. Stage 2 — ReAct + catalog tools** (no independent verifier and no RAG):

```powershell
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run --no-capture-output -n cmu-llm python -m capstone_app --config config\capstone_pipeline.demo_02_catalog_tools.json
```

**4. Stage 3 — Researcher + Evidence Verifier** (catalog tools, no RAG):

```powershell
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run --no-capture-output -n cmu-llm python -m capstone_app --config config\capstone_pipeline.demo_03_multiagent_no_rag.json
```

**5. Stage 4 — Multi-agent with documentary RAG** (BM25 over the five Markdown context files, *not* the SQL index):

```powershell
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run --no-capture-output -n cmu-llm python -m capstone_app --config config\capstone_pipeline.demo_04_multiagent_doc_rag.json
```

Alternatively, `./run_demo_four_stages.ps1` runs stages 1–4; add `-IncludeFull` to include the end-to-end run. The PowerShell script expects the Conda path above.

**Runs never overwrite existing run directories.** This archive includes the five results already produced. To execute the examples again, append a *new* `--run-id` to the commands (for example `--run-id capstone_full_retake_01`). The fixed four-stage HTML comparator recognizes the canonical demo run IDs; for a fresh comparison, use a separate workspace directory or update its run mapping to your new IDs. Do not delete or alter the archived evidence merely to rerun the project.

## Saved results in this archive

| Workspace directory | Recorded pipeline status | Pilot structural match | SQL predicate groundedness proxy | Classification pilot | Escalation (verified stages) |
| --- | --- | ---: | ---: | ---: | ---: |
| `workspace/capstone_full_v08` | `completed` | 80% | 100% | 80% | 20% |
| `workspace/demo_01_sql_only` | `completed_with_warnings` | 60% | 100% | 100% | n/a |
| `workspace/demo_02_catalog_tools` | `completed_with_warnings` | 80% | 100% | 100% | n/a |
| `workspace/demo_03_multiagent_no_rag` | `completed` | 100% | 100% | 100% | 0% |
| `workspace/demo_04_multiagent_doc_rag` | `completed` | 80% | 100% | 80% | 20% |

These values come from each run's `research/evaluation_metrics.json`. The references are **developer-authored synthetic cases (n=5)**, not independent expert judgments. Structural matching is not full natural-language correctness; the groundedness proxy evaluates SQL predicates, not every business claim. Different runs can produce different values from the local model. Stage 4 **does not necessarily outperform stage 3**: merely retrieving a document does not guarantee its correct use.

## Viewing the evidence

Open the HTML files directly in a browser and choose the **`workspace` directory** when prompted:

- `Capstone_Workspace_Explorer_v11_Pilot_Evaluation.html` — full pipeline overview; AST, tasks, original model prompts/responses, REASON/ACT/OBSERVE, tool provenance, verification and pilot metrics.
- `Capstone_Artifact_Explorer_v10_Pilot_Evaluation.html` — raw SQL/JSON/Markdown artifacts plus structured summaries.
- `Capstone_Business_Rule_Review_Demo_v04_Pilot_Evaluation.html` — user-facing candidate review prototype. Approvals and comments are **on-screen only**; reinvestigation is intentionally inactive.
- `Capstone_4_Stages_Comparison_v08.html` — side-by-side results for `ApproveOperation`, `RegisterOperation`, `RegisterOperationAfterCheck` and `HasPendingOperationCheck` across the four staged experiments.

The researcher can request tools by itself; the controller also applies **explicit, labeled catalog evidence gates**. Never attribute controller-selected tools to the model. The verifier LLM can accept unsupported results; deterministic checks can still veto publication. `technically_evidenced` never means approved by a domain expert.

## Run outputs and evaluation

Each `workspace/<run_id>/` contains `sources_manifest.json`, `sql_sources/`, `ast_files/`, `metadata/`, `research/research_tasks.json`, research traces under `research/agent_runs/`, optional RAG artifacts, and `research/evaluation_metrics.json`. Multi-agent runs also contain `research/verifications/`, `research/findings.json`, `research/pending.json` and `research/multiagent_summary.json`.

`evaluation/pilot_synthetic.py` calculates synthetic structural and predicate checks from `evaluation/pilot_reference_system1.json`. `evaluation/compare_to_reference.py` is a separate **implemented** comparator for explicitly reviewed reference cases; its output is not a production accuracy certification. The template for reviewed cases is `evaluation/reference_cases_TEMPLATE.json`.

## Boundaries and limitations

- Qwen3-0.6B on CPU can select `finish` early, omit observations or confuse conditions across called procedures. These cases appear in trace records and pending outcomes.
- The ReAct loop is implemented with Python tools, **not MCP**. Tool calls may be requested by Qwen or enforced by the controller; the origin is logged.
- Documentary retrieval uses lexical **BM25**, not vector embeddings. Stage 4 indexes five fictional Markdown files; a positive retrieval does not prove causal improvement in the final rule.
- Source extraction is implemented for local files (`mock` mode). ODBC mode explicitly raises `NotImplementedError`. No arbitrary SQL execution, persistent human approval or Java source analysis is implemented.
- The archived JSON reflects the Windows filesystem used for those runs; absolute source paths in manifests are historical provenance and do not need to resolve on a different computer for offline viewer inspection.
