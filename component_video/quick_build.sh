#!/bin/bash

# =============================================================================
# Quick Build Script - Video Frame Capture
# =============================================================================
# Script simple para hacer builds rápidos durante desarrollo

set -e

echo "🚀 Quick Build - Video Frame Capture"
echo "===================================="

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Función de log
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Verificar Poetry
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry no está instalado"
    exit 1
fi

# Instalar dependencias si es necesario
log "Verificando dependencias..."
poetry install

# Instalar PyInstaller si no está
if ! poetry run pyinstaller --version &> /dev/null; then
    log "Instalando PyInstaller..."
    poetry add --group dev pyinstaller
fi

# Limpiar builds anteriores
log "Limpiando builds anteriores..."
rm -rf dist build *.spec

# Detectar plataforma
case "$(uname -s)" in
    Darwin*)    PLATFORM="macOS" ;;
    Linux*)     PLATFORM="Linux" ;;
    *)          PLATFORM="Unknown" ;;
esac

log "Construyendo para $PLATFORM..."

# Build simple con PyInstaller
poetry run pyinstaller \
    --name "VideoFrameCapture" \
    --onefile \
    --windowed \
    --add-data "src:src" \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "PySide6.QtMultimedia" \
    --hidden-import "PySide6.QtMultimediaWidgets" \
    --hidden-import "cv2" \
    --hidden-import "numpy" \
    --exclude-module "tkinter" \
    --exclude-module "matplotlib" \
    --exclude-module "scipy" \
    --exclude-module "pandas" \
    src/video_frame_capture/main.py

if [ $? -eq 0 ]; then
    success "¡Build completado!"

    # Mostrar información
    log "Ubicación: dist/VideoFrameCapture"

    if [ -f "dist/VideoFrameCapture" ]; then
        SIZE=$(du -sh dist/VideoFrameCapture | cut -f1)
        log "Tamaño: $SIZE"
    fi

    # En macOS, intentar crear .app bundle básico
    if [ "$PLATFORM" = "macOS" ]; then
        log "Creando .app bundle..."
        mkdir -p "dist/VideoFrameCapture.app/Contents/MacOS"
        mv "dist/VideoFrameCapture" "dist/VideoFrameCapture.app/Contents/MacOS/"

        # Crear Info.plist básico
        cat > "dist/VideoFrameCapture.app/Contents/Info.plist" << EOF
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
</dict>
</plist>
EOF
        success ".app bundle creado en dist/VideoFrameCapture.app"
    fi

    echo ""
    echo "🎉 ¡Listo para usar!"
    echo "   Ejecutable en: dist/"
else
    echo "❌ Build falló"
    exit 1
fi