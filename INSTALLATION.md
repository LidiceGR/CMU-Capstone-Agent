# Installation and execution requirements

These steps install or reuse a Python environment for the **existing** Capstone research pipeline. Tested project examples target **Python 3.11** and local Windows PowerShell. Use the working `cmu-llm` environment if it is already configured.

## 1. Prerequisites

- Windows 10/11 with PowerShell; Conda/Miniconda or Anaconda available locally.
- Python **3.11** inside a Conda environment. The system uses annotations unsupported by the user's older global Python 3.8.
- Sufficient RAM and disk space to load `Qwen/Qwen3-0.6B` on CPU and store its Hugging Face cache. No GPU is required.
- Network access for the **first model download**, unless the model files are already cached locally. Later offline use depends on the local Hugging Face cache.
- A current web browser that supports selecting a local folder (`webkitdirectory`) for the offline HTML viewers.

No SQL Server connection, ODBC driver, external API, vector database or Java runtime is required to run the supplied `dummy_system1` demonstrations.

## 2. Create or reuse the environment

Use PowerShell from the project directory, for example `D:\Proyectos\CMUAgent\Proyectos`.

```powershell
# If the environment does not already exist:
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" create -n cmu-llm python=3.11 -y

# Confirm that the project is executed with this interpreter:
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run -n cmu-llm python --version
```

The path to `conda.exe` is machine-specific; replace it if your installation differs. If you already have `cmu-llm`, do **not** recreate it.

## 3. Install required packages

The project uses `sqlfluff`, `transformers`, `accelerate` and `torch`. The runtime requirements do not include development or test-only packages.

```powershell
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run --no-capture-output -n cmu-llm python -m pip install -r requirements-capstone.txt
```

Do not run plain global `python` for this project. For a CPU-only PyTorch setup, follow the PyTorch installation instructions suitable for your operating system and then install the remaining requirements. This repository does not bundle model weights or third-party Python packages.

## 4. Verify the installation

```powershell
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run -n cmu-llm python -c "import sqlfluff, transformers, accelerate, torch; print('Dependencies OK')"

# Preview pipeline stages without running Qwen or altering stored results:
& "D:\devenv\Anaconda32024.02\Scripts\conda.exe" run --no-capture-output -n cmu-llm python -m capstone_app --config config\capstone_pipeline.capstone_full_v08.json --run-id install_check_only --dry-run
```

The `--dry-run` command prints the pipeline plan; it does not produce a new workspace folder. `install_check_only` must be a directory name that does not already exist.

## 5. Run the five examples

The five exact commands are documented in [README.md](README.md):

1. `config/capstone_pipeline.capstone_full_v08.json` (complete pipeline)
2. `config/capstone_pipeline.demo_01_sql_only.json` (SQL-only baseline)
3. `config/capstone_pipeline.demo_02_catalog_tools.json` (ReAct and catalogs)
4. `config/capstone_pipeline.demo_03_multiagent_no_rag.json` (verifier, no RAG)
5. `config/capstone_pipeline.demo_04_multiagent_doc_rag.json` (verifier plus documentary BM25)

A convenience script runs all four staged experiments:

```powershell
.\run_demo_four_stages.ps1
```

The five demonstration workspaces are **already included** in this archive. All five canonical run IDs therefore exist. Supply a fresh `--run-id` when re-executing a command or point `workspace` to a new location. Existing run folders are deliberately never overwritten.

## 6. Inspect the results

Open `Capstone_Workspace_Explorer_v11_Pilot_Evaluation.html` or `Capstone_4_Stages_Comparison_v08.html` in a browser and select the local `workspace` folder. No server installation is required. The viewer reads local files in the browser and does not upload them to a service.

## 7. Supported and unsupported modes

**Supported:** local SQL/catalog extraction, SQLFluff AST, inventory, logical workflow tasks, Qwen-based research, read-only local tools, catalog grounding, verifier, BM25 Markdown retrieval, saved run traces, pilot metrics and offline visualization.

**Not supported:** live ODBC collection, arbitrary SQL execution, Java analysis, embeddings, MCP service hosting and persistent human approval actions. `mode=odbc` explicitly raises `NotImplementedError` in `source_extractor/extractor.py`.
