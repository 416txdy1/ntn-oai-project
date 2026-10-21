@echo off
setlocal
chcp 65001 >nul
title NTN Repeated Handover Demo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ntn_live_demo\launch_replay.ps1" %*
set "REPLAY_EXIT=%ERRORLEVEL%"
echo.
echo Handover replay exit code: %REPLAY_EXIT%
pause
exit /b %REPLAY_EXIT%
