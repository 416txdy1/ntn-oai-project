$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = "E:\jingwenpeng\2026autumn\ntn-oai-project"
$planRoot = Join-Path $projectRoot ".planning\2026-09-24-stk-quadriga-oai-integration-plan"
$logPath = Join-Path $planRoot "step01-discovery-transcript.txt"
$resultPath = Join-Path $planRoot "STEP01_CONTRACT_DISCOVERY_DONE.json"
$skillRoot = "C:\Users\duya\.codex\skills\planning-with-files"

Set-Location $projectRoot
$Host.UI.RawUI.WindowTitle = "Step 1 - QuaDRiGa contract discovery"
Start-Transcript -LiteralPath $logPath -Force | Out-Null

try {
    Write-Host "Step 1：QuaDRiGa 接口契约与目录骨架——只读发现" -ForegroundColor Cyan
    Write-Host "PS> resolve active plan" -ForegroundColor DarkGray
    $env:PWF_PLAN_ROOT = $projectRoot
    $env:PLAN_ID = "2026-09-24-stk-quadriga-oai-integration-plan"
    & (Join-Path $skillRoot "scripts\resolve-plan-dir.ps1")

    Write-Host "PS> Get-Content task_plan.md, progress.md, findings.md" -ForegroundColor DarkGray
    Get-Content (Join-Path $planRoot "task_plan.md")
    Get-Content (Join-Path $planRoot "progress.md")
    Get-Content (Join-Path $planRoot "findings.md")

    Write-Host "PS> git status --short --branch" -ForegroundColor DarkGray
    git status --short --branch
    if ($LASTEXITCODE -ne 0) { throw "git status failed" }

    Write-Host "PS> git diff --stat" -ForegroundColor DarkGray
    git diff --stat
    if ($LASTEXITCODE -ne 0) { throw "git diff --stat failed" }

    Write-Host "PS> rg --files local_ntn oai_patch docs" -ForegroundColor DarkGray
    rg --files local_ntn oai_patch docs 2>$null
    if ($LASTEXITCODE -gt 1) { throw "rg --files failed" }

    Write-Host "PS> rg architecture/schema keywords" -ForegroundColor DarkGray
    rg -n -S "STKTRACE|sample_rate|sample clock|channel|doppler|delay|path_loss|visibility|metadata|schema" local_ntn oai_patch README.md sources.lock
    if ($LASTEXITCODE -gt 1) { throw "rg keyword search failed" }

    Write-Host "PS> show trace parser/exporter/test interfaces" -ForegroundColor DarkGray
    $inspectFiles = @(
        "local_ntn/stk_trace.h",
        "local_ntn/stk_trace.c",
        "local_ntn/stk_trace_channel.c",
        "local_ntn/export_stk_trace.py",
        "local_ntn/test_trace.py",
        "local_ntn/README.md"
    )
    foreach ($file in $inspectFiles) {
        if (Test-Path -LiteralPath $file) {
            Write-Host "===== $file =====" -ForegroundColor Yellow
            Get-Content -LiteralPath $file
        }
    }

    [ordered]@{
        status = "success"
        timestamp = (Get-Date).ToString("o")
        plan_id = $env:PLAN_ID
        transcript = $logPath
    } | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Host "只读发现完成：$resultPath" -ForegroundColor Green
}
catch {
    [ordered]@{
        status = "failed"
        timestamp = (Get-Date).ToString("o")
        error = $_.Exception.Message
        transcript = $logPath
    } | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Host "执行失败：$($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Stop-Transcript | Out-Null
    Read-Host "按 Enter 关闭窗口"
}
