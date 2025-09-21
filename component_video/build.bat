@echo off
REM =============================================================================
REM Simple Build Script for Windows - Video Frame Capture
REM Compatible with Windows Command Prompt
REM =============================================================================

echo.
echo 🚀 Video Frame Capture - Build para Windows
echo ============================================
echo.

REM Verificar Poetry
where poetry >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Poetry no está instalado
    echo Instala desde: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

REM Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no está instalado
    echo Descarga desde: https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Dependencias verificadas

REM Instalar dependencias
echo.
echo [INFO] Instalando dependencias...
poetry install
if %errorlevel% neq 0 (
    echo ❌ Error instalando dependencias
    pause
    exit /b 1
)

REM Instalar PyInstaller si no está
poetry run pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando PyInstaller...
    poetry add --group dev pyinstaller
)

REM Limpiar builds anteriores
echo.
echo [INFO] Limpiando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
del /q *.spec >nul 2>&1

REM Build con PyInstaller
echo.
echo [INFO] Construyendo aplicación...
poetry run pyinstaller ^
    --name "VideoFrameCapture" ^
    --onefile ^
    --windowed ^
    --add-data "src;src" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "PySide6.QtMultimedia" ^
    --hidden-import "PySide6.QtMultimediaWidgets" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --exclude-module "tkinter" ^
    --exclude-module "matplotlib" ^
    --exclude-module "scipy" ^
    --exclude-module "pandas" ^
    src\video_frame_capture\main.py

if %errorlevel% neq 0 (
    echo ❌ Build falló
    pause
    exit /b 1
)

REM Verificar que el ejecutable se creó
if not exist "dist\VideoFrameCapture.exe" (
    echo ❌ Ejecutable no encontrado
    pause
    exit /b 1
)

REM Mostrar información del build
echo.
echo ✅ ¡Build completado!
echo.
echo 📦 Ejecutable: dist\VideoFrameCapture.exe

REM Calcular tamaño (aproximado)
for %%A in (dist\VideoFrameCapture.exe) do (
    set size=%%~zA
    set /a sizeMB=!size!/1048576
)
echo 📊 Tamaño: %sizeMB% MB (aproximado)

REM Crear paquete de distribución
echo.
echo [INFO] Creando paquete de distribución...
mkdir "dist\VideoFrameCapture_Package" 2>nul
copy "dist\VideoFrameCapture.exe" "dist\VideoFrameCapture_Package\"

REM Crear README
echo Video Frame Capture v1.0.0 > "dist\VideoFrameCapture_Package\README.txt"
echo ========================== >> "dist\VideoFrameCapture_Package\README.txt"
echo. >> "dist\VideoFrameCapture_Package\README.txt"
echo Professional video frame capture application >> "dist\VideoFrameCapture_Package\README.txt"
echo. >> "dist\VideoFrameCapture_Package\README.txt"
echo To run: Double-click VideoFrameCapture.exe >> "dist\VideoFrameCapture_Package\README.txt"
echo. >> "dist\VideoFrameCapture_Package\README.txt"
echo Requirements: Windows 10 or later >> "dist\VideoFrameCapture_Package\README.txt"

echo.
echo 🎉 ¡Completado!
echo.
echo 📁 Archivos en: dist\
echo 🚀 Para usar: Ejecuta dist\VideoFrameCapture.exe
echo 📦 Para distribuir: Comprime dist\VideoFrameCapture_Package\
echo.

REM Preguntar si abrir la carpeta
set /p openFolder="¿Abrir carpeta dist? (S/N): "
if /i "%openFolder%"=="S" (
    explorer dist
)

echo.
echo Presiona cualquier tecla para salir...
pause >nul