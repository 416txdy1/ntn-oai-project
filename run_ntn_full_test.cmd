@echo off
setlocal
chcp 65001 >nul
title NTN full acceptance test
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ntn_test_launcher\launch.ps1" %*
set "TEST_EXIT=%ERRORLEVEL%"
echo.
echo Test launcher exit code: %TEST_EXIT%
pause
exit /b %TEST_EXIT%
