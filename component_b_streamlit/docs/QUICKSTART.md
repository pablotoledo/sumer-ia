# 🚀 Guía de Inicio Rápido

Procesa tu primera transcripción en 5 minutos.

## 1. Instalar Dependencias

```bash
# Instalar UV si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias del proyecto
uv sync
```

## 2. Configurar Proveedor LLM

Copia el archivo de ejemplo y edita con tus credenciales:

```bash
cp fastagent.config.yaml.example fastagent.config.yaml
```

### Opción A: Azure OpenAI (Recomendado)

```yaml
default_model: azure.gpt-4.1

azure:
  api_key: "tu-api-key"
  base_url: "https://tu-recurso.cognitiveservices.azure.com/"
  azure_deployment: "gpt-4.1"
  api_version: "2025-01-01-preview"
```

### Opción B: Ollama Local (Gratuito)

```bash
# Instalar Ollama primero: https://ollama.ai
ollama pull llama3.1
```

```yaml
default_model: generic.llama3.1

generic:
  api_key: "ollama"
  base_url: "http://localhost:11434/v1"
```

## 3. Ejecutar la Aplicación

```bash
uv run streamlit run streamlit_app/streamlit_app.py
```

Abre http://localhost:8501 en tu navegador.

## 4. Procesar tu Primera Transcripción

1. Ve a la página **🏠 Inicio**
2. Pega tu texto o sube un archivo
3. Haz clic en **🚀 Procesar**
4. Descarga el resultado en Markdown

## 🔧 Solución de Problemas

### "Azure OpenAI no está configurado"
- Verifica que `fastagent.config.yaml` tenga tu API key correcta
- Confirma que la URL base sea válida

### Errores 429 (Rate Limit)
- El sistema maneja esto automáticamente con reintentos
- Para S0 tier, usa el preset "Conservador" en ⚙️ Configuración

### Problemas de dependencias
```bash
uv sync --reinstall
```

## 📚 Más Información

- [Configuración detallada](CONFIGURATION.md)
- [Funciones avanzadas](ADVANCED.md)
- [README principal](../README.md)
