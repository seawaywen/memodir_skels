@echo off
goto check_Permissions

:check_Permissions
    net session >nul 2>&1
    echo %errorLevel%
