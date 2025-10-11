"""
Tests para agentes especializados usando mocks (sin configuración real)
Verifican la estructura y lógica sin depender de APIs externas
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_specialized_agents_imports():
    """Verifica que los agentes especializados se pueden importar correctamente"""
    from src.agents.specialized_agents import fast

    assert fast is not None
    assert hasattr(fast, 'name')
    assert fast.name == "Content Processing Pipeline"


def test_specialized_agents_structure():
    """Verifica que la estructura de agentes especializados es correcta"""
    from src.agents.specialized_agents import fast

    # Verificar que los agentes están registrados
    agent_names = list(fast.agents.keys())

    expected_agents = ["punctuator", "formatter", "titler", "qa_generator", "content_pipeline"]

    for agent in expected_agents:
        assert agent in agent_names, f"Agente '{agent}' no encontrado en {agent_names}"


def test_config_loading():
    """Verifica que la carga de configuración funciona"""
    from src.agents.specialized_agents import load_config, DEFAULT_MODEL

    config = load_config()
    assert isinstance(config, dict)
    assert isinstance(DEFAULT_MODEL, str)


@patch('src.agents.specialized_agents.fast')
def test_agent_interface_integration(mock_fast):
    """Verifica que la integración con agent_interface funciona"""
    from src.streamlit_interface.core.agent_interface import AgentInterface

    # Mock de config manager
    mock_config = MagicMock()

    # Crear instancia de AgentInterface
    interface = AgentInterface(mock_config)

    # Verificar que los métodos necesarios existen
    assert hasattr(interface, 'process_content')
    assert hasattr(interface, 'test_agent_connection')
    assert hasattr(interface, 'get_available_agents')


def test_agent_definitions():
    """Verifica que las definiciones de agentes tienen la estructura correcta"""
    from src.agents.specialized_agents import fast

    # Verificar punctuator
    punctuator = fast.agents.get("punctuator")
    assert punctuator is not None

    # Acceder a la instrucción a través del config
    instruction = punctuator.get('config', {}).instruction if isinstance(punctuator, dict) else punctuator.instruction
    assert instruction is not None
    assert "punctuation" in instruction.lower()

    # Verificar formatter
    formatter = fast.agents.get("formatter")
    assert formatter is not None
    formatter_instruction = formatter.get('config', {}).instruction if isinstance(formatter, dict) else formatter.instruction
    assert "format" in formatter_instruction.lower() or "transform" in formatter_instruction.lower()

    # Verificar titler
    titler = fast.agents.get("titler")
    assert titler is not None
    titler_instruction = titler.get('config', {}).instruction if isinstance(titler, dict) else titler.instruction
    assert "title" in titler_instruction.lower()

    # Verificar qa_generator
    qa_generator = fast.agents.get("qa_generator")
    assert qa_generator is not None
    qa_instruction = qa_generator.get('config', {}).instruction if isinstance(qa_generator, dict) else qa_generator.instruction
    assert ("question" in qa_instruction.lower() or
            "pregunta" in qa_instruction.lower())


def test_chain_definition():
    """Verifica que la cadena de procesamiento está definida correctamente"""
    from src.agents.specialized_agents import fast

    # Verificar que content_pipeline existe
    content_pipeline = fast.agents.get("content_pipeline")
    assert content_pipeline is not None

    # Verificar que es una cadena (tiene secuencia)
    assert 'sequence' in content_pipeline


def test_agent_parameters():
    """Verifica que los parámetros de los agentes son apropiados"""
    from src.agents.specialized_agents import fast

    for agent_name, agent in fast.agents.items():
        if hasattr(agent, 'request_params'):
            params = agent.request_params

            # Verificar que los tokens están en rango razonable
            if hasattr(params, 'maxTokens'):
                assert 0 < params.maxTokens <= 8192, f"maxTokens fuera de rango para {agent_name}"

            # Verificar que la temperatura está en rango válido
            if hasattr(params, 'temperature'):
                assert 0 <= params.temperature <= 1, f"temperature fuera de rango para {agent_name}"


def test_multilingual_support():
    """Verifica que las instrucciones soportan múltiples idiomas"""
    from src.agents.specialized_agents import fast

    # Verificar que las instrucciones mencionan soporte para español
    spanish_aware_agents = []

    for agent_name, agent in fast.agents.items():
        instruction = agent.get('config', {}).instruction if isinstance(agent, dict) else getattr(agent, 'instruction', None)
        if instruction and "spanish" in instruction.lower():
            spanish_aware_agents.append(agent_name)

    # Al menos algunos agentes deben estar conscientes del español
    assert len(spanish_aware_agents) > 0, "Ningún agente menciona soporte para español"


def test_content_preservation_focus():
    """Verifica que las instrucciones enfatizan preservación de contenido"""
    from src.agents.specialized_agents import fast

    preservation_keywords = ["preserve", "maintain", "retain", "keep", "content"]

    agents_with_preservation = []

    for agent_name, agent in fast.agents.items():
        instruction = agent.get('config', {}).instruction if isinstance(agent, dict) else getattr(agent, 'instruction', None)
        if instruction:
            instruction_lower = instruction.lower()
            if any(keyword in instruction_lower for keyword in preservation_keywords):
                agents_with_preservation.append(agent_name)

    # Los agentes principales deben mencionar preservación
    assert len(agents_with_preservation) >= 2, "Muy pocos agentes enfatizan preservación de contenido"


@patch('src.agents.specialized_agents.yaml.safe_load')
@patch('builtins.open')
@patch('pathlib.Path.exists')
def test_config_loading_with_file(mock_exists, mock_open, mock_yaml):
    """Verifica que la carga de configuración maneja archivos correctamente"""
    from src.agents.specialized_agents import load_config

    # Mock que el archivo existe
    mock_exists.return_value = True

    # Mock del contenido del archivo
    mock_yaml.return_value = {
        'default_model': 'azure.gpt-4.1',
        'azure': {'api_key': 'test_key'}
    }

    config = load_config()

    assert config['default_model'] == 'azure.gpt-4.1'
    assert 'azure' in config


def test_agent_temperature_progression():
    """Verifica que las temperaturas de agentes siguen una progresión lógica"""
    from src.agents.specialized_agents import fast

    # Punctuator debe tener temperatura baja (tarea mecánica)
    punctuator = fast.agents.get("punctuator")
    if punctuator and hasattr(punctuator, 'request_params') and hasattr(punctuator.request_params, 'temperature'):
        assert punctuator.request_params.temperature <= 0.4, "Punctuator debe tener temperatura baja"

    # QA Generator debe tener temperatura más alta (creatividad)
    qa_gen = fast.agents.get("qa_generator")
    if qa_gen and hasattr(qa_gen, 'request_params') and hasattr(qa_gen.request_params, 'temperature'):
        assert qa_gen.request_params.temperature >= 0.5, "QA Generator debe tener temperatura más alta"


def test_agent_instruction_specificity():
    """Verifica que las instrucciones de agentes son específicas y claras"""
    from src.agents.specialized_agents import fast

    for agent_name, agent in fast.agents.items():
        instruction = agent.get('config', {}).instruction if isinstance(agent, dict) else getattr(agent, 'instruction', None)
        if instruction:
            # Verificar longitud mínima (instrucciones detalladas), excepto para cadenas
            if agent_name != "content_pipeline":
                assert len(instruction) > 100, f"Instrucción de {agent_name} muy corta"

            # Verificar que menciona la tarea específica
            if agent_name == "punctuator":
                assert "punctuation" in instruction.lower()
            elif agent_name == "formatter":
                assert "format" in instruction.lower()
            elif agent_name == "titler":
                assert "title" in instruction.lower()
            elif agent_name == "qa_generator":
                assert ("question" in instruction.lower() or "pregunta" in instruction.lower())


if __name__ == "__main__":
    # Permitir ejecutar tests directamente
    pytest.main([__file__, "-v"])