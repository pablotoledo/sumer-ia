#!/bin/bash
# FastAgent Streamlit Interface - Script de inicio
# ==============================================

echo "🤖 FastAgent Streamlit Interface"
echo "=================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio component_b_streamlit"
    exit 1
fi

# Verificar que UV esté disponible
if ! command -v uv &> /dev/null; then
    echo "❌ Error: UV no está instalado"
    echo "   Instala UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "🔍 Verificando dependencias..."

# Verificar que Streamlit esté disponible
if ! uv run python -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit no está instalado. Instalando dependencias..."
    uv sync --extra streamlit
fi

echo "✅ Dependencias verificadas"
echo ""
echo "🚀 Iniciando FastAgent Streamlit Interface..."
echo ""
echo "   📱 La aplicación se abrirá en: http://localhost:8501"
echo "   🛑 Para detener: Ctrl+C"
echo ""

# Ejecutar Streamlit
uv run streamlit run src/streamlit_interface/app.py --server.port 8501 --server.address localhost