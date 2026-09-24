param([string]$LogName = 'debug-session.log')
$Host.UI.RawUI.WindowTitle = 'NTN OAI - ' + $LogName
Set-Location 'E:\jingwenpeng\2026autumn\ntn-oai-project'
Write-Host 'NTN OAI debug transcript (updates live). No git commits.' -ForegroundColor Cyan
Get-Content -LiteralPath (Join-Path $PSScriptRoot $LogName) -Wait
