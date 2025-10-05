"""
Configuration Manager
====================

Gestiona la configuración de FastAgent de forma centralizada,
incluyendo proveedores LLM, agentes y parámetros del sistema.
"""

import yaml
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import json

class ConfigManager:
    """Gestor centralizado de configuración para FastAgent."""
    
    def __init__(self):
        self.config_path = Path("fastagent.config.yaml")
        self.example_config_path = Path("fastagent.config.yaml.example")
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración desde el archivo."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            elif self.example_config_path.exists():
                # Si no existe config, usar example como template
                with open(self.example_config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                # Configuración por defecto
                self._config = self._get_default_config()
                
        except Exception as e:
            st.error(f"Error cargando configuración: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuración por defecto."""
        return {
            'default_model': 'azure.gpt-4.1',
            'azure': {
                'api_key': 'YOUR_AZURE_API_KEY_HERE',
                'base_url': 'https://your-resource-name.cognitiveservices.azure.com/',
                'azure_deployment': 'gpt-4.1',
                'api_version': '2025-01-01-preview',
                'max_retries': 8,
                'retry_delay': 90,
                'timeout': 180
            },
            'generic': {
                'api_key': 'ollama',
                'base_url': 'http://192.168.1.100:11434/v1'
            },
            'logger': {
                'progress_display': True,
                'show_chat': True,
                'show_tools': True,
                'truncate_tools': True,
                'level': 'info'
            },
            'rate_limiting': {
                'max_tokens_per_request': 50000,
                'requests_per_minute': 3,
                'max_retries': 3,
                'retry_base_delay': 60,
                'delay_between_requests': 30
            },
            'mcp': {
                'servers': {
                    'fetch': {
                        'command': 'uvx',
                        'args': ['mcp-server-fetch']
                    },
                    'filesystem': {
                        'command': 'npx',
                        'args': ['-y', '@modelcontextprotocol/server-filesystem', '.']
                    }
                }
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración actual."""
        return self._config.copy()
    
    def update_config(self, updates: Dict[str, Any]):
        """Actualiza la configuración con nuevos valores."""
        self._deep_update(self._config, updates)
        self._save_config()
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Actualiza recursivamente diccionarios anidados."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _save_config(self):
        """Guarda la configuración al archivo."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            st.success("✅ Configuración guardada correctamente")
        except Exception as e:
            st.error(f"❌ Error guardando configuración: {e}")
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Retorna configuración de un proveedor específico."""
        return self._config.get(provider, {})
    
    def update_provider_config(self, provider: str, config: Dict[str, Any]):
        """Actualiza configuración de un proveedor específico."""
        self._config[provider] = config
        self._save_config()
    
    def get_available_providers(self) -> list:
        """Retorna lista de proveedores configurados."""
        providers = []
        provider_keys = ['azure', 'generic', 'openai', 'anthropic', 'google']
        
        for provider in provider_keys:
            if provider in self._config:
                providers.append(provider)
        
        return providers
    
    def is_provider_configured(self, provider: str) -> bool:
        """Verifica si un proveedor está correctamente configurado."""
        config = self.get_provider_config(provider)
        
        if provider == 'azure':
            return (config.get('api_key') and 
                   config.get('api_key') != 'YOUR_AZURE_API_KEY_HERE' and
                   config.get('base_url'))
        
        elif provider == 'generic':  # Ollama
            return config.get('base_url') is not None
        
        elif provider in ['openai', 'anthropic', 'google']:
            return config.get('api_key') is not None
        
        return False
    
    def get_default_model(self) -> str:
        """Retorna el modelo por defecto."""
        return self._config.get('default_model', 'azure.gpt-4.1')
    
    def set_default_model(self, model: str):
        """Establece el modelo por defecto."""
        self._config['default_model'] = model
        self._save_config()
    
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Retorna configuración de rate limiting."""
        return self._config.get('rate_limiting', {})
    
    def update_rate_limiting_config(self, config: Dict[str, Any]):
        """Actualiza configuración de rate limiting."""
        self._config['rate_limiting'] = config
        self._save_config()
    
    def get_agent_instructions(self) -> Dict[str, str]:
        """Retorna las instrucciones de los agentes desde el código."""
        # Estas instrucciones se pueden extraer del código o mantener aquí
        return {
            'punctuator': """Add proper punctuation and capitalization to speech-to-text content while preserving 100% of the original words.

RULES:
- Add punctuation marks (periods, commas, question marks, exclamation points)
- Capitalize proper nouns and sentence beginnings  
- DO NOT remove, change, or rephrase any words
- DO NOT eliminate filler words like "eh", "bueno", "entonces" 
- Keep ALL content exactly as provided, just add punctuation""",
            
            'simple_processor': """You are an educational content processor that transforms speech-to-text transcriptions into professional educational documents.

TASK: Process each content segment through these steps:
1. PUNCTUATION: Add proper punctuation and capitalization
2. TITLE: Create a descriptive title for this segment
3. FORMATTING: Structure content with appropriate headings and paragraphs
4. Q&A: Generate 3-5 educational questions with detailed answers

PRESERVE: 100% of original content, no elimination or paraphrasing""",
            
            'meeting_processor': """You are a meeting content processor specialized in extracting actionable insights from diarized meetings.

TASK: Process meeting segments to extract:
1. DECISIONS: What decisions were made and by whom
2. ACTION ITEMS: Tasks assigned with responsible parties and deadlines
3. UNRESOLVED QUESTIONS: Issues that need follow-up
4. TECHNICAL DISCUSSIONS: Key technical points by participant

FORMAT: Create structured output with clear sections for decisions, actions, and Q&A."""
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """Valida la configuración actual."""
        validation = {
            'has_provider': False,
            'valid_model': False,
            'rate_limiting_ok': False
        }
        
        # Verificar si hay al menos un proveedor configurado
        for provider in ['azure', 'generic', 'openai', 'anthropic', 'google']:
            if self.is_provider_configured(provider):
                validation['has_provider'] = True
                break
        
        # Verificar modelo por defecto
        default_model = self.get_default_model()
        if default_model and '.' in default_model:
            validation['valid_model'] = True
        
        # Verificar rate limiting
        rate_config = self.get_rate_limiting_config()
        if (rate_config.get('requests_per_minute', 0) > 0 and
            rate_config.get('delay_between_requests', 0) > 0):
            validation['rate_limiting_ok'] = True
        
        return validation
    
    def export_config_json(self) -> str:
        """Exporta la configuración a JSON para debugging."""
        return json.dumps(self._config, indent=2, ensure_ascii=False)
    
    def reset_to_defaults(self):
        """Resetea la configuración a valores por defecto."""
        self._config = self._get_default_config()
        self._save_config()