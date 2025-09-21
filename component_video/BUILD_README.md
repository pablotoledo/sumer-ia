# 🚀 Video Frame Capture - Build System Multiplataforma

Este proyecto incluye un sistema completo de build para generar ejecutables nativos en **macOS**, **Linux** y **Windows**.

## 📋 Requisitos Previos

- **Poetry** - Para gestión de dependencias
- **Python 3.9+** - Requisito del proyecto
- **PyInstaller** - Se instala automáticamente

### 🖥️ Requisitos por Sistema Operativo

#### macOS
- macOS 10.14+
- Xcode Command Line Tools: `xcode-select --install`

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip libgl1-mesa-glx libxcb-xinerama0
```

#### Linux (CentOS/RHEL)
```bash
sudo yum install python3 python3-pip mesa-libGL libxcb
```

#### Windows
- Windows 10/11
- Python desde [python.org](https://python.org/downloads/)
- Poetry desde [python-poetry.org](https://python-poetry.org/docs/#windows-powershell-install-instructions)

## 🛠️ Scripts Disponibles por Plataforma

### 🍎 **macOS / Linux**

#### 1. **Universal Build** (`universal_build.sh`) - ⭐ **Recomendado**
```bash
./universal_build.sh
```
- ✅ **Detección automática** del sistema operativo
- ✅ **Configuración específica** por plataforma
- ✅ **Dependencias automáticas** (Qt, OpenGL, etc.)
- ✅ **App bundles** nativos (.app, .desktop, etc.)

#### 2. **Quick Build** (`quick_build.sh`)
```bash
./quick_build.sh
```
- ✅ Build rápido para desarrollo
- ✅ Solo macOS/Linux

#### 3. **Advanced Pipeline** (`build_pipeline.sh`)
```bash
./build_pipeline.sh current --clean
```

### 🪟 **Windows**

#### 1. **PowerShell** (`build.ps1`) - ⭐ **Recomendado**
```powershell
.\build.ps1
.\build.ps1 -Clean
.\build.ps1 -Debug
```

#### 2. **Command Prompt** (`build.bat`)
```cmd
build.bat
```

#### 3. **Git Bash/WSL** (`universal_build.sh`)
```bash
./universal_build.sh
```

## 📁 Estructura de Output por Plataforma

### 🍎 **macOS**
```
dist/
├── VideoFrameCapture              # Ejecutable standalone
└── VideoFrameCapture.app/         # App Bundle nativo
    ├── Contents/
    │   ├── Info.plist             # Metadatos
    │   └── MacOS/
    │       └── VideoFrameCapture  # Ejecutable
```

### 🐧 **Linux**
```
dist/
├── VideoFrameCapture              # Ejecutable
├── VideoFrameCapture.desktop      # Desktop entry
└── VideoFrameCapture_Package/     # Carpeta de distribución
    ├── VideoFrameCapture
    └── README.txt
```

### 🪟 **Windows**
```
dist/
├── VideoFrameCapture.exe          # Ejecutable
├── VideoFrameCapture_Package/     # Carpeta de distribución
│   ├── VideoFrameCapture.exe
│   ├── README.txt
│   └── Run_VideoFrameCapture.bat
└── VideoFrameCapture_Windows_v1.0.0.zip  # ZIP de distribución
```

## ⚙️ Configuración

### build_config.yaml
Archivo de configuración para personalizar builds:

```yaml
app:
  name: "VideoFrameCapture"
  version: "1.0.0"

build:
  output_dir: "dist"
  use_upx: true

icons:
  macos: "assets/icon.icns"
  windows: "assets/icon.ico"
```

## 🎯 Ejemplos de Uso

### Desarrollo Rápido
```bash
# Build rápido para testing
./quick_build.sh

# Ejecutar el build
./dist/VideoFrameCapture.app/Contents/MacOS/VideoFrameCapture  # macOS
./dist/VideoFrameCapture                                        # Linux
```

### Release Production
```bash
# Build limpio para release
./build_pipeline.sh current --clean

# Crear paquetes para distribución
./build_pipeline.sh all --clean
```

### Debug Build
```bash
# Build con console para debugging
./build_pipeline.sh current --debug
```

## 📦 Distribución

Los builds generan:

1. **Ejecutables nativos** - Funcionan sin Python instalado
2. **Paquetes ZIP** - Listos para distribución
3. **App bundles** - Instalación nativa en cada plataforma

### Tamaños aproximados:
- **macOS**: ~80-120 MB
- **Linux**: ~70-100 MB
- **Windows**: ~60-90 MB

## 🔧 Troubleshooting

### Error: "Poetry no encontrado"
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

### Error: "PyInstaller falla"
```bash
# Limpiar cache y reinstalar
poetry env remove --all
poetry install
poetry add --group dev pyinstaller
```

### Build muy grande
- Edita `build_config.yaml` para excluir más módulos
- Usa `--exclude-module` en quick_build.sh

### App no inicia en macOS
```bash
# Dar permisos de ejecución
chmod +x dist/VideoFrameCapture.app/Contents/MacOS/VideoFrameCapture

# Si hay problemas de firma
xattr -cr dist/VideoFrameCapture.app
```

## 🚀 Automatización CI/CD

### GitHub Actions
```yaml
# .github/workflows/build.yml
name: Build Releases

on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Poetry
      run: pip install poetry

    - name: Build
      run: ./build_pipeline.sh current --clean

    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: builds-${{ matrix.os }}
        path: dist/
```

## 📄 Notas Importantes

- **Cross-compilation**: Solo se puede buildar para la plataforma actual
- **Dependencias nativas**: OpenCV y Qt se incluyen automáticamente
- **Tamaño**: Los ejecutables son auto-contenidos (incluyen Python + deps)
- **Performance**: Los ejecutables tienen performance nativa
- **Distribución**: No requieren Python instalado en el sistema destino

## 🆘 Soporte

Si tienes problemas con el build system:

1. Revisa los logs de error completos
2. Verifica que todas las dependencias estén instaladas
3. Prueba con `--clean` para limpiar cache
4. Consulta la documentación de PyInstaller para casos específicos

---

¡Happy Building! 🎉