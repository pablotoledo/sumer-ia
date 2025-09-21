# =============================================================================
# PowerShell Build Script - Video Frame Capture
# Compatible con Windows 10/11 y PowerShell Core
# =============================================================================

param(
    [switch]$Clean,
    [switch]$Debug,
    [switch]$Help
)

# Colores para output
$ColorInfo = "Cyan"
$ColorSuccess = "Green"
$ColorError = "Red"
$ColorWarning = "Yellow"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Help {
    Write-ColorOutput "🚀 Video Frame Capture - Build Script para Windows" $ColorInfo
    Write-ColorOutput "=================================================" $ColorInfo
    Write-Host ""
    Write-ColorOutput "Uso:" $ColorInfo
    Write-ColorOutput "  .\build.ps1 [-Clean] [-Debug] [-Help]" "White"
    Write-Host ""
    Write-ColorOutput "Opciones:" $ColorInfo
    Write-ColorOutput "  -Clean    Limpiar builds anteriores" "White"
    Write-ColorOutput "  -Debug    Build en modo debug (incluir console)" "White"
    Write-ColorOutput "  -Help     Mostrar esta ayuda" "White"
    Write-Host ""
    Write-ColorOutput "Ejemplos:" $ColorInfo
    Write-ColorOutput "  .\build.ps1                # Build normal" "White"
    Write-ColorOutput "  .\build.ps1 -Clean         # Build limpio" "White"
    Write-ColorOutput "  .\build.ps1 -Debug         # Build con console" "White"
}

function Test-Dependencies {
    Write-ColorOutput "[INFO] Verificando dependencias..." $ColorInfo

    # Verificar Python
    try {
        $pythonVersion = python --version 2>$null
        if (-not $pythonVersion) {
            $pythonVersion = python3 --version 2>$null
        }
        if ($pythonVersion) {
            Write-ColorOutput "[SUCCESS] Python encontrado: $pythonVersion" $ColorSuccess
        } else {
            throw "Python no encontrado"
        }
    } catch {
        Write-ColorOutput "[ERROR] Python no está instalado" $ColorError
        Write-ColorOutput "Descarga desde: https://python.org/downloads/" $ColorWarning
        exit 1
    }

    # Verificar Poetry
    try {
        $poetryVersion = poetry --version 2>$null
        if ($poetryVersion) {
            Write-ColorOutput "[SUCCESS] Poetry encontrado: $poetryVersion" $ColorSuccess
        } else {
            throw "Poetry no encontrado"
        }
    } catch {
        Write-ColorOutput "[ERROR] Poetry no está instalado" $ColorError
        Write-ColorOutput "Instala con: (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -" $ColorWarning
        exit 1
    }

    # Verificar pyproject.toml
    if (-not (Test-Path "pyproject.toml")) {
        Write-ColorOutput "[ERROR] No se encontró pyproject.toml" $ColorError
        Write-ColorOutput "Ejecuta este script desde la raíz del proyecto" $ColorWarning
        exit 1
    }

    Write-ColorOutput "[SUCCESS] Dependencias verificadas" $ColorSuccess
}

function Install-Dependencies {
    Write-ColorOutput "[INFO] Instalando dependencias..." $ColorInfo

    try {
        poetry install
        Write-ColorOutput "[SUCCESS] Dependencias instaladas" $ColorSuccess
    } catch {
        Write-ColorOutput "[ERROR] Falló la instalación de dependencias" $ColorError
        exit 1
    }

    # Instalar PyInstaller si no está
    try {
        poetry run pyinstaller --version >$null 2>&1
        Write-ColorOutput "[SUCCESS] PyInstaller disponible" $ColorSuccess
    } catch {
        Write-ColorOutput "[INFO] Instalando PyInstaller..." $ColorInfo
        poetry add --group dev pyinstaller
    }
}

function Clear-PreviousBuilds {
    if ($Clean) {
        Write-ColorOutput "[INFO] Limpiando builds anteriores..." $ColorInfo

        $foldersToRemove = @("dist", "build")
        $filesToRemove = @("*.spec")

        foreach ($folder in $foldersToRemove) {
            if (Test-Path $folder) {
                Remove-Item -Recurse -Force $folder
                Write-ColorOutput "[INFO] Eliminado: $folder" $ColorInfo
            }
        }

        foreach ($pattern in $filesToRemove) {
            Get-ChildItem -Path . -Name $pattern | ForEach-Object {
                Remove-Item -Force $_
                Write-ColorOutput "[INFO] Eliminado: $_" $ColorInfo
            }
        }

        Write-ColorOutput "[SUCCESS] Build limpiado" $ColorSuccess
    }
}

function Build-Application {
    Write-ColorOutput "[INFO] Construyendo aplicación para Windows..." $ColorInfo

    # Configurar argumentos
    $args = @(
        "--name", "VideoFrameCapture",
        "--onefile",
        "--add-data", "src;src",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtMultimedia",
        "--hidden-import", "PySide6.QtMultimediaWidgets",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas"
    )

    # Agregar windowed o console según modo debug
    if ($Debug) {
        $args += "--console"
        Write-ColorOutput "[INFO] Modo debug activado (incluye console)" $ColorWarning
    } else {
        $args += "--windowed"
    }

    # Agregar ícono si existe
    if (Test-Path "assets\icon.ico") {
        $args += "--icon", "assets\icon.ico"
    }

    # Archivo principal
    $args += "src\video_frame_capture\main.py"

    try {
        Write-ColorOutput "[INFO] Ejecutando PyInstaller..." $ColorInfo
        poetry run pyinstaller @args

        if (Test-Path "dist\VideoFrameCapture.exe") {
            $size = [math]::Round((Get-Item "dist\VideoFrameCapture.exe").Length / 1MB, 1)
            Write-ColorOutput "[SUCCESS] ¡Build completado!" $ColorSuccess
            Write-ColorOutput "[INFO] Ejecutable: dist\VideoFrameCapture.exe" $ColorInfo
            Write-ColorOutput "[INFO] Tamaño: $size MB" $ColorInfo

            Create-WindowsPackage
        } else {
            throw "Ejecutable no encontrado"
        }
    } catch {
        Write-ColorOutput "[ERROR] Build falló: $($_.Exception.Message)" $ColorError
        exit 1
    }
}

function Create-WindowsPackage {
    Write-ColorOutput "[INFO] Creando paquete de distribución..." $ColorInfo

    # Crear directorio de release
    $releaseDir = "dist\VideoFrameCapture_Windows"
    if (Test-Path $releaseDir) {
        Remove-Item -Recurse -Force $releaseDir
    }
    New-Item -ItemType Directory -Path $releaseDir | Out-Null

    # Copiar ejecutable
    Copy-Item "dist\VideoFrameCapture.exe" "$releaseDir\"

    # Crear README para Windows
    $readmeContent = @"
Video Frame Capture v1.0.0
===========================

Professional desktop application for video frame capture and export.

Installation:
1. Extract all files to a folder
2. Double-click VideoFrameCapture.exe to run

System Requirements:
- Windows 10 or Windows 11
- DirectX compatible graphics
- 4GB RAM minimum

Features:
- Load and play video files (MP4, AVI, MOV, MKV, WMV)
- Capture frames at any timestamp
- Export selected frames as ZIP archive
- Professional thumbnail gallery with selection
- Timeline navigation with precise seeking

For support, visit:
https://github.com/your-repo/video-frame-capture

Built with PyInstaller on Windows
"@

    $readmeContent | Out-File -FilePath "$releaseDir\README.txt" -Encoding UTF8

    # Crear script de ejecución
    $runScript = @"
@echo off
echo Starting Video Frame Capture...
VideoFrameCapture.exe
if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause >nul
)
"@

    $runScript | Out-File -FilePath "$releaseDir\Run_VideoFrameCapture.bat" -Encoding ASCII

    Write-ColorOutput "[SUCCESS] Paquete creado en: $releaseDir" $ColorSuccess

    # Crear ZIP si 7-Zip está disponible
    if (Get-Command "7z" -ErrorAction SilentlyContinue) {
        Write-ColorOutput "[INFO] Creando archivo ZIP..." $ColorInfo
        $zipFile = "dist\VideoFrameCapture_Windows_v1.0.0.zip"
        7z a "$zipFile" "$releaseDir\*" >$null
        if (Test-Path $zipFile) {
            Write-ColorOutput "[SUCCESS] ZIP creado: $zipFile" $ColorSuccess
        }
    }
}

function Show-FinalInstructions {
    Write-Host ""
    Write-ColorOutput "🎉 ¡Build completado para Windows!" $ColorSuccess
    Write-ColorOutput "===================================" $ColorSuccess
    Write-Host ""
    Write-ColorOutput "📦 Archivos generados:" $ColorInfo
    Write-ColorOutput "   - dist\VideoFrameCapture.exe (ejecutable principal)" "White"
    Write-ColorOutput "   - dist\VideoFrameCapture_Windows\ (paquete completo)" "White"
    Write-Host ""
    Write-ColorOutput "🚀 Para usar:" $ColorInfo
    Write-ColorOutput "   Doble click en VideoFrameCapture.exe" "White"
    Write-Host ""
    Write-ColorOutput "📱 Para distribuir:" $ColorInfo
    Write-ColorOutput "   Comparte la carpeta VideoFrameCapture_Windows" "White"
    Write-ColorOutput "   o el archivo ZIP si está disponible" "White"
    Write-Host ""
    Write-ColorOutput "💡 Notas:" $ColorInfo
    Write-ColorOutput "   - No requiere Python instalado" "White"
    Write-ColorOutput "   - Incluye todas las dependencias" "White"
    Write-ColorOutput "   - Compatible con Windows 10/11" "White"
    Write-Host ""
}

# Función principal
function Main {
    if ($Help) {
        Show-Help
        return
    }

    Write-ColorOutput "🚀 Video Frame Capture - Build Script para Windows" $ColorInfo
    Write-ColorOutput "===================================================" $ColorInfo
    Write-Host ""

    Test-Dependencies
    Install-Dependencies
    Clear-PreviousBuilds
    Build-Application
    Show-FinalInstructions
}

# Ejecutar main
try {
    Main
} catch {
    Write-ColorOutput "[ERROR] Error inesperado: $($_.Exception.Message)" $ColorError
    exit 1
}