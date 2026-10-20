@echo off
title Antigravity -> Claude Code Migrator
color 0B
cd /d "%~dp0"
python main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Hata] Program bir hatayla sonlandi.
    pause
)
