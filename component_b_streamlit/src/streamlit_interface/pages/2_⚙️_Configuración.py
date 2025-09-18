#!/usr/bin/env python3
"""
Página de Configuración
======================

Configuración de proveedores LLM y parámetros del sistema.
"""

import streamlit as st
import sys
from pathlib import Path

# Configurar path para imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.streamlit_interface.core.config_manager import ConfigManager
from src.streamlit_interface.components.ui_components import (
    setup_page_config, show_sidebar, show_config_status
)

def main():
    """Página principal de configuración."""
    
    setup_page_config()
    
    # Inicializar config manager
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    config_manager = st.session_state.config_manager
    
    show_sidebar()
    
    st.title("⚙️ Configuración del Sistema")
    
    # Estado general
    show_config_status(config_manager)
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3 = st.tabs([
        "🔗 Proveedores LLM", 
        "🎯 Modelo Por Defecto", 
        "⏱️ Rate Limiting"
    ])
    
    with tab1:
        show_providers_config(config_manager)
    
    with tab2:
        show_default_model_config(config_manager)
    
    with tab3:
        show_rate_limiting_config(config_manager)

def show_providers_config(config_manager):
    """Muestra configuración de proveedores LLM."""
    
    st.header("Configuración de Proveedores LLM")
    
    # Selección de proveedor a configurar
    provider_options = {
        "azure": "🟦 Azure OpenAI",
        "generic": "🦙 Ollama (Local/Remoto)", 
        "openai": "🟢 OpenAI",
        "anthropic": "🟣 Anthropic Claude"
    }
    
    selected_provider = st.selectbox(
        "Selecciona el proveedor a configurar:",
        options=list(provider_options.keys()),
        format_func=lambda x: provider_options[x]
    )
    
    if selected_provider:
        current_config = config_manager.get_provider_config(selected_provider)
        
        # Estado actual del proveedor
        is_configured = config_manager.is_provider_configured(selected_provider)
        
        if is_configured:
            st.success(f"✅ {provider_options[selected_provider]} está configurado")
        else:
            st.warning(f"⚠️ {provider_options[selected_provider]} no está configurado")
        
        # Formulario específico por proveedor
        if selected_provider == "azure":
            show_azure_form(current_config, config_manager)
        elif selected_provider == "generic":
            show_ollama_form(current_config, config_manager)
        elif selected_provider == "openai":
            show_openai_form(current_config, config_manager)
        elif selected_provider == "anthropic":
            show_anthropic_form(current_config, config_manager)

def show_azure_form(config: dict, config_manager):
    """Formulario para Azure OpenAI."""
    with st.form("azure_config"):
        api_key = st.text_input(
            "API Key",
            value=config.get('api_key', ''),
            type="password",
            help="Tu Azure OpenAI API key"
        )
        
        base_url = st.text_input(
            "Base URL",
            value=config.get('base_url', ''),
            help="URL de tu recurso Azure OpenAI"
        )
        
        deployment = st.text_input(
            "Deployment",
            value=config.get('azure_deployment', 'gpt-4.1'),
            help="Nombre del deployment en Azure"
        )
        
        submitted = st.form_submit_button("💾 Guardar Configuración Azure")
        
        if submitted:
            new_config = {
                'api_key': api_key,
                'base_url': base_url,
                'azure_deployment': deployment,
                'api_version': '2025-01-01-preview',
                'max_retries': 8,
                'retry_delay': 90,
                'timeout': 180
            }
            
            config_manager.update_provider_config('azure', new_config)
            st.success("✅ Configuración de Azure guardada")
            st.rerun()

def show_ollama_form(config: dict, config_manager):
    """Formulario para Ollama."""
    with st.form("ollama_config"):
        base_url = st.text_input(
            "URL del Servidor Ollama",
            value=config.get('base_url', 'http://localhost:11434/v1'),
            help="URL completa del servidor Ollama (incluye /v1)"
        )
        
        st.info("💡 **Tip**: Para servidor local usa `http://localhost:11434/v1`")
        
        submitted = st.form_submit_button("💾 Guardar Configuración Ollama")
        
        if submitted:
            new_config = {
                'api_key': 'ollama',
                'base_url': base_url
            }
            
            config_manager.update_provider_config('generic', new_config)
            st.success("✅ Configuración de Ollama guardada")
            st.rerun()

def show_openai_form(config: dict, config_manager):
    """Formulario para OpenAI."""
    with st.form("openai_config"):
        api_key = st.text_input(
            "API Key",
            value=config.get('api_key', ''),
            type="password",
            help="Tu OpenAI API key"
        )
        
        submitted = st.form_submit_button("💾 Guardar Configuración OpenAI")
        
        if submitted:
            new_config = {'api_key': api_key}
            config_manager.update_provider_config('openai', new_config)
            st.success("✅ Configuración de OpenAI guardada")
            st.rerun()

def show_anthropic_form(config: dict, config_manager):
    """Formulario para Anthropic."""
    with st.form("anthropic_config"):
        api_key = st.text_input(
            "API Key",
            value=config.get('api_key', ''),
            type="password",
            help="Tu Anthropic API key"
        )
        
        submitted = st.form_submit_button("💾 Guardar Configuración Anthropic")
        
        if submitted:
            new_config = {'api_key': api_key}
            config_manager.update_provider_config('anthropic', new_config)
            st.success("✅ Configuración de Anthropic guardada")
            st.rerun()

def show_default_model_config(config_manager):
    """Configuración del modelo por defecto."""
    
    st.header("Modelo Por Defecto")
    
    current_model = config_manager.get_default_model()
    
    st.info(f"🎯 **Modelo actual**: `{current_model}`")
    
    # Opciones de modelo según proveedores configurados
    model_options = []
    
    if config_manager.is_provider_configured('azure'):
        model_options.extend(["azure.gpt-4.1", "azure.gpt-4o", "azure.gpt-4"])
    
    if config_manager.is_provider_configured('generic'):
        model_options.extend(["generic.llama3.1", "generic.mistral"])
    
    if config_manager.is_provider_configured('openai'):
        model_options.extend(["gpt-4o", "gpt-4", "o1-mini"])
    
    if config_manager.is_provider_configured('anthropic'):
        model_options.extend(["haiku", "sonnet", "opus"])
    
    if not model_options:
        st.warning("⚠️ No hay proveedores configurados. Configura al menos uno en la pestaña 'Proveedores LLM'.")
        return
    
    # Selección de nuevo modelo
    new_model = st.selectbox(
        "Selecciona el modelo por defecto:",
        options=model_options,
        index=model_options.index(current_model) if current_model in model_options else 0
    )
    
    if st.button("💾 Actualizar Modelo Por Defecto"):
        config_manager.set_default_model(new_model)
        st.success(f"✅ Modelo por defecto actualizado a: `{new_model}`")
        st.rerun()

def show_rate_limiting_config(config_manager):
    """Configuración de rate limiting."""
    
    st.header("Configuración de Rate Limiting")
    
    st.info("⚡ Estos parámetros controlan cómo el sistema maneja los límites de las APIs.")
    
    current_config = config_manager.get_rate_limiting_config()
    
    with st.form("rate_limiting_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            requests_per_minute = st.number_input(
                "Requests por Minuto",
                value=current_config.get('requests_per_minute', 3),
                min_value=1,
                max_value=60,
                help="Máximo número de requests por minuto"
            )
            
            delay_between_requests = st.number_input(
                "Delay entre Requests (segundos)",
                value=current_config.get('delay_between_requests', 30),
                min_value=5,
                max_value=300,
                help="Tiempo de espera entre requests consecutivos"
            )
        
        with col2:
            max_tokens = st.number_input(
                "Max Tokens por Request",
                value=current_config.get('max_tokens_per_request', 50000),
                min_value=1000,
                max_value=100000,
                step=1000,
                help="Máximo número de tokens por request individual"
            )
            
            backoff_factor = st.number_input(
                "Factor de Backoff",
                value=current_config.get('backoff_factor', 3.0),
                min_value=1.0,
                max_value=10.0,
                step=0.5,
                help="Multiplicador para el tiempo de espera en reintentos"
            )
        
        # Presets comunes
        st.subheader("Presets Comunes")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("🐌 Conservador"):
                requests_per_minute = 2
                delay_between_requests = 45
                max_tokens = 30000
                backoff_factor = 4.0
        
        with col2:
            if st.form_submit_button("⚖️ Balanceado"):
                requests_per_minute = 5
                delay_between_requests = 20
                max_tokens = 50000
                backoff_factor = 2.0
        
        with col3:
            if st.form_submit_button("🚀 Agresivo"):
                requests_per_minute = 10
                delay_between_requests = 10
                max_tokens = 80000
                backoff_factor = 1.5
        
        submitted = st.form_submit_button("💾 Guardar Configuración")
        
        if submitted:
            new_config = {
                'max_tokens_per_request': max_tokens,
                'requests_per_minute': requests_per_minute,
                'backoff_factor': backoff_factor,
                'max_backoff': 600,
                'delay_between_requests': delay_between_requests
            }
            
            config_manager.update_rate_limiting_config(new_config)
            st.success("✅ Configuración de rate limiting guardada")

if __name__ == "__main__":
    main()