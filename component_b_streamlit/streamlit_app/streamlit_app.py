#!/usr/bin/env python3
"""
FastAgent Streamlit Interface
============================

Página principal - Redirige a Inicio y muestra estado compacto en sidebar.
"""

import streamlit as st
import sys
from pathlib import Path

# Añadir directorios al path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))
sys.path.append(str(current_dir))

from components.config_manager import ConfigManager
from components.ui_components import setup_page_config, show_sidebar


def main():
    """Página principal - Redirige a Inicio."""
    
    setup_page_config()
    
    # Inicializar config manager
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    config_manager = st.session_state.config_manager
    
    show_sidebar()
    
    # Mostrar estado y redirigir
    st.title("🚀 FastAgent")
    st.caption("Sistema de procesamiento de transcripciones con IA")
    
    # Estado del sistema
    validation = config_manager.validate_config()
    
    if all(validation.values()):
        st.success("✅ **Sistema configurado y listo**")
        st.info("👆 Usa el menú lateral para navegar a **🏠 Inicio** y procesar tu contenido.")
    else:
        st.warning("⚠️ **Sistema no configurado**")
        st.info("👆 Ve a **⚙️ Configuración** en el menú lateral para configurar el sistema.")
    
    st.markdown("---")
    
    # Quick navigation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Ir a Inicio", type="primary", use_container_width=True):
            st.switch_page("pages/0_inicio.py")
    
    with col2:
        if st.button("⚙️ Configurar", use_container_width=True):
            st.switch_page("pages/1_configuracion.py")
    
    # Info
    st.markdown("---")
    st.markdown("""
    ### 📚 Guía Rápida
    
    1. **Configurar**: Añade tu API key en ⚙️ Configuración
    2. **Procesar**: Pega o sube tu transcripción en 🏠 Inicio
    3. **Descargar**: Obtén tu documento procesado en Markdown
    
    ### 📖 Documentación
    
    - [Guía de Inicio Rápido](docs/QUICKSTART.md)
    - [Configuración Detallada](docs/CONFIGURATION.md)
    """)


if __name__ == "__main__":
    main()