param(
    [string]$Distribution = 'Ubuntu-22.04',
    [ValidateRange(1,4)][int]$Repeats = 2,
    [string]$Source,
    [switch]$Smoke,
    [switch]$PrepareOnly
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
try {
    if (-not $Source) {
        $configuration = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'media-source.local.json'),[Text.Encoding]::UTF8) | ConvertFrom-Json
        $Source = $configuration.source
    }
    $media = Get-Item -LiteralPath $Source
    if ($media.PSIsContainer) { throw 'Specify one exact audio/video file.' }
    $scriptPath = Join-Path $PSScriptRoot 'causal.py'
    $linuxScript = & wsl.exe -d $Distribution --exec wslpath -a ($scriptPath.Replace('\','/'))
    if ($LASTEXITCODE -ne 0) { throw 'Cannot access WSL experiment script.' }
    $linuxSource = & wsl.exe -d $Distribution --exec wslpath -a ($media.FullName.Replace('\','/'))
    if ($LASTEXITCODE -ne 0) { throw 'Cannot access source media from WSL.' }
    $arguments = @('-d',$Distribution,'--exec','sudo','python3','-B','-u',($linuxScript -join "`n").Trim(),
        '--source',($linuxSource -join "`n").Trim(),'--repeats',[string]$Repeats)
    if ($Smoke) { $arguments += '--smoke' }
    if ($PrepareOnly) { $arguments += '--prepare-only' }
    Write-Host 'NTN audiovisual channel comparison: fixed / normal switching / IQ-channel intervention.'
    Write-Host 'Default: two repeats, six runs, two satellite switches in each dynamic long run.'
    Write-Host 'Allow approximately 1-3 hours. Keep console/player open; Ctrl+C requests owned cleanup.'
    Write-Host 'Exit 0 = supported; 2 = inconclusive; 1 = failure/interrupted. Smoke is NOT long-run validation.'
    & wsl.exe @arguments
    exit $LASTEXITCODE
} catch {
    Write-Host "Causal experiment launcher failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
