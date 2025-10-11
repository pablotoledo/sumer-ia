@echo off
REM WhisperX CLI Helper Script for Windows
REM Simplifies running the transcribe_cli.py script with uv

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Load .env file if it exists
if exist "%SCRIPT_DIR%.env" (
    for /f "usebackq tokens=*" %%a in ("%SCRIPT_DIR%.env") do (
        set "line=%%a"
        REM Skip comments and empty lines
        if not "!line:~0,1!"=="#" if not "!line!"=="" (
            set "%%a"
        )
    )
)

REM Run the CLI with uv
uv run python "%SCRIPT_DIR%transcribe_cli.py" %*
