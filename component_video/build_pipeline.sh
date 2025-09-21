#!/bin/bash

# =============================================================================
# Video Frame Capture - Cross-Platform Build Pipeline
# =============================================================================
# Este script genera binarios ejecutables para múltiples plataformas
# usando PyInstaller y Poetry
#
# Requisitos:
# - Poetry instalado
# - PyInstaller (se instala automáticamente)
# - Sistema operativo compatible (macOS, Linux, Windows)
#
# Uso:
#   ./build_pipeline.sh [platform] [--clean] [--debug]
#
# Plataformas soportadas:
#   - current: Construir solo para la plataforma actual
#   - all: Construir para todas las plataformas posibles desde el SO actual
#   - macos: Solo macOS (requiere macOS)
#   - linux: Solo Linux (requiere Linux)
#   - windows: Solo Windows (requiere Windows)
# =============================================================================

set -e  # Exit on any error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables globales
PROJECT_NAME="video-frame-capture"
APP_NAME="VideoFrameCapture"
VERSION="1.0.0"
BUILD_DIR="dist"
SPEC_DIR="build_specs"
PLATFORM=""
CLEAN_BUILD=false
DEBUG_MODE=false

# Detectar plataforma actual
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    CURRENT_PLATFORM="macos" ;;
        Linux*)     CURRENT_PLATFORM="linux" ;;
        CYGWIN*|MINGW*|MSYS*) CURRENT_PLATFORM="windows" ;;
        *)          CURRENT_PLATFORM="unknown" ;;
    esac
}

# Función de ayuda
show_help() {
    echo -e "${BLUE}Video Frame Capture - Build Pipeline${NC}"
    echo ""
    echo "Uso: $0 [PLATFORM] [OPTIONS]"
    echo ""
    echo "Plataformas:"
    echo "  current     Construir para la plataforma actual ($CURRENT_PLATFORM)"
    echo "  all         Construir para todas las plataformas posibles"
    echo "  macos       Solo macOS (requiere macOS)"
    echo "  linux       Solo Linux (requiere Linux)"
    echo "  windows     Solo Windows (requiere Windows)"
    echo ""
    echo "Opciones:"
    echo "  --clean     Limpiar builds anteriores"
    echo "  --debug     Modo debug (incluir console)"
    echo "  --help      Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 current                 # Build para plataforma actual"
    echo "  $0 all --clean             # Build limpio para todas las plataformas"
    echo "  $0 macos --debug           # Build debug para macOS"
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar dependencias
check_dependencies() {
    log_info "Verificando dependencias..."

    # Verificar Poetry
    if ! command -v poetry &> /dev/null; then
        log_error "Poetry no está instalado. Por favor instala Poetry primero."
        exit 1
    fi

    # Verificar que estemos en un proyecto Poetry
    if [ ! -f "pyproject.toml" ]; then
        log_error "No se encontró pyproject.toml. Ejecuta este script desde la raíz del proyecto."
        exit 1
    fi

    log_success "Dependencias verificadas"
}

# Instalar PyInstaller si no está disponible
install_pyinstaller() {
    log_info "Verificando PyInstaller..."

    if ! poetry run pyinstaller --version &> /dev/null; then
        log_info "Instalando PyInstaller..."
        poetry add --group dev pyinstaller
    fi

    log_success "PyInstaller disponible"
}

# Limpiar builds anteriores
clean_build() {
    if [ "$CLEAN_BUILD" = true ] || [ "$1" = "force" ]; then
        log_info "Limpiando builds anteriores..."
        rm -rf $BUILD_DIR
        rm -rf build
        rm -rf $SPEC_DIR
        rm -f *.spec
        log_success "Build limpiado"
    fi
}

# Crear directorios necesarios
create_directories() {
    mkdir -p $BUILD_DIR
    mkdir -p $SPEC_DIR
}

# Generar archivo .spec personalizado
generate_spec_file() {
    local platform=$1
    local spec_file="$SPEC_DIR/${APP_NAME}_${platform}.spec"

    log_info "Generando archivo spec para $platform..."

    # Determinar configuración según plataforma
    local console_flag="False"
    local icon_file=""
    local app_suffix=""

    if [ "$DEBUG_MODE" = true ]; then
        console_flag="True"
    fi

    case $platform in
        "macos")
            icon_file="# icon='assets/icon.icns',"
            app_suffix=".app"
            ;;
        "windows")
            icon_file="# icon='assets/icon.ico',"
            app_suffix=".exe"
            ;;
        "linux")
            icon_file="# icon='assets/icon.png',"
            app_suffix=""
            ;;
    esac

    cat > "$spec_file" << EOF
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Configuración del proyecto
project_root = Path('.')
main_script = project_root / 'src' / 'video_frame_capture' / 'main.py'

a = Analysis(
    [str(main_script)],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Incluir archivos de datos si los hay
        # ('src/video_frame_capture/assets', 'assets'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'cv2',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='${APP_NAME}${app_suffix}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=${console_flag},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    ${icon_file}
)

EOF

    # Agregar configuración específica para macOS App Bundle
    if [ "$platform" = "macos" ]; then
        cat >> "$spec_file" << EOF

app = BUNDLE(
    exe,
    name='${APP_NAME}.app',
    ${icon_file}
    bundle_identifier='com.videocapture.${PROJECT_NAME}',
    version='${VERSION}',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'NSAppleEventsUsageDescription': 'This app needs access to control other applications.',
        'NSCameraUsageDescription': 'This app needs access to camera for video capture.',
        'NSMicrophoneUsageDescription': 'This app needs access to microphone for audio capture.',
    },
)
EOF
    fi

    log_success "Archivo spec generado: $spec_file"
}

# Build para plataforma específica
build_platform() {
    local platform=$1

    log_info "Construyendo para $platform..."

    # Verificar compatibilidad
    if [ "$platform" != "$CURRENT_PLATFORM" ] && [ "$platform" != "current" ]; then
        log_warning "Construyendo para $platform desde $CURRENT_PLATFORM - puede no funcionar correctamente"
    fi

    # Generar archivo spec
    local spec_file="$SPEC_DIR/${APP_NAME}_${platform}.spec"
    generate_spec_file $platform

    # Construir con PyInstaller
    log_info "Ejecutando PyInstaller..."
    poetry run pyinstaller "$spec_file" \
        --distpath "$BUILD_DIR/$platform" \
        --workpath "build/$platform" \
        --clean \
        --noconfirm

    if [ $? -eq 0 ]; then
        log_success "Build completado para $platform"

        # Mostrar información del build
        local build_path="$BUILD_DIR/$platform"
        local build_size=$(du -sh "$build_path" 2>/dev/null | cut -f1 || echo "Unknown")
        log_info "Ubicación: $build_path"
        log_info "Tamaño: $build_size"

        # Crear ZIP del build
        create_release_package "$platform" "$build_path"
    else
        log_error "Build falló para $platform"
        return 1
    fi
}

# Crear paquete de release
create_release_package() {
    local platform=$1
    local build_path=$2

    log_info "Creando paquete de release para $platform..."

    local release_name="${APP_NAME}_v${VERSION}_${platform}"
    local release_path="$BUILD_DIR/${release_name}"

    # Crear directorio de release
    mkdir -p "$release_path"

    # Copiar ejecutable y archivos necesarios
    cp -r "$build_path"/* "$release_path/"

    # Crear README para el release
    cat > "$release_path/README.txt" << EOF
${APP_NAME} v${VERSION}
========================

Professional desktop application for video frame capture and export.

Built for: ${platform}
Build date: $(date)

Installation:
- Extract all files to a directory
- Run the ${APP_NAME} executable

System Requirements:
- Modern operating system (${platform})
- OpenGL support
- Sufficient RAM for video processing

For support and updates, visit:
https://github.com/your-repo/video-frame-capture

Generated by Video Frame Capture Build Pipeline
EOF

    # Crear ZIP del release
    cd "$BUILD_DIR"
    zip -r "${release_name}.zip" "${release_name}/"
    cd ..

    log_success "Paquete de release creado: $BUILD_DIR/${release_name}.zip"
}

# Build para todas las plataformas
build_all() {
    log_info "Construyendo para todas las plataformas compatibles..."

    local platforms=()

    # Determinar qué plataformas podemos construir
    case $CURRENT_PLATFORM in
        "macos")
            platforms=("macos")
            log_info "Desde macOS, solo se puede construir para macOS"
            ;;
        "linux")
            platforms=("linux")
            log_info "Desde Linux, solo se puede construir para Linux"
            ;;
        "windows")
            platforms=("windows")
            log_info "Desde Windows, solo se puede construir para Windows"
            ;;
        *)
            log_error "Plataforma no soportada: $CURRENT_PLATFORM"
            exit 1
            ;;
    esac

    local success_count=0
    local total_count=${#platforms[@]}

    for platform in "${platforms[@]}"; do
        if build_platform "$platform"; then
            ((success_count++))
        fi
    done

    log_info "Builds completados: $success_count/$total_count"

    if [ $success_count -eq $total_count ]; then
        log_success "¡Todos los builds completados exitosamente!"
    else
        log_warning "Algunos builds fallaron"
        exit 1
    fi
}

# Mostrar resumen final
show_summary() {
    log_info "=== RESUMEN DEL BUILD ==="
    log_info "Proyecto: $PROJECT_NAME v$VERSION"
    log_info "Plataforma de build: $CURRENT_PLATFORM"
    log_info "Directorio de salida: $BUILD_DIR"

    if [ -d "$BUILD_DIR" ]; then
        log_info "Archivos generados:"
        find "$BUILD_DIR" -name "*.zip" -o -name "$APP_NAME*" | head -10 | while read file; do
            local size=$(du -sh "$file" 2>/dev/null | cut -f1 || echo "?")
            log_info "  - $(basename "$file") ($size)"
        done
    fi

    log_success "¡Build pipeline completado!"
}

# Main function
main() {
    echo -e "${BLUE}🚀 Video Frame Capture - Build Pipeline${NC}"
    echo "========================================"

    detect_platform

    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            current|all|macos|linux|windows)
                PLATFORM="$1"
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --debug)
                DEBUG_MODE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Default platform
    if [ -z "$PLATFORM" ]; then
        PLATFORM="current"
    fi

    # Verificar dependencias
    check_dependencies
    install_pyinstaller

    # Limpiar si se solicitó
    clean_build

    # Crear directorios
    create_directories

    # Ejecutar build según plataforma
    case $PLATFORM in
        "current")
            build_platform "$CURRENT_PLATFORM"
            ;;
        "all")
            build_all
            ;;
        "macos"|"linux"|"windows")
            build_platform "$PLATFORM"
            ;;
        *)
            log_error "Plataforma no válida: $PLATFORM"
            show_help
            exit 1
            ;;
    esac

    # Mostrar resumen
    show_summary
}

# Ejecutar main con todos los argumentos
main "$@"