$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$planDir = 'E:\jingwenpeng\2026autumn\ntn-oai-project\.planning\2026-09-24-stk-quadriga-oai-integration-plan'
$backupRoot = (Get-Content -Raw -LiteralPath (Join-Path $planDir 'step-00-latest.txt')).Trim()
$outputLog = Join-Path $backupRoot 'baseline-regressions.txt'

Write-Host 'STEP 0: VISIBLE BASELINE REGRESSION' -ForegroundColor Green
Write-Host "Backup: $backupRoot"
$command = "cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project && OAI_UE_CONFIG=/home/duyaya/.local/share/oai-stk/ue.stk-20260923.conf GIT_PAGER=cat PAGER=cat bash local_ntn/run_regressions.sh"
Write-Host "`n>>> wsl.exe bash -lc '$command' 2>&1 | Tee-Object '$outputLog'" -ForegroundColor Cyan

wsl.exe bash -lc $command 2>&1 | Tee-Object -LiteralPath $outputLog
$exitCode = $LASTEXITCODE
Write-Host "`nRegression exit code: $exitCode"

$result = [ordered]@{
    status = if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' }
    completed_at = (Get-Date).ToString('o')
    regression_exit_code = $exitCode
    output_log = $outputLog
}
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backupRoot 'STEP00_VERIFIED.json') -Encoding utf8

if ($exitCode -eq 0) {
    Write-Host 'STEP 0 VISIBLE REGRESSION PASS' -ForegroundColor Green
} else {
    Write-Host 'STEP 0 VISIBLE REGRESSION FAILED' -ForegroundColor Red
}

Read-Host 'The visible terminal will remain open for inspection. Press Enter when you want to close this script'
