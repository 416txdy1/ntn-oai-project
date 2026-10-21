param(
    [string]$Distribution = 'Ubuntu-22.04',
    [string]$ProjectRoot = '/home/kayoko/ntn-workspaces/ntn-live-miso',
    [ValidateSet('siso','miso4-subarray')][string]$SpatialMode = 'siso',
    [ValidateRange(1,8)][int]$QdWorkers = 8,
    [ValidateSet('static','firsthandover','full')][string]$Case = 'firsthandover',
    [switch]$Prepare,
    [switch]$Headless,
    [switch]$SkipRegressions,
    [string]$Source,
    [switch]$UseConfiguredSource
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
try {
    $demo = Join-Path $PSScriptRoot 'demo.py'
    $linuxDemo = & wsl.exe -d $Distribution --exec wslpath -a ($demo.Replace('\','/'))
    if ($LASTEXITCODE -ne 0) { throw 'Cannot access WSL demo files.' }
    $linuxDemo = ($linuxDemo -join "`n").Trim()
    if ($Prepare) {
        $prepareScript = $linuxDemo.Substring(0,$linuxDemo.LastIndexOf('/')) + '/prepare.py'
        & wsl.exe -d $Distribution --exec python3 -u $prepareScript
        if ($LASTEXITCODE -ne 0) { throw 'Ordinary-user dependency preparation failed.' }
    }
    Write-Host 'Keep this console and player open. Ctrl+C requests cleanup.'
    $arguments = @('-d',$Distribution,'--exec','sudo','python3','-u',$linuxDemo,'--case',$Case,
        '--root',$ProjectRoot,'--spatial-mode',$SpatialMode,'--qd-workers',[string]$QdWorkers)
    Write-Host "Independent runtime: $ProjectRoot; spatial mode: $SpatialMode; requested workers: $QdWorkers (SISO uses one)"
    if ($UseConfiguredSource -and -not $Source) {
        $configuration = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'media-source.local.json'),[Text.Encoding]::UTF8) | ConvertFrom-Json
        $Source = $configuration.source
    }
    if ($Source) {
        $resolvedSource = Get-Item -LiteralPath $Source
        if ($resolvedSource.PSIsContainer) {
            $videos = @(Get-ChildItem -LiteralPath $Source -File | Where-Object { $_.Extension -in '.mp4','.mkv','.mov','.webm' })
            if ($videos.Count -ne 1) { throw 'Source folder must contain exactly one video; otherwise specify the exact file.' }
            $resolvedSource = $videos[0]
        }
        $linuxSource = & wsl.exe -d $Distribution --exec wslpath -a ($resolvedSource.FullName.Replace('\','/'))
        if ($LASTEXITCODE -ne 0) { throw 'Cannot translate media source path.' }
        $arguments += @('--source',($linuxSource -join "`n").Trim())
    }
    if ($Source) {
        Write-Host "Live case: $Case. Windows Edge will play the UE-relayed video and audio."
        if ($Headless) { Write-Host 'Source playback uses a visible Windows player; Headless applies only to synthetic video.' }
    } else {
        Write-Host "Live case: $Case. A Linux browser window will display the UE stream."
    }
    if ($Headless) { $arguments += '--headless' }
    if ($SkipRegressions) { $arguments += '--skip-regressions' }
    & wsl.exe @arguments
    exit $LASTEXITCODE
} catch {
    Write-Host "Live demo launcher failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
