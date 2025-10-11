@echo off
REM Build script for Windows portable executable
REM Run this from Windows PowerShell or CMD, not from WSL

echo Installing dependencies...
poetry install --with build

echo Building Windows executable...
poetry run pyinstaller video_frame_capture.spec --clean

echo Build complete!
echo Executable location: dist\VideoFrameCapture.exe
pause
