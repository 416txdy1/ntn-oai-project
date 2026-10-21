param([string]$LogName = 'debug-session.log')
$Host.UI.RawUI.WindowTitle = 'NTN OAI - ' + $LogName
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
Write-Host 'NTN OAI debug transcript (updates live). No git commits.' -ForegroundColor Cyan
Get-Content -LiteralPath (Join-Path $PSScriptRoot $LogName) -Wait
