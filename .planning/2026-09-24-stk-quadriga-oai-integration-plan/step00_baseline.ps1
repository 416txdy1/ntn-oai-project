$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$projectRoot = 'E:\jingwenpeng\2026autumn\ntn-oai-project'
$oaiRoot = '\\wsl.localhost\Ubuntu-22.04\home\duyaya\OAI\openairinterface5g'
$planDir = Join-Path $projectRoot '.planning\2026-09-24-stk-quadriga-oai-integration-plan'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $planDir "backups\step-00-baseline-$stamp"
$projectBackup = Join-Path $backupRoot 'project'
$oaiBackup = Join-Path $backupRoot 'oai'

New-Item -ItemType Directory -Path $projectBackup, $oaiBackup -Force | Out-Null
Set-Content -LiteralPath (Join-Path $planDir 'step-00-latest.txt') -Value $backupRoot -Encoding utf8
$transcript = Join-Path $backupRoot 'baseline-transcript.txt'
Start-Transcript -LiteralPath $transcript -Force

function Show-Command([string]$command) {
    Write-Host "`n>>> $command" -ForegroundColor Cyan
}

function Backup-File([string]$sourceRoot, [string]$relativePath, [string]$destinationRoot) {
    $source = Join-Path $sourceRoot $relativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required baseline file is missing: $source"
    }
    $destination = Join-Path $destinationRoot $relativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
    Write-Host "BACKUP $source -> $destination"
}

try {
    Write-Host 'STEP 0: BASELINE LOCK' -ForegroundColor Green
    Write-Host "Project: $projectRoot"
    Write-Host "OAI:     $oaiRoot"
    Write-Host "Backup:  $backupRoot"

    Show-Command "git -C '$projectRoot' rev-parse HEAD"
    $projectCommit = (git -C $projectRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Project git rev-parse failed' }
    Write-Host $projectCommit

    Show-Command "git -C '$projectRoot' status --short"
    git -C $projectRoot status --short
    if ($LASTEXITCODE -ne 0) { throw 'Project git status failed' }

    Show-Command "git -C '$projectRoot' diff --stat"
    git -C $projectRoot diff --stat
    if ($LASTEXITCODE -ne 0) { throw 'Project git diff --stat failed' }

    Show-Command "wsl.exe bash -lc 'cd /home/duyaya/OAI/openairinterface5g && git rev-parse HEAD'"
    $oaiCommit = (wsl.exe bash -lc 'cd /home/duyaya/OAI/openairinterface5g && git rev-parse HEAD').Trim()
    if ($LASTEXITCODE -ne 0) { throw 'OAI git rev-parse failed' }
    Write-Host $oaiCommit

    Show-Command "wsl.exe bash -lc 'cd /home/duyaya/OAI/openairinterface5g && git status --short'"
    wsl.exe bash -lc 'cd /home/duyaya/OAI/openairinterface5g && git status --short'
    if ($LASTEXITCODE -ne 0) { throw 'OAI git status failed' }

    $projectFiles = @(
        'README.md',
        'sources.lock',
        'local_ntn\README.md',
        'local_ntn\DEBUGGING_GUIDE.md',
        'local_ntn\export_stk_trace.py',
        'local_ntn\stk_trace.h',
        'local_ntn\stk_trace.c',
        'local_ntn\stk_trace_channel.c',
        'local_ntn\experiment.py',
        'local_ntn\prepare_local.py',
        'local_ntn\validate_dynamic.py',
        'local_ntn\run_local.sh',
        'local_ntn\run_regressions.sh',
        'local_ntn\test_trace.c',
        'local_ntn\test_trace_validation.c',
        'local_ntn\test_trace_validation.py',
        'local_ntn\test_real_iq.c',
        'local_ntn\test_real_iq.py',
        'local_ntn\test_local_setup.py'
    )
    $oaiFiles = @(
        'radio\rfsimulator\apply_channelmod.c',
        'radio\rfsimulator\rfsimulator.h',
        'radio\rfsimulator\CMakeLists.txt',
        'radio\rfsimulator\simulator.cpp',
        'radio\rfsimulator\stk_channel_model.c',
        'radio\rfsimulator\stk_trace.h',
        'radio\rfsimulator\stk_trace.c',
        'radio\rfsimulator\stk_trace_channel.c',
        'openair1\SIMULATION\TOOLS\sim.h',
        'radio\COMMON\common_lib.h',
        'radio\COMMON\common_lib.c',
        'executables\nr-ue.c',
        'executables\nr-ue-ru.c',
        'executables\nr-ue-ru.h'
    )

    Show-Command 'Copy relevant project and OAI source files into the step backup'
    foreach ($file in $projectFiles) { Backup-File $projectRoot $file $projectBackup }
    foreach ($file in $oaiFiles) { Backup-File $oaiRoot $file $oaiBackup }

    Show-Command 'Get-FileHash SHA256 for every backed-up source file'
    $hashes = Get-ChildItem -LiteralPath $projectBackup, $oaiBackup -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
            [pscustomobject]@{
                RelativePath = $_.FullName.Substring($backupRoot.Length + 1)
                SHA256 = $hash.Hash
            }
        }
    $hashes | Format-Table -AutoSize
    $hashes | Export-Csv -LiteralPath (Join-Path $backupRoot 'sha256.csv') -NoTypeInformation -Encoding utf8

    $manifest = [ordered]@{
        step = 0
        created_at = (Get-Date).ToString('o')
        project_root = $projectRoot
        project_commit = $projectCommit
        oai_root = '/home/duyaya/OAI/openairinterface5g'
        oai_commit = $oaiCommit
        project_files = $projectFiles
        oai_files = $oaiFiles
        contains_credentials = $false
        regression_command = 'OAI_UE_CONFIG=/home/duyaya/.local/share/oai-stk/ue.stk-20260923.conf bash local_ntn/run_regressions.sh'
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backupRoot 'baseline-manifest.json') -Encoding utf8

    @"
Rollback scope: files listed in baseline-manifest.json only.
Stop gNB and UE before restoring runtime source files.
Review every destination before copying; do not restore the whole OAI tree.
Project backup root: $projectBackup
OAI backup root: $oaiBackup
No UE credential file, database content, raw UE log, build output, or private key is included.
"@ | Set-Content -LiteralPath (Join-Path $backupRoot 'RESTORE-INSTRUCTIONS.txt') -Encoding utf8

    Show-Command "wsl.exe bash -lc 'cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project && OAI_UE_CONFIG=/home/duyaya/.local/share/oai-stk/ue.stk-20260923.conf bash local_ntn/run_regressions.sh'"
    wsl.exe bash -lc 'cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project && OAI_UE_CONFIG=/home/duyaya/.local/share/oai-stk/ue.stk-20260923.conf bash local_ntn/run_regressions.sh'
    $regressionExit = $LASTEXITCODE
    Write-Host "Regression exit code: $regressionExit"
    if ($regressionExit -ne 0) { throw "Baseline regression failed with exit code $regressionExit" }

    $result = [ordered]@{
        status = 'PASS'
        completed_at = (Get-Date).ToString('o')
        project_commit = $projectCommit
        oai_commit = $oaiCommit
        regression_exit_code = $regressionExit
        backup_root = $backupRoot
    }
    $result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backupRoot 'STEP00_DONE.json') -Encoding utf8
    Write-Host "`nSTEP 0 PASS" -ForegroundColor Green
    Write-Host "Backup and transcript: $backupRoot"
}
catch {
    $failure = [ordered]@{
        status = 'FAIL'
        failed_at = (Get-Date).ToString('o')
        error = $_.Exception.Message
        backup_root = $backupRoot
    }
    $failure | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backupRoot 'STEP00_FAILED.json') -Encoding utf8
    Write-Host "`nSTEP 0 FAILED: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Stop-Transcript
}

Read-Host 'The visible terminal will remain open for inspection. Press Enter when you want to close this script'
