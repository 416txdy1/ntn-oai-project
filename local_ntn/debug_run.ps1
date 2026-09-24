param([Parameter(Mandatory=$true)][string]$Command, [string]$LogName = 'debug-checks.log')
$log = Join-Path $PSScriptRoot $LogName
('PS> ' + $Command) | Tee-Object -FilePath $log -Append
& ([scriptblock]::Create($Command)) 2>&1 | Tee-Object -FilePath $log -Append
('Exit code: ' + $LASTEXITCODE) | Tee-Object -FilePath $log -Append
