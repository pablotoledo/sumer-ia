#!/usr/bin/env python3
"""
Página de Configuración Simplificada
====================================

Configuración con 3 niveles: Básica, Avanzada y Experto.
"""

import streamlit as st
import sys
from pathlib import Path

# Añadir el directorio padre al path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir.parent))
sys.path.append(str(parent_dir))

from components.config_manager import ConfigManager
from components.ui_components import (
    setup_page_config, show_sidebar, show_provider_form, 
    show_config_status
)


def main():
    """Página principal de configuración."""
    
    setup_page_config()
    
    # Inicializar config manager
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    config_manager = st.session_state.config_manager
    
    show_sidebar()
    
    st.title("⚙️ Configuración")
    
    # Estado del sistema (compacto)
    show_compact_status(config_manager)
    
    st.markdown("---")
    
    # Tabs simplificados
    tab1, tab2, tab3 = st.tabs([
        "⭐ Básica",
        "🔧 Avanzada", 
        "🚀 Experto"
    ])
    
    with tab1:
        show_basic_config(config_manager)
    
    with tab2:
        show_advanced_config(config_manager)
    
    with tab3:
        show_expert_config(config_manager)


def show_compact_status(config_manager):
    """Muestra estado del sistema en línea compacta."""
    
    validation = config_manager.validate_config()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if validation.get('has_provider'):
            st.success("✅ Proveedor")
        else:
            st.error("❌ Sin proveedor")
    
    with col2:
        if validation.get('valid_model'):
            st.success("✅ Modelo")
        else:
            st.warning("⚠️ Sin modelo")
    
    with col3:
        if validation.get('rate_limiting_ok'):
            st.success("✅ Rate Limit")
        else:
            st.warning("⚠️ Rate Limit")
    
    with col4:
        if all(validation.values()):
            st.success("✅ Listo")
        else:
            st.error("❌ Incompleto")


def show_basic_config(config_manager):
    """Tab Básica: Solo proveedor, API key y modelo."""
    
    st.header("Configuración Básica")
    st.caption("Solo 3 campos para empezar a procesar")
    
    # Selección de proveedor
    provider_options = {
        "azure": "🔷 Azure OpenAI (Recomendado)",
        "generic": "🦙 Ollama (Local/Gratuito)"
    }
    
    current_model = config_manager.get_default_model()
    current_provider = current_model.split('.')[0] if '.' in current_model else 'azure'
    
    selected_provider = st.selectbox(
        "1️⃣ Proveedor LLM:",
        options=list(provider_options.keys()),
        format_func=lambda x: provider_options[x],
        index=0 if current_provider == 'azure' else 1
    )
    
    current_config = config_manager.get_provider_config(selected_provider)
    is_configured = config_manager.is_provider_configured(selected_provider)
    
    # Formulario según proveedor
    with st.form("basic_provider_form"):
        if selected_provider == "azure":
            api_key = st.text_input(
                "2️⃣ API Key:",
                value=current_config.get('api_key', '') if current_config else '',
                type="password",
                placeholder="Tu API key de Azure"
            )
            
            base_url = st.text_input(
                "3️⃣ Base URL:",
                value=current_config.get('base_url', '') if current_config else '',
                placeholder="https://tu-recurso.cognitiveservices.azure.com/"
            )
            
            # Deployment con valor por defecto inteligente
            deployment = st.text_input(
                "Deployment (modelo):",
                value=current_config.get('azure_deployment', 'gpt-4.1') if current_config else 'gpt-4.1'
            )
            
            if st.form_submit_button("💾 Guardar Configuración", type="primary", use_container_width=True):
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
                    st.error("❌ Completa API Key y Base URL")
        
        else:  # generic/Ollama
            base_url = st.text_input(
                "2️⃣ URL de Ollama:",
                value=current_config.get('base_url', 'http://localhost:11434/v1') if current_config else 'http://localhost:11434/v1'
            )
            
            model = st.text_input(
                "3️⃣ Modelo:",
                value="llama3.1",
                help="Modelos comunes: llama3.1, mistral, codellama"
            )
            
            if st.form_submit_button("💾 Guardar Configuración", type="primary", use_container_width=True):
                config_manager.update_provider_config("generic", {
                    "api_key": "ollama",
                    "base_url": base_url
                })
                config_manager.set_default_model(f"generic.{model}")
                st.success("✅ Configuración guardada")
                st.rerun()
    
    # Indicador de estado
    if is_configured:
        st.success(f"✅ **{provider_options[selected_provider]}** está configurado")
        st.info(f"🎯 Modelo actual: `{config_manager.get_default_model()}`")
    else:
        st.warning("⚠️ Completa la configuración para procesar contenido")


def show_advanced_config(config_manager):
    """Tab Avanzada: Rate limiting con presets y opciones adicionales."""
    
    st.header("Configuración Avanzada")
    st.caption("Rate limiting y opciones de procesamiento")
    
    # Rate Limiting con presets destacados
    st.subheader("⏱️ Rate Limiting")
    
    current_config = config_manager.get_rate_limiting_config()
    
    # Presets como buttons prominentes
    st.markdown("**Presets recomendados:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🐌 Conservador\n(S0 Tier)", use_container_width=True):
            apply_preset(config_manager, 'conservador')
    
    with col2:
        if st.button("⚖️ Balanceado\n(Recomendado)", use_container_width=True):
            apply_preset(config_manager, 'balanceado')
    
    with col3:
        if st.button("🚀 Agresivo\n(Alto tier)", use_container_width=True):
            apply_preset(config_manager, 'agresivo')
    
    # Mostrar valores actuales
    st.markdown("---")
    st.markdown("**Valores actuales:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Delay entre requests", f"{current_config.get('delay_between_requests', 30)}s")
        st.metric("Max reintentos", current_config.get('max_retries', 3))
    
    with col2:
        st.metric("Requests/min", current_config.get('requests_per_minute', 3))
        st.metric("Retry delay base", f"{current_config.get('retry_base_delay', 60)}s")
    
    # Ajuste manual (colapsado)
    with st.expander("🔧 Ajuste manual"):
        with st.form("rate_limiting_manual"):
            col1, col2 = st.columns(2)
            
            with col1:
                delay_between = st.number_input(
                    "Delay entre requests (s)",
                    value=current_config.get('delay_between_requests', 30),
                    min_value=0, max_value=120
                )
                max_retries = st.number_input(
                    "Max reintentos",
                    value=current_config.get('max_retries', 3),
                    min_value=0, max_value=10
                )
            
            with col2:
                requests_per_min = st.number_input(
                    "Requests/min",
                    value=current_config.get('requests_per_minute', 3),
                    min_value=1, max_value=60
                )
                retry_base_delay = st.number_input(
                    "Retry delay base (s)",
                    value=current_config.get('retry_base_delay', 60),
                    min_value=10, max_value=300
                )
            
            if st.form_submit_button("💾 Guardar"):
                config_manager.update_rate_limiting_config({
                    'delay_between_requests': delay_between,
                    'max_retries': max_retries,
                    'requests_per_minute': requests_per_min,
                    'retry_base_delay': retry_base_delay,
                    'max_tokens_per_request': current_config.get('max_tokens_per_request', 50000)
                })
                st.success("✅ Guardado")
                st.rerun()
    
    # Proveedores adicionales
    st.markdown("---")
    st.subheader("🔗 Proveedores Adicionales")
    
    other_providers = {
        "openai": "🟢 OpenAI",
        "anthropic": "🟣 Anthropic Claude"
    }
    
    for provider_id, provider_name in other_providers.items():
        is_configured = config_manager.is_provider_configured(provider_id)
        status = "✅" if is_configured else "❌"
        
        with st.expander(f"{status} {provider_name}"):
            current = config_manager.get_provider_config(provider_id) or {}
            
            if provider_id == "openai":
                api_key = st.text_input(
                    "OpenAI API Key:",
                    value=current.get('api_key', ''),
                    type="password",
                    key=f"openai_key"
                )
                if st.button("Guardar OpenAI", key="save_openai"):
                    if api_key:
                        config_manager.update_provider_config("openai", {"api_key": api_key})
                        st.success("✅ Guardado")
                        st.rerun()
            
            elif provider_id == "anthropic":
                api_key = st.text_input(
                    "Anthropic API Key:",
                    value=current.get('api_key', ''),
                    type="password",
                    key=f"anthropic_key"
                )
                if st.button("Guardar Anthropic", key="save_anthropic"):
                    if api_key:
                        config_manager.update_provider_config("anthropic", {"api_key": api_key})
                        st.success("✅ Guardado")
                        st.rerun()


def show_expert_config(config_manager):
    """Tab Experto: Funciones avanzadas con advertencia."""
    
    st.header("Configuración Experto")
    
    # Toggle de modo experto
    if 'expert_mode_enabled' not in st.session_state:
        st.session_state.expert_mode_enabled = False
    
    if not st.session_state.expert_mode_enabled:
        st.warning("""
        ⚠️ **Modo Experto**
        
        Esta sección contiene configuraciones avanzadas que pueden afectar
        el funcionamiento del sistema si se modifican incorrectamente.
        """)
        
        if st.button("🔓 Habilitar Modo Experto", type="primary"):
            st.session_state.expert_mode_enabled = True
            st.rerun()
        return
    
    st.success("🔓 Modo Experto habilitado")
    
    if st.button("🔒 Deshabilitar Modo Experto"):
        st.session_state.expert_mode_enabled = False
        st.rerun()
    
    st.markdown("---")
    
    # Sección 1: Modelo por defecto manual
    st.subheader("🎯 Modelo Por Defecto")
    
    current_model = config_manager.get_default_model()
    
    model_options = []
    if config_manager.is_provider_configured('azure'):
        model_options.extend(["azure.gpt-4.1", "azure.gpt-4o", "azure.gpt-4"])
    if config_manager.is_provider_configured('generic'):
        model_options.extend(["generic.llama3.1", "generic.mistral", "generic.codellama"])
    if config_manager.is_provider_configured('openai'):
        model_options.extend(["gpt-4o", "gpt-4", "o1-mini"])
    if config_manager.is_provider_configured('anthropic'):
        model_options.extend(["haiku", "sonnet", "opus"])
    
    if model_options:
        new_model = st.selectbox(
            "Modelo:",
            options=model_options,
            index=model_options.index(current_model) if current_model in model_options else 0
        )
        
        if st.button("Cambiar modelo"):
            config_manager.set_default_model(new_model)
            st.success(f"✅ Modelo cambiado a: {new_model}")
            st.rerun()
    else:
        st.warning("⚠️ Sin proveedores configurados")
    
    st.markdown("---")
    
    # Sección 2: Exportar/Importar
    st.subheader("📦 Exportar/Importar Configuración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Exportar Config"):
            config_json = config_manager.export_config_json()
            st.download_button(
                label="💾 Descargar JSON",
                data=config_json,
                file_name="fastagent_config.json",
                mime="application/json"
            )
    
    with col2:
        uploaded = st.file_uploader("📥 Importar", type=['json'], key="import_config")
        if uploaded:
            try:
                import json
                new_config = json.load(uploaded)
                config_manager.update_config(new_config)
                st.success("✅ Configuración importada")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    
    # Sección 3: Reset
    st.subheader("🔄 Reset Configuración")
    
    st.error("⚠️ **PELIGRO**: Esto eliminará toda la configuración actual")
    
    confirm = st.checkbox("Confirmo que quiero resetear la configuración")
    
    if confirm:
        if st.button("🗑️ Resetear Todo", type="primary"):
            config_manager.reset_to_defaults()
            st.session_state.expert_mode_enabled = False
            st.success("✅ Configuración reseteada")
            st.rerun()
    
    st.markdown("---")
    
    # Sección 4: Debug
    st.subheader("🔍 Debug")
    
    with st.expander("Ver configuración completa (YAML)"):
        config = config_manager.get_config()
        st.json(config)
    
    with st.expander("Ver validación"):
        validation = config_manager.validate_config()
        for key, value in validation.items():
            status = "✅" if value else "❌"
            st.write(f"{status} {key}")


def apply_preset(config_manager, preset_name: str):
    """Aplica un preset de rate limiting."""
    
    presets = {
        'conservador': {
            'max_tokens_per_request': 30000,
            'requests_per_minute': 2,
            'max_retries': 5,
            'delay_between_requests': 45,
            'retry_base_delay': 90
        },
        'balanceado': {
            'max_tokens_per_request': 50000,
            'requests_per_minute': 5,
            'max_retries': 3,
            'delay_between_requests': 20,
            'retry_base_delay': 60
        },
        'agresivo': {
            'max_tokens_per_request': 80000,
            'requests_per_minute': 10,
            'max_retries': 2,
            'delay_between_requests': 10,
            'retry_base_delay': 30
        }
    }
    
    if preset_name in presets:
        config_manager.update_rate_limiting_config(presets[preset_name])
        st.success(f"✅ Preset '{preset_name}' aplicado")
        st.rerun()


if __name__ == "__main__":
    main()