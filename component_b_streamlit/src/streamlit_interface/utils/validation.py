"""
Validation Utilities
===================

Utilidades para validar configuraciones, contenido y parámetros.
"""

import re
import yaml
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import requests

def validate_api_key(api_key: str, provider: str) -> Tuple[bool, str]:
    """
    Valida formato de API key según el proveedor.

    Args:
        api_key: API key a validar
        provider: Proveedor (azure, openai, anthropic, etc.)

    Returns:
        Tuple (es_válido, mensaje)
    """

    if not api_key or api_key.strip() == "":
        return False, "API key no puede estar vacía"

    # Validaciones específicas por proveedor
    if provider == "azure":
        if api_key == "YOUR_AZURE_API_KEY_HERE":
            return False, "Debes reemplazar el placeholder con tu API key real"

        if len(api_key) < 20:
            return False, "Azure API key parece demasiado corta"

        return True, "API key válida"

    elif provider == "openai":
        if not api_key.startswith("sk-"):
            return False, "OpenAI API key debe comenzar con 'sk-'"

        if len(api_key) < 40:
            return False, "OpenAI API key parece demasiado corta"

        return True, "API key válida"

    elif provider == "anthropic":
        if not api_key.startswith("sk-ant-"):
            return False, "Anthropic API key debe comenzar con 'sk-ant-'"

        if len(api_key) < 40:
            return False, "Anthropic API key parece demasiado corta"

        return True, "API key válida"

    elif provider == "generic":  # Ollama
        # Ollama no requiere validación especial
        return True, "Configuración válida"

    return True, "API key válida"

def validate_url(url: str, url_type: str = "general") -> Tuple[bool, str]:
    """
    Valida formato de URL.

    Args:
        url: URL a validar
        url_type: Tipo de URL (azure_base, ollama, general)

    Returns:
        Tuple (es_válida, mensaje)
    """

    if not url or url.strip() == "":
        return False, "URL no puede estar vacía"

    # Validación básica de formato
    url_pattern = re.compile(
        r'^https?://'  # http:// o https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # puerto opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if not url_pattern.match(url):
        return False, "Formato de URL inválido"

    # Validaciones específicas por tipo
    if url_type == "azure_base":
        if not "cognitiveservices.azure.com" in url:
            return False, "URL de Azure debe contener 'cognitiveservices.azure.com'"

        if not url.startswith("https://"):
            return False, "Azure requiere HTTPS"

    elif url_type == "ollama":
        if not url.endswith("/v1"):
            return False, "URL de Ollama debe terminar en '/v1'"

        # Verificar puertos comunes de Ollama
        if ":11434" not in url and "localhost" in url:
            return False, "Puerto de Ollama por defecto es 11434"

    return True, "URL válida"

def validate_content(content: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Valida contenido de entrada para procesamiento.

    Args:
        content: Contenido STT a validar

    Returns:
        Tuple (es_válido, mensaje, estadísticas)
    """

    if not content or content.strip() == "":
        return False, "El contenido no puede estar vacío", {}

    # Estadísticas básicas
    words = content.split()
    word_count = len(words)
    char_count = len(content)
    line_count = len(content.split('\n'))

    stats = {
        'word_count': word_count,
        'char_count': char_count,
        'line_count': line_count,
        'estimated_processing_time': max(1, word_count // 200)  # minutos estimados
    }

    # Validaciones de tamaño
    if word_count < 10:
        return False, "El contenido es demasiado corto (mínimo 10 palabras)", stats

    if word_count > 50000:
        return False, "El contenido es demasiado largo (máximo 50,000 palabras)", stats

    # Validaciones de calidad
    warnings = []

    # Verificar si parece transcripción STT
    stt_indicators = ['eh', 'bueno', 'entonces', 'mm', 'ah', 'este']
    has_stt_indicators = any(indicator in content.lower() for indicator in stt_indicators)

    if not has_stt_indicators:
        warnings.append("El contenido no parece una transcripción STT típica")

    # Verificar puntuación limitada (característico de STT)
    punctuation_ratio = sum(1 for char in content if char in '.,!?;:') / char_count
    if punctuation_ratio > 0.05:
        warnings.append("El contenido ya tiene mucha puntuación (¿ya está procesado?)")

    # Verificar idioma predominante (español esperado)
    spanish_words = ['que', 'es', 'el', 'la', 'de', 'en', 'un', 'para', 'con', 'por']
    spanish_count = sum(1 for word in words[:100] if word.lower() in spanish_words)

    if spanish_count < 5:
        warnings.append("El contenido no parece estar en español")

    stats['warnings'] = warnings

    return True, "Contenido válido", stats

def validate_rate_limiting_config(config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida configuración de rate limiting.

    Args:
        config: Configuración de rate limiting

    Returns:
        Tuple (es_válida, mensaje)
    """

    required_fields = [
        'requests_per_minute',
        'delay_between_requests',
        'max_tokens_per_request',
        'backoff_factor',
        'max_backoff'
    ]

    # Verificar campos requeridos
    for field in required_fields:
        if field not in config:
            return False, f"Campo requerido faltante: {field}"

        if not isinstance(config[field], (int, float)):
            return False, f"Campo {field} debe ser numérico"

    # Validaciones de rangos
    validations = [
        (config['requests_per_minute'] > 0, "requests_per_minute debe ser mayor a 0"),
        (config['requests_per_minute'] <= 60, "requests_per_minute no debe exceder 60"),
        (config['delay_between_requests'] >= 0, "delay_between_requests debe ser >= 0"),
        (config['delay_between_requests'] <= 300, "delay_between_requests no debe exceder 300s"),
        (config['max_tokens_per_request'] > 0, "max_tokens_per_request debe ser mayor a 0"),
        (config['max_tokens_per_request'] <= 150000, "max_tokens_per_request no debe exceder 150,000"),
        (config['backoff_factor'] >= 1.0, "backoff_factor debe ser >= 1.0"),
        (config['backoff_factor'] <= 10.0, "backoff_factor no debe exceder 10.0"),
        (config['max_backoff'] >= 60, "max_backoff debe ser >= 60s"),
        (config['max_backoff'] <= 3600, "max_backoff no debe exceder 1 hora")
    ]

    for is_valid, message in validations:
        if not is_valid:
            return False, message

    # Validaciones de lógica
    if config['delay_between_requests'] > config['max_backoff']:
        return False, "delay_between_requests no puede ser mayor que max_backoff"

    return True, "Configuración de rate limiting válida"

def validate_file_upload(file_content: bytes, file_name: str, max_size_mb: int = 10) -> Tuple[bool, str]:
    """
    Valida archivo subido.

    Args:
        file_content: Contenido del archivo en bytes
        file_name: Nombre del archivo
        max_size_mb: Tamaño máximo en MB

    Returns:
        Tuple (es_válido, mensaje)
    """

    # Validar tamaño
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"Archivo demasiado grande: {size_mb:.1f}MB (máximo: {max_size_mb}MB)"

    # Validar extensión
    allowed_extensions = {'.txt', '.md', '.pdf', '.png', '.jpg', '.jpeg'}
    file_extension = Path(file_name).suffix.lower()

    if file_extension not in allowed_extensions:
        return False, f"Extensión no permitida: {file_extension}"

    # Validar contenido para archivos de texto
    if file_extension in {'.txt', '.md'}:
        try:
            content = file_content.decode('utf-8')
            if len(content.strip()) == 0:
                return False, "Archivo de texto está vacío"
        except UnicodeDecodeError:
            return False, "Archivo de texto no está en formato UTF-8"

    return True, "Archivo válido"

def validate_model_name(model_name: str, available_providers: List[str]) -> Tuple[bool, str]:
    """
    Valida nombre de modelo.

    Args:
        model_name: Nombre del modelo (ej: "azure.gpt-4.1")
        available_providers: Lista de proveedores configurados

    Returns:
        Tuple (es_válido, mensaje)
    """

    if not model_name or model_name.strip() == "":
        return False, "Nombre de modelo no puede estar vacío"

    # Validar formato
    if '.' not in model_name:
        return False, "Nombre de modelo debe tener formato 'proveedor.modelo'"

    provider, model = model_name.split('.', 1)

    # Validar proveedor
    if provider not in available_providers:
        return False, f"Proveedor '{provider}' no está configurado"

    # Validaciones específicas por proveedor
    valid_models = {
        'azure': ['gpt-4.1', 'gpt-4o', 'gpt-4'],
        'openai': ['gpt-4o', 'gpt-4', 'o1-mini', 'o3-mini'],
        'anthropic': ['haiku', 'sonnet', 'opus'],
        'generic': ['llama3.1', 'mistral', 'codellama']  # Ollama
    }

    if provider in valid_models and model not in valid_models[provider]:
        available = ', '.join(valid_models[provider])
        return False, f"Modelo '{model}' no válido para {provider}. Disponibles: {available}"

    return True, "Modelo válido"

def test_connection(provider: str, config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Prueba conexión con un proveedor.

    Args:
        provider: Nombre del proveedor
        config: Configuración del proveedor

    Returns:
        Tuple (conexión_exitosa, mensaje)
    """

    try:
        if provider == "generic":  # Ollama
            base_url = config.get('base_url', '')
            if not base_url:
                return False, "URL base no configurada"

            # Probar endpoint de Ollama
            test_url = base_url.replace('/v1', '/api/tags')
            response = requests.get(test_url, timeout=5)

            if response.status_code == 200:
                return True, "Conexión exitosa con Ollama"
            else:
                return False, f"Ollama responde con código {response.status_code}"

        elif provider == "azure":
            # Para Azure, solo validamos formato por ahora
            # Una prueba real requeriría una llamada a la API
            base_url = config.get('base_url', '')
            api_key = config.get('api_key', '')

            if not base_url or not api_key:
                return False, "URL base y API key requeridos"

            if api_key == "YOUR_AZURE_API_KEY_HERE":
                return False, "API key es un placeholder"

            return True, "Configuración de Azure válida (no se probó la conexión real)"

        else:
            # Para otros proveedores, solo validación básica
            api_key = config.get('api_key', '')
            if not api_key:
                return False, "API key requerida"

            return True, f"Configuración de {provider} válida (no se probó la conexión real)"

    except requests.RequestException as e:
        return False, f"Error de conexión: {e}"

    except Exception as e:
        return False, f"Error inesperado: {e}"

def validate_yaml_config(config_path: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Valida archivo de configuración YAML.

    Args:
        config_path: Ruta al archivo de configuración

    Returns:
        Tuple (es_válido, mensaje, configuración_parseada)
    """

    try:
        if not Path(config_path).exists():
            return False, f"Archivo no existe: {config_path}", None

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            return False, "Configuración debe ser un diccionario YAML", None

        # Validaciones básicas
        required_sections = ['default_model']

        for section in required_sections:
            if section not in config:
                return False, f"Sección requerida faltante: {section}", None

        return True, "Configuración YAML válida", config

    except yaml.YAMLError as e:
        return False, f"Error parseando YAML: {e}", None

    except Exception as e:
        return False, f"Error leyendo archivo: {e}", None