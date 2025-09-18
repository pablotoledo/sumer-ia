#!/usr/bin/env python3
"""
Página de Procesamiento
======================

Página principal para procesar contenido STT con FastAgent.
"""

import streamlit as st
import sys
from pathlib import Path

# Configurar path para imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.streamlit_interface.core.config_manager import ConfigManager
from src.streamlit_interface.core.agent_interface import AgentInterface, run_async_in_streamlit
from src.streamlit_interface.components.ui_components import (
    setup_page_config, show_sidebar, show_config_status,
    show_file_uploader, show_download_button, show_error_message,
    create_progress_callback
)

def main():
    """Página principal de procesamiento."""
    
    setup_page_config()
    
    # Inicializar componentes
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    if 'agent_interface' not in st.session_state:
        st.session_state.agent_interface = AgentInterface(st.session_state.config_manager)
    
    config_manager = st.session_state.config_manager
    agent_interface = st.session_state.agent_interface
    
    show_sidebar()
    
    st.title("📝 Procesamiento de Contenido")
    
    # Verificar configuración antes de continuar
    if not show_config_status(config_manager):
        st.error("❌ **Sistema no configurado**")
        st.info("👆 Dirígete a la página de **Configuración** para configurar al menos un proveedor LLM.")
        if st.button("⚙️ Ir a Configuración"):
            st.switch_page("pages/2_⚙️_Configuración.py")
        return
    
    # Input de contenido
    st.header("📤 Contenido a Procesar")
    
    # Método de input
    input_method = st.radio(
        "¿Cómo quieres proporcionar el contenido?",
        ["📝 Escribir texto", "📁 Subir archivo de texto"],
        horizontal=True
    )
    
    content = ""
    
    if input_method == "📝 Escribir texto":
        content = st.text_area(
            "Pega aquí tu transcripción STT:",
            height=200,
            placeholder="Ejemplo: bueno eh entonces vamos a hablar sobre inversiones..."
        )
    
    else:  # Subir archivo
        uploaded_file = show_file_uploader(['txt'], max_size_mb=5)
        if uploaded_file:
            try:
                content = uploaded_file.read().decode('utf-8')
                st.success(f"✅ Archivo cargado: {len(content)} caracteres")
                
                # Preview del contenido
                with st.expander("👀 Preview del contenido"):
                    st.text_area("Contenido:", content[:1000] + "..." if len(content) > 1000 else content, disabled=True)
            
            except UnicodeDecodeError:
                st.error("❌ Error: El archivo debe estar en formato UTF-8")
                content = ""
    
    if content:
        # Estadísticas del contenido
        word_count = len(content.split())
        char_count = len(content)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 Palabras", word_count)
        with col2:
            st.metric("🔤 Caracteres", char_count)
        with col3:
            estimated_segments = max(1, word_count // 800)  # ~800 palabras por segmento
            st.metric("📊 Segmentos estimados", estimated_segments)
        
        # Configuración básica
        st.header("⚙️ Configuración")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Selección de agente
            agent_options = {
                "auto": "🔍 Auto-detección (Recomendado)",
                "simple_processor": "📚 Procesador General",
                "meeting_processor": "👥 Procesador de Reuniones"
            }
            
            selected_agent = st.selectbox(
                "Agente a utilizar:",
                options=["auto", "simple_processor", "meeting_processor"],
                format_func=lambda x: agent_options.get(x, x),
                help="Auto-detección analiza el contenido y selecciona el agente más apropiado"
            )
        
        with col2:
            enable_qa = st.checkbox("Generar Q&A", value=True, help="Generar preguntas y respuestas educativas")
        
        # Documentos adicionales
        st.subheader("📎 Documentos Adicionales (Opcional)")
        
        additional_files = st.file_uploader(
            "Documentos para contexto:",
            type=['pdf', 'png', 'jpg', 'jpeg', 'txt'],
            accept_multiple_files=True,
            help="PDFs, imágenes u otros documentos para enriquecer el contexto"
        )
        
        # Botón de procesamiento
        st.header("🚀 Procesamiento")
        
        if st.button("▶️ Procesar Contenido", type="primary", use_container_width=True):
            process_content(agent_interface, content, selected_agent, additional_files)

def process_content(agent_interface, content, selected_agent, additional_files):
    """Ejecuta el procesamiento del contenido."""
    
    # Preparar archivos adicionales
    document_paths = []
    temp_files = []
    
    if additional_files:
        for file in additional_files:
            # Guardar archivo temporal
            temp_path = run_async_in_streamlit(
                agent_interface.save_temp_file(file.getvalue(), Path(file.name).suffix)
            )
            document_paths.append(temp_path)
            temp_files.append(temp_path)
    
    # Crear callback de progreso
    progress_callback = create_progress_callback()
    
    try:
        # Ejecutar procesamiento
        agent_override = None if selected_agent == "auto" else selected_agent
        
        result = run_async_in_streamlit(
            agent_interface.process_content(
                content=content,
                documents=document_paths if document_paths else None,
                progress_callback=progress_callback,
                agent_override=agent_override
            )
        )
        
        # Guardar resultado en session state
        st.session_state.processing_result = result
        
        if result['success']:
            st.success("🎉 **Procesamiento completado exitosamente!**")
            
            # Mostrar métricas básicas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Segmentos", result['total_segments'])
            
            with col2:
                st.metric("🤖 Agente", result['agent_used'])
            
            with col3:
                st.metric("🔄 Reintentos", result['retry_count'])
            
            # Mostrar resultado
            st.subheader("📄 Documento Procesado")
            
            document = result['document']
            
            # Tabs para diferentes vistas
            tab1, tab2 = st.tabs(["📖 Vista Markdown", "📝 Texto Plano"])
            
            with tab1:
                st.markdown(document)
            
            with tab2:
                st.text_area("Documento completo:", document, height=400, disabled=True)
            
            # Opciones de descarga
            st.subheader("💾 Descargar Resultados")
            
            col1, col2 = st.columns(2)
            
            with col1:
                show_download_button(
                    document, 
                    "documento_procesado.md", 
                    "Descargar como Markdown"
                )
            
            with col2:
                # Versión sin markdown para .txt
                plain_text = document.replace('#', '').replace('**', '').replace('*', '')
                show_download_button(
                    plain_text, 
                    "documento_procesado.txt", 
                    "Descargar como TXT"
                )
        
        else:
            st.error(f"❌ Error durante el procesamiento: {result.get('error', 'Error desconocido')}")
            show_error_message(Exception(result.get('error', 'Error desconocido')), "procesamiento")
    
    except Exception as e:
        st.error("❌ Error inesperado durante el procesamiento")
        show_error_message(e, "procesamiento")
    
    finally:
        # Limpiar archivos temporales
        if temp_files:
            agent_interface.cleanup_temp_files(temp_files)

if __name__ == "__main__":
    main()