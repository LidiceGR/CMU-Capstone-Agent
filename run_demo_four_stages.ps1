# Run all four controlled Capstone experiments in the existing cmu-llm environment.
# Usage: .\run_demo_four_stages.ps1
# Optional full separate run: .\run_demo_four_stages.ps1 -IncludeFull
param([switch]$IncludeFull)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$conda = 'D:\devenv\Anaconda32024.02\Scripts\conda.exe'
if (-not (Test-Path $conda)) { throw "Conda executable not found: $conda" }
$configs = @(
    'config\capstone_pipeline.demo_01_sql_only.json',
    'config\capstone_pipeline.demo_02_catalog_tools.json',
    'config\capstone_pipeline.demo_03_multiagent_no_rag.json',
    'config\capstone_pipeline.demo_04_multiagent_doc_rag.json'
)
if ($IncludeFull) { $configs += 'config\capstone_pipeline.capstone_full_v08.json' }
foreach ($config in $configs) {
    Write-Host "`n[demo_started] config=$config" -ForegroundColor Cyan
    & $conda run --no-capture-output -n cmu-llm python -m capstone_app --config $config
    if ($LASTEXITCODE -ne 0) {
        throw "Demo stopped on $config with exit code $LASTEXITCODE. Inspect its run folder; do not delete prior runs."
    }
    Write-Host "[demo_completed] config=$config" -ForegroundColor Green
}
Write-Host "`n[demo_finished] Open Capstone_4_Stages_Comparison_v08.html and choose the workspace folder." -ForegroundColor Green
