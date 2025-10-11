@echo off
REM FastAgent CLI Helper Script for Windows
REM Simplifies running the fastagent_cli.py script with uv

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Load .env file if exists
if exist "%SCRIPT_DIR%.env" (
    for /f "usebackq tokens=* delims=" %%a in ("%SCRIPT_DIR%.env") do (
        REM Skip comments and empty lines
        echo %%a | findstr /r "^#" >nul || echo %%a | findstr /r "^$" >nul || set %%a
    )
)

REM Run the CLI with uv
uv run python "%SCRIPT_DIR%fastagent_cli.py" %*
