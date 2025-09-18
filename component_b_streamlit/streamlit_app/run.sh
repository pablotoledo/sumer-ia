#!/bin/bash
# FastAgent Streamlit Interface - Script de inicio
# ==============================================

echo "🤖 FastAgent Streamlit Interface"
echo "=================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Error: Este script debe ejecutarse desde el directorio streamlit_app"
    echo "   Uso: cd streamlit_app && ./run.sh"
    exit 1
fi

# Verificar que Python esté disponible
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python no está instalado o no está en el PATH"
    exit 1
fi

# Verificar que Streamlit esté instalado
if ! python -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit no está instalado. Instalando dependencias..."
    pip install -r requirements.txt
fi

# Verificar que FastAgent esté disponible
echo "🔍 Verificando FastAgent..."
cd ..
if ! python -c "from src.enhanced_agents import fast" &> /dev/null; then
    echo "❌ Error: FastAgent no está disponible"
    echo "   Asegúrate de estar en el directorio component_b_streamlit"
    echo "   y que las dependencias de FastAgent estén instaladas"
    exit 1
fi
cd streamlit_app

echo "✅ FastAgent disponible"
echo ""

# Verificar configuración
echo "🔧 Verificando configuración..."
if [ -f "../fastagent.config.yaml" ]; then
    echo "✅ Archivo de configuración encontrado"
else
    echo "⚠️  Archivo de configuración no encontrado"
    echo "   Se usará la configuración por defecto"
fi

echo ""
echo "🚀 Iniciando FastAgent Streamlit Interface..."
echo ""
echo "   📱 La aplicación se abrirá en: http://localhost:8501"
echo "   🛑 Para detener: Ctrl+C"
echo ""

# Configurar variables de entorno opcionales
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=localhost

# Iniciar Streamlit
streamlit run streamlit_app.py