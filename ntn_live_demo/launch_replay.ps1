param(
    [string]$Distribution = 'Ubuntu-22.04',
    [string]$ProjectRoot = '/home/kayoko/ntn-workspaces/ntn-live-miso',
    [ValidateSet('siso','miso4-subarray')][string]$SpatialMode = 'siso',
    [ValidateRange(1,8)][int]$QdWorkers = 8,
    [ValidateRange(1,8)][int]$Rounds = 4,
    [string]$Source,
    [switch]$SkipRegressions
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
try {
    if (-not $Source) {
        $configuration = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'media-source.local.json'),[Text.Encoding]::UTF8) | ConvertFrom-Json
        $Source = $configuration.source
    }
    $media = Get-Item -LiteralPath $Source
    if ($media.PSIsContainer) { throw 'Specify the exact audio/video file.' }
    $scriptPath = Join-Path $PSScriptRoot 'replay_handovers.py'
    $linuxScript = & wsl.exe -d $Distribution --exec wslpath -a ($scriptPath.Replace('\','/'))
    if ($LASTEXITCODE -ne 0) { throw 'Cannot access WSL experiment script.' }
    $linuxSource = & wsl.exe -d $Distribution --exec wslpath -a ($media.FullName.Replace('\','/'))
    if ($LASTEXITCODE -ne 0) { throw 'Cannot access video from WSL.' }
    $arguments = @('-d',$Distribution,'--exec','sudo','python3','-B','-u',($linuxScript -join "`n").Trim(),
        '--source',($linuxSource -join "`n").Trim(),'--rounds',[string]$Rounds,
        '--root',$ProjectRoot,'--spatial-mode',$SpatialMode,'--qd-workers',[string]$QdWorkers)
    if ($SkipRegressions) { $arguments += '--skip-regressions' }
    Write-Host "Repeated handover demo: $Rounds rounds; no fixed-channel waiting group."
    Write-Host 'Each round reconnects and replays the verified S06 -> S05 transition; this is not one continuous trajectory.'
    Write-Host 'Keep player OPEN, visible and unmuted. It restarts automatically BETWEEN rounds.'
    & wsl.exe @arguments
    exit $LASTEXITCODE
} catch {
    Write-Host "Handover replay failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
