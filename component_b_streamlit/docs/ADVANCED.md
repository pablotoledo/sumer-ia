# Funciones Avanzadas

Guía para usuarios avanzados y desarrolladores.

## 🤖 Agentes Personalizados

### Agentes Disponibles

1. **simple_processor** - Procesador general para contenido educativo
2. **meeting_processor** - Especializado en reuniones con múltiples participantes

### Edición de Prompts

Los prompts de los agentes se encuentran en:
- `src/agents/specialized_agents.py`

Para modificar un prompt:
1. Localiza el decorador `@fast.agent` del agente
2. Edita el parámetro `instruction`
3. Reinicia la aplicación

## 🧠 Segmentación Inteligente

### Método Inteligente (GPT-4.1)

Para contenido >3000 palabras, GPT-4.1 analiza:
- Transiciones temáticas
- Cambios de contexto
- Puntos de corte semánticos

### Método Programático

División simple cada 2500 palabras buscando límites de oraciones.

## 🔌 Servidores MCP

FastAgent soporta servidores MCP para extender funcionalidades:

```yaml
mcp:
  servers:
    fetch:
      command: uvx
      args: [mcp-server-fetch]
    filesystem:
      command: npx
      args: [-y, @modelcontextprotocol/server-filesystem, .]
```

## 🔧 CLI

```bash
# Procesar archivo por línea de comandos
uv run python scripts/cli.py --file input.txt --output result.md

# Ver ayuda
uv run python scripts/cli.py --help
```

## 📊 Debugging

### Logs verbosos

En configuración:
```yaml
logger:
  level: debug
  show_tools: true
  truncate_tools: false
```

### Verificar configuración

```bash
cat fastagent.config.yaml
```

### Probar conexión

Desde la UI: ⚙️ Configuración > Experto > Ver Configuración Completa
