# Simple Windows build script using pip
# Requires Python 3.9+ installed on Windows

Write-Host "Installing dependencies with pip..." -ForegroundColor Green

# Install dependencies
python -m pip install --upgrade pip
python -m pip install PySide6>=6.6.0 opencv-python>=4.8.0 numpy>=1.24.0 Pillow>=10.0.0 cv2PySide6>=1.0.0 psutil>=5.9.0
python -m pip install pyinstaller>=6.4.0

Write-Host "`nBuilding Windows executable..." -ForegroundColor Green

# Build with PyInstaller
python -m PyInstaller video_frame_capture.spec --clean

Write-Host "`nBuild complete!" -ForegroundColor Green

# Check if executable exists
if (Test-Path "dist\VideoFrameCapture.exe") {
    $size = (Get-Item "dist\VideoFrameCapture.exe").Length / 1MB
    Write-Host ("Executable location: dist\VideoFrameCapture.exe") -ForegroundColor Cyan
    Write-Host ("Executable size: {0:N2} MB" -f $size) -ForegroundColor Yellow
} else {
    Write-Host "ERROR: Executable not found!" -ForegroundColor Red
}
