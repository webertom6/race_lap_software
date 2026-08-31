@echo off
setlocal
title Race Lap App - close this window to stop
cd /d "%~dp0"

type "ascii\ascii-logo.txt"
type "ascii\ascii-name.txt"
echo.
echo Race Lap App
echo This window IS the app - closing it stops the server.
echo Don't click inside this window while it's running: it can pause the
echo app (press Enter if it looks frozen).
echo.
set /p _unused="Press ENTER to start..."

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo uv not found, attempting to install it...
    powershell -NoProfile -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    where uv >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: could not find or install uv.
        echo This first-time setup step needs an internet connection.
        echo If uv was just installed, close this window and double-click
        echo this script again so the new PATH takes effect.
        echo If you already have uv installed, make sure it is on your PATH.
        echo.
        pause
        exit /b 1
    )
)

set RACE_LAP_LAUNCHER=1
uv sync
if %errorlevel% neq 0 (
    echo.
    echo ERROR: uv sync failed. Check the messages above.
    pause
    exit /b 1
)

uv run app.py

echo.
echo The app has stopped.
pause
