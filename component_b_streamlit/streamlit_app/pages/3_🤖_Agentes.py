#!/usr/bin/env python3
"""
Gestión de Agentes
==================

Página para gestionar y personalizar agentes FastAgent.
"""

import streamlit as st
import sys
from pathlib import Path
import streamlit.components.v1 as components

# Añadir el directorio padre al path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir.parent))
sys.path.append(str(parent_dir))

from components.config_manager import ConfigManager
from components.ui_components import (
    setup_page_config, show_sidebar, show_expandable_content
)

def main():
    """Página principal de gestión de agentes."""
    
    setup_page_config()
    
    # Inicializar config manager
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    config_manager = st.session_state.config_manager
    
    show_sidebar()
    
    st.title("🤖 Gestión de Agentes")
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Vista General",
        "✏️ Editar Prompts",
        "🧪 Probar Agentes",
        "📊 Configuración Avanzada"
    ])
    
    with tab1:
        show_agents_overview()
    
    with tab2:
        show_prompts_editor(config_manager)
    
    with tab3:
        show_agent_testing()
    
    with tab4:
        show_advanced_config()

def show_agents_overview():
    """Muestra vista general de los agentes disponibles."""
    
    st.header("📋 Agentes Disponibles")
    
    st.info("💡 FastAgent utiliza un sistema multi-agente especializado para diferentes tipos de contenido.")
    
    # Información de agentes
    agents_info = [
        {
            "name": "🔍 Auto-Detector",
            "description": "Analiza el contenido automáticamente y selecciona el agente más apropiado",
            "use_case": "Recomendado para la mayoría de casos",
            "features": [
                "Detecta reuniones diarizadas vs contenido lineal",
                "Identifica participantes en reuniones",
                "Analiza estructura del contenido",
                "Selección inteligente de agente especializado"
            ]
        },
        {
            "name": "📚 Simple Processor",
            "description": "Procesador general para contenido educativo lineal",
            "use_case": "Conferencias, clases, presentaciones, podcasts",
            "features": [
                "Segmentación semántica inteligente",
                "Generación de títulos descriptivos", 
                "Formateo profesional del contenido",
                "Q&A educativo con referencias contextuales",
                "Preservación del 85-95% del contenido original"
            ]
        },
        {
            "name": "👥 Meeting Processor", 
            "description": "Procesador especializado para reuniones diarizadas",
            "use_case": "Reuniones de Teams, Zoom, Google Meet con speakers identificados",
            "features": [
                "Extracción de decisiones tomadas",
                "Identificación de action items y responsables",
                "Seguimiento de temas no resueltos",
                "Resumen por participante principal",
                "Timeline de conversaciones"
            ]
        }
    ]
    
    for agent in agents_info:
        with st.expander(f"{agent['name']} - {agent['description']}"):
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("📝 Caso de Uso")
                st.write(agent['use_case'])
            
            with col2:
                st.subheader("✨ Características")
                for feature in agent['features']:
                    st.write(f"• {feature}")
    
    # Flujo de procesamiento
    st.markdown("---")
    st.subheader("🔄 Flujo de Procesamiento")

    # Renderizar diagrama Mermaid usando HTML directo
    mermaid_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.0/dist/mermaid.min.js"></script>
        <style>
            body {
                margin: 0;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .mermaid-container {
                width: 100%;
                height: 100%;
                overflow: auto;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                padding: 20px;
                box-sizing: border-box;
            }
            .mermaid {
                width: 100%;
                height: auto;
                min-height: 400px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            /* Estilos para el diagrama */
            .mermaid svg {
                max-width: 100%;
                height: auto;
                cursor: grab;
            }
            .mermaid svg:active {
                cursor: grabbing;
            }
        </style>
    </head>
    <body>
        <div class="mermaid-container">
            <div class="mermaid">
            graph TD
                A[📝 Contenido Input] --> B[🔍 Content Format Detector]
                B --> C{¿Formato Detectado?}
                C -->|Reunión Diarizada| D[👥 Meeting Processor]
                C -->|Contenido Lineal| E[📚 Simple Processor]
                D --> F[📋 Meeting Output]
                E --> G[📄 Educational Output]
                F --> H[📥 Documento Final]
                G --> H

                style A fill:#e1f5fe
                style B fill:#f3e5f5
                style C fill:#fff3e0
                style D fill:#e8f5e8
                style E fill:#e8f5e8
                style F fill:#fff8e1
                style G fill:#fff8e1
                style H fill:#e3f2fd
            </div>
        </div>

        <script>
            mermaid.initialize({
                startOnLoad: true,
                theme: 'default',
                flowchart: {
                    useMaxWidth: false,
                    htmlLabels: true,
                    curve: 'basis'
                }
            });

            // Hacer el SVG navegable
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() {
                    const svg = document.querySelector('.mermaid svg');
                    if (svg) {
                        let isDown = false;
                        let startX, startY, scrollLeft, scrollTop;
                        const container = document.querySelector('.mermaid-container');

                        svg.addEventListener('mousedown', (e) => {
                            isDown = true;
                            startX = e.pageX - container.offsetLeft;
                            startY = e.pageY - container.offsetTop;
                            scrollLeft = container.scrollLeft;
                            scrollTop = container.scrollTop;
                        });

                        svg.addEventListener('mouseleave', () => {
                            isDown = false;
                        });

                        svg.addEventListener('mouseup', () => {
                            isDown = false;
                        });

                        svg.addEventListener('mousemove', (e) => {
                            if (!isDown) return;
                            e.preventDefault();
                            const x = e.pageX - container.offsetLeft;
                            const y = e.pageY - container.offsetTop;
                            const walkX = (x - startX) * 2;
                            const walkY = (y - startY) * 2;
                            container.scrollLeft = scrollLeft - walkX;
                            container.scrollTop = scrollTop - walkY;
                        });
                    }
                }, 1000);
            });
        </script>
    </body>
    </html>
    """

    components.html(mermaid_html, height=600, scrolling=True)

    st.markdown("""
    **Proceso detallado:**

    1. **Análisis de Formato**: El sistema analiza automáticamente el contenido para detectar el tipo
    2. **Segmentación**: Se divide el contenido en segmentos manejables (300-1000 palabras)
    3. **Procesamiento**: Cada segmento se procesa con el agente especializado apropiado
    4. **Q&A Generation**: Se generan preguntas y respuestas educativas para cada segmento
    5. **Ensamblaje**: Se combina todo en un documento final estructurado
    """)

def show_prompts_editor(config_manager):
    """Editor de prompts de los agentes."""
    
    st.header("✏️ Editor de Prompts")
    
    st.warning("""
    ⚠️ **Advertencia**: Modificar los prompts de los agentes puede afectar significativamente 
    la calidad del procesamiento. Solo modifica si entiendes las implicaciones.
    """)
    
    # Obtener instrucciones actuales
    current_instructions = config_manager.get_agent_instructions()
    
    # Selección de agente a editar
    agent_to_edit = st.selectbox(
        "Selecciona el agente a editar:",
        options=list(current_instructions.keys()),
        format_func=lambda x: {
            'punctuator': '🔤 Punctuator - Puntuación y capitalización',
            'simple_processor': '📚 Simple Processor - Procesamiento general',
            'meeting_processor': '👥 Meeting Processor - Procesamiento de reuniones'
        }.get(x, x)
    )
    
    if agent_to_edit:
        st.subheader(f"Editando: {agent_to_edit}")
        
        # Mostrar prompt actual
        current_prompt = current_instructions[agent_to_edit]
        
        # Tabs para edición
        edit_tab1, edit_tab2 = st.tabs(["✏️ Editor", "👀 Preview"])
        
        with edit_tab1:
            # Editor de texto
            new_prompt = st.text_area(
                "Instrucciones del agente:",
                value=current_prompt,
                height=300,
                help="Define cómo debe comportarse este agente"
            )
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Guardar Cambios"):
                    # Aquí se guardarían los cambios
                    # En una implementación real, esto modificaría el código fuente o una base de datos
                    st.success("✅ Cambios guardados (simulado)")
                    st.info("🔄 Reinicia la aplicación para aplicar los cambios")
            
            with col2:
                if st.button("🔄 Restaurar Original"):
                    st.session_state[f"prompt_{agent_to_edit}"] = current_prompt
                    st.success("✅ Prompt restaurado al original")
            
            with col3:
                if st.button("📤 Exportar Prompt"):
                    st.download_button(
                        label="💾 Descargar",
                        data=new_prompt,
                        file_name=f"{agent_to_edit}_prompt.txt",
                        mime="text/plain"
                    )
        
        with edit_tab2:
            # Preview del prompt
            st.markdown("### 👀 Preview del Prompt")
            st.code(new_prompt, language="text")
            
            # Análisis del prompt
            st.markdown("### 📊 Análisis del Prompt")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📝 Caracteres", len(new_prompt))
            
            with col2:
                st.metric("🔤 Palabras", len(new_prompt.split()))
            
            with col3:
                st.metric("📄 Líneas", len(new_prompt.split('\n')))
            
            # Verificaciones de calidad
            st.markdown("### ✅ Verificaciones de Calidad")
            
            checks = {
                "Tiene instrucciones claras": "TASK:" in new_prompt or "RULES:" in new_prompt,
                "Menciona preservación de contenido": "preserve" in new_prompt.lower() or "100%" in new_prompt,
                "Define formato de salida": "format" in new_prompt.lower() or "output" in new_prompt.lower(),
                "Incluye ejemplos": "ejemplo" in new_prompt.lower() or "example" in new_prompt.lower()
            }
            
            for check, passed in checks.items():
                if passed:
                    st.success(f"✅ {check}")
                else:
                    st.warning(f"⚠️ {check}")

def show_agent_testing():
    """Interfaz para probar agentes."""
    
    st.header("🧪 Probar Agentes")
    
    st.info("💡 Prueba los agentes con contenido de ejemplo para verificar su funcionamiento.")
    
    # Selección de agente a probar
    test_agent = st.selectbox(
        "Agente a probar:",
        options=["simple_processor", "meeting_processor"],
        format_func=lambda x: {
            'simple_processor': '📚 Simple Processor',
            'meeting_processor': '👥 Meeting Processor'
        }.get(x, x)
    )
    
    # Contenido de prueba
    test_content = st.text_area(
        "Contenido de prueba:",
        height=150,
        placeholder="Introduce contenido para probar el agente..."
    )
    
    # Configuración de prueba
    with st.expander("⚙️ Configuración de Prueba"):
        use_mock_mode = st.checkbox(
            "Modo simulación", 
            value=True,
            help="Simula la respuesta del agente sin usar la API real"
        )
        
        include_qa = st.checkbox("Incluir Q&A", value=True)
        
        test_segments = st.slider(
            "Número de segmentos a simular:", 
            min_value=1, 
            max_value=5, 
            value=1
        )
    
    # Botón de prueba
    if st.button("🚀 Ejecutar Prueba"):
        if not test_content.strip():
            st.error("❌ Introduce contenido para probar")
            return
        
        with st.spinner("Probando agente..."):
            # Simular resultado de prueba
            if use_mock_mode:
                result = simulate_agent_test(test_agent, test_content, include_qa, test_segments)
                show_test_results(result)
            else:
                st.info("🔄 Modo de prueba real no implementado aún")

def simulate_agent_test(agent_name, content, include_qa, segments):
    """Simula el resultado de probar un agente."""
    
    if agent_name == "simple_processor":
        return {
            "agent": "simple_processor",
            "success": True,
            "processed_content": f"""
# Contenido Procesado

## Segmento 1: Resumen del Tema Principal

{content[:200]}...

**Puntos clave:**
- Información estructurada y clara
- Contenido formateado profesionalmente
- Preservación del contenido original

## Preguntas y Respuestas

#### ¿Cuál es el tema principal tratado?
**Respuesta:** El contenido trata sobre [tema principal identificado en el texto]...

#### ¿Qué aspectos destacan en la información?
**Respuesta:** Los aspectos más relevantes incluyen...
""",
            "metrics": {
                "original_words": len(content.split()),
                "processed_words": len(content.split()) + 50,
                "segments": segments,
                "qa_questions": 4 if include_qa else 0
            }
        }
    
    else:  # meeting_processor
        return {
            "agent": "meeting_processor",
            "success": True,
            "processed_content": f"""
# Resumen de Reunión

## 🎯 Decisiones Tomadas
1. **Decisión Principal** - Propuesta: [Participante] - Estado: ✅ Aprobado

## 📋 Action Items
- [ ] **[Responsable]**: Tarea específica (Deadline: Esta semana)

## 🔍 Temas Técnicos Discutidos

### Tema Principal
**Participantes principales**: [Lista de participantes]
**Problema**: [Descripción del problema]
**Solución acordada**: [Solución propuesta]

## ❓ Q&A Específico de la Reunión

#### ¿Qué decisiones se tomaron?
**Respuesta:** Se decidió implementar [solución específica]...
""",
            "metrics": {
                "original_words": len(content.split()),
                "processed_words": len(content.split()) + 75,
                "segments": segments,
                "decisions": 2,
                "action_items": 3
            }
        }

def show_test_results(result):
    """Muestra los resultados de la prueba."""
    
    if result["success"]:
        st.success("✅ Prueba completada exitosamente")
        
        # Métricas
        st.subheader("📊 Métricas")
        
        metrics = result["metrics"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📝 Palabras originales", metrics["original_words"])
        
        with col2:
            st.metric("📄 Palabras procesadas", metrics["processed_words"])
        
        with col3:
            if "qa_questions" in metrics:
                st.metric("❓ Preguntas Q&A", metrics["qa_questions"])
            elif "decisions" in metrics:
                st.metric("🎯 Decisiones", metrics["decisions"])
        
        # Resultado procesado
        st.subheader("📄 Contenido Procesado")
        st.markdown(result["processed_content"])
        
        # Opción de descarga
        st.download_button(
            label="💾 Descargar resultado de prueba",
            data=result["processed_content"],
            file_name=f"test_{result['agent']}.md",
            mime="text/markdown"
        )
    
    else:
        st.error("❌ Error en la prueba")
        st.code(result.get("error", "Error desconocido"))

def show_advanced_config():
    """Configuración avanzada de agentes."""
    
    st.header("📊 Configuración Avanzada")
    
    # Parámetros de segmentación
    st.subheader("✂️ Parámetros de Segmentación")
    
    with st.form("segmentation_config"):
        target_segment_size = st.slider(
            "Tamaño objetivo por segmento (palabras):",
            min_value=300,
            max_value=2000,
            value=1200,
            help="Tamaño ideal de cada segmento para procesamiento"
        )
        
        max_segments = st.slider(
            "Máximo número de segmentos:",
            min_value=5,
            max_value=50,
            value=20,
            help="Límite máximo de segmentos para evitar procesamiento excesivo"
        )
        
        semantic_threshold = st.slider(
            "Umbral de similaridad semántica:",
            min_value=0.1,
            max_value=0.9,
            value=0.6,
            step=0.1,
            help="Umbral para determinar cuándo separar contenido en segmentos"
        )
        
        if st.form_submit_button("💾 Guardar Configuración de Segmentación"):
            st.success("✅ Configuración guardada (simulado)")
    
    # Parámetros de Q&A
    st.subheader("❓ Parámetros de Q&A")
    
    with st.form("qa_config"):
        questions_per_segment = st.slider(
            "Preguntas por segmento:",
            min_value=2,
            max_value=8,
            value=4
        )
        
        qa_types = st.multiselect(
            "Tipos de preguntas a generar:",
            ["Conceptuales", "Ejemplos prácticos", "Datos específicos", "Comparaciones", "Aplicaciones"],
            default=["Conceptuales", "Ejemplos prácticos"]
        )
        
        include_references = st.checkbox(
            "Incluir referencias en respuestas",
            value=True,
            help="Las respuestas incluirán referencias al contenido original"
        )
        
        if st.form_submit_button("💾 Guardar Configuración de Q&A"):
            st.success("✅ Configuración guardada (simulado)")
    
    # Información del sistema
    st.subheader("ℹ️ Información del Sistema")
    
    system_info = {
        "Versión FastAgent": "1.0.0",
        "Agentes disponibles": 3,
        "Servidores MCP": 2,
        "Último reinicio": "2024-01-15 10:30:00"
    }
    
    for key, value in system_info.items():
        st.write(f"**{key}**: {value}")

if __name__ == "__main__":
    main()