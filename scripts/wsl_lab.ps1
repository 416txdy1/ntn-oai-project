# 在 Windows 主源码目录中调用 WSL 的 Linux 运行副本。
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('sync','build','test','up','preflight','smoke-static','smoke-dynamic','full-pass','status','stop')]
    [string]$Action,
    [string]$Distribution = 'Ubuntu-22.04',
    [string]$RuntimeProject,
    [ValidateRange(120,7200)][int]$MaxWallSeconds = 1800
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeProject) {
    $configPath = Join-Path $projectRoot '.runtime\wsl-target.json'
    if (-not (Test-Path -LiteralPath $configPath)) {
        throw '请传入 -RuntimeProject 指定已配置的 WSL 项目目录，或创建 .runtime/wsl-target.json。'
    }
    $RuntimeProject = (Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json).runtime_project
}
if (-not $RuntimeProject.StartsWith('/') -or $RuntimeProject.StartsWith('/mnt/')) {
    throw 'RuntimeProject 必须是 WSL Linux 文件系统中的绝对项目路径。'
}
$linuxSource = (& wsl.exe -d $Distribution -- wslpath -a -u ($projectRoot.Replace('\', '/')) | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw '无法转换 Windows 项目路径。' }
Write-Host "Source: $projectRoot"
Write-Host "Runtime: $RuntimeProject"
Write-Host "Action: $Action (full-pass baseline: hermite, timing assist off)"
& wsl.exe -d $Distribution -u root -- bash "$linuxSource/scripts/wsl_lab.sh" $Action $linuxSource $RuntimeProject $MaxWallSeconds
exit $LASTEXITCODE