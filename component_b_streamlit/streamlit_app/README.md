# 🤖 FastAgent Streamlit Interface

Interfaz web para el sistema FastAgent de procesamiento multi-agente que transforma transcripciones STT en documentos educativos profesionales con Q&A automático.

## 🚀 Características

- **📊 Dashboard**: Vista general del sistema y métricas de uso
- **⚙️ Configuración**: Gestión visual de proveedores LLM (Azure OpenAI, Ollama, etc.)
- **🤖 Agentes**: Personalización de agentes y prompts del sistema
- **📝 Procesamiento**: Interface principal para procesar contenido con visualización en tiempo real
- **📥 Descarga**: Exportación de resultados en múltiples formatos

## 🛠️ Instalación

### Prerrequisitos

1. **Python 3.11+**
2. **FastAgent configurado** en el proyecto padre
3. **Dependencias del proyecto FastAgent** ya instaladas

### Pasos de instalación

```bash
# 1. Navegar al directorio de la aplicación Streamlit
cd component_b_streamlit/streamlit_app

# 2. Instalar dependencias específicas de Streamlit
pip install -r requirements.txt

# 3. Verificar que FastAgent esté disponible (desde el directorio padre)
cd ..
python -c "from src.enhanced_agents import fast; print('✅ FastAgent disponible')"
```

## 🏃‍♂️ Ejecución

### Modo Desarrollo

```bash
# Desde el directorio streamlit_app
streamlit run streamlit_app.py
```

### Modo Producción

```bash
# Con configuración específica
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### Variables de Entorno (Opcional)

```bash
# Configurar puerto personalizado
export STREAMLIT_SERVER_PORT=8080

# Configurar tema
export STREAMLIT_THEME_BASE=dark

# Ejecutar
streamlit run streamlit_app.py
```

## 📁 Estructura del Proyecto

```
streamlit_app/
├── streamlit_app.py              # Aplicación principal
├── pages/
│   ├── 1_📊_Dashboard.py         # Dashboard con métricas
│   ├── 2_⚙️_Configuración.py     # Configuración de proveedores
│   ├── 3_📝_Procesamiento.py     # Procesamiento principal
│   └── 4_🤖_Agentes.py           # Gestión de agentes
├── components/
│   ├── config_manager.py         # Gestión de configuración
│   ├── agent_interface.py        # Interface con FastAgent
│   └── ui_components.py          # Componentes UI reutilizables
├── utils/
│   ├── validation.py             # Validaciones
│   └── file_handlers.py          # Manejo de archivos
├── assets/
│   └── styles.css                # Estilos personalizados
├── requirements.txt              # Dependencias
└── README.md                     # Este archivo
```

## ⚙️ Configuración

### 1. Configuración Inicial

Al ejecutar por primera vez:

1. Ve a la página **⚙️ Configuración**
2. Configura al menos un proveedor LLM:
   - **Azure OpenAI** (recomendado para producción)
   - **Ollama** (para desarrollo local)
   - **OpenAI** (alternativa)
   - **Anthropic** (para casos específicos)

### 2. Proveedores LLM

#### Azure OpenAI (Recomendado)
```yaml
azure:
  api_key: "tu_api_key_aqui"
  base_url: "https://tu-recurso.cognitiveservices.azure.com/"
  azure_deployment: "gpt-4.1"
  api_version: "2025-01-01-preview"
```

#### Ollama (Local)
```yaml
generic:
  api_key: "ollama"
  base_url: "http://localhost:11434/v1"
```

### 3. Rate Limiting

Configura límites apropiados según tu plan:

- **Azure S0**: Conservador (2-3 requests/min)
- **Azure S1+**: Balanceado (5-10 requests/min)
- **Ollama**: Agresivo (sin límites)

## 🎯 Uso Básico

### 1. Procesamiento Simple

1. **Input**: 
   - Escribe o sube un archivo de transcripción STT
   - Opcionalmente añade documentos PDF/imágenes para contexto

2. **Configuración**:
   - Deja "Auto-detección" para que seleccione el agente apropiado
   - Habilita Q&A para generar preguntas y respuestas

3. **Procesamiento**:
   - Haz clic en "🚀 Iniciar Procesamiento"
   - Observa el progreso en tiempo real

4. **Resultados**:
   - Ve el documento generado
   - Descarga en formato TXT o MD

### 2. Procesamiento Avanzado

- **Reuniones diarizadas**: El sistema detecta automáticamente y extrae decisiones/action items
- **Contenido multimodal**: Incluye PDFs para enriquecer el contexto
- **Agentes específicos**: Selecciona manualmente el agente si conoces el tipo de contenido

## 🔧 Troubleshooting

### Errores Comunes

#### 1. "No se pudieron inicializar los agentes"
```bash
# Verificar que FastAgent esté disponible
cd ../  # ir al directorio padre
python -c "from src.enhanced_agents import fast"
```

#### 2. "Error de rate limiting (429)"
- Aumenta `delay_between_requests` en Configuración
- Reduce `requests_per_minute`
- Verifica tu plan de Azure OpenAI

#### 3. "API key no válida"
- Verifica que la API key esté correcta en Configuración
- Para Azure: asegúrate de usar la URL correcta
- Para Ollama: verifica que el servidor esté corriendo

#### 4. "Conexión rechazada con Ollama"
```bash
# Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no está corriendo, iniciarlo
ollama serve
```

### Logs y Debug

Para ver logs detallados:

```bash
# Ejecutar con logs de debug
streamlit run streamlit_app.py --logger.level debug
```

Los logs de FastAgent se guardan según la configuración en `fastagent.config.yaml`.

## 🔒 Seguridad

### Buenas Prácticas

1. **API Keys**:
   - Nunca hardcodees API keys en el código
   - Usa variables de entorno o archivos de configuración seguros
   - Rota las keys regularmente

2. **Archivos subidos**:
   - Los archivos se procesan temporalmente y se eliminan después
   - No se almacenan permanentemente en el servidor

3. **Configuración**:
   - La configuración se guarda en `fastagent.config.yaml`
   - Asegúrate de que este archivo no se suba a repositorios públicos

## 📈 Performance

### Optimización

1. **Rate Limiting**: Ajusta según tu proveedor y plan
2. **Tamaño de contenido**: El sistema maneja hasta 50,000 palabras
3. **Archivos multimodales**: Límite de 10MB por archivo
4. **Cache**: Los resultados se mantienen en sesión para evitar reprocesamiento

### Métricas Esperadas

- **Contenido 5K palabras**: ~3-5 minutos
- **Contenido 20K palabras**: ~15-25 minutos
- **Retención de contenido**: 85-95%
- **Q&A**: 3-5 preguntas por segmento

## 🤝 Contribución

### Desarrollo

Para contribuir al desarrollo:

1. Fork del repositorio
2. Crea una rama feature
3. Desarrolla tu funcionalidad
4. Añade tests si es necesario
5. Submit Pull Request

### Estructura de commits

```
feat: nueva funcionalidad
fix: corrección de bug
docs: documentación
style: formateo
refactor: refactorización
test: tests
```

## 📋 Roadmap

### Próximas funcionalidades

- [ ] Autenticación de usuarios
- [ ] Historial de procesamientos
- [ ] Templates de configuración
- [ ] Exportación a más formatos
- [ ] API REST integrada
- [ ] Métricas avanzadas
- [ ] Soporte para más proveedores LLM

## 📞 Soporte

### Enlaces útiles

- [📚 Documentación FastAgent](https://fast-agent.ai/)
- [🐙 Repositorio GitHub](https://github.com/evalstate/fast-agent)
- [❓ Issues](https://github.com/evalstate/fast-agent/issues)
- [💬 Discusiones](https://github.com/evalstate/fast-agent/discussions)

### Contacto

Para soporte específico de esta interfaz Streamlit, crea un issue en el repositorio principal mencionando "Streamlit Interface".

---

**🎉 ¡Disfruta procesando contenido con FastAgent!**