# Sumer-IA: Flujo de Trabajo de Análisis de Transcripciones

Un flujo de trabajo de agentes inteligentes para estructurar y formatear transcripciones largas utilizando el framework fast-agent.

## Descripción

Este proyecto implementa un sistema de agentes especializados que trabajan en conjunto para procesar transcripciones de texto en bruto y convertirlas en documentos bien estructurados y formateados. El sistema utiliza el framework `fast-agent` para coordinar múltiples agentes que realizan tareas específicas:

- **Segmentador**: Divide el texto en fragmentos temáticamente coherentes
- **Titulador**: Genera títulos descriptivos para cada fragmento
- **Formateador**: Aplica formato Markdown manteniendo la fidelidad del contenido
- **Evaluador de Calidad**: Verifica que no haya pérdida de información ni alucinaciones

## Estructura del Proyecto

```
sumer-ia/
├── agents/
│   ├── __init__.py
│   └── transcription_agents.py   # Definiciones de agentes especializados
├── workflows/
│   ├── __init__.py
│   └── main_workflow.py         # Orquestador y flujos de trabajo
├── tools/
│   ├── __init__.py
│   └── verification_server.py   # Servidor MCP de verificación
├── prompts/
│   └── formatter_prompt.md      # Prompts externos para agentes
├── fastagent.config.yaml        # Configuración de API keys y servidores MCP
├── pyproject.toml              # Gestión de dependencias
├── main.py                     # Punto de entrada de la aplicación
└── README.md                   # Este archivo
```

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/pablotoledo/sumer-ia.git
cd sumer-ia
```

2. Instala las dependencias usando `uv`:
```bash
# Instala uv si no lo tienes
pip install uv

# Crea un entorno virtual e instala las dependencias
uv venv
uv pip install -e .
```

3. Configura tus claves de API en `fastagent.config.yaml`:
```yaml
providers:
  anthropic:
    api_key: "tu_clave_anthropic"
  openai:
    api_key: "tu_clave_openai"
```

## Uso

Ejecuta el flujo de trabajo principal:

```bash
uv run start
```

O directamente:
```bash
uv run main.py
```

## Arquitectura

### Agentes

- **Segmentador**: Analiza el texto y lo divide en fragmentos temáticamente coherentes
- **Titulador**: Genera títulos concisos y descriptivos para cada fragmento
- **Formateador**: Aplica formato Markdown preservando el contenido original
- **Evaluador de Calidad**: Utiliza herramientas MCP para verificar fidelidad y detectar alucinaciones

### Flujos de Trabajo

- **Evaluador-Optimizador**: Combina el formateador con el evaluador de calidad para refinamiento iterativo
- **Orquestador Principal**: Coordina todos los agentes para procesar la transcripción completa

### Herramientas MCP

El servidor de verificación proporciona:
- `fidelity_check`: Verifica que el contenido procesado mantiene la fidelidad semántica
- `hallucination_check`: Detecta información añadida no presente en el original

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## Contacto

Pablo Toledo - [GitHub](https://github.com/pablotoledo)

Link del Proyecto: [https://github.com/pablotoledo/sumer-ia](https://github.com/pablotoledo/sumer-ia)