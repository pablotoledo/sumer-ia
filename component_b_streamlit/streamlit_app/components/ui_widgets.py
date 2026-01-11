"""
UI Widgets - Componentes Reutilizables
=====================================

Componentes de UI reutilizables para la aplicación FastAgent.
"""

import streamlit as st
from typing import Dict, Any, Callable, Optional


def simple_provider_selector(options: Dict[str, str], current: str = 'azure') -> str:
    """Selector simple de proveedor LLM."""
    return st.selectbox(
        "Proveedor:",
        options=list(options.keys()),
        format_func=lambda x: options[x],
        index=list(options.keys()).index(current) if current in options else 0
    )


def rate_limit_preset_selector(on_select: Callable[[str], None]) -> None:
    """Selector de presets de rate limiting."""
    
    presets = {
        'conservador': ('🐌 Conservador', 'Para S0 Tier de Azure'),
        'balanceado': ('⚖️ Balanceado', 'Recomendado para la mayoría'),
        'agresivo': ('🚀 Agresivo', 'Para tiers altos de Azure')
    }
    
    cols = st.columns(len(presets))
    
    for i, (key, (label, help_text)) in enumerate(presets.items()):
        with cols[i]:
            if st.button(label, help=help_text, use_container_width=True):
                on_select(key)


def collapsible_advanced_section(
    title: str, 
    content_func: Callable[[], None],
    warning_text: Optional[str] = None,
    expanded: bool = False
) -> None:
    """Sección avanzada colapsable con advertencia opcional."""
    
    with st.expander(title, expanded=expanded):
        if warning_text:
            st.warning(warning_text)
        content_func()


def status_indicator(
    is_ok: bool, 
    ok_text: str, 
    error_text: str,
    inline: bool = True
) -> None:
    """Indicador de estado consistente."""
    
    if is_ok:
        if inline:
            st.success(f"✅ {ok_text}")
        else:
            st.success(ok_text)
    else:
        if inline:
            st.error(f"❌ {error_text}")
        else:
            st.error(error_text)


def processing_progress(
    current: int, 
    total: int, 
    status_text: str
) -> tuple:
    """
    Barra de progreso consistente para procesamiento.
    
    Returns:
        Tuple of (progress_bar, status_element) for later updates.
    """
    progress = current / total if total > 0 else 0
    
    progress_bar = st.progress(progress)
    status_element = st.empty()
    status_element.text(status_text)
    
    return progress_bar, status_element


def metrics_row(metrics: Dict[str, Any], columns: int = 4) -> None:
    """Fila de métricas consistente."""
    
    cols = st.columns(columns)
    
    for i, (label, value) in enumerate(metrics.items()):
        with cols[i % columns]:
            st.metric(label, value)


def config_form_field(
    label: str,
    value: Any,
    field_type: str = "text",
    help_text: Optional[str] = None,
    **kwargs
) -> Any:
    """Campo de formulario de configuración consistente."""
    
    if field_type == "text":
        return st.text_input(label, value=str(value) if value else "", help=help_text, **kwargs)
    elif field_type == "password":
        return st.text_input(label, value=str(value) if value else "", type="password", help=help_text, **kwargs)
    elif field_type == "number":
        return st.number_input(label, value=int(value) if value else 0, help=help_text, **kwargs)
    elif field_type == "checkbox":
        return st.checkbox(label, value=bool(value), help=help_text, **kwargs)
    elif field_type == "select":
        return st.selectbox(label, help=help_text, **kwargs)
    else:
        return st.text_input(label, value=str(value) if value else "", help=help_text, **kwargs)


def action_buttons(
    primary_label: str,
    primary_action: Callable[[], None],
    secondary_label: Optional[str] = None,
    secondary_action: Optional[Callable[[], None]] = None,
    disabled: bool = False
) -> None:
    """Botones de acción consistentes."""
    
    if secondary_label and secondary_action:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(primary_label, type="primary", use_container_width=True, disabled=disabled):
                primary_action()
        with col2:
            if st.button(secondary_label, use_container_width=True):
                secondary_action()
    else:
        if st.button(primary_label, type="primary", use_container_width=True, disabled=disabled):
            primary_action()


def compact_status_bar(validation: Dict[str, bool]) -> None:
    """Barra de estado compacta para sidebar o header."""
    
    status_items = [
        ('has_provider', 'Proveedor', 'Sin proveedor'),
        ('valid_model', 'Modelo', 'Sin modelo'),
        ('rate_limiting_ok', 'Rate Limit', 'Rate Limit'),
    ]
    
    cols = st.columns(len(status_items) + 1)
    
    for i, (key, ok_text, error_text) in enumerate(status_items):
        with cols[i]:
            is_ok = validation.get(key, False)
            if is_ok:
                st.success(f"✅ {ok_text}")
            else:
                st.error(f"❌ {error_text}")
    
    with cols[-1]:
        if all(validation.values()):
            st.success("✅ Listo")
        else:
            st.error("❌ Incompleto")
