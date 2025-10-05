#!/usr/bin/env python3
"""
Página de Configuración
======================

Configuración de proveedores LLM y parámetros del sistema.
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
    
    st.title("⚙️ Configuración del Sistema")
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔗 Proveedores LLM", 
        "🎯 Modelo Por Defecto", 
        "⏱️ Rate Limiting", 
        "🔧 Avanzado"
    ])
    
    with tab1:
        show_providers_config(config_manager)
    
    with tab2:
        show_default_model_config(config_manager)
    
    with tab3:
        show_rate_limiting_config(config_manager)
    
    with tab4:
        show_advanced_config(config_manager)

def show_providers_config(config_manager):
    """Muestra configuración de proveedores LLM."""
    
    st.header("Configuración de Proveedores LLM")
    
    # Estado general
    show_config_status(config_manager)
    
    st.markdown("---")
    
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
        st.markdown("---")
        current_config = config_manager.get_provider_config(selected_provider)
        
        # Estado actual del proveedor
        is_configured = config_manager.is_provider_configured(selected_provider)
        
        if is_configured:
            st.success(f"✅ {provider_options[selected_provider]} está configurado")
        else:
            st.warning(f"⚠️ {provider_options[selected_provider]} no está configurado")
        
        # Formulario de configuración
        show_provider_form(selected_provider, current_config, config_manager)
        
        # Información adicional por proveedor
        show_provider_info(selected_provider)

def show_provider_info(provider: str):
    """Muestra información específica del proveedor."""
    
    if provider == "azure":
        with st.expander("ℹ️ Información sobre Azure OpenAI"):
            st.markdown("""
            **Azure OpenAI** es la opción recomendada para producción.
            
            **Ventajas:**
            - Mejor calidad en español
            - Respeta el idioma del texto original
            - Mayor retención de contenido
            
            **Configuración requerida:**
            - API Key de tu recurso Azure OpenAI
            - URL base del recurso (ej: https://mi-recurso.cognitiveservices.azure.com/)
            - Nombre del deployment
            - Versión de la API
            
            **Nota sobre Rate Limiting:**
            Azure OpenAI tiene límites estrictos. Configurar delays apropiados es crucial.
            """)
    
    elif provider == "generic":
        with st.expander("ℹ️ Información sobre Ollama"):
            st.markdown("""
            **Ollama** permite usar modelos locales sin API keys.
            
            **Ventajas:**
            - Sin rate limits
            - Privacidad total (local)
            - Gratuito
            
            **Desventajas:**
            - Puede responder en inglés aunque el input sea español
            - Menor calidad general comparado con Azure
            
            **Configuración:**
            - Para servidor local: `http://localhost:11434/v1`
            - Para servidor remoto: `http://IP_DEL_SERVIDOR:11434/v1`
            
            **Modelos recomendados:**
            - llama3.1 (general)
            - mistral (español)
            - codellama (código)
            """)
    
    elif provider == "openai":
        with st.expander("ℹ️ Información sobre OpenAI"):
            st.markdown("""
            **OpenAI** ofrece los modelos GPT originales.
            
            **Ventajas:**
            - Acceso a modelos o1/o3 con reasoning
            - API ampliamente soportada
            - Buena documentación
            
            **Configuración:**
            - Solo requiere API Key
            - Modelos disponibles: gpt-4o, gpt-4, o1-mini, o3-mini
            """)
    
    elif provider == "anthropic":
        with st.expander("ℹ️ Información sobre Anthropic"):
            st.markdown("""
            **Anthropic Claude** es excelente para análisis y razonamiento.
            
            **Ventajas:**
            - Muy bueno para análisis detallado
            - Contexto largo (200k tokens)
            - Excelente seguimiento de instrucciones
            
            **Modelos disponibles:**
            - haiku (rápido y económico)
            - sonnet (balance calidad/velocidad)
            - opus (máxima calidad)
            """)

def show_default_model_config(config_manager):
    """Configuración del modelo por defecto."""
    
    st.header("Modelo Por Defecto")
    
    current_model = config_manager.get_default_model()
    
    st.info(f"🎯 **Modelo actual**: `{current_model}`")
    
    # Opciones de modelo según proveedores configurados
    model_options = []
    
    if config_manager.is_provider_configured('azure'):
        model_options.extend([
            "azure.gpt-4.1",
            "azure.gpt-4o", 
            "azure.gpt-4"
        ])
    
    if config_manager.is_provider_configured('generic'):
        model_options.extend([
            "generic.llama3.1",
            "generic.mistral",
            "generic.codellama"
        ])
    
    if config_manager.is_provider_configured('openai'):
        model_options.extend([
            "gpt-4o",
            "gpt-4",
            "o1-mini",
            "o3-mini"
        ])
    
    if config_manager.is_provider_configured('anthropic'):
        model_options.extend([
            "haiku",
            "sonnet", 
            "opus"
        ])
    
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
    
    # Información sobre modelos
    with st.expander("ℹ️ Información sobre Modelos"):
        st.markdown("""
        **Azure OpenAI:**
        - `azure.gpt-4.1`: Último modelo, mejor rendimiento
        - `azure.gpt-4o`: Optimizado para velocidad
        - `azure.gpt-4`: Modelo estándar
        
        **Ollama:**
        - `generic.llama3.1`: Modelo general, buena calidad
        - `generic.mistral`: Especializado en español
        - `generic.codellama`: Optimizado para código
        
        **OpenAI:**
        - `gpt-4o`: Optimizado para velocidad y multimodal
        - `o1-mini`: Con capacidades de reasoning
        - `o3-mini`: Última generación con reasoning avanzado
        
        **Anthropic:**
        - `haiku`: Rápido y económico
        - `sonnet`: Balance perfecto
        - `opus`: Máxima calidad y capacidad
        """)

def show_rate_limiting_config(config_manager):
    """Configuración de rate limiting."""
    
    st.header("Configuración de Rate Limiting")
    
    st.info("⚡ Estos parámetros controlan cómo el sistema maneja los límites de las APIs.")
    
    current_config = config_manager.get_rate_limiting_config()
    
    with st.form("rate_limiting_form"):
        st.subheader("Parámetros de Rate Limiting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_tokens = st.number_input(
                "Max Tokens por Request",
                value=current_config.get('max_tokens_per_request', 50000),
                min_value=1000,
                max_value=100000,
                step=1000,
                help="Máximo número de tokens por request individual"
            )
            
            requests_per_minute = st.number_input(
                "Requests por Minuto",
                value=current_config.get('requests_per_minute', 3),
                min_value=1,
                max_value=60,
                help="Máximo número de requests por minuto"
            )
        
        with col2:
            max_retries = st.number_input(
                "Máximo de Reintentos",
                value=current_config.get('max_retries', 3),
                min_value=0,
                max_value=10,
                help="Número máximo de reintentos en caso de error 429"
            )

            delay_between_requests = st.number_input(
                "Delay entre Requests (segundos)",
                value=current_config.get('delay_between_requests', 30),
                min_value=0,
                max_value=300,
                help="Tiempo de espera entre requests consecutivos (proactivo)"
            )
        
        retry_base_delay = st.number_input(
            "Delay Base para Reintentos (segundos)",
            value=current_config.get('retry_base_delay', 60),
            min_value=10,
            max_value=300,
            help="Tiempo inicial de espera en el primer reintento (se duplica exponencialmente)"
        )
        
        # Presets comunes
        st.subheader("Presets Comunes")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("🐌 Conservador (S0 Tier)"):
                max_tokens = 30000
                requests_per_minute = 2
                max_retries = 5
                delay_between_requests = 45
                retry_base_delay = 90

        with col2:
            if st.form_submit_button("⚖️ Balanceado"):
                max_tokens = 50000
                requests_per_minute = 5
                max_retries = 3
                delay_between_requests = 20
                retry_base_delay = 60

        with col3:
            if st.form_submit_button("🚀 Agresivo"):
                max_tokens = 80000
                requests_per_minute = 10
                max_retries = 2
                delay_between_requests = 10
                retry_base_delay = 30
        
        submitted = st.form_submit_button("💾 Guardar Configuración")
        
        if submitted:
            new_config = {
                'max_tokens_per_request': max_tokens,
                'requests_per_minute': requests_per_minute,
                'max_retries': max_retries,
                'retry_base_delay': retry_base_delay,
                'delay_between_requests': delay_between_requests
            }

            config_manager.update_rate_limiting_config(new_config)
            st.success("✅ Configuración de rate limiting guardada")

def show_advanced_config(config_manager):
    """Configuración avanzada."""
    
    st.header("Configuración Avanzada")
    
    # Exportar configuración
    st.subheader("🔧 Exportar/Importar Configuración")
    
    if st.button("📤 Exportar Configuración Actual"):
        config_json = config_manager.export_config_json()
        st.download_button(
            label="💾 Descargar configuración.json",
            data=config_json,
            file_name="fastagent_config.json",
            mime="application/json"
        )
    
    # Reset configuración
    st.subheader("🔄 Reset Configuración")
    
    st.warning("⚠️ **Cuidado**: Esto borrará toda la configuración actual.")
    
    if st.button("🗑️ Resetear a Valores Por Defecto"):
        if st.button("✅ Confirmar Reset", type="primary"):
            config_manager.reset_to_defaults()
            st.success("✅ Configuración reseteada")
            st.rerun()
    
    # Información del sistema
    st.subheader("📊 Información del Sistema")
    
    config = config_manager.get_config()
    validation = config_manager.validate_config()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Proveedores Configurados",
            len([p for p in ['azure', 'generic', 'openai', 'anthropic'] 
                if config_manager.is_provider_configured(p)])
        )
        
        st.metric(
            "Modelo Por Defecto",
            config.get('default_model', 'No configurado')
        )
    
    with col2:
        st.metric(
            "Rate Limiting",
            "✅ OK" if validation['rate_limiting_ok'] else "❌ Error"
        )
        
        st.metric(
            "Configuración Válida",
            "✅ Sí" if all(validation.values()) else "❌ No"
        )
    
    # Debug: mostrar configuración completa
    with st.expander("🔍 Ver Configuración Completa (Debug)"):
        st.json(config)

if __name__ == "__main__":
    main()