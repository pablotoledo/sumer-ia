"""
Configuration Loader for FastAgent CLI
======================================

Loads configuration from environment variables, config files, and command-line arguments.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import argparse


class EnvironmentConfig:
    """Load configuration from environment variables."""

    @staticmethod
    def get_provider() -> Optional[str]:
        """Get LLM provider from environment (FASTAGENT_PROVIDER)."""
        return os.getenv('FASTAGENT_PROVIDER')

    @staticmethod
    def get_model() -> Optional[str]:
        """Get model from environment (FASTAGENT_MODEL)."""
        return os.getenv('FASTAGENT_MODEL')

    @staticmethod
    def get_delay() -> Optional[int]:
        """Get delay between requests from environment (FASTAGENT_DELAY)."""
        delay = os.getenv('FASTAGENT_DELAY')
        return int(delay) if delay else None

    @staticmethod
    def get_max_retries() -> Optional[int]:
        """Get max retries from environment (FASTAGENT_MAX_RETRIES)."""
        retries = os.getenv('FASTAGENT_MAX_RETRIES')
        return int(retries) if retries else None

    @staticmethod
    def get_retry_delay() -> Optional[int]:
        """Get retry delay from environment (FASTAGENT_RETRY_DELAY)."""
        delay = os.getenv('FASTAGENT_RETRY_DELAY')
        return int(delay) if delay else None

    @staticmethod
    def get_output_dir() -> Optional[str]:
        """Get output directory from environment (FASTAGENT_OUTPUT_DIR)."""
        return os.getenv('FASTAGENT_OUTPUT_DIR')

    # Azure OpenAI
    @staticmethod
    def get_azure_api_key() -> Optional[str]:
        """Get Azure API key from environment (AZURE_API_KEY)."""
        return os.getenv('AZURE_API_KEY')

    @staticmethod
    def get_azure_base_url() -> Optional[str]:
        """Get Azure base URL from environment (AZURE_BASE_URL)."""
        return os.getenv('AZURE_BASE_URL')

    @staticmethod
    def get_azure_deployment() -> Optional[str]:
        """Get Azure deployment from environment (AZURE_DEPLOYMENT)."""
        return os.getenv('AZURE_DEPLOYMENT')

    @staticmethod
    def get_azure_api_version() -> Optional[str]:
        """Get Azure API version from environment (AZURE_API_VERSION)."""
        return os.getenv('AZURE_API_VERSION')

    # Ollama
    @staticmethod
    def get_ollama_base_url() -> Optional[str]:
        """Get Ollama base URL from environment (OLLAMA_BASE_URL)."""
        return os.getenv('OLLAMA_BASE_URL')

    # OpenAI
    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """Get OpenAI API key from environment (OPENAI_API_KEY)."""
        return os.getenv('OPENAI_API_KEY')

    # Anthropic
    @staticmethod
    def get_anthropic_api_key() -> Optional[str]:
        """Get Anthropic API key from environment (ANTHROPIC_API_KEY)."""
        return os.getenv('ANTHROPIC_API_KEY')


def load_fastagent_config(config_path: str = 'fastagent.config.yaml') -> Dict[str, Any]:
    """
    Load FastAgent configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)

    if not config_file.exists():
        # Try alternate locations
        alt_paths = [
            Path('.') / 'fastagent.config.yaml',
            Path(__file__).parent.parent.parent / 'fastagent.config.yaml',
        ]

        for alt_path in alt_paths:
            if alt_path.exists():
                config_file = alt_path
                break
        else:
            # Return default empty config
            return {}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except Exception as e:
        print(f"Warning: Could not load config from {config_file}: {e}")
        return {}


def get_preset_config(preset: str) -> Dict[str, Any]:
    """
    Get preset configuration.

    Args:
        preset: Preset name (fast, balanced, conservative, intelligent)

    Returns:
        Preset configuration dictionary
    """
    presets = {
        'fast': {
            'segmentation': 'programmatic',
            'enable_qa': False,
            'delay_between_requests': 10,
            'max_retries': 2,
            'retry_base_delay': 30
        },
        'balanced': {
            'segmentation': 'auto',
            'enable_qa': True,
            'qa_questions': 3,
            'delay_between_requests': 20,
            'max_retries': 3,
            'retry_base_delay': 60
        },
        'conservative': {
            'segmentation': 'programmatic',
            'enable_qa': True,
            'qa_questions': 4,
            'delay_between_requests': 45,
            'max_retries': 5,
            'retry_base_delay': 90
        },
        'intelligent': {
            'segmentation': 'intelligent',
            'enable_qa': True,
            'qa_questions': 5,
            'delay_between_requests': 30,
            'max_retries': 3,
            'retry_base_delay': 60
        }
    }

    return presets.get(preset, presets['balanced'])


def merge_configs(args: argparse.Namespace, env: EnvironmentConfig) -> Dict[str, Any]:
    """
    Merge configurations from multiple sources.

    Priority (highest to lowest):
    1. Command-line arguments
    2. Preset (if specified)
    3. Environment variables
    4. fastagent.config.yaml
    5. Defaults

    Args:
        args: Parsed command-line arguments
        env: Environment configuration

    Returns:
        Merged configuration dictionary
    """
    # Load base config from YAML
    yaml_config = load_fastagent_config(args.config)

    # Start with defaults
    config = {
        'input': args.input,
        'output': args.output,
        'documents': args.documents,
        'output_format': args.output_format,
        'agent': args.agent,
        'verbose': args.verbose,
        'no_progress': args.no_progress,
        'dry_run': args.dry_run,
    }

    # Apply preset if specified (overrides defaults)
    if args.preset:
        preset_config = get_preset_config(args.preset)
        config.update(preset_config)

    # Apply YAML config
    if yaml_config:
        # Model configuration
        if 'default_model' in yaml_config and not args.model:
            config['model'] = yaml_config['default_model']

        # Rate limiting from YAML
        if 'rate_limiting' in yaml_config:
            rate_config = yaml_config['rate_limiting']
            if 'delay_between_requests' not in config:
                config['delay_between_requests'] = rate_config.get('delay_between_requests', 30)
            if 'max_retries' not in config:
                config['max_retries'] = rate_config.get('max_retries', 3)
            if 'retry_base_delay' not in config:
                config['retry_base_delay'] = rate_config.get('retry_base_delay', 60)

    # Apply environment variables (override YAML)
    config['provider'] = args.provider or env.get_provider()
    config['model'] = args.model or env.get_model() or config.get('model', 'azure.gpt-4.1')

    # Rate limiting from environment
    if args.delay is not None:
        config['delay_between_requests'] = args.delay
    elif env.get_delay() is not None:
        config['delay_between_requests'] = env.get_delay()
    elif 'delay_between_requests' not in config:
        config['delay_between_requests'] = 30

    if args.max_retries is not None:
        config['max_retries'] = args.max_retries
    elif env.get_max_retries() is not None:
        config['max_retries'] = env.get_max_retries()
    elif 'max_retries' not in config:
        config['max_retries'] = 3

    if args.retry_delay is not None:
        config['retry_base_delay'] = args.retry_delay
    elif env.get_retry_delay() is not None:
        config['retry_base_delay'] = env.get_retry_delay()
    elif 'retry_base_delay' not in config:
        config['retry_base_delay'] = 60

    # Processing options from args (highest priority)
    if args.segmentation != 'auto':
        config['segmentation'] = args.segmentation
    elif 'segmentation' not in config:
        config['segmentation'] = 'auto'

    config['enable_qa'] = args.enable_qa
    config['qa_questions'] = args.qa_questions

    # Store YAML config for provider credentials
    config['yaml_config'] = yaml_config

    return config


def apply_config_to_manager(config: Dict[str, Any], config_manager) -> None:
    """
    Apply CLI configuration to ConfigManager instance.

    Args:
        config: Merged configuration dictionary
        config_manager: ConfigManager instance to update
    """
    # Update rate limiting
    rate_limiting_config = {
        'delay_between_requests': config.get('delay_between_requests', 30),
        'max_retries': config.get('max_retries', 3),
        'retry_base_delay': config.get('retry_base_delay', 60),
        'max_tokens_per_request': config.get('max_tokens_per_request', 50000),
        'requests_per_minute': config.get('requests_per_minute', 3),
    }

    config_manager.update_rate_limiting_config(rate_limiting_config)

    # Update default model if specified
    if config.get('model'):
        config_manager.set_default_model(config['model'])
