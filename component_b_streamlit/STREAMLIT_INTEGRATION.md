# 🤖 FastAgent - Integración Streamlit

Esta es la integración oficial de Streamlit en el proyecto FastAgent, proporcionando una interfaz web intuitiva para el sistema de procesamiento multi-agente.

## 🚀 Instalación y Configuración

### Instalación con Poetry/UV

```bash
# 1. Instalar dependencias base
uv sync

# 2. Instalar dependencias específicas de Streamlit
uv sync --extra streamlit

# 3. Verificar instalación
uv run python -c "import streamlit; print('✅ Streamlit disponible')"
```

### Scripts de Entrada Disponibles

El proyecto incluye scripts predefinidos en `pyproject.toml`:

```bash
# Opción 1: Script principal (recomendado)
fastagent-ui

# Opción 2: Script alternativo
fastagent-dashboard

# Opción 3: Ejecución directa
uv run python -m src.streamlit_interface.app

# Opción 4: Streamlit manual
uv run streamlit run src/streamlit_interface/app.py
```

## 📁 Estructura Integrada

```
src/streamlit_interface/
├── __init__.py              # Módulo principal
├── app.py                   # Aplicación Streamlit principal
├── core/
│   ├── config_manager.py    # Gestión de configuración
│   └── agent_interface.py   # Interface con FastAgent
├── components/
│   └── ui_components.py     # Componentes UI reutilizables
└── pages/
    ├── 1_📝_Procesamiento.py # Página principal de procesamiento
    └── 2_⚙️_Configuración.py # Configuración de proveedores
```

## ⚙️ Configuración

### Proveedores LLM Soportados

La interfaz soporta todos los proveedores configurados en `fastagent.config.yaml`:

```yaml
# Azure OpenAI (recomendado)
azure:
  api_key: "tu_azure_key"
  base_url: "https://tu-recurso.cognitiveservices.azure.com/"
  azure_deployment: "gpt-4.1"

# Ollama (local)
generic:
  api_key: "ollama"
  base_url: "http://localhost:11434/v1"

# OpenAI
openai:
  api_key: "tu_openai_key"

# Anthropic
anthropic:
  api_key: "tu_anthropic_key"
```

### Configuración Automática

La interfaz lee automáticamente la configuración del archivo `fastagent.config.yaml` en la raíz del proyecto. Los cambios se guardan inmediatamente.

## 🎯 Uso Básico

### 1. Primer Uso

```bash
# 1. Ejecutar la interfaz
fastagent-ui

# 2. Abrir navegador en http://localhost:8501

# 3. Ir a "⚙️ Configuración" y configurar al menos un proveedor LLM

# 4. Procesar contenido en "📝 Procesamiento"
```

### 2. Flujo de Procesamiento

1. **Input de Contenido**:
   - Escribir texto directamente
   - Subir archivo `.txt`
   - Añadir documentos PDF/imágenes para contexto

2. **Configuración**:
   - Seleccionar agente (auto-detección recomendada)
   - Habilitar/deshabilitar Q&A

3. **Procesamiento**:
   - Visualización en tiempo real
   - Manejo automático de rate limiting
   - Progreso por segmentos

4. **Resultados**:
   - Vista previa del documento
   - Descarga en formato MD o TXT
   - Estadísticas del procesamiento

## 🛠️ Desarrollo

### Estructura de Módulos

La integración sigue la estructura estándar de Poetry:

- **src/streamlit_interface/**: Módulo principal
- **Import relativos**: Usa imports relativos para mejor mantenibilidad
- **Configuración centralizada**: Un solo ConfigManager para toda la app
- **Separación de responsabilidades**: UI, lógica de negocio y configuración separadas

### Ejecutar en Modo Desarrollo

```bash
# Con recarga automática
uv run streamlit run src/streamlit_interface/app.py --server.runOnSave true

# Con puerto personalizado
uv run streamlit run src/streamlit_interface/app.py --server.port 8502

# Con logs de debug
uv run streamlit run src/streamlit_interface/app.py --logger.level debug
```

### Añadir Nuevas Páginas

Para añadir nuevas páginas:

1. Crear archivo en `src/streamlit_interface/pages/`
2. Seguir el patrón de nomenclatura: `N_🔸_Nombre.py`
3. Importar módulos usando paths relativos desde project root

Ejemplo:
```python
# src/streamlit_interface/pages/3_📊_Analytics.py
import sys
from pathlib import Path

# Configurar path para imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.streamlit_interface.core.config_manager import ConfigManager
# ... resto de la página
```

## 🔧 Personalización

### Temas y Estilos

La interfaz incluye estilos personalizados en `assets/styles.css` (del proyecto standalone), pero para la integración Poetry se usan los estilos de Streamlit por defecto. Para personalizar:

```python
# En cualquier página
st.markdown("""
<style>
.main-container {
    max-width: 1200px;
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)
```

### Configuración de Streamlit

La configuración se puede personalizar creando `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"

[server]
port = 8501
enableCORS = false
```

## 📊 Monitoreo y Logs

### Logs de FastAgent

Los logs del sistema FastAgent se configuran en `fastagent.config.yaml`:

```yaml
logger:
  progress_display: true
  show_chat: true
  level: "info"
```

### Logs de Streamlit

```bash
# Ver logs en tiempo real
uv run streamlit run src/streamlit_interface/app.py --logger.level debug

# Logs estructurados
tail -f ~/.streamlit/logs/streamlit.log
```

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. "ModuleNotFoundError"
```bash
# Verificar que estás en el directorio correcto
pwd  # Debe terminar en component_b_streamlit

# Reinstalar dependencias
uv sync --extra streamlit
```

#### 2. "FastAgent no disponible"
```bash
# Verificar que FastAgent funciona
uv run python -c "from src.enhanced_agents import fast; print('✅ OK')"

# Si falla, verificar estructura del proyecto
ls src/  # Debe mostrar enhanced_agents.py
```

#### 3. "Configuración no encontrada"
```bash
# Verificar archivo de configuración
ls fastagent.config.yaml

# Si no existe, copiar del ejemplo
cp fastagent.config.yaml.example fastagent.config.yaml
```

#### 4. "Error de rate limiting"
- Verificar configuración de rate limiting en la interfaz
- Reducir `requests_per_minute` 
- Aumentar `delay_between_requests`

### Logs de Debug

Para debug avanzado:

```bash
# Ejecutar con máximo nivel de logs
uv run streamlit run src/streamlit_interface/app.py \
  --logger.level debug \
  --server.headless true
```

## 🔄 Migración desde Versión Standalone

Si estás migrando desde la versión standalone de Streamlit:

```bash
# 1. Los archivos ya no están en streamlit_app/
# 2. Usar imports desde src.streamlit_interface
# 3. Ejecutar con fastagent-ui en lugar de ./run.sh
# 4. La configuración sigue siendo fastagent.config.yaml
```

## 📈 Performance

### Optimizaciones Incluidas

- **Caching de configuración**: ConfigManager usa singleton pattern
- **Imports lazy**: Módulos FastAgent se cargan bajo demanda
- **Session state**: Preserva estado entre recargas
- **Async handling**: Manejo correcto de operaciones asíncronas

### Métricas Típicas

- **Tiempo de inicio**: ~2-3 segundos
- **Procesamiento 5K palabras**: ~3-5 minutos (depende del proveedor)
- **Uso de memoria**: ~100-200MB (base) + uso de FastAgent

## 🤝 Contribución

### Añadir Funcionalidades

1. Fork del repositorio
2. Crear rama: `git checkout -b feature/streamlit-nueva-feature`
3. Desarrollar en `src/streamlit_interface/`
4. Seguir estructura de imports existente
5. Submit PR

### Convenciones de Código

- **Imports**: Usar paths relativos desde project root
- **Naming**: snake_case para archivos, PascalCase para clases
- **Docs**: Docstrings en español para funciones principales
- **Types**: Type hints donde sea posible

---

## 📋 Resumen

La integración Streamlit en FastAgent proporciona:

✅ **Interfaz intuitiva** para usuarios no técnicos  
✅ **Integración completa** con el sistema Poetry/UV  
✅ **Configuración centralizada** con fastagent.config.yaml  
✅ **Scripts de entrada** predefinidos  
✅ **Mantenimiento simplificado** con una sola base de código  

Para usar la interfaz web: `fastagent-ui`  
Para procesamiento por línea de comandos: `uv run python robust_main.py`

¡Ambas opciones están completamente integradas y mantienen toda la funcionalidad del sistema FastAgent! 🎉