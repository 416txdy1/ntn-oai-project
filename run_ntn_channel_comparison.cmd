@echo off
setlocal
chcp 65001 >nul
title NTN Channel and Live Video Comparison
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ntn_live_demo\launch_causal.ps1" %*
set "SUITE_EXIT=%ERRORLEVEL%"
echo.
echo Channel comparison exit code: %SUITE_EXIT%
echo 0 = supported, 2 = inconclusive, 1 = failure/interrupted.
pause
exit /b %SUITE_EXIT%
