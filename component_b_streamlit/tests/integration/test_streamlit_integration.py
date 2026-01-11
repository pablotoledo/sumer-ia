#!/usr/bin/env python3
"""
Test de Integración Streamlit
============================

Script para verificar que la integración Streamlit funciona correctamente.
"""

import sys
import importlib.util
from pathlib import Path

def test_imports():
    """Prueba que todos los imports funcionen correctamente."""
    
    print("🧪 Probando imports de Streamlit Integration...")
    
    try:
        # Test import de streamlit
        import streamlit as st
        print("✅ Streamlit disponible")
    except ImportError as e:
        print(f"❌ Error importando Streamlit: {e}")
        return False
    
    try:
        # Test import del módulo principal
        from src.streamlit_interface import main, run_streamlit
        print("✅ Módulo streamlit_interface disponible")
    except ImportError as e:
        print(f"❌ Error importando streamlit_interface: {e}")
        return False
    
    try:
        # Test import de ConfigManager
        from src.streamlit_interface.core.config_manager import ConfigManager
        print("✅ ConfigManager disponible")
    except ImportError as e:
        print(f"❌ Error importando ConfigManager: {e}")
        return False
    
    try:
        # Test import de AgentInterface
        from src.streamlit_interface.core.agent_interface import AgentInterface
        print("✅ AgentInterface disponible")
    except ImportError as e:
        print(f"❌ Error importando AgentInterface: {e}")
        return False
    
    return True

def test_config_manager():
    """Prueba el ConfigManager."""
    
    print("\n🧪 Probando ConfigManager...")
    
    try:
        from src.streamlit_interface.core.config_manager import ConfigManager
        
        # Crear instancia
        config_manager = ConfigManager()
        print("✅ ConfigManager inicializado")
        
        # Probar métodos básicos
        config = config_manager.get_config()
        print(f"✅ Configuración cargada: {len(config)} secciones")
        
        # Probar validación
        validation = config_manager.validate_config()
        print(f"✅ Validación ejecutada: {validation}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en ConfigManager: {e}")
        return False

def test_fastagent_availability():
    """Prueba que FastAgent esté disponible."""
    
    print("\n🧪 Probando disponibilidad de FastAgent...")
    
    try:
        # Test import de enhanced_agents
        from src.enhanced_agents import fast
        print("✅ FastAgent enhanced_agents disponible")
        
        # Test import de robust_main
        import robust_main
        print("✅ robust_main disponible")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando FastAgent: {e}")
        print("   Asegúrate de estar en el directorio correcto del proyecto")
        return False

def test_pyproject_scripts():
    """Verifica que los scripts estén definidos en pyproject.toml."""
    
    print("\n🧪 Verificando scripts en pyproject.toml...")
    
    try:
        import toml
        
        with open('pyproject.toml', 'r') as f:
            config = toml.load(f)
        
        scripts = config.get('project', {}).get('scripts', {})
        
        expected_scripts = ['fastagent-ui', 'fastagent-dashboard']
        
        for script in expected_scripts:
            if script in scripts:
                print(f"✅ Script '{script}' definido: {scripts[script]}")
            else:
                print(f"❌ Script '{script}' no encontrado")
                return False
        
        return True
        
    except ImportError:
        print("⚠️ toml no disponible, saltando verificación de scripts")
        return True
    except Exception as e:
        print(f"❌ Error verificando pyproject.toml: {e}")
        return False

def test_streamlit_dependencies():
    """Verifica dependencias específicas de Streamlit."""
    
    print("\n🧪 Probando dependencias de Streamlit...")
    
    dependencies = [
        ('plotly', 'Gráficos interactivos'),
        ('pandas', 'Manipulación de datos'),
        ('requests', 'HTTP requests'),
        ('yaml', 'Configuración YAML')  # pyyaml se importa como 'yaml'
    ]
    
    all_ok = True
    
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"✅ {package} disponible ({description})")
        except ImportError:
            print(f"❌ {package} no disponible ({description})")
            all_ok = False
    
    return all_ok

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
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE TESTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Resultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! La integración Streamlit está lista.")
        print("\n🚀 Para usar la interfaz:")
        print("   fastagent-ui")
        print("   # o")
        print("   uv run python -m src.streamlit_interface.app")
    else:
        print("⚠️ Algunos tests fallaron. Revisa las dependencias o configuración.")
        print("\n🔧 Para instalar dependencias:")
        print("   uv sync --extra streamlit")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)