"""
UI Components
=============

Componentes de interfaz reutilizables para la aplicación Streamlit.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import time

def setup_page_config():
    """Configura la página de Streamlit."""
    st.set_page_config(
        page_title="FastAgent Interface",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/evalstate/fast-agent',
            'Report a bug': "https://github.com/evalstate/fast-agent/issues",
            'About': "# FastAgent Interface\nInterfaz web para el sistema FastAgent de procesamiento multi-agente."
        }
    )

def show_header():
    """Muestra el header principal de la aplicación."""
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1>🤖 FastAgent Interface</h1>
        <p style='font-size: 1.2rem; color: #666; margin-bottom: 2rem;'>
            Sistema de procesamiento multi-agente para transcripciones STT
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_sidebar():
    """Muestra la barra lateral con navegación."""
    with st.sidebar:
        st.markdown("## 🧭 Navegación")
        
        # Estado del sistema
        st.markdown("### 📊 Estado del Sistema")
        
        # Verificar configuración
        if 'config_manager' in st.session_state:
            validation = st.session_state.config_manager.validate_config()
            
            if validation['has_provider']:
                st.success("✅ Proveedor configurado")
            else:
                st.error("❌ Sin proveedor LLM")
            
            if validation['valid_model']:
                st.success("✅ Modelo válido")
            else:
                st.warning("⚠️ Modelo no configurado")
        
        st.markdown("---")
        
        # Información de ayuda
        st.markdown("""
        ### 💡 Ayuda Rápida
        
        **🏠 Inicio**: Vista general del sistema
        
        **⚙️ Configuración**: 
        - Configurar Azure OpenAI
        - Configurar Ollama
        - Ajustar rate limiting
        
        **🤖 Agentes**:
        - Modificar prompts del sistema
        - Personalizar comportamiento
        
        **📝 Procesamiento**:
        - Subir archivos STT
        - Procesar con Q&A
        - Descargar resultados
        """)
        
        st.markdown("---")
        
        # Enlaces útiles
        st.markdown("""
        ### 🔗 Enlaces Útiles
        - [FastAgent Docs](https://fast-agent.ai/)
        - [Repositorio GitHub](https://github.com/evalstate/fast-agent)
        - [Reportar Bug](https://github.com/evalstate/fast-agent/issues)
        """)

def show_config_status(config_manager) -> bool:
    """Muestra el estado de configuración y retorna si está lista."""
    validation = config_manager.validate_config()
    
    if all(validation.values()):
        st.success("✅ Sistema configurado correctamente")
        return True
    else:
        st.warning("⚠️ Configuración incompleta")
        
        with st.expander("Ver detalles de configuración"):
            if not validation['has_provider']:
                st.error("❌ No hay proveedores LLM configurados")
            if not validation['valid_model']:
                st.error("❌ Modelo por defecto no válido")
            if not validation['rate_limiting_ok']:
                st.error("❌ Rate limiting mal configurado")
        
        return False

def show_metrics_cards(metrics: Dict[str, Any]):
    """Muestra métricas en tarjetas."""
    cols = st.columns(len(metrics))
    
    for i, (key, value) in enumerate(metrics.items()):
        with cols[i]:
            st.metric(
                label=key,
                value=value.get('value', 0),
                delta=value.get('delta', None)
            )

def show_file_uploader(accepted_types: List[str], max_size_mb: int = 10) -> Optional[Any]:
    """Muestra un uploader de archivos configurado."""
    uploaded_file = st.file_uploader(
        "Selecciona un archivo",
        type=accepted_types,
        help=f"Archivos soportados: {', '.join(accepted_types)}. Tamaño máximo: {max_size_mb}MB"
    )
    
    if uploaded_file:
        # Verificar tamaño
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            st.error(f"❌ Archivo muy grande: {file_size_mb:.1f}MB. Máximo permitido: {max_size_mb}MB")
            return None
        
        # Mostrar información del archivo
        st.info(f"📁 **{uploaded_file.name}** ({file_size_mb:.1f}MB)")
        
        return uploaded_file
    
    return None

def show_download_button(content: str, filename: str, label: str = "Descargar"):
    """Muestra un botón de descarga."""
    st.download_button(
        label=f"📥 {label}",
        data=content,
        file_name=filename,
        mime="text/plain" if filename.endswith('.txt') else "text/markdown"
    )

def show_error_message(error: Exception, context: str = ""):
    """Muestra mensaje de error formateado."""
    st.error(f"❌ Error{' en ' + context if context else ''}")
    
    with st.expander("Ver detalles del error"):
        st.code(str(error))
        
        # Sugerencias basadas en el tipo de error
        error_str = str(error).lower()
        
        if "429" in error_str or "rate limit" in error_str:
            st.warning("""
            **Posible solución**: Error de rate limiting
            - Aumenta el delay entre requests en Configuración
            - Reduce la frecuencia de requests por minuto
            - Verifica tu plan de Azure OpenAI
            """)
        
        elif "api key" in error_str or "unauthorized" in error_str:
            st.warning("""
            **Posible solución**: Problema de autenticación
            - Verifica tu API key en Configuración
            - Asegúrate de que la API key esté activa
            - Revisa los permisos de tu cuenta
            """)
        
        elif "connection" in error_str or "timeout" in error_str:
            st.warning("""
            **Posible solución**: Problema de conectividad
            - Verifica tu conexión a internet
            - Revisa la URL del proveedor
            - Aumenta el timeout en configuración
            """)

def create_progress_callback():
    """Crea un callback de progreso para Streamlit."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def callback(message: str, progress: float):
        progress_bar.progress(progress)
        status_text.text(message)
    
    return callback