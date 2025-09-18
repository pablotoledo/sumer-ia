#!/usr/bin/env python3
"""
FastAgent Streamlit Interface - Aplicación Principal
===================================================

Aplicación Streamlit integrada con Poetry para el sistema FastAgent.
"""

import streamlit as st
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Configurar imports absolutos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.streamlit_interface.core.config_manager import ConfigManager
from src.streamlit_interface.components.ui_components import setup_page_config, show_sidebar, show_header

def setup_streamlit_app():
    """Configura la aplicación Streamlit."""
    
    # Configuración básica de la página
    setup_page_config()
    
    # Inicializar el gestor de configuración
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    # Mostrar header principal
    show_header()
    
    # Sidebar con navegación
    show_sidebar()

def main():
    """Función principal de la aplicación para ejecutar desde línea de comandos."""
    
    setup_streamlit_app()
    
    # Contenido principal
    st.markdown("""
    ## 🚀 Bienvenido al FastAgent Interface
    
    Esta aplicación te permite interactuar de forma intuitiva con el sistema FastAgent 
    de procesamiento multi-agente para transformar transcripciones STT en documentos 
    educativos profesionales con Q&A automático.
    
    ### 🎯 Características principales:
    
    - **📊 Dashboard**: Vista general del sistema y métricas de uso
    - **⚙️ Configuración**: Gestión de proveedores LLM (Azure OpenAI, Ollama, etc.)
    - **🤖 Agentes**: Personalización de agentes y prompts del sistema
    - **📝 Procesamiento**: Interface principal para procesar contenido con visualización en tiempo real
    
    ### 🏗️ Sistema Multi-Agente
    
    El sistema utiliza una arquitectura distribuida con:
    - **Auto-detección de formato**: Distingue entre reuniones diarizadas y contenido lineal
    - **6 agentes especializados**: Punctuator, Segmenter, Titler, Formatter, Q&A Generator, etc.
    - **Soporte multimodal**: Integración con PDFs, imágenes y documentos adicionales
    - **Rate limiting inteligente**: Manejo automático de límites de Azure OpenAI
    
    ### 🚀 Comenzar
    
    1. **Configura tu proveedor LLM** en la página de Configuración
    2. **Personaliza los agentes** si lo deseas (opcional)
    3. **Procesa tu contenido** en la página de Procesamiento
    4. **Descarga los resultados** en formato TXT o MD
    
    ---
    
    💡 **Tip**: Usa la navegación del sidebar izquierdo para acceder a las diferentes funciones.
    """)
    
    # Status de configuración
    config = st.session_state.config_manager.get_config()
    
    st.markdown("### 📋 Estado del Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if config.get('azure', {}).get('api_key') and config.get('azure', {}).get('api_key') != "YOUR_AZURE_API_KEY_HERE":
            st.success("✅ Azure OpenAI configurado")
        else:
            st.warning("⚠️ Azure OpenAI no configurado")
    
    with col2:
        if config.get('generic', {}).get('base_url'):
            st.success("✅ Ollama configurado")
        else:
            st.info("ℹ️ Ollama no configurado")
    
    with col3:
        default_model = config.get('default_model', 'No configurado')
        st.info(f"🎯 Modelo por defecto: `{default_model}`")
    
    # Botones de navegación rápida
    st.markdown("### 🚀 Acciones Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Ir a Procesamiento", type="primary", use_container_width=True):
            st.switch_page("pages/1_📝_Procesamiento.py")
    
    with col2:
        if st.button("⚙️ Configurar Sistema", use_container_width=True):
            st.switch_page("pages/2_⚙️_Configuración.py")
    
    with col3:
        if st.button("🔄 Recargar Página", use_container_width=True):
            st.rerun()

def run_streamlit():
    """Ejecuta la aplicación Streamlit programáticamente."""
    
    import os
    
    # Obtener la ruta del archivo actual
    app_file = Path(__file__).resolve()
    
    # Configurar variables de entorno para Streamlit
    env = os.environ.copy()
    env.update({
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_SERVER_PORT': '8501',
        'STREAMLIT_SERVER_ADDRESS': 'localhost'
    })
    
    # Ejecutar Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 
        str(app_file),
        '--server.port', '8501',
        '--server.address', 'localhost'
    ]
    
    print("🚀 Iniciando FastAgent Streamlit Interface...")
    print(f"📱 La aplicación se abrirá en: http://localhost:8501")
    print("🛑 Para detener: Ctrl+C")
    
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n👋 FastAgent Streamlit Interface detenida")

if __name__ == "__main__":
    # Si se ejecuta directamente, configurar la app para Streamlit
    main()