#!/usr/bin/env python3
"""
Dashboard
=========

Panel de control principal con métricas y estado del sistema.
"""

import streamlit as st
import sys
from pathlib import Path

# Añadir el directorio padre al path
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(parent_dir))

from src.streamlit_interface.core.config_manager import ConfigManager
from src.streamlit_interface.components.ui_components import (
    setup_page_config, show_sidebar, show_config_status
)

def main():
    """Dashboard principal."""

    setup_page_config()

    # Inicializar config manager
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()

    config_manager = st.session_state.config_manager

    show_sidebar()

    st.title("📊 Dashboard FastAgent")

    # Estado general del sistema
    show_system_status(config_manager)

    st.markdown("---")

    # Información del sistema y acciones rápidas
    col1, col2 = st.columns([1, 1])

    with col1:
        show_system_info(config_manager)

    with col2:
        show_quick_actions(config_manager)

def show_system_status(config_manager):
    """Muestra el estado general del sistema."""

    st.subheader("🔧 Estado del Sistema")

    validation = config_manager.validate_config()

    # Indicadores de estado
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if validation['has_provider']:
            st.success("✅ Proveedor LLM")
        else:
            st.error("❌ Sin Proveedor")

    with col2:
        if validation['valid_model']:
            st.success("✅ Modelo Válido")
        else:
            st.warning("⚠️ Modelo No Configurado")

    with col3:
        if validation['rate_limiting_ok']:
            st.success("✅ Rate Limiting")
        else:
            st.warning("⚠️ Rate Limiting")

    with col4:
        overall_status = all(validation.values())
        if overall_status:
            st.success("✅ Sistema Listo")
        else:
            st.error("❌ Configuración Incompleta")

    # Proveedores configurados
    providers = []
    for provider in ['azure', 'generic', 'openai', 'anthropic']:
        if config_manager.is_provider_configured(provider):
            providers.append(provider.title())

    if providers:
        st.info(f"🔗 **Proveedores activos**: {', '.join(providers)}")
    else:
        st.warning("⚠️ No hay proveedores LLM configurados")

    # Modelo por defecto
    default_model = config_manager.get_default_model()
    st.info(f"🎯 **Modelo por defecto**: `{default_model}`")


def show_system_info(config_manager):
    """Muestra información del sistema."""

    st.subheader("ℹ️ Información del Sistema")

    config = config_manager.get_config()
    rate_config = config_manager.get_rate_limiting_config()

    # Información de configuración
    info_data = {
        "🔧 Configuración": {
            "Requests/min": rate_config.get('requests_per_minute', 'No configurado'),
            "Delay entre requests": f"{rate_config.get('delay_between_requests', 0)}s",
            "Max tokens/request": f"{rate_config.get('max_tokens_per_request', 0):,}",
            "Factor de backoff": rate_config.get('backoff_factor', 'No configurado')
        },
        "🎯 Agentes": {
            "Disponibles": "simple_processor, meeting_processor",
            "Por defecto": "Auto-detección",
            "Q&A": "Habilitado",
            "Multimodal": "Soportado"
        }
    }

    for category, items in info_data.items():
        with st.expander(category):
            for key, value in items.items():
                st.write(f"**{key}**: {value}")

    # Estado de los servidores MCP
    st.subheader("🔗 Servidores MCP")

    mcp_servers = config.get('mcp', {}).get('servers', {})

    if mcp_servers:
        for server_name, server_config in mcp_servers.items():
            command = server_config.get('command', 'No especificado')
            st.write(f"**{server_name}**: `{command}`")
    else:
        st.info("No hay servidores MCP configurados")


def show_quick_actions(config_manager):
    """Muestra acciones rápidas."""

    st.subheader("⚡ Acciones Rápidas")

    # Verificar estado para habilitar/deshabilitar acciones
    validation = config_manager.validate_config()
    is_ready = all(validation.values())

    # Acción: Ir a procesamiento
    if st.button("📝 Procesar Contenido", use_container_width=True, disabled=not is_ready):
        st.switch_page("pages/3_📝_Procesamiento.py")

    if not is_ready:
        st.caption("⚠️ Completa la configuración primero")

    # Acción: Configurar sistema
    if st.button("⚙️ Configurar Sistema", use_container_width=True):
        st.switch_page("pages/2_⚙️_Configuración.py")

    # Acción: Ver agentes
    if st.button("🤖 Gestionar Agentes", use_container_width=True):
        st.switch_page("pages/4_🤖_Agentes.py")

    st.markdown("---")

    # Enlaces útiles
    st.subheader("🔗 Enlaces Útiles")

    st.markdown("""
    - [📚 Documentación FastAgent](https://fast-agent.ai/)
    - [🐙 Repositorio GitHub](https://github.com/evalstate/fast-agent)
    - [❓ Reportar Issue](https://github.com/evalstate/fast-agent/issues)
    - [💬 Discusiones](https://github.com/evalstate/fast-agent/discussions)
    """)

    # Tips de uso
    with st.expander("💡 Tips de Uso"):
        st.markdown("""
        **Para mejores resultados:**

        1. **Configura Azure OpenAI** para mejor calidad en español
        2. **Usa auto-detección** para seleccionar el agente apropiado
        3. **Incluye documentos adicionales** para contexto enriquecido
        4. **Ajusta rate limiting** según tu plan de Azure
        5. **Revisa los logs** si encuentras errores 429
        """)


if __name__ == "__main__":
    main()