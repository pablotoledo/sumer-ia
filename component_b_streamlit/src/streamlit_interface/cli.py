#!/usr/bin/env python3
"""
CLI Entry Points para FastAgent Streamlit Interface
==================================================

Scripts de entrada optimizados para ejecutar desde Poetry.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_streamlit_app():
    """Punto de entrada principal para fastagent-ui."""
    
    print("🤖 FastAgent Streamlit Interface")
    print("=" * 40)
    
    # Obtener la ruta del archivo app.py (interfaz limpia)
    app_file = Path(__file__).parent.parent.parent / "streamlit_app" / "streamlit_app.py"
    
    if not app_file.exists():
        print(f"❌ Error: No se encontró {app_file}")
        sys.exit(1)
    
    # Configurar comando de Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run',
        str(app_file),
        '--server.port', '8501',
        '--server.address', 'localhost',
        '--server.headless', 'true'
    ]
    
    print("🚀 Iniciando FastAgent Streamlit Interface...")
    print("📱 La aplicación se abrirá en: http://localhost:8501")
    print("🛑 Para detener: Ctrl+C")
    print()
    
    try:
        # Ejecutar Streamlit
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 FastAgent Streamlit Interface detenida")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando Streamlit: {e}")
        print("\n🔧 Posibles soluciones:")
        print("   1. Verificar que Streamlit esté instalado: uv add streamlit")
        print("   2. Instalar dependencias extra: uv sync --extra streamlit")
        print("   3. Ejecutar manualmente: uv run streamlit run streamlit_app/streamlit_app.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

def check_dependencies():
    """Verifica que las dependencias estén instaladas."""
    
    required_packages = ['streamlit', 'plotly', 'pandas']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Dependencias faltantes: {', '.join(missing)}")
        print("🔧 Ejecuta: uv sync --extra streamlit")
        return False
    
    return True

def main():
    """Función principal del CLI."""
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Ejecutar aplicación
    run_streamlit_app()

if __name__ == "__main__":
    main()