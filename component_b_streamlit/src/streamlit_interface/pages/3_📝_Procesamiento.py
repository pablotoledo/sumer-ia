#!/usr/bin/env python3
"""
Página de Procesamiento
======================

Página principal para procesar contenido STT con FastAgent.
"""

import streamlit as st
import sys
from pathlib import Path
import tempfile
import os

# Añadir el directorio padre al path
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(parent_dir))

from src.streamlit_interface.core.config_manager import ConfigManager
from src.streamlit_interface.components.ui_components import (
    setup_page_config, show_sidebar, show_config_status,
    show_file_uploader, show_download_button, show_error_message,
    show_expandable_content, show_metrics_cards
)
from src.streamlit_interface.core.agent_interface import (
    AgentInterface, run_async_in_streamlit, create_progress_callback
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
        return

    # Tabs principales
    tab1, tab2, tab3 = st.tabs([
        "📤 Input y Configuración",
        "⚡ Procesamiento",
        "📥 Resultados"
    ])

    with tab1:
        show_input_tab(config_manager, agent_interface)

    with tab2:
        show_processing_tab(agent_interface)

    with tab3:
        show_results_tab()

def show_input_tab(config_manager, agent_interface):
    """Tab de input y configuración."""

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

    # Guardar contenido en session state
    if content:
        st.session_state.input_content = content

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

    st.markdown("---")

    # Documentos adicionales (multimodal)
    st.subheader("📎 Documentos Adicionales (Opcional)")

    st.info("💡 Puedes subir PDFs, imágenes u otros documentos para enriquecer el contexto del procesamiento.")

    additional_files = st.file_uploader(
        "Documentos adicionales:",
        type=['pdf', 'png', 'jpg', 'jpeg', 'txt', 'md'],
        accept_multiple_files=True
    )

    if additional_files:
        st.session_state.additional_files = additional_files

        for file in additional_files:
            file_size_mb = len(file.getvalue()) / (1024 * 1024)
            st.success(f"📎 **{file.name}** ({file_size_mb:.1f}MB)")

    st.markdown("---")

    # Configuración de procesamiento
    st.subheader("⚙️ Configuración de Procesamiento")

    # Selección de agente
    available_agents = agent_interface.get_available_agents()

    agent_options = {
        "auto": "🔍 Auto-detección (Recomendado)",
        "simple_processor": "📚 Procesador General",
        "meeting_processor": "👥 Procesador de Reuniones"
    }

    selected_agent = st.selectbox(
        "Agente a utilizar:",
        options=["auto"] + available_agents,
        format_func=lambda x: agent_options.get(x, x),
        help="Auto-detección analiza el contenido y selecciona el agente más apropiado"
    )

    if selected_agent != "auto":
        description = agent_interface.get_agent_description(selected_agent)
        st.info(f"ℹ️ {description}")

    st.session_state.selected_agent = selected_agent if selected_agent != "auto" else None

    # Configuración de Q&A
    st.subheader("❓ Configuración de Q&A")

    enable_qa = st.checkbox("Generar preguntas y respuestas", value=True)

    if enable_qa:
        qa_config = st.expander("🔧 Configuración avanzada de Q&A")
        with qa_config:
            questions_per_segment = st.slider(
                "Preguntas por segmento:",
                min_value=2,
                max_value=8,
                value=4,
                help="Número de preguntas a generar por cada segmento procesado"
            )

            qa_focus = st.multiselect(
                "Enfoque de las preguntas:",
                ["Conceptos clave", "Ejemplos prácticos", "Datos específicos", "Comparaciones", "Aplicaciones"],
                default=["Conceptos clave", "Ejemplos prácticos"]
            )

    st.session_state.enable_qa = enable_qa

    # Test de conexión
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("🔗 Probar Conexión con Agentes", help="Verifica que los agentes FastAgent estén funcionando"):
            with st.spinner("Probando conexión..."):
                success = run_async_in_streamlit(
                    agent_interface.test_agent_connection()
                )

                if success:
                    st.success("✅ Conexión exitosa con FastAgent")
                else:
                    st.error("❌ Error de conexión con FastAgent")

    with col2:
        # Indicador de listo para procesar
        ready_to_process = (
            'input_content' in st.session_state and
            len(st.session_state.input_content.strip()) > 50
        )

        if ready_to_process:
            st.success("✅ Listo para procesar")
        else:
            st.warning("⚠️ Necesitas contenido")

def show_processing_tab(agent_interface):
    """Tab de procesamiento."""

    st.header("⚡ Procesamiento en Tiempo Real")

    # Verificar si hay contenido para procesar
    if 'input_content' not in st.session_state or not st.session_state.input_content.strip():
        st.warning("⚠️ No hay contenido para procesar. Ve al tab **Input y Configuración**.")
        return

    content = st.session_state.input_content

    # Resumen del contenido a procesar
    st.subheader("📋 Resumen del Procesamiento")

    col1, col2, col3 = st.columns(3)

    with col1:
        word_count = len(content.split())
        st.metric("📝 Palabras", word_count)

    with col2:
        estimated_time = max(1, word_count // 200)  # ~200 palabras por minuto
        st.metric("⏱️ Tiempo estimado", f"{estimated_time} min")

    with col3:
        agent_name = st.session_state.get('selected_agent', 'Auto-detección')
        st.metric("🤖 Agente", agent_name)

    # Documentos adicionales
    if 'additional_files' in st.session_state and st.session_state.additional_files:
        st.info(f"📎 **{len(st.session_state.additional_files)} documentos adicionales** se incluirán en el contexto")

    st.markdown("---")

    # Botón de procesamiento
    if st.button("🚀 Iniciar Procesamiento", type="primary", use_container_width=True):
        process_content(agent_interface)

def process_content(agent_interface):
    """Ejecuta el procesamiento del contenido."""

    content = st.session_state.input_content
    selected_agent = st.session_state.get('selected_agent')

    # Preparar archivos adicionales
    document_paths = []
    temp_files = []

    if 'additional_files' in st.session_state and st.session_state.additional_files:
        for file in st.session_state.additional_files:
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
        result = run_async_in_streamlit(
            agent_interface.process_content(
                content=content,
                documents=document_paths if document_paths else None,
                progress_callback=progress_callback,
                agent_override=selected_agent
            )
        )

        # Guardar resultado en session state
        st.session_state.processing_result = result

        if result['success']:
            st.success("🎉 **Procesamiento completado exitosamente!**")

            # Mostrar métricas
            metrics = {
                "Segmentos procesados": {"value": result['total_segments']},
                "Agente utilizado": {"value": result['agent_used']},
                "Reintentos": {"value": result['retry_count']}
            }

            show_metrics_cards(metrics)

            # Preview del resultado
            st.subheader("👀 Preview del Resultado")

            document = result['document']
            preview_length = 500

            if len(document) > preview_length:
                preview = document[:preview_length] + "\n\n... [Contenido truncado para preview]"
            else:
                preview = document

            st.text_area("Preview:", preview, height=200, disabled=True)

            st.info("💡 Ve al tab **Resultados** para ver el documento completo y descargarlo.")

        else:
            st.error(f"❌ Error durante el procesamiento: {result.get('error', 'Error desconocido')}")

            # Mostrar sugerencias de error
            show_error_message(Exception(result.get('error', 'Error desconocido')), "procesamiento")

    except Exception as e:
        st.error("❌ Error inesperado durante el procesamiento")
        show_error_message(e, "procesamiento")

    finally:
        # Limpiar archivos temporales
        if temp_files:
            agent_interface.cleanup_temp_files(temp_files)

def show_results_tab():
    """Tab de resultados."""

    st.header("📥 Resultados del Procesamiento")

    if 'processing_result' not in st.session_state:
        st.info("ℹ️ No hay resultados disponibles. Procesa contenido primero en el tab **Procesamiento**.")
        return

    result = st.session_state.processing_result

    if not result.get('success', False):
        st.error("❌ El último procesamiento falló.")
        return

    # Información del procesamiento
    st.subheader("📊 Información del Procesamiento")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🤖 Agente usado", result['agent_used'])

    with col2:
        st.metric("📄 Segmentos", result['total_segments'])

    with col3:
        st.metric("🔄 Reintentos", result['retry_count'])

    with col4:
        word_count = len(result['document'].split())
        st.metric("📝 Palabras finales", word_count)

    st.markdown("---")

    # Documento final
    st.subheader("📄 Documento Procesado")

    document = result['document']

    # Tabs para diferentes vistas
    view_tab1, view_tab2, view_tab3 = st.tabs([
        "📖 Vista Markdown",
        "📝 Texto Plano",
        "🔍 Vista por Segmentos"
    ])

    with view_tab1:
        st.markdown(document)

    with view_tab2:
        st.text_area("Documento completo:", document, height=400, disabled=True)

    with view_tab3:
        show_segments_view(result)

    st.markdown("---")

    # Opciones de descarga
    st.subheader("💾 Descargar Resultados")

    col1, col2, col3 = st.columns(3)

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

    with col3:
        # Solo la sección Q&A
        qa_section = extract_qa_section(document)
        if qa_section:
            show_download_button(
                qa_section,
                "preguntas_respuestas.md",
                "Solo Q&A"
            )

    # Estadísticas detalladas
    with st.expander("📊 Estadísticas Detalladas"):
        show_detailed_stats(result)

def show_segments_view(result):
    """Muestra vista detallada por segmentos."""

    segments = result.get('segments', [])

    if not segments:
        st.warning("No hay información detallada de segmentos disponible.")
        return

    for i, segment in enumerate(segments):
        with st.expander(f"Segmento {segment['segment_number']} {' ❌' if segment.get('error') else ''}"):

            if segment.get('error'):
                st.error(f"Error: {segment['processed_content']}")
            else:
                # Contenido original
                st.subheader("📝 Contenido Original")
                st.text_area(
                    f"Original {segment['segment_number']}:",
                    segment['original_content'],
                    height=100,
                    disabled=True,
                    key=f"orig_{i}"
                )

                # Contenido procesado
                st.subheader("✨ Contenido Procesado")
                st.markdown(segment['processed_content'])

                # Metadatos
                st.subheader("🔧 Metadatos")
                st.json({
                    'agente_usado': segment['agent_used'],
                    'palabras_originales': len(segment['original_content'].split()),
                    'palabras_procesadas': len(segment['processed_content'].split())
                })

def extract_qa_section(document: str) -> str:
    """Extrae solo la sección de Q&A del documento."""
    lines = document.split('\n')
    qa_section = []
    in_qa = False

    for line in lines:
        if 'preguntas y respuestas' in line.lower() or 'q&a' in line.lower():
            in_qa = True

        if in_qa:
            qa_section.append(line)

    return '\n'.join(qa_section) if qa_section else ""

def show_detailed_stats(result):
    """Muestra estadísticas detalladas del procesamiento."""

    original_content = result.get('original_content', '')
    final_document = result.get('document', '')

    # Métricas de transformación
    original_words = len(original_content.split())
    final_words = len(final_document.split())
    retention_rate = (final_words / original_words * 100) if original_words > 0 else 0

    col1, col2 = st.columns(2)

    with col1:
        st.metric("📝 Palabras originales", original_words)
        st.metric("📄 Palabras finales", final_words)
        st.metric("📊 Tasa de retención", f"{retention_rate:.1f}%")

    with col2:
        multimodal_files = result.get('multimodal_files', [])
        st.metric("📎 Archivos multimodales", len(multimodal_files))
        st.metric("🔄 Total de reintentos", result.get('retry_count', 0))
        st.metric("🤖 Agente utilizado", result.get('agent_used', 'Desconocido'))

    # Lista de archivos multimodales
    if multimodal_files:
        st.subheader("📎 Archivos Multimodales Utilizados")
        for file_path in multimodal_files:
            file_name = Path(file_path).name
            st.text(f"• {file_name}")

if __name__ == "__main__":
    main()