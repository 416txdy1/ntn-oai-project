param(
    [string]$Distribution = 'Ubuntu-22.04',
    [string]$ProjectRoot = '/home/kayoko/ntn-workspaces/ntn-live-miso',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
try {
    $runner = Join-Path $PSScriptRoot 'full_test.py'
    Write-Host "WSL distribution: $Distribution"
    Write-Host "Independent project: $ProjectRoot"
    Write-Host 'This runs five continuous traffic cases, offline regressions, and original-platform checks.'
    Write-Host 'Keep this window open. Use Ctrl+C for controlled cancellation.'
    $linuxRunner = & wsl.exe -d $Distribution --exec wslpath -a ($runner.Replace('\', '/'))
    if ($LASTEXITCODE -ne 0 -or -not $linuxRunner) { throw 'Cannot access WSL or translate the runner path.' }
    $linuxRunner = ($linuxRunner -join "`n").Trim()
    $arguments = @('-d', $Distribution, '--cd', $ProjectRoot, '--exec', 'sudo', 'python3', '-u', $linuxRunner, '--root', $ProjectRoot)
    if ($CheckOnly) { $arguments += '--check-only' }
    & wsl.exe @arguments
    exit $LASTEXITCODE
} catch {
    Write-Host "Launcher failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
