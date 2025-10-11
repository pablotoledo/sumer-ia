# Build script for Windows portable executable
# Run this from Windows PowerShell

Write-Host "Installing dependencies..." -ForegroundColor Green
poetry install --with build

Write-Host "`nBuilding Windows executable..." -ForegroundColor Green
poetry run pyinstaller video_frame_capture.spec --clean

Write-Host "`nBuild complete!" -ForegroundColor Green
Write-Host "Executable location: dist\VideoFrameCapture.exe" -ForegroundColor Cyan

# Check if executable exists
if (Test-Path "dist\VideoFrameCapture.exe") {
    $size = (Get-Item "dist\VideoFrameCapture.exe").Length / 1MB
    Write-Host ("Executable size: {0:N2} MB" -f $size) -ForegroundColor Yellow
}
