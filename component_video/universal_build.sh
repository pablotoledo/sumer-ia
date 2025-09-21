#!/bin/bash

# =============================================================================
# Universal Build Script - Video Frame Capture
# Compatible con: macOS, Linux, Windows (Git Bash/WSL)
# =============================================================================

set -e

# Detectar sistema operativo y configurar variables
detect_os() {
    case "$(uname -s 2>/dev/null || echo Windows)" in
        Darwin*)
            OS="macos"
            EXE_EXT=""
            APP_BUNDLE=true
            ;;
        Linux*)
            OS="linux"
            EXE_EXT=""
            APP_BUNDLE=false
            # Detectar distribución
            if command -v apt-get >/dev/null 2>&1; then
                DISTRO="debian"
            elif command -v yum >/dev/null 2>&1; then
                DISTRO="redhat"
            elif command -v pacman >/dev/null 2>&1; then
                DISTRO="arch"
            else
                DISTRO="generic"
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*|Windows*)
            OS="windows"
            EXE_EXT=".exe"
            APP_BUNDLE=false
            ;;
        *)
            echo "❌ Sistema operativo no soportado: $(uname -s 2>/dev/null || echo Unknown)"
            exit 1
            ;;
    esac
}

# Función de logging universal (sin colores en Windows)
log() {
    if [[ "$OS" == "windows" ]]; then
        echo "[INFO] $1"
    else
        echo -e "\033[0;34m[INFO]\033[0m $1"
    fi
}

success() {
    if [[ "$OS" == "windows" ]]; then
        echo "[SUCCESS] $1"
    else
        echo -e "\033[0;32m[SUCCESS]\033[0m $1"
    fi
}

error() {
    if [[ "$OS" == "windows" ]]; then
        echo "[ERROR] $1"
    else
        echo -e "\033[0;31m[ERROR]\033[0m $1"
    fi
}

# Verificar dependencias según el OS
check_dependencies() {
    log "Verificando dependencias para $OS..."

    # Verificar Python
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        error "Python no está instalado"
        case $OS in
            "macos")
                echo "Instala con: brew install python3"
                ;;
            "linux")
                echo "Instala con: sudo apt install python3 python3-pip  # Ubuntu/Debian"
                echo "          o: sudo yum install python3 python3-pip  # CentOS/RHEL"
                ;;
            "windows")
                echo "Descarga desde: https://python.org/downloads/"
                ;;
        esac
        exit 1
    fi

    # Determinar comando Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    # Verificar Poetry
    if ! command -v poetry >/dev/null 2>&1; then
        error "Poetry no está instalado"
        echo "Instala con:"
        case $OS in
            "windows")
                echo "  (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -"
                ;;
            *)
                echo "  curl -sSL https://install.python-poetry.org | $PYTHON_CMD -"
                ;;
        esac
        exit 1
    fi

    # Verificar que estemos en el directorio correcto
    if [ ! -f "pyproject.toml" ]; then
        error "No se encontró pyproject.toml. Ejecuta desde la raíz del proyecto."
        exit 1
    fi

    success "Dependencias verificadas"
}

# Instalar dependencias específicas del OS
install_os_dependencies() {
    log "Instalando dependencias específicas para $OS..."

    case $OS in
        "linux")
            # Dependencias para Qt/PySide6 en Linux
            log "Verificando dependencias de sistema para Linux..."

            # Lista de paquetes necesarios según la distribución
            case $DISTRO in
                "debian")
                    PACKAGES="libgl1-mesa-glx libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0"
                    if ! dpkg -l $PACKAGES >/dev/null 2>&1; then
                        log "Instalando dependencias del sistema..."
                        sudo apt-get update
                        sudo apt-get install -y $PACKAGES
                    fi
                    ;;
                "redhat")
                    log "Para CentOS/RHEL, instala: sudo yum install mesa-libGL libxcb"
                    ;;
                *)
                    log "Distribución no reconocida, puede necesitar paquetes adicionales"
                    ;;
            esac
            ;;
        "windows")
            log "Windows detectado - las dependencias se instalan automáticamente"
            ;;
        "macos")
            log "macOS detectado - las dependencias se instalan automáticamente"
            ;;
    esac
}

# Configurar PyInstaller según el OS
configure_pyinstaller() {
    local extra_args=""

    case $OS in
        "windows")
            extra_args="--icon=assets/icon.ico"
            ;;
        "macos")
            extra_args="--icon=assets/icon.icns"
            ;;
        "linux")
            extra_args="--icon=assets/icon.png"
            ;;
    esac

    echo "$extra_args"
}

# Crear archivos de configuración específicos
create_os_configs() {
    case $OS in
        "windows")
            # Crear .bat file para Windows
            cat > "run_build.bat" << 'EOF'
@echo off
echo Building Video Frame Capture for Windows...
call poetry install
call poetry run pyinstaller --name "VideoFrameCapture" --onefile --windowed --add-data "src;src" --hidden-import "PySide6.QtCore" --hidden-import "PySide6.QtGui" --hidden-import "PySide6.QtWidgets" --hidden-import "PySide6.QtMultimedia" --hidden-import "PySide6.QtMultimediaWidgets" --hidden-import "cv2" --hidden-import "numpy" --exclude-module "tkinter" --exclude-module "matplotlib" src/video_frame_capture/main.py
echo Build completed! Check dist/ folder
pause
EOF
            log "Archivo run_build.bat creado para Windows"
            ;;
        "linux")
            # Crear .desktop file para Linux
            cat > "VideoFrameCapture.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Video Frame Capture
Comment=Professional video frame capture application
Exec=${PWD}/dist/VideoFrameCapture
Icon=${PWD}/assets/icon.png
Terminal=false
Categories=AudioVideo;Video;
EOF
            log "Archivo .desktop creado para Linux"
            ;;
    esac
}

# Build principal
build_app() {
    log "Iniciando build para $OS..."

    # Instalar dependencias de Poetry
    log "Instalando dependencias de Python..."
    poetry install

    # Agregar PyInstaller si no está
    if ! poetry run pyinstaller --version >/dev/null 2>&1; then
        log "Instalando PyInstaller..."
        poetry add --group dev pyinstaller
    fi

    # Limpiar builds anteriores
    log "Limpiando builds anteriores..."
    rm -rf dist build *.spec 2>/dev/null || true

    # Configurar argumentos específicos del OS
    local icon_args=$(configure_pyinstaller)

    # Determinar el separador de datos según el OS
    local data_separator
    if [[ "$OS" == "windows" ]]; then
        data_separator=";"
    else
        data_separator=":"
    fi

    # Build con PyInstaller
    log "Ejecutando PyInstaller..."

    # Crear comando base
    local cmd="poetry run pyinstaller"
    cmd="$cmd --name VideoFrameCapture${EXE_EXT}"
    cmd="$cmd --onefile"
    cmd="$cmd --windowed"
    cmd="$cmd --add-data src${data_separator}src"
    cmd="$cmd --hidden-import PySide6.QtCore"
    cmd="$cmd --hidden-import PySide6.QtGui"
    cmd="$cmd --hidden-import PySide6.QtWidgets"
    cmd="$cmd --hidden-import PySide6.QtMultimedia"
    cmd="$cmd --hidden-import PySide6.QtMultimediaWidgets"
    cmd="$cmd --hidden-import cv2"
    cmd="$cmd --hidden-import numpy"
    cmd="$cmd --exclude-module tkinter"
    cmd="$cmd --exclude-module matplotlib"
    cmd="$cmd --exclude-module scipy"
    cmd="$cmd --exclude-module pandas"

    # Agregar ícono si existe
    if [[ -n "$icon_args" ]]; then
        cmd="$cmd $icon_args"
    fi

    cmd="$cmd src/video_frame_capture/main.py"

    # Ejecutar comando
    eval $cmd

    if [ $? -eq 0 ]; then
        success "¡Build completado!"

        # Mostrar información del build
        local executable="dist/VideoFrameCapture${EXE_EXT}"
        if [ -f "$executable" ]; then
            local size
            if command -v du >/dev/null 2>&1; then
                size=$(du -sh "$executable" 2>/dev/null | cut -f1 || echo "Unknown")
            else
                size="Unknown"
            fi
            log "Ejecutable: $executable"
            log "Tamaño: $size"
        fi

        # Crear estructura específica del OS
        post_build_setup
    else
        error "Build falló"
        exit 1
    fi
}

# Configuración post-build específica del OS
post_build_setup() {
    case $OS in
        "macos")
            if [[ "$APP_BUNDLE" == true ]]; then
                log "Creando App Bundle para macOS..."
                create_macos_bundle
            fi
            ;;
        "linux")
            log "Configurando ejecutable para Linux..."
            chmod +x "dist/VideoFrameCapture"
            create_os_configs
            ;;
        "windows")
            log "Configurando ejecutable para Windows..."
            create_os_configs
            ;;
    esac
}

# Crear App Bundle para macOS
create_macos_bundle() {
    local bundle_dir="dist/VideoFrameCapture.app"
    mkdir -p "$bundle_dir/Contents/MacOS"
    mv "dist/VideoFrameCapture" "$bundle_dir/Contents/MacOS/"

    # Crear Info.plist
    cat > "$bundle_dir/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>VideoFrameCapture</string>
    <key>CFBundleIdentifier</key>
    <string>com.videocapture.app</string>
    <key>CFBundleName</key>
    <string>Video Frame Capture</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>This app processes video files for frame capture.</string>
</dict>
</plist>
EOF

    success "App Bundle creado: $bundle_dir"
}

# Mostrar instrucciones finales
show_final_instructions() {
    echo ""
    echo "🎉 ¡Build completado para $OS!"
    echo "=================================="

    case $OS in
        "macos")
            echo "📦 Ejecutable: dist/VideoFrameCapture.app"
            echo "🚀 Para usar: Doble click en VideoFrameCapture.app"
            echo "📱 Para distribuir: Comprime VideoFrameCapture.app"
            ;;
        "linux")
            echo "📦 Ejecutable: dist/VideoFrameCapture"
            echo "🚀 Para usar: ./dist/VideoFrameCapture"
            echo "📱 Para distribuir: Crea un .tar.gz o .AppImage"
            echo "🔧 Desktop file: VideoFrameCapture.desktop (copia a ~/.local/share/applications/)"
            ;;
        "windows")
            echo "📦 Ejecutable: dist/VideoFrameCapture.exe"
            echo "🚀 Para usar: Doble click en VideoFrameCapture.exe"
            echo "📱 Para distribuir: Crea un instalador con NSIS o Inno Setup"
            echo "🔧 Batch file: run_build.bat (para rebuilds rápidos)"
            ;;
    esac

    echo ""
    echo "💡 Notas:"
    echo "   - El ejecutable incluye todas las dependencias"
    echo "   - No requiere Python instalado en el sistema destino"
    echo "   - Tamaño típico: 70-120MB según el OS"
}

# Función principal
main() {
    echo "🚀 Universal Build Script - Video Frame Capture"
    echo "=============================================="

    detect_os
    log "Sistema detectado: $OS"

    check_dependencies
    install_os_dependencies
    build_app
    show_final_instructions
}

# Ejecutar main
main "$@"