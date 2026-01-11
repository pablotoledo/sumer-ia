#!/usr/bin/env python3
"""
Test de Integración Streamlit
============================

Script para verificar que la integración Streamlit funciona correctamente.
"""

import sys
import importlib.util
from pathlib import Path
import pytest


def test_imports():
    """Prueba que todos los imports funcionen correctamente."""
    # Test import de streamlit
    import streamlit as st
    
    # Test import del módulo principal
    from src.streamlit_interface import main, run_streamlit
    
    # Test import de ConfigManager
    from src.streamlit_interface.core.config_manager import ConfigManager
    
    # Test import de AgentInterface
    from src.streamlit_interface.core.agent_interface import AgentInterface
    
    assert st is not None
    assert main is not None
    assert ConfigManager is not None
    assert AgentInterface is not None


def test_config_manager():
    """Prueba el ConfigManager."""
    from src.streamlit_interface.core.config_manager import ConfigManager
    
    # Crear instancia
    config_manager = ConfigManager()
    assert config_manager is not None
    
    # Probar métodos básicos
    config = config_manager.get_config()
    assert isinstance(config, dict)
    assert len(config) > 0
    
    # Probar validación
    validation = config_manager.validate_config()
    assert isinstance(validation, dict)
    assert 'has_provider' in validation


def test_fastagent_availability():
    """Prueba que FastAgent esté disponible."""
    # Test import de enhanced_agents
    from src.enhanced_agents import fast
    assert fast is not None


def test_pyproject_scripts():
    """Verifica que los scripts estén definidos en pyproject.toml."""
    try:
        import toml
    except ImportError:
        pytest.skip("toml not available")
    
    with open('pyproject.toml', 'r') as f:
        config = toml.load(f)
    
    scripts = config.get('project', {}).get('scripts', {})
    
    expected_scripts = ['fastagent-ui', 'fastagent-dashboard']
    
    for script in expected_scripts:
        assert script in scripts, f"Script '{script}' no encontrado en pyproject.toml"


def test_streamlit_dependencies():
    """Verifica dependencias específicas de Streamlit."""
    dependencies = [
        'plotly',
        'pandas',
        'requests',
        'yaml'  # pyyaml se importa como 'yaml'
    ]
    
    for package in dependencies:
        module = __import__(package)
        assert module is not None, f"{package} no disponible"


def main():
    """Ejecuta todas las pruebas."""
    
    print("🚀 FastAgent Streamlit Integration - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports básicos", test_imports),
        ("ConfigManager", test_config_manager),
        ("FastAgent disponibilidad", test_fastagent_availability),
        ("Scripts pyproject.toml", test_pyproject_scripts),
        ("Dependencias Streamlit", test_streamlit_dependencies)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            test_func()
            print(f"✅ PASS")
            results.append((test_name, True))
        except Exception as e:
            print(f"❌ FAIL: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Resultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! La integración Streamlit está lista.")


if __name__ == "__main__":
    main()