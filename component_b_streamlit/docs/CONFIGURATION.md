# Configuración Detallada

Guía completa de todas las opciones de configuración de FastAgent.

## 📋 Archivo de Configuración

El archivo principal es `fastagent.config.yaml`. Se puede editar manualmente o a través de la interfaz web.

## 🎯 Presets de Configuración

FastAgent incluye 3 presets predefinidos:

### 🔷 Básico - Azure OpenAI
**Ideal para**: Usuarios con acceso a Azure OpenAI en producción.

```yaml
default_model: azure.gpt-4.1
rate_limiting:
  requests_per_minute: 3
  delay_between_requests: 30
  max_retries: 3
```

**Requiere**: API Key de Azure + Base URL

### 🦙 Local - Ollama
**Ideal para**: Desarrollo local sin costos.

```yaml
default_model: generic.llama3.1
rate_limiting:
  requests_per_minute: 60
  delay_between_requests: 0
```

**Requiere**: Ollama instalado y ejecutándose (`ollama pull llama3.1`)

### 🔧 Desarrollo
**Ideal para**: Debugging y desarrollo.

```yaml
logger:
  level: debug
  show_tools: true
  truncate_tools: false
```

## 🔗 Proveedores LLM

### Azure OpenAI
```yaml
azure:
  api_key: "tu-api-key"
  base_url: "https://tu-recurso.cognitiveservices.azure.com/"
  azure_deployment: "gpt-4.1"
  api_version: "2025-01-01-preview"
```

### Ollama (Local)
```yaml
generic:
  api_key: "ollama"
  base_url: "http://localhost:11434/v1"
```

### OpenAI
```yaml
openai:
  api_key: "sk-..."
```

### Anthropic Claude
```yaml
anthropic:
  api_key: "sk-ant-..."
```

## ⏱️ Rate Limiting

Parámetros para controlar la frecuencia de requests:

| Parámetro | Descripción | Rango recomendado |
|-----------|-------------|-------------------|
| `delay_between_requests` | Segundos entre requests | 10-45 |
| `requests_per_minute` | Máximo requests/min | 2-10 |
| `max_retries` | Reintentos en error 429 | 2-5 |
| `retry_base_delay` | Delay inicial en retry | 30-90 |
| `max_tokens_per_request` | Tokens máximos | 30000-80000 |

### Presets de Rate Limiting:

| Preset | delay | req/min | reintentos | Uso |
|--------|-------|---------|------------|-----|
| 🐌 Conservador | 45s | 2 | 5 | S0 Tier Azure |
| ⚖️ Balanceado | 20s | 5 | 3 | Uso general |
| 🚀 Agresivo | 10s | 10 | 2 | Tier alto |

## 📝 Logger

```yaml
logger:
  progress_display: true  # Barra de progreso
  show_chat: true         # Mostrar mensajes
  show_tools: true        # Mostrar uso de herramientas
  truncate_tools: true    # Truncar output largo
  level: info             # debug, info, warning, error
```

## 🔒 Seguridad

> ⚠️ **IMPORTANTE**: Nunca commitear API keys al repositorio.

- Usa `.gitignore` para excluir `fastagent.config.yaml`
- Usa variables de entorno para producción
- El archivo `fastagent.config.yaml.example` es seguro para commitear
