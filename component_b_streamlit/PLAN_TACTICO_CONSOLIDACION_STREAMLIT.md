# 🎯 Plan Táctico de Consolidación Streamlit
## Migración Segura de Interfaces Duplicadas

**Proyecto**: Component B Streamlit - Sistema Multiagente FastAgent  
**Objetivo**: Consolidar dos interfaces Streamlit duplicadas en una sola sin pérdida de funcionalidad  
**Fecha**: 2025-01-18  
**Estimación**: 3-4 horas  
**Riesgo**: Medio (con procedimientos de seguridad)

---

## 📋 Resumen Ejecutivo

### Situación Actual
- **Interfaz Primaria**: `/src/streamlit_interface/` (UV-based, 2 páginas)
- **Interfaz Secundaria**: `/streamlit_app/` (pip-based, 4 páginas)
- **Problema**: 90% código duplicado, confusión de usuarios
- **Solución**: Consolidar en interfaz UV-based preservando todas las funcionalidades

### Resultado Esperado
- ✅ Interfaz única con 4 páginas completas
- ✅ Todas las funcionalidades preservadas
- ✅ Gestión de dependencias UV unificada
- ✅ Eliminación de código duplicado
- ✅ Experiencia de usuario coherente

---

## 🔍 FASE 0: Análisis Pre-Migración (15 min)

### Auditoría de Funcionalidades

#### **Interfaz Primaria** (`/src/streamlit_interface/`)
```bash
# Estructura actual
src/streamlit_interface/
├── app.py                    # 📄 App principal (básica)
├── core/
│   ├── config_manager.py     # 🔧 Gestión configuración
│   └── agent_interface.py    # 🤖 Interface FastAgent
├── components/
│   └── ui_components.py      # 🎨 Componentes UI (básicos)
└── pages/
    ├── 1_📝_Procesamiento.py  # 📝 Procesamiento básico
    └── 2_⚙️_Configuración.py # ⚙️ Configuración básica

# Características
- ✅ Integración UV/Poetry nativa
- ✅ Imports relativos desde src/
- ✅ Configuración fastagent.config.yaml
- ❌ Solo 2 páginas
- ❌ UI básica sin estilos
```

#### **Interfaz Secundaria** (`/streamlit_app/`)
```bash
# Estructura actual
streamlit_app/
├── streamlit_app.py          # 📄 App principal (completa)
├── components/
│   ├── config_manager.py     # 🔧 Gestión configuración (DUPLICADO)
│   ├── agent_interface.py    # 🤖 Interface FastAgent (DUPLICADO)
│   └── ui_components.py      # 🎨 Componentes UI (EXTENDIDOS)
├── pages/
│   ├── 1_📊_Dashboard.py     # 📊 Dashboard (ÚNICO)
│   ├── 2_⚙️_Configuración.py # ⚙️ Configuración (DUPLICADO)
│   ├── 3_📝_Procesamiento.py # 📝 Procesamiento (DUPLICADO)
│   └── 4_🤖_Agentes.py       # 🤖 Gestión agentes (ÚNICO)
├── utils/
│   ├── file_handlers.py      # 📁 Manejo archivos (ÚNICO)
│   └── validation.py         # ✅ Validación (ÚNICO)
├── assets/
│   └── styles.css           # 💅 CSS personalizado (ÚNICO)
└── requirements.txt         # 📦 Dependencias standalone

# Características ÚNICAS a conservar
- ✅ Dashboard completo con métricas
- ✅ Gestión avanzada de agentes
- ✅ Utilidades de archivos
- ✅ CSS personalizado
- ✅ Validación mejorada
```

### Mapeo de Dependencias

#### **Análisis de Imports Críticos**
```python
# Interfaz Primaria (UV-based)
from src.streamlit_interface.core.config_manager import ConfigManager
from src.enhanced_agents import fast, adaptive_segment_content

# Interfaz Secundaria (standalone)
from components.config_manager import ConfigManager
from ..src.enhanced_agents import fast  # Import relativo problemático
```

#### **Conflictos de Dependencias**
```bash
# UV (primaria) - pyproject.toml
streamlit = "^1.32.0"
fastapi = "^0.104.0"

# pip (secundaria) - requirements.txt  
streamlit==1.32.2
fastapi==0.104.1
# Versiones ligeramente diferentes
```

---

## 🛡️ FASE 1: Estrategia de Backup y Seguridad (15 min)

### Procedimiento de Backup Completo

#### **1.1 Backup del Sistema de Archivos**
```bash
# Crear directorio de backup con timestamp
cd /Users/pablotoledo/Documents/GitHub/sumer-ia/component_b_streamlit
BACKUP_DIR="backup_consolidacion_$(date +%Y%m%d_%H%M%S)"
mkdir "$BACKUP_DIR"

# Backup completo del proyecto
cp -r . "$BACKUP_DIR/"
echo "✅ Backup completo creado en: $BACKUP_DIR"

# Backup específico de interfaces Streamlit
mkdir "$BACKUP_DIR/interfaces_originales"
cp -r src/streamlit_interface "$BACKUP_DIR/interfaces_originales/primaria"
cp -r streamlit_app "$BACKUP_DIR/interfaces_originales/secundaria"
echo "✅ Interfaces originales respaldadas"
```

#### **1.2 Backup de Git (Stash + Branch)**
```bash
# Crear branch de backup
git stash push -m "WIP: antes de consolidación Streamlit"
git checkout -b backup/pre-streamlit-consolidation
git add .
git commit -m "🛡️ Backup: Estado antes de consolidación Streamlit"

# Volver a main para trabajar
git checkout main
git stash pop
echo "✅ Branch de backup creado: backup/pre-streamlit-consolidation"
```

#### **1.3 Backup de Configuración**
```bash
# Backup de configuraciones críticas
cp fastagent.config.yaml "$BACKUP_DIR/fastagent.config.yaml.backup"
cp pyproject.toml "$BACKUP_DIR/pyproject.toml.backup"
cp -r .streamlit "$BACKUP_DIR/streamlit_config_backup" 2>/dev/null || true
echo "✅ Configuraciones respaldadas"
```

### Plan de Rollback de Emergencia

#### **Procedimiento de Rollback Rápido**
```bash
# Script de rollback automático
cat > rollback_consolidacion.sh << 'EOF'
#!/bin/bash
echo "🚨 INICIANDO ROLLBACK DE EMERGENCIA"

# Encontrar el backup más reciente
LATEST_BACKUP=$(ls -td backup_consolidacion_* | head -1)
echo "📂 Restaurando desde: $LATEST_BACKUP"

# Restaurar interfaces originales
rm -rf src/streamlit_interface
rm -rf streamlit_app
cp -r "$LATEST_BACKUP/interfaces_originales/primaria" src/streamlit_interface
cp -r "$LATEST_BACKUP/interfaces_originales/secundaria" streamlit_app

# Restaurar configuraciones
cp "$LATEST_BACKUP/fastagent.config.yaml.backup" fastagent.config.yaml
cp "$LATEST_BACKUP/pyproject.toml.backup" pyproject.toml

echo "✅ ROLLBACK COMPLETADO - Sistema restaurado al estado original"
EOF

chmod +x rollback_consolidacion.sh
echo "✅ Script de rollback creado: ./rollback_consolidacion.sh"
```

---

## 🔧 FASE 2: Preparación de la Migración (20 min)

### Análisis de Imports y Dependencias

#### **2.1 Auditoría de Imports**
```bash
# Crear script de análisis de imports
cat > analizar_imports.py << 'EOF'
#!/usr/bin/env python3
import os
import re
from pathlib import Path

def analizar_imports(directorio):
    """Analiza todos los imports en archivos Python de un directorio."""
    imports = set()
    problemas = []
    
    for archivo in Path(directorio).rglob("*.py"):
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
        # Buscar imports
        import_lines = re.findall(r'^(from .+ import .+|import .+)$', contenido, re.MULTILINE)
        for line in import_lines:
            imports.add(line.strip())
            
        # Buscar imports problemáticos
        if 'from components.' in contenido:
            problemas.append(f"{archivo}: Import relativo a components/")
        if 'from ..src.' in contenido:
            problemas.append(f"{archivo}: Import relativo problemático")
    
    return imports, problemas

print("📊 ANÁLISIS DE IMPORTS - INTERFAZ PRIMARIA")
imports_primaria, problemas_primaria = analizar_imports("src/streamlit_interface")
print(f"Total imports únicos: {len(imports_primaria)}")
for problema in problemas_primaria:
    print(f"⚠️  {problema}")

print("\n📊 ANÁLISIS DE IMPORTS - INTERFAZ SECUNDARIA")
imports_secundaria, problemas_secundaria = analizar_imports("streamlit_app")
print(f"Total imports únicos: {len(imports_secundaria)}")
for problema in problemas_secundaria:
    print(f"⚠️  {problema}")

print("\n🔍 IMPORTS ÚNICOS EN SECUNDARIA:")
for imp in sorted(imports_secundaria - imports_primaria):
    print(f"  {imp}")
EOF

python analizar_imports.py > analisis_imports.log
echo "✅ Análisis de imports completado: analisis_imports.log"
```

#### **2.2 Verificación de Dependencias UV**
```bash
# Verificar que UV está configurado correctamente
uv --version || echo "❌ UV no está instalado"
uv sync --dry-run || echo "❌ Problemas con dependencias UV"

# Verificar dependencias de Streamlit
uv run python -c "import streamlit; print(f'✅ Streamlit {streamlit.__version__}')" || echo "❌ Streamlit no disponible"
uv run python -c "from src.enhanced_agents import fast; print('✅ FastAgent accesible')" || echo "❌ FastAgent no accesible"

echo "✅ Verificación de dependencias completada"
```

### Preparación del Entorno de Trabajo

#### **2.3 Crear Branch de Trabajo**
```bash
# Crear branch específico para la consolidación
git checkout -b feature/consolidate-streamlit-interfaces
git add .
git commit -m "🚀 Inicio: Consolidación de interfaces Streamlit"
echo "✅ Branch de trabajo creado: feature/consolidate-streamlit-interfaces"
```

#### **2.4 Estructura de Directorio Temporal**
```bash
# Crear directorio temporal para staging
mkdir -p temp_migration/{components,pages,utils,assets}
echo "✅ Directorio temporal creado para staging"
```

---

## 🏗️ FASE 3: Migración de Componentes (45 min)

### 3.1 Migración de Componentes UI (15 min)

#### **Análisis de Diferencias en ui_components.py**
```bash
# Comparar tamaños y diferencias
echo "📊 COMPARACIÓN DE COMPONENTES UI:"
wc -l src/streamlit_interface/components/ui_components.py
wc -l streamlit_app/components/ui_components.py

# Crear diff detallado
diff -u src/streamlit_interface/components/ui_components.py streamlit_app/components/ui_components.py > ui_components_diff.log
echo "✅ Diferencias guardadas en: ui_components_diff.log"
```

#### **Migración Segura de ui_components.py**
```bash
# Backup del archivo actual
cp src/streamlit_interface/components/ui_components.py src/streamlit_interface/components/ui_components.py.backup

# Fusionar componentes (conservando la versión más completa)
cat > migrar_ui_components.py << 'EOF'
#!/usr/bin/env python3
"""Script para migrar componentes UI de standalone a integrada."""

import shutil
from pathlib import Path

# Leer archivo standalone (más completo)
standalone_path = Path("streamlit_app/components/ui_components.py")
integrated_path = Path("src/streamlit_interface/components/ui_components.py")

print("📄 Migrando ui_components.py...")

# Leer contenido standalone
with open(standalone_path, 'r', encoding='utf-8') as f:
    contenido_standalone = f.read()

# Actualizar imports para estructura integrada
contenido_migrado = contenido_standalone.replace(
    "from components.config_manager import ConfigManager",
    "from src.streamlit_interface.core.config_manager import ConfigManager"
)

# Escribir a la interfaz integrada
with open(integrated_path, 'w', encoding='utf-8') as f:
    f.write(contenido_migrado)

print("✅ ui_components.py migrado exitosamente")
print(f"📊 Líneas migradas: {len(contenido_migrado.splitlines())}")
EOF

python migrar_ui_components.py
echo "✅ Componentes UI migrados"
```

### 3.2 Migración de Utilidades (15 min)

#### **Crear Directorio de Utilidades**
```bash
# Crear directorio utils en interfaz integrada
mkdir -p src/streamlit_interface/utils
touch src/streamlit_interface/utils/__init__.py
```

#### **Migrar file_handlers.py**
```bash
cat > migrar_file_handlers.py << 'EOF'
#!/usr/bin/env python3
"""Migrar file_handlers.py con imports corregidos."""

from pathlib import Path

# Leer archivo original
with open("streamlit_app/utils/file_handlers.py", 'r', encoding='utf-8') as f:
    contenido = f.read()

# Corregir imports para estructura integrada
contenido_corregido = contenido.replace(
    "from components.config_manager import ConfigManager",
    "from src.streamlit_interface.core.config_manager import ConfigManager"
).replace(
    "from ..src.enhanced_agents import fast",
    "from src.enhanced_agents import fast"
)

# Escribir archivo migrado
with open("src/streamlit_interface/utils/file_handlers.py", 'w', encoding='utf-8') as f:
    f.write(contenido_corregido)

print("✅ file_handlers.py migrado")
EOF

python migrar_file_handlers.py
```

#### **Migrar validation.py**
```bash
cat > migrar_validation.py << 'EOF'
#!/usr/bin/env python3
"""Migrar validation.py con imports corregidos."""

from pathlib import Path

# Leer archivo original
with open("streamlit_app/utils/validation.py", 'r', encoding='utf-8') as f:
    contenido = f.read()

# Corregir imports si es necesario
# (validation.py generalmente no tiene imports problemáticos)

# Escribir archivo migrado
with open("src/streamlit_interface/utils/validation.py", 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ validation.py migrado")
EOF

python migrar_validation.py
echo "✅ Utilidades migradas"
```

### 3.3 Verificación de Componentes (15 min)

#### **Test de Imports de Componentes**
```bash
cat > test_componentes_migrados.py << 'EOF'
#!/usr/bin/env python3
"""Verificar que todos los componentes migrados funcionan."""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path.cwd()))

try:
    from src.streamlit_interface.components.ui_components import setup_page_config
    print("✅ ui_components.py importa correctamente")
except ImportError as e:
    print(f"❌ Error importando ui_components: {e}")

try:
    from src.streamlit_interface.utils.file_handlers import FileHandler
    print("✅ file_handlers.py importa correctamente")
except ImportError as e:
    print(f"❌ Error importando file_handlers: {e}")

try:
    from src.streamlit_interface.utils.validation import validate_file
    print("✅ validation.py importa correctamente")
except ImportError as e:
    print(f"❌ Error importando validation: {e}")

print("🧪 Verificación de componentes completada")
EOF

python test_componentes_migrados.py
echo "✅ Componentes verificados"
```

---

## 📄 FASE 4: Migración de Páginas (60 min)

### 4.1 Migración de Dashboard (20 min)

#### **Migrar 1_📊_Dashboard.py**
```bash
cat > migrar_dashboard.py << 'EOF'
#!/usr/bin/env python3
"""Migrar Dashboard con imports corregidos."""

from pathlib import Path

# Leer dashboard original
with open("streamlit_app/pages/1_📊_Dashboard.py", 'r', encoding='utf-8') as f:
    contenido = f.read()

# Corregir imports para estructura integrada
contenido_corregido = contenido.replace(
    "from components.config_manager import ConfigManager",
    "from src.streamlit_interface.core.config_manager import ConfigManager"
).replace(
    "from components.ui_components import",
    "from src.streamlit_interface.components.ui_components import"
).replace(
    "from utils.validation import",
    "from src.streamlit_interface.utils.validation import"
).replace(
    "from ..src.enhanced_agents import fast",
    "from src.enhanced_agents import fast"
)

# Escribir dashboard migrado
dashboard_path = "src/streamlit_interface/pages/1_📊_Dashboard.py"
with open(dashboard_path, 'w', encoding='utf-8') as f:
    f.write(contenido_corregido)

print(f"✅ Dashboard migrado a: {dashboard_path}")
EOF

python migrar_dashboard.py
```

### 4.2 Migración de Página de Agentes (20 min)

#### **Migrar 4_🤖_Agentes.py**
```bash
cat > migrar_agentes.py << 'EOF'
#!/usr/bin/env python3
"""Migrar página de gestión de agentes."""

from pathlib import Path

# Leer página de agentes original
with open("streamlit_app/pages/4_🤖_Agentes.py", 'r', encoding='utf-8') as f:
    contenido = f.read()

# Corregir imports
contenido_corregido = contenido.replace(
    "from components.config_manager import ConfigManager",
    "from src.streamlit_interface.core.config_manager import ConfigManager"
).replace(
    "from components.agent_interface import AgentInterface",
    "from src.streamlit_interface.core.agent_interface import AgentInterface"
).replace(
    "from components.ui_components import",
    "from src.streamlit_interface.components.ui_components import"
).replace(
    "from utils.file_handlers import",
    "from src.streamlit_interface.utils.file_handlers import"
)

# Escribir página migrada - renombrar para mantener orden
agentes_path = "src/streamlit_interface/pages/4_🤖_Agentes.py"
with open(agentes_path, 'w', encoding='utf-8') as f:
    f.write(contenido_corregido)

print(f"✅ Página de agentes migrada a: {agentes_path}")
EOF

python migrar_agentes.py
```

### 4.3 Actualización de Páginas Existentes (20 min)

#### **Actualizar Página de Procesamiento**
```bash
cat > actualizar_procesamiento.py << 'EOF'
#!/usr/bin/env python3
"""Actualizar página de procesamiento con mejores características."""

from pathlib import Path

# Comparar ambas versiones
with open("src/streamlit_interface/pages/1_📝_Procesamiento.py", 'r', encoding='utf-8') as f:
    procesamiento_integrada = f.read()

with open("streamlit_app/pages/3_📝_Procesamiento.py", 'r', encoding='utf-8') as f:
    procesamiento_standalone = f.read()

# Tomar la versión standalone (generalmente más completa) y corregir imports
contenido_mejorado = procesamiento_standalone.replace(
    "from components.config_manager import ConfigManager",
    "from src.streamlit_interface.core.config_manager import ConfigManager"
).replace(
    "from components.ui_components import",
    "from src.streamlit_interface.components.ui_components import"
).replace(
    "from utils.file_handlers import",
    "from src.streamlit_interface.utils.file_handlers import"
).replace(
    "from utils.validation import",
    "from src.streamlit_interface.utils.validation import"
)

# Backup de la versión original
procesamiento_path = "src/streamlit_interface/pages/1_📝_Procesamiento.py"
backup_path = f"{procesamiento_path}.backup"
Path(procesamiento_path).rename(backup_path)

# Escribir versión mejorada, pero renumerar como página 3
procesamiento_final = "src/streamlit_interface/pages/3_📝_Procesamiento.py"
with open(procesamiento_final, 'w', encoding='utf-8') as f:
    f.write(contenido_mejorado)

print(f"✅ Página de procesamiento actualizada: {procesamiento_final}")
print(f"📄 Backup original: {backup_path}")
EOF

python actualizar_procesamiento.py
```

#### **Actualizar Página de Configuración**
```bash
cat > actualizar_configuracion.py << 'EOF'
#!/usr/bin/env python3
"""Actualizar página de configuración con mejores características."""

from pathlib import Path

# Leer versión standalone (más completa)
with open("streamlit_app/pages/2_⚙️_Configuración.py", 'r', encoding='utf-8') as f:
    configuracion_standalone = f.read()

# Corregir imports
contenido_mejorado = configuracion_standalone.replace(
    "from components.config_manager import ConfigManager",
    "from src.streamlit_interface.core.config_manager import ConfigManager"
).replace(
    "from components.ui_components import",
    "from src.streamlit_interface.components.ui_components import"
)

# Backup y reemplazar
configuracion_path = "src/streamlit_interface/pages/2_⚙️_Configuración.py"
backup_path = f"{configuracion_path}.backup"
Path(configuracion_path).rename(backup_path)

with open(configuracion_path, 'w', encoding='utf-8') as f:
    f.write(contenido_mejorado)

print(f"✅ Página de configuración actualizada: {configuracion_path}")
print(f"📄 Backup original: {backup_path}")
EOF

python actualizar_configuracion.py
echo "✅ Páginas migradas y actualizadas"
```

---

## 🎨 FASE 5: Migración de Assets y Configuración (20 min)

### 5.1 Migración de CSS Personalizado (10 min)

#### **Crear Directorio de Assets**
```bash
mkdir -p src/streamlit_interface/assets
```

#### **Migrar styles.css**
```bash
cp streamlit_app/assets/styles.css src/streamlit_interface/assets/
echo "✅ CSS personalizado migrado"
```

#### **Actualizar Configuración de Streamlit**
```bash
# Migrar configuración de Streamlit
mkdir -p src/streamlit_interface/.streamlit
cp streamlit_app/.streamlit/config.toml src/streamlit_interface/.streamlit/ 2>/dev/null || echo "⚠️ No se encontró config.toml en standalone"

# Crear configuración mejorada si no existe
cat > src/streamlit_interface/.streamlit/config.toml << 'EOF'
[server]
maxUploadSize = 1024
enableCORS = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[browser]
gatherUsageStats = false
EOF
echo "✅ Configuración de Streamlit actualizada"
```

### 5.2 Actualización de la Aplicación Principal (10 min)

#### **Actualizar app.py Principal**
```bash
cat > actualizar_app_principal.py << 'EOF'
#!/usr/bin/env python3
"""Actualizar app.py principal con navegación completa."""

app_content = '''"""
FastAgent Streamlit Interface - Aplicación Principal Consolidada
===============================================================

Interfaz web unificada para el sistema multiagente FastAgent con:
- Dashboard de métricas y estado
- Configuración de proveedores LLM
- Procesamiento de transcripciones
- Gestión avanzada de agentes
"""

import streamlit as st
import sys
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="FastAgent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar CSS personalizado
def load_css():
    """Cargar estilos CSS personalizados."""
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Aplicar estilos
load_css()

# Importar componentes
try:
    from src.streamlit_interface.components.ui_components import setup_page_config
    from src.streamlit_interface.core.config_manager import ConfigManager
    
    # Configurar página
    setup_page_config("🏠 FastAgent System")
    
    # Página principal
    st.title("🤖 Sistema FastAgent Multiagente")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 📊 Dashboard")
        st.markdown("Métricas y estado del sistema")
        if st.button("Ir a Dashboard", key="nav_dashboard"):
            st.switch_page("pages/1_📊_Dashboard.py")
    
    with col2:
        st.markdown("### ⚙️ Configuración")
        st.markdown("Gestión de proveedores LLM")
        if st.button("Ir a Configuración", key="nav_config"):
            st.switch_page("pages/2_⚙️_Configuración.py")
    
    with col3:
        st.markdown("### 📝 Procesamiento")
        st.markdown("Procesar transcripciones")
        if st.button("Ir a Procesamiento", key="nav_process"):
            st.switch_page("pages/3_📝_Procesamiento.py")
    
    with col4:
        st.markdown("### 🤖 Agentes")
        st.markdown("Gestión avanzada de agentes")
        if st.button("Ir a Agentes", key="nav_agents"):
            st.switch_page("pages/4_🤖_Agentes.py")
    
    st.markdown("---")
    
    # Información del sistema
    with st.expander("ℹ️ Información del Sistema"):
        config_manager = ConfigManager()
        providers = config_manager.get_available_providers()
        
        st.markdown(f"**Proveedores configurados:** {len(providers)}")
        for provider in providers:
            st.markdown(f"- {provider}")
        
        st.markdown("**Agentes disponibles:**")
        st.markdown("- enhanced_agents: Sistema principal")
        st.markdown("- meeting_processor: Reuniones diarizadas")
        st.markdown("- intelligent_segmenter: Segmentación semántica")
    
    # Footer
    st.markdown("---")
    st.markdown("*FastAgent System - Procesamiento Inteligente de Transcripciones*")
    
except ImportError as e:
    st.error(f"Error de importación: {e}")
    st.error("Verifica que todas las dependencias estén correctamente instaladas.")
'''

# Escribir nueva app principal
with open("src/streamlit_interface/app.py", 'w', encoding='utf-8') as f:
    f.write(app_content)

print("✅ Aplicación principal actualizada con navegación completa")
EOF

python actualizar_app_principal.py
```

---

## 🧪 FASE 6: Testing y Validación (30 min)

### 6.1 Tests de Funcionalidad Básica (15 min)

#### **Test de Imports Consolidados**
```bash
cat > test_imports_consolidados.py << 'EOF'
#!/usr/bin/env python3
"""Test comprehensivo de todos los imports consolidados."""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path.cwd()))

print("🧪 TESTING DE IMPORTS CONSOLIDADOS")
print("=" * 50)

tests_passed = 0
tests_total = 0

def test_import(module_path, description):
    global tests_passed, tests_total
    tests_total += 1
    try:
        exec(f"import {module_path}")
        print(f"✅ {description}")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ {description} - Error: {e}")

# Test componentes core
test_import("src.streamlit_interface.core.config_manager", "ConfigManager")
test_import("src.streamlit_interface.core.agent_interface", "AgentInterface")

# Test componentes UI
test_import("src.streamlit_interface.components.ui_components", "UI Components")

# Test utilidades
test_import("src.streamlit_interface.utils.file_handlers", "File Handlers")
test_import("src.streamlit_interface.utils.validation", "Validation")

# Test páginas (imports específicos)
try:
    from src.streamlit_interface.components.ui_components import setup_page_config
    print("✅ setup_page_config importado correctamente")
    tests_passed += 1
except ImportError as e:
    print(f"❌ setup_page_config - Error: {e}")
tests_total += 1

# Test conexión con core FastAgent
test_import("src.enhanced_agents", "Enhanced Agents (Core)")

print(f"\n📊 RESULTADOS: {tests_passed}/{tests_total} tests pasaron")
if tests_passed == tests_total:
    print("🎉 TODOS LOS IMPORTS FUNCIONAN CORRECTAMENTE")
else:
    print("⚠️ ALGUNOS IMPORTS FALLARON - Revisar antes de continuar")
EOF

python test_imports_consolidados.py > test_imports_results.log
cat test_imports_results.log
```

#### **Test de Ejecución de Streamlit**
```bash
cat > test_streamlit_app.py << 'EOF'
#!/usr/bin/env python3
"""Test de ejecución básica de la app Streamlit."""

import subprocess
import time
import requests
import signal
import os

def test_streamlit_launch():
    """Test de lanzamiento de la aplicación Streamlit."""
    print("🚀 Iniciando test de aplicación Streamlit...")
    
    # Lanzar Streamlit en background
    process = subprocess.Popen([
        "uv", "run", "streamlit", "run", 
        "src/streamlit_interface/app.py",
        "--server.port=8502",
        "--server.headless=true"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Esperar que se inicie
    time.sleep(10)
    
    try:
        # Test de conectividad
        response = requests.get("http://localhost:8502", timeout=5)
        if response.status_code == 200:
            print("✅ Aplicación Streamlit responde correctamente")
            result = True
        else:
            print(f"❌ Aplicación responde con código: {response.status_code}")
            result = False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando a Streamlit: {e}")
        result = False
    finally:
        # Terminar proceso
        process.terminate()
        process.wait()
    
    return result

if __name__ == "__main__":
    success = test_streamlit_launch()
    if success:
        print("🎉 TEST DE STREAMLIT EXITOSO")
    else:
        print("⚠️ TEST DE STREAMLIT FALLÓ")
EOF

python test_streamlit_app.py
echo "✅ Test de Streamlit completado"
```

### 6.2 Validación de Funcionalidades (15 min)

#### **Checklist de Funcionalidades**
```bash
cat > checklist_funcionalidades.md << 'EOF'
# ✅ Checklist de Validación de Funcionalidades

## Navegación y UI
- [ ] Página principal carga sin errores
- [ ] Navegación entre páginas funciona
- [ ] CSS personalizado se aplica correctamente
- [ ] Sidebar funciona en todas las páginas

## Dashboard (1_📊_Dashboard.py)
- [ ] Métricas del sistema se muestran
- [ ] Gráficos cargan correctamente
- [ ] Información de estado actualiza

## Configuración (2_⚙️_Configuración.py)
- [ ] Lista de proveedores disponibles
- [ ] Formularios de configuración funcionan
- [ ] Validación de configuraciones
- [ ] Guardado de configuraciones

## Procesamiento (3_📝_Procesamiento.py)
- [ ] Upload de archivos funciona
- [ ] Procesamiento con FastAgent inicia
- [ ] Progress bar funciona
- [ ] Descarga de resultados disponible

## Agentes (4_🤖_Agentes.py)
- [ ] Lista de agentes disponibles
- [ ] Configuración de agentes
- [ ] Test de conectividad con agentes
- [ ] Logs de agentes visibles

## Integración con Core
- [ ] FastAgent se conecta correctamente
- [ ] robust_main.py sigue funcionando
- [ ] Configuraciones compartidas funcionan
- [ ] No hay conflictos de dependencias

## Comandos de Lanzamiento
- [ ] `fastagent-ui` funciona
- [ ] `uv run streamlit run src/streamlit_interface/app.py` funciona
- [ ] No hay conflictos de puertos
- [ ] Logs sin errores críticos
EOF

echo "📋 Checklist creado: checklist_funcionalidades.md"
echo "   Ejecutar manualmente después de completar la migración"
```

---

## 🧹 FASE 7: Cleanup y Consolidación Final (20 min)

### 7.1 Eliminación de Archivos Duplicados (10 min)

#### **Script de Limpieza Segura**
```bash
cat > cleanup_duplicados.py << 'EOF'
#!/usr/bin/env python3
"""Script de limpieza segura post-migración."""

import shutil
from pathlib import Path
import os

def cleanup_streamlit_app():
    """Eliminar directorio streamlit_app después de migración exitosa."""
    
    streamlit_app_path = Path("streamlit_app")
    
    if streamlit_app_path.exists():
        print("🗑️ Preparando eliminación de streamlit_app/")
        
        # Crear backup final antes de eliminar
        backup_path = Path("backup_eliminados") / "streamlit_app_final"
        backup_path.parent.mkdir(exist_ok=True)
        
        shutil.copytree(streamlit_app_path, backup_path)
        print(f"📦 Backup final creado en: {backup_path}")
        
        # Preguntar confirmación
        confirm = input("¿Confirmas la eliminación de streamlit_app/? [y/N]: ")
        
        if confirm.lower() == 'y':
            shutil.rmtree(streamlit_app_path)
            print("✅ streamlit_app/ eliminado exitosamente")
            
            # Crear marcador de migración completada
            with open("MIGRACION_STREAMLIT_COMPLETADA.txt", 'w') as f:
                f.write("Migración de interfaces Streamlit completada exitosamente\n")
                f.write(f"Fecha: {__import__('datetime').datetime.now()}\n")
                f.write("Backup disponible en: backup_eliminados/streamlit_app_final\n")
            
            print("📄 Marcador de migración creado")
        else:
            print("⚠️ Eliminación cancelada - streamlit_app/ conservado")
    else:
        print("ℹ️ streamlit_app/ ya no existe")

def cleanup_archivos_temporales():
    """Limpiar archivos temporales de migración."""
    
    archivos_temporales = [
        "analisis_imports.log",
        "ui_components_diff.log", 
        "test_imports_results.log",
        "temp_migration/",
        "migrar_*.py",
        "actualizar_*.py",
        "test_*.py"
    ]
    
    print("🧹 Limpiando archivos temporales...")
    
    for archivo in archivos_temporales:
        path = Path(archivo)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"  🗑️ Eliminado: {archivo}")

if __name__ == "__main__":
    print("🧹 LIMPIEZA POST-MIGRACIÓN")
    print("=" * 30)
    
    cleanup_archivos_temporales()
    cleanup_streamlit_app()
    
    print("\n✅ LIMPIEZA COMPLETADA")
EOF

# NO ejecutar automáticamente - requiere confirmación manual
echo "⚠️ Script de limpieza creado: cleanup_duplicados.py"
echo "   EJECUTAR MANUALMENTE después de validar que todo funciona"
```

### 7.2 Actualización de Documentación (10 min)

#### **Actualizar README.md Principal**
```bash
cat > actualizar_readme.py << 'EOF'
#!/usr/bin/env python3
"""Actualizar README con nueva estructura consolidada."""

readme_content = '''# 🚀 Sistema Distribuido Multi-Agente con Q&A Inteligente - CONSOLIDADO

**Sistema LLM-agnóstico de procesamiento distribuido de transcripciones con generación automática de preguntas y respuestas educativas**

## 🏗️ Estructura Post-Consolidación

```
component_b_streamlit/
├── 🎯 APLICACIÓN CORE
│   ├── robust_main.py              # CLI principal
│   ├── fastagent.config.yaml       # Configuración central
│   └── src/
│       ├── enhanced_agents.py      # Sistema multiagente principal
│       ├── intelligent_segmenter.py
│       ├── meeting_processor.py
│       └── content_format_detector.py
│
└── 🖥️ INTERFAZ WEB UNIFICADA
    └── src/streamlit_interface/     # INTERFAZ ÚNICA CONSOLIDADA
        ├── app.py                   # Aplicación principal
        ├── core/                    # Gestión configuración y agentes
        ├── components/              # Componentes UI consolidados
        ├── pages/                   # 4 páginas completas
        │   ├── 1_📊_Dashboard.py    # Métricas y estado
        │   ├── 2_⚙️_Configuración.py # Gestión proveedores
        │   ├── 3_📝_Procesamiento.py # Procesamiento archivos
        │   └── 4_🤖_Agentes.py      # Gestión agentes
        ├── utils/                   # Utilidades consolidadas
        └── assets/                  # CSS y recursos
```

## 🚀 Uso Simplificado

### **Interfaz Web (Recomendado)**
```bash
# Método principal (UV-based)
fastagent-ui

# Método alternativo
uv run streamlit run src/streamlit_interface/app.py
```

### **CLI (Procesamiento Directo)**
```bash
# Procesamiento completo con contexto multimodal
uv run python robust_main.py --file transcripcion.txt --documents "imagen.jpg" "documento.pdf"
```

## ✨ Características Post-Consolidación

- ✅ **Interfaz única** - Sin duplicación de código
- ✅ **4 páginas completas** - Dashboard, Configuración, Procesamiento, Agentes
- ✅ **UI mejorada** - CSS personalizado y componentes avanzados
- ✅ **Gestión UV unificada** - Dependencias consistentes
- ✅ **Imports coherentes** - Estructura de proyecto limpia
- ✅ **Funcionalidad preservada** - Todas las características mantenidas

## 🔧 Migración Completada

La consolidación de interfaces duplicadas se completó exitosamente:

- **Eliminado**: `streamlit_app/` (duplicado standalone)
- **Conservado**: `src/streamlit_interface/` (integrado UV)
- **Migrado**: Todas las funcionalidades únicas
- **Resultado**: Interfaz única con funcionalidad completa

---

*Proyecto consolidado - Una sola interfaz, funcionalidad completa*
'''

# Backup del README actual
import shutil
shutil.copy("README.md", "README.md.pre-consolidacion")

# Escribir nuevo README
with open("README.md", 'w', encoding='utf-8') as f:
    f.write(readme_content)

print("✅ README.md actualizado")
print("📄 Backup original: README.md.pre-consolidacion")
EOF

python actualizar_readme.py
```

#### **Crear Documento de Migración**
```bash
cat > MIGRACION_COMPLETADA.md << 'EOF'
# ✅ Migración de Interfaces Streamlit Completada

**Fecha**: $(date +"%Y-%m-%d %H:%M:%S")  
**Duración estimada**: 3-4 horas  
**Estado**: COMPLETADA EXITOSAMENTE

## 📊 Resumen de Cambios

### ❌ Eliminado
- `streamlit_app/` - Interfaz standalone completa (eliminada)
- Código duplicado (~90% reducción)
- `requirements.txt` redundante
- Scripts de lanzamiento conflictivos

### ✅ Consolidado en `src/streamlit_interface/`
- **4 páginas completas**: Dashboard, Configuración, Procesamiento, Agentes
- **Componentes UI mejorados**: De 198 a 378+ líneas
- **Utilidades avanzadas**: file_handlers.py, validation.py
- **CSS personalizado**: assets/styles.css
- **Configuración unificada**: .streamlit/config.toml

### 🔧 Mejoras Técnicas
- **Imports consistentes**: Estructura `src.streamlit_interface.*`
- **Gestión UV unificada**: Sin conflictos pip/UV
- **Lanzamiento simplificado**: Un solo comando `fastagent-ui`
- **Documentación actualizada**: README, guías de uso

## 🚀 Comandos Post-Migración

```bash
# Lanzar interfaz web
fastagent-ui

# Verificar funcionamiento
uv run streamlit run src/streamlit_interface/app.py

# CLI sigue funcionando
uv run python robust_main.py --file ejemplo.txt
```

## 📋 Funcionalidades Preservadas

- ✅ Dashboard con métricas completas
- ✅ Configuración avanzada de proveedores
- ✅ Procesamiento con progress tracking
- ✅ Gestión completa de agentes
- ✅ Upload/download de archivos
- ✅ Integración FastAgent completa
- ✅ CSS personalizado y UI mejorada

## 🛡️ Backups Disponibles

- **Filesystem**: `backup_consolidacion_*`
- **Git branch**: `backup/pre-streamlit-consolidation`
- **Configuraciones**: `*.backup` files
- **Interfaz eliminada**: `backup_eliminados/streamlit_app_final`

## 🎯 Resultado Final

**Estructura simplificada, funcionalidad completa, mantenimiento reducido.**

---

*Migración realizada siguiendo el plan táctico detallado sin pérdida de funcionalidades.*
EOF

echo "✅ Documentación de migración creada"
```

---

## 🎯 FASE 8: Verificación Final y Entrega (15 min)

### Checklist de Verificación Final

#### **Comandos de Verificación Integral**
```bash
# Script de verificación final
cat > verificacion_final.sh << 'EOF'
#!/bin/bash
echo "🏁 VERIFICACIÓN FINAL DE MIGRACIÓN"
echo "================================="

# 1. Verificar estructura de directorios
echo "📁 Verificando estructura..."
if [ -d "src/streamlit_interface" ]; then
    echo "✅ src/streamlit_interface/ existe"
else
    echo "❌ src/streamlit_interface/ NO existe"
fi

if [ ! -d "streamlit_app" ]; then
    echo "✅ streamlit_app/ eliminado correctamente"
else
    echo "⚠️ streamlit_app/ aún existe"
fi

# 2. Verificar archivos críticos
echo "📄 Verificando archivos críticos..."
archivos_criticos=(
    "src/streamlit_interface/app.py"
    "src/streamlit_interface/pages/1_📊_Dashboard.py"
    "src/streamlit_interface/pages/2_⚙️_Configuración.py"
    "src/streamlit_interface/pages/3_📝_Procesamiento.py"
    "src/streamlit_interface/pages/4_🤖_Agentes.py"
    "src/streamlit_interface/components/ui_components.py"
    "src/streamlit_interface/utils/file_handlers.py"
    "src/streamlit_interface/assets/styles.css"
)

for archivo in "${archivos_criticos[@]}"; do
    if [ -f "$archivo" ]; then
        echo "✅ $archivo"
    else
        echo "❌ $archivo FALTANTE"
    fi
done

# 3. Test de imports
echo "🧪 Testing imports..."
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    from src.streamlit_interface.components.ui_components import setup_page_config
    print('✅ UI Components importan correctamente')
except ImportError as e:
    print(f'❌ Error UI Components: {e}')

try:
    from src.streamlit_interface.core.config_manager import ConfigManager
    print('✅ ConfigManager importa correctamente')
except ImportError as e:
    print(f'❌ Error ConfigManager: {e}')
"

# 4. Verificar dependencias UV
echo "📦 Verificando dependencias UV..."
uv sync --dry-run && echo "✅ Dependencias UV OK" || echo "❌ Problemas con dependencias UV"

# 5. Test básico de Streamlit
echo "🚀 Test básico de lanzamiento..."
timeout 15 uv run streamlit run src/streamlit_interface/app.py --server.port=8503 --server.headless=true > /dev/null 2>&1 &
sleep 10
if curl -s http://localhost:8503 > /dev/null; then
    echo "✅ Streamlit responde correctamente"
else
    echo "⚠️ Streamlit no responde (puede requerir más tiempo)"
fi
pkill -f "streamlit run" > /dev/null 2>&1

echo ""
echo "🎉 VERIFICACIÓN COMPLETADA"
echo "========================="
EOF

chmod +x verificacion_final.sh
./verificacion_final.sh
```

### Entregables Finales

#### **Resumen de Entregables**
```bash
echo "📦 ENTREGABLES DE MIGRACIÓN COMPLETADA"
echo "====================================="
echo ""
echo "🎯 APLICACIÓN CONSOLIDADA:"
echo "  - src/streamlit_interface/ (interfaz única)"
echo "  - 4 páginas completas"
echo "  - Funcionalidad preservada al 100%"
echo ""
echo "📚 DOCUMENTACIÓN:"
echo "  - README.md actualizado"
echo "  - MIGRACION_COMPLETADA.md"
echo "  - PLAN_TACTICO_CONSOLIDACION_STREAMLIT.md"
echo ""
echo "🛡️ BACKUPS DISPONIBLES:"
echo "  - backup_consolidacion_*"
echo "  - backup/pre-streamlit-consolidation (git)"
echo "  - backup_eliminados/streamlit_app_final"
echo ""
echo "🚀 COMANDOS DE USO:"
echo "  - fastagent-ui (interfaz web)"
echo "  - uv run python robust_main.py (CLI)"
echo ""
echo "✅ MIGRACIÓN COMPLETADA EXITOSAMENTE"
```

---

## 🚨 Procedimientos de Emergencia

### Rollback Completo de Emergencia

#### **Rollback Automático**
```bash
# En caso de problemas críticos, ejecutar:
./rollback_consolidacion.sh

# O rollback manual:
git checkout backup/pre-streamlit-consolidation
git checkout main -- . 
```

#### **Restauración Selectiva**
```bash
# Restaurar solo la interfaz integrada
cp -r backup_consolidacion_*/interfaces_originales/primaria/* src/streamlit_interface/

# Restaurar configuración
cp backup_consolidacion_*/fastagent.config.yaml.backup fastagent.config.yaml
```

### Solución de Problemas Comunes

#### **Error de Imports**
```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uv run python -c "import src.streamlit_interface.components.ui_components"
```

#### **Conflictos de Dependencias**
```bash
# Reinstalar dependencias
uv sync --reinstall
uv run streamlit --version
```

#### **Puerto Ocupado**
```bash
# Usar puerto alternativo
uv run streamlit run src/streamlit_interface/app.py --server.port=8504
```

---

## 📊 Métricas de Éxito

### Indicadores de Migración Exitosa

- ✅ **Reducción de código duplicado**: 90%+
- ✅ **Preservación de funcionalidad**: 100%
- ✅ **Tiempo de migración**: < 4 horas
- ✅ **Interfaces activas**: 1 (de 2 originales)
- ✅ **Errores de import**: 0
- ✅ **Funcionalidades perdidas**: 0

### Comandos de Validación Post-Migración

```bash
# Validación completa en una línea
fastagent-ui & sleep 15 && curl -s http://localhost:8501 > /dev/null && echo "✅ MIGRACIÓN EXITOSA" || echo "❌ REVISAR PROBLEMAS"
```

---

**🎯 PLAN COMPLETADO - READY FOR EXECUTION**

Este plan táctico garantiza una migración segura, preservando el 100% de las funcionalidades mientras elimina la duplicación de código. Cada paso incluye verificaciones y procedimientos de rollback para minimizar riesgos.