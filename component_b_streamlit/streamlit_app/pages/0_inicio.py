#!/usr/bin/env python3
"""
Página de Inicio - FastAgent
============================

Página principal simplificada con procesamiento inline.
Permite procesar transcripciones en menos de 5 minutos.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Añadir directorios al path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir.parent))
sys.path.append(str(parent_dir))

from components.config_manager import ConfigManager
from components.ui_components import (
    setup_page_config, show_sidebar, show_config_status,
    show_file_uploader, show_error_message, show_metrics_cards
)
from components.agent_interface import (
    AgentInterface, run_async_in_streamlit
)


def clear_session_state():
    """Limpia todo el estado de sesión relacionado con procesamiento."""
    keys_to_clear = [
        'processing_result',
        'input_content',
        'additional_files',
        'selected_agent',
        'use_intelligent_segmentation',
        'enable_qa',
        'questions_per_section',
        'agent_interface'  # Forzar recreación del agent interface
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def main():
    """Página principal de inicio."""
    
    setup_page_config()
    
    # Inicializar componentes
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    if 'agent_interface' not in st.session_state:
        st.session_state.agent_interface = AgentInterface(st.session_state.config_manager)
    
    config_manager = st.session_state.config_manager
    agent_interface = st.session_state.agent_interface
    
    show_sidebar()
    
    st.title("🏠 FastAgent - Inicio")
    
    # Verificar configuración
    validation = config_manager.validate_config()
    is_configured = validation.get('has_provider', False)
    
    if not is_configured:
        show_setup_wizard(config_manager)
        return
    
    # Mostrar estado del sistema en formato compacto
    show_compact_status(config_manager)
    
    # Botón para limpiar sesión (en caso de estado colgado)
    with st.sidebar:
        st.markdown("---")
        if st.button("🗑️ Limpiar Sesión", use_container_width=True, help="Limpia todo el estado y empieza de nuevo"):
            clear_session_state()
            st.rerun()
    
    st.markdown("---")
    
    # Panel principal de procesamiento
    show_processing_panel(config_manager, agent_interface)
    
    # Panel de resultados (si hay)
    if 'processing_result' in st.session_state and st.session_state.processing_result.get('success'):
        st.markdown("---")
        show_results_panel()


def show_setup_wizard(config_manager):
    """Muestra un wizard de configuración rápida si el sistema no está configurado."""
    
    st.warning("⚠️ **Sistema no configurado**")
    
    st.markdown("""
    ### 👋 ¡Bienvenido a FastAgent!
    
    Para comenzar, necesitas configurar un proveedor LLM.
    """)
    
    with st.expander("⚡ Configuración Rápida", expanded=True):
        provider = st.selectbox(
            "Selecciona tu proveedor:",
            ["azure", "generic"],
            format_func=lambda x: "🔷 Azure OpenAI (Recomendado)" if x == "azure" else "🔧 Ollama (Local)"
        )
        
        if provider == "azure":
            api_key = st.text_input("API Key:", type="password")
            base_url = st.text_input(
                "Base URL:",
                placeholder="https://tu-recurso.cognitiveservices.azure.com/"
            )
            deployment = st.text_input("Deployment:", value="gpt-4.1")
            
            if st.button("💾 Guardar y Continuar", type="primary"):
                if api_key and base_url:
                    config_manager.update_provider_config("azure", {
                        "api_key": api_key,
                        "base_url": base_url,
                        "azure_deployment": deployment,
                        "api_version": "2025-01-01-preview"
                    })
                    config_manager.set_default_model(f"azure.{deployment}")
                    st.success("✅ Configuración guardada")
                    st.rerun()
                else:
                    st.error("❌ Por favor completa API Key y Base URL")
        
        else:  # generic/Ollama
            base_url = st.text_input(
                "URL de Ollama:",
                value="http://localhost:11434/v1"
            )
            model = st.text_input("Modelo:", value="llama3.1")
            
            if st.button("💾 Guardar y Continuar", type="primary"):
                config_manager.update_provider_config("generic", {
                    "api_key": "ollama",
                    "base_url": base_url
                })
                config_manager.set_default_model(f"generic.{model}")
                st.success("✅ Configuración guardada")
                st.rerun()
    
    st.info("💡 Para configuración avanzada, ve a **⚙️ Configuración**")


def show_compact_status(config_manager):
    """Muestra estado del sistema en formato compacto."""
    
    validation = config_manager.validate_config()
    default_model = config_manager.get_default_model()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if validation.get('has_provider'):
            st.success(f"✅ **Modelo**: `{default_model}`")
        else:
            st.error("❌ Sin proveedor")
    
    with col2:
        if validation.get('rate_limiting_ok'):
            rate_config = config_manager.get_rate_limiting_config()
            delay = rate_config.get('delay_between_requests', 0)
            st.info(f"⏱️ **Delay**: {delay}s")
        else:
            st.warning("⚠️ Rate limiting")
    
    with col3:
        if all(validation.values()):
            st.success("✅ **Listo**")
        else:
            st.warning("⚠️ Revisar config")


def show_processing_panel(config_manager, agent_interface):
    """Panel principal de procesamiento simplificado."""
    
    st.subheader("📝 Procesar Transcripción")
    
    # Dos columnas: texto + archivos complementarios
    col_main, col_files = st.columns([2, 1])
    
    content = ""
    
    with col_main:
        # Input de contenido
        input_method = st.radio(
            "Método de entrada:",
            ["📝 Pegar texto", "📁 Subir archivo"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if input_method == "📝 Pegar texto":
            content = st.text_area(
                "Pega aquí tu transcripción:",
                height=250,
                placeholder="Pega aquí el texto de tu transcripción STT...",
                key="main_text_input"
            )
        else:
            uploaded_file = st.file_uploader(
                "Sube tu archivo de transcripción:",
                type=['txt', 'md'],
                key="main_file_uploader"
            )
            if uploaded_file:
                try:
                    content = uploaded_file.read().decode('utf-8')
                    st.success(f"✅ {len(content):,} caracteres cargados")
                except UnicodeDecodeError:
                    st.error("❌ El archivo debe estar en formato UTF-8")
    
    with col_files:
        st.markdown("**📎 Contexto adicional** (opcional)")
        st.caption("PDFs, imágenes o PPTs para enriquecer el procesamiento")
        
        additional_files = st.file_uploader(
            "Archivos de contexto:",
            type=['pdf', 'png', 'jpg', 'jpeg', 'pptx', 'ppt', 'txt', 'docx'],
            accept_multiple_files=True,
            key="additional_files_uploader",
            label_visibility="collapsed"
        )
        
        if additional_files:
            st.session_state.additional_files = additional_files
            for f in additional_files:
                size_kb = len(f.getvalue()) / 1024
                st.success(f"📎 {f.name} ({size_kb:.0f}KB)")
        else:
            st.session_state.additional_files = []
            st.info("💡 Añade PDFs, imágenes o presentaciones para dar contexto al LLM")
    
    # Guardar contenido y mostrar métricas
    if content:
        st.session_state.input_content = content
        
        # Métricas rápidas
        word_count = len(content.split())
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 Palabras", f"{word_count:,}")
        with col2:
            estimated_time = max(1, word_count // 200)
            st.metric("⏱️ Tiempo est.", f"~{estimated_time} min")
        with col3:
            files_count = len(st.session_state.get('additional_files', []))
            st.metric("📎 Archivos contexto", files_count)
    
    # Opciones avanzadas (colapsadas)
    with st.expander("🔧 Opciones avanzadas"):
        show_advanced_options(agent_interface)
    
    # Botón de procesamiento
    st.markdown("---")
    
    ready = content and len(content.strip()) > 50
    
    if st.button(
        "🚀 Procesar Contenido",
        type="primary",
        use_container_width=True,
        disabled=not ready
    ):
        process_content_inline(agent_interface, content)
    
    if not ready and content:
        st.warning("⚠️ El contenido debe tener al menos 50 caracteres")


def show_advanced_options(agent_interface):
    """Muestra opciones avanzadas colapsables."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Selección de agente
        agent_options = {
            "auto": "🔍 Auto-detección",
            "simple_processor": "📚 General",
            "meeting_processor": "👥 Reuniones"
        }
        
        available_agents = agent_interface.get_available_agents()
        
        selected = st.selectbox(
            "Agente:",
            options=["auto"] + available_agents,
            format_func=lambda x: agent_options.get(x, x)
        )
        
        st.session_state.selected_agent = None if selected == "auto" else selected
    
    with col2:
        # Método de segmentación
        word_count = len(st.session_state.get('input_content', '').split())
        
        use_intelligent = st.checkbox(
            "🧠 Segmentación inteligente",
            value=word_count > 3000,
            help="Usa GPT-4.1 para encontrar cortes semánticos óptimos"
        )
        
        st.session_state.use_intelligent_segmentation = use_intelligent
    
    # Configuración de Q&A
    st.markdown("---")
    st.markdown("**❓ Generación de Q&A**")
    
    col_qa1, col_qa2 = st.columns(2)
    
    with col_qa1:
        enable_qa = st.checkbox(
            "Generar preguntas y respuestas",
            value=st.session_state.get('enable_qa', True),
            help="Genera preguntas educativas al final de cada sección"
        )
        st.session_state.enable_qa = enable_qa
    
    with col_qa2:
        if enable_qa:
            questions_per_section = st.slider(
                "Preguntas por sección:",
                min_value=2,
                max_value=8,
                value=st.session_state.get('questions_per_section', 4),
                help="Número de preguntas a generar por cada segmento"
            )
            st.session_state.questions_per_section = questions_per_section
        else:
            st.info("Q&A deshabilitado")


def process_content_inline(agent_interface, content):
    """Procesa el contenido y muestra resultados inline con progreso dinámico."""
    
    progress_container = st.empty()
    
    with progress_container.container():
        st.markdown("### 🔄 Procesando...")
        
        # UI de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        segment_info = st.empty()
        
        def update_progress(message: str, progress: float):
            """Callback para actualizar UI de progreso."""
            progress_bar.progress(min(1.0, max(0.0, progress)))
            status_text.markdown(f"**{message}**")
        
        # Preparar archivos adicionales
        document_paths = []
        temp_files = []
        
        if 'additional_files' in st.session_state and st.session_state.additional_files:
            update_progress("📎 Preparando archivos adicionales...", 0.05)
            
            for file in st.session_state.additional_files:
                temp_path = run_async_in_streamlit(
                    agent_interface.save_temp_file(file.getvalue(), Path(file.name).suffix)
                )
                document_paths.append(temp_path)
                temp_files.append(temp_path)
        
        update_progress("🧠 Analizando contenido...", 0.08)
        
        try:
            selected_agent = st.session_state.get('selected_agent')
            use_intelligent = st.session_state.get('use_intelligent_segmentation', True)
            enable_qa = st.session_state.get('enable_qa', True)
            questions_per_section = st.session_state.get('questions_per_section', 4)
            
            # Procesar con callback de progreso dinámico
            result = run_async_in_streamlit(
                agent_interface.process_content(
                    content=content,
                    documents=document_paths if document_paths else None,
                    progress_callback=update_progress,
                    agent_override=selected_agent,
                    use_intelligent_segmentation=use_intelligent,
                    enable_qa=enable_qa,
                    questions_per_section=questions_per_section
                )
            )
            
            update_progress("✨ Generando documento final...", 0.95)
            
            # Guardar resultado
            st.session_state.processing_result = result
            
            if result.get('success'):
                update_progress("🎉 ¡Procesamiento completado!", 1.0)
                segment_info.success(
                    f"✅ **{result.get('total_segments', 0)} segmentos** procesados "
                    f"con agente **{result.get('agent_used', 'N/A')}** "
                    f"({result.get('retry_count', 0)} reintentos)"
                )
            else:
                update_progress(f"❌ Error: {result.get('error', 'Error desconocido')}", 1.0)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("Ver detalles del error"):
                st.code(traceback.format_exc())
        
        finally:
            if temp_files:
                agent_interface.cleanup_temp_files(temp_files)
    
    # Forzar rerun para mostrar resultados
    st.rerun()


def show_results_panel():
    """Panel de resultados del procesamiento."""
    
    result = st.session_state.processing_result
    
    if not result.get('success'):
        st.error(f"❌ Error: {result.get('error', 'Error desconocido')}")
        return
    
    st.subheader("📄 Resultado")
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Segmentos", result.get('total_segments', 0))
    with col2:
        st.metric("🤖 Agente", result.get('agent_used', 'N/A'))
    with col3:
        method = "🧠 AI" if result.get('segmentation_method') == 'intelligent_ai' else "📐"
        st.metric("Método", method)
    with col4:
        st.metric("🔄 Reintentos", result.get('retry_count', 0))
    
    # Documento
    document = result.get('document', '')
    
    # Vista previa (colapsada por defecto para documentos largos)
    if len(document) > 2000:
        with st.expander("👀 Vista previa", expanded=False):
            st.markdown(document[:2000] + "\n\n... [truncado]")
    else:
        with st.expander("👀 Vista previa", expanded=True):
            st.markdown(document)
    
    # Descargas
    st.markdown("### 💾 Descargar")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📥 Descargar .md",
            data=document,
            file_name=f"documento_{timestamp}.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        if st.button("🔄 Procesar otro", use_container_width=True):
            # Limpiar estado completamente
            clear_session_state()
            st.rerun()


if __name__ == "__main__":
    main()
