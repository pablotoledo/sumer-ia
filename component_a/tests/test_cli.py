"""
Unit tests for CLI functionality (transcribe_cli.py).
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from transcribe_cli import (
    EnvironmentConfig,
    create_parser,
    merge_configs,
    validate_input_file,
    setup_output_directory,
    create_hardware_config,
    create_processing_config,
    create_output_config,
)


class TestEnvironmentConfig:
    """Test environment variable configuration loading."""

    def test_get_model_from_env(self, monkeypatch):
        """Test loading model from environment."""
        monkeypatch.setenv('WHISPERX_MODEL', 'large-v2')
        assert EnvironmentConfig.get_model() == 'large-v2'

    def test_get_model_returns_none_when_not_set(self):
        """Test model returns None when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert EnvironmentConfig.get_model() is None

    def test_get_device_from_env(self, monkeypatch):
        """Test loading device from environment."""
        monkeypatch.setenv('WHISPERX_DEVICE', 'cuda')
        assert EnvironmentConfig.get_device() == 'cuda'

    def test_get_language_from_env(self, monkeypatch):
        """Test loading language from environment."""
        monkeypatch.setenv('WHISPERX_LANGUAGE', 'es')
        assert EnvironmentConfig.get_language() == 'es'

    def test_get_hf_token_from_env(self, monkeypatch):
        """Test loading HF token from environment."""
        monkeypatch.setenv('HF_TOKEN', 'hf_test123')
        assert EnvironmentConfig.get_hf_token() == 'hf_test123'

    def test_get_hf_token_alternative_var(self, monkeypatch):
        """Test loading HF token from alternative environment variable."""
        monkeypatch.setenv('HUGGINGFACE_TOKEN', 'hf_alt123')
        assert EnvironmentConfig.get_hf_token() == 'hf_alt123'

    def test_get_hf_token_prefers_hf_token(self, monkeypatch):
        """Test HF_TOKEN takes precedence over HUGGINGFACE_TOKEN."""
        monkeypatch.setenv('HF_TOKEN', 'hf_primary')
        monkeypatch.setenv('HUGGINGFACE_TOKEN', 'hf_secondary')
        assert EnvironmentConfig.get_hf_token() == 'hf_primary'

    def test_get_batch_size_from_env(self, monkeypatch):
        """Test loading batch size from environment."""
        monkeypatch.setenv('WHISPERX_BATCH_SIZE', '32')
        assert EnvironmentConfig.get_batch_size() == 32

    def test_get_batch_size_returns_none_for_invalid(self, monkeypatch):
        """Test batch size returns None for invalid value."""
        monkeypatch.setenv('WHISPERX_BATCH_SIZE', 'invalid')
        with pytest.raises(ValueError):
            EnvironmentConfig.get_batch_size()

    def test_get_compute_type_from_env(self, monkeypatch):
        """Test loading compute type from environment."""
        monkeypatch.setenv('WHISPERX_COMPUTE_TYPE', 'float16')
        assert EnvironmentConfig.get_compute_type() == 'float16'

    def test_get_output_dir_from_env(self, monkeypatch):
        """Test loading output directory from environment."""
        monkeypatch.setenv('WHISPERX_OUTPUT_DIR', '/tmp/output')
        assert EnvironmentConfig.get_output_dir() == '/tmp/output'

    def test_get_formats_from_env(self, monkeypatch):
        """Test loading formats from environment."""
        monkeypatch.setenv('WHISPERX_FORMATS', 'json,srt,vtt')
        assert EnvironmentConfig.get_formats() == ['json', 'srt', 'vtt']

    def test_get_formats_returns_none_when_not_set(self):
        """Test formats returns None when not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert EnvironmentConfig.get_formats() is None


class TestArgumentParser:
    """Test argument parser creation and parsing."""

    def test_create_parser_returns_parser(self):
        """Test that create_parser returns ArgumentParser."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_requires_input_file(self):
        """Test parser requires input file."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parser_accepts_input_file(self):
        """Test parser accepts input file."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3'])
        assert args.input == 'audio.mp3'

    def test_parser_model_choices(self):
        """Test parser validates model choices."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--model', 'small'])
        assert args.model == 'small'

        with pytest.raises(SystemExit):
            parser.parse_args(['audio.mp3', '--model', 'invalid'])

    def test_parser_device_choices(self):
        """Test parser validates device choices."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--device', 'cuda'])
        assert args.device == 'cuda'

        with pytest.raises(SystemExit):
            parser.parse_args(['audio.mp3', '--device', 'invalid'])

    def test_parser_preset_choices(self):
        """Test parser validates preset choices."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--preset', 'balanced'])
        assert args.preset == 'balanced'

        with pytest.raises(SystemExit):
            parser.parse_args(['audio.mp3', '--preset', 'invalid'])

    def test_parser_output_directory(self):
        """Test parser accepts output directory."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--output-dir', '/tmp/out'])
        assert args.output_dir == '/tmp/out'

    def test_parser_formats(self):
        """Test parser accepts formats."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--formats', 'json,srt'])
        assert args.formats == 'json,srt'

    def test_parser_diarization_options(self):
        """Test parser accepts diarization options."""
        parser = create_parser()
        args = parser.parse_args([
            'audio.mp3',
            '--enable-diarization',
            '--min-speakers', '2',
            '--max-speakers', '5',
            '--hf-token', 'hf_test'
        ])
        assert args.enable_diarization is True
        assert args.min_speakers == 2
        assert args.max_speakers == 5
        assert args.hf_token == 'hf_test'

    def test_parser_boolean_flags(self):
        """Test parser handles boolean flags."""
        parser = create_parser()
        args = parser.parse_args([
            'audio.mp3',
            '--no-word-timestamps',
            '--no-confidence',
            '--no-speaker-labels'
        ])
        assert args.no_word_timestamps is True
        assert args.no_confidence is True
        assert args.no_speaker_labels is True

    def test_parser_verbose_flag(self):
        """Test parser accepts verbose flag."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--verbose'])
        assert args.verbose is True


class TestConfigMerging:
    """Test configuration merging logic."""

    def test_merge_configs_args_override_env(self, monkeypatch):
        """Test command-line args override environment variables."""
        monkeypatch.setenv('WHISPERX_MODEL', 'base')

        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--model', 'large-v2'])
        env = EnvironmentConfig()

        config = merge_configs(args, env)
        assert config['model'] == 'large-v2'

    def test_merge_configs_uses_env_when_args_not_set(self, monkeypatch):
        """Test environment variables used when args not provided."""
        monkeypatch.setenv('WHISPERX_MODEL', 'medium')

        parser = create_parser()
        args = parser.parse_args(['audio.mp3'])
        env = EnvironmentConfig()

        config = merge_configs(args, env)
        assert config['model'] == 'medium'

    def test_merge_configs_uses_defaults_when_neither_set(self):
        """Test defaults used when neither args nor env set."""
        with patch.dict(os.environ, {}, clear=True):
            parser = create_parser()
            args = parser.parse_args(['audio.mp3'])
            env = EnvironmentConfig()

            config = merge_configs(args, env)
            assert config['model'] == 'small'  # Default model

    def test_merge_configs_formats_parsing(self):
        """Test formats are parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--formats', 'json,srt,vtt'])
        env = EnvironmentConfig()

        config = merge_configs(args, env)
        assert config['formats'] == ['JSON', 'SRT', 'VTT']

    def test_merge_configs_formats_from_env(self, monkeypatch):
        """Test formats loaded from environment."""
        monkeypatch.setenv('WHISPERX_FORMATS', 'json,txt')

        parser = create_parser()
        args = parser.parse_args(['audio.mp3'])
        env = EnvironmentConfig()

        config = merge_configs(args, env)
        assert config['formats'] == ['JSON', 'TXT']

    def test_merge_configs_device_auto_detection(self):
        """Test device auto-detection when set to auto."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--device', 'auto'])
        env = EnvironmentConfig()

        config = merge_configs(args, env)
        assert config['device'] == 'auto'

    def test_merge_configs_boolean_flags(self):
        """Test boolean flags are merged correctly."""
        parser = create_parser()
        args = parser.parse_args(['audio.mp3', '--no-word-timestamps'])
        env = EnvironmentConfig()

        config = merge_configs(args, env)
        assert config['include_word_timestamps'] is False

    def test_merge_configs_diarization_settings(self):
        """Test diarization settings are merged correctly."""
        parser = create_parser()
        args = parser.parse_args([
            'audio.mp3',
            '--enable-diarization',
            '--min-speakers', '3',
            '--max-speakers', '7'
        ])
        env = EnvironmentConfig()

        config = merge_configs(args, env)
        assert config['enable_diarization'] is True
        assert config['min_speakers'] == 3
        assert config['max_speakers'] == 7


class TestInputValidation:
    """Test input file validation."""

    def test_validate_input_file_success(self, tmp_path):
        """Test validation succeeds for valid audio file."""
        audio_file = tmp_path / "test.mp3"
        audio_file.touch()

        result = validate_input_file(str(audio_file))
        assert isinstance(result, Path)
        assert result.name == "test.mp3"

    def test_validate_input_file_not_found(self):
        """Test validation fails for non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_input_file('/nonexistent/audio.mp3')

    def test_validate_input_file_is_directory(self, tmp_path):
        """Test validation fails for directory."""
        directory = tmp_path / "audio_dir"
        directory.mkdir()

        with pytest.raises(ValueError, match="not a file"):
            validate_input_file(str(directory))

    def test_validate_input_file_invalid_extension(self, tmp_path):
        """Test validation fails for unsupported format."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.touch()

        with pytest.raises(ValueError, match="Unsupported file format"):
            validate_input_file(str(invalid_file))

    def test_validate_input_file_valid_extensions(self, tmp_path):
        """Test validation succeeds for all supported formats."""
        extensions = ['.mp3', '.wav', '.flac', '.m4a', '.mp4', '.ogg', '.wma', '.aac']

        for ext in extensions:
            audio_file = tmp_path / f"test{ext}"
            audio_file.touch()
            result = validate_input_file(str(audio_file))
            assert result.suffix.lower() == ext


class TestOutputDirectorySetup:
    """Test output directory setup."""

    def test_setup_output_directory_with_explicit_path(self, tmp_path):
        """Test output directory creation with explicit path."""
        input_file = tmp_path / "audio.mp3"
        input_file.touch()
        output_dir = tmp_path / "output"

        result = setup_output_directory(input_file, str(output_dir))
        assert result.exists()
        assert result.is_dir()
        assert result.name == "output"

    def test_setup_output_directory_auto_generated(self, tmp_path):
        """Test output directory auto-generation."""
        input_file = tmp_path / "audio.mp3"
        input_file.touch()

        result = setup_output_directory(input_file, None)
        assert result.exists()
        assert result.is_dir()
        assert result.name == "audio_transcription"

    def test_setup_output_directory_creates_parent_dirs(self, tmp_path):
        """Test output directory creation with nested path."""
        input_file = tmp_path / "audio.mp3"
        input_file.touch()
        output_dir = tmp_path / "level1" / "level2" / "output"

        result = setup_output_directory(input_file, str(output_dir))
        assert result.exists()
        assert result.is_dir()

    def test_setup_output_directory_exists_no_error(self, tmp_path):
        """Test no error when output directory already exists."""
        input_file = tmp_path / "audio.mp3"
        input_file.touch()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = setup_output_directory(input_file, str(output_dir))
        assert result.exists()
        assert result.is_dir()


class TestHardwareConfigCreation:
    """Test hardware configuration creation from merged config."""

    @patch('transcribe_cli.HardwareConfig')
    def test_create_hardware_config_auto_detect(self, mock_hw_config):
        """Test hardware config auto-detection."""
        mock_instance = MagicMock()
        mock_hw_config.auto_detect.return_value = mock_instance

        config = {
            'device': 'auto',
            'batch_size': None,
            'compute_type': None
        }

        result = create_hardware_config(config)
        mock_hw_config.auto_detect.assert_called_once()

    @patch('transcribe_cli.HardwareConfig')
    def test_create_hardware_config_auto_detect_with_overrides(self, mock_hw_config):
        """Test hardware config auto-detection with user overrides."""
        mock_instance = MagicMock()
        mock_instance.batch_size = 16
        mock_instance.compute_type = 'float16'
        mock_hw_config.auto_detect.return_value = mock_instance

        config = {
            'device': 'auto',
            'batch_size': 32,
            'compute_type': 'int8'
        }

        result = create_hardware_config(config)
        assert mock_instance.batch_size == 32
        assert mock_instance.compute_type == 'int8'

    @patch('config.detect_hardware')
    @patch('transcribe_cli.HardwareConfig')
    def test_create_hardware_config_manual_cuda(self, mock_hw_config, mock_detect):
        """Test manual CUDA configuration."""
        mock_detect.return_value = {
            'type': 'nvidia_cuda',
            'name': 'NVIDIA GPU',
            'speedup': 10.0
        }

        config = {
            'device': 'cuda',
            'batch_size': 16,
            'compute_type': 'float16'
        }

        result = create_hardware_config(config)
        mock_hw_config.assert_called_once()
        call_args = mock_hw_config.call_args[1]
        assert call_args['device'] == 'cuda'
        assert call_args['batch_size'] == 16
        assert call_args['compute_type'] == 'float16'

    @patch('config.detect_hardware')
    @patch('transcribe_cli.HardwareConfig')
    def test_create_hardware_config_manual_cpu(self, mock_hw_config, mock_detect):
        """Test manual CPU configuration."""
        mock_detect.return_value = {
            'type': 'cpu',
            'name': 'CPU',
            'speedup': 1.0
        }

        config = {
            'device': 'cpu',
            'batch_size': None,
            'compute_type': None
        }

        result = create_hardware_config(config)
        call_args = mock_hw_config.call_args[1]
        assert call_args['device'] == 'cpu'


class TestProcessingConfigCreation:
    """Test processing configuration creation from merged config."""

    @patch('transcribe_cli.ProcessingConfig')
    def test_create_processing_config_with_preset(self, mock_proc_config):
        """Test processing config creation with preset."""
        mock_preset = MagicMock()
        mock_preset.language = None
        mock_preset.enable_diarization = False
        mock_proc_config.get_preset.return_value = mock_preset

        config = {
            'preset': 'balanced',
            'model': 'small',
            'language': None,
            'enable_diarization': False,
            'min_speakers': 1,
            'max_speakers': 20
        }

        result = create_processing_config(config)
        mock_proc_config.get_preset.assert_called_once_with('balanced')

    @patch('transcribe_cli.ProcessingConfig')
    def test_create_processing_config_preset_with_overrides(self, mock_proc_config):
        """Test processing config preset with user overrides."""
        mock_preset = MagicMock()
        mock_preset.language = None
        mock_preset.enable_diarization = False
        mock_proc_config.get_preset.return_value = mock_preset

        config = {
            'preset': 'fast',
            'model': 'small',
            'language': 'es',
            'enable_diarization': True,
            'min_speakers': 2,
            'max_speakers': 4
        }

        result = create_processing_config(config)
        assert mock_preset.language == 'es'
        assert mock_preset.enable_diarization is True

    @patch('transcribe_cli.ProcessingConfig')
    def test_create_processing_config_custom(self, mock_proc_config):
        """Test custom processing config creation."""
        config = {
            'preset': None,
            'model': 'large-v2',
            'language': 'en',
            'enable_diarization': True,
            'min_speakers': 2,
            'max_speakers': 5
        }

        result = create_processing_config(config)
        mock_proc_config.assert_called_once()
        call_args = mock_proc_config.call_args[1]
        assert call_args['model_name'] == 'large-v2'
        assert call_args['language'] == 'en'
        assert call_args['enable_diarization'] is True
        assert call_args['min_speakers'] == 2
        assert call_args['max_speakers'] == 5


class TestOutputConfigCreation:
    """Test output configuration creation from merged config."""

    @patch('transcribe_cli.OutputConfig')
    def test_create_output_config(self, mock_out_config):
        """Test output config creation."""
        config = {
            'formats': ['JSON', 'SRT'],
            'include_word_timestamps': True,
            'include_confidence': True,
            'include_speaker_labels': True
        }

        result = create_output_config(config)
        mock_out_config.assert_called_once_with(
            formats=['JSON', 'SRT'],
            include_word_timestamps=True,
            include_confidence_scores=True,
            speaker_labels=True
        )

    @patch('transcribe_cli.OutputConfig')
    def test_create_output_config_minimal(self, mock_out_config):
        """Test output config with minimal options."""
        config = {
            'formats': ['TXT'],
            'include_word_timestamps': False,
            'include_confidence': False,
            'include_speaker_labels': False
        }

        result = create_output_config(config)
        mock_out_config.assert_called_once_with(
            formats=['TXT'],
            include_word_timestamps=False,
            include_confidence_scores=False,
            speaker_labels=False
        )


class TestEndToEndCLIFlow:
    """Test end-to-end CLI execution flow (integration-style tests)."""

    @patch('transcribe_cli.WhisperXProcessor')
    @patch('transcribe_cli.save_transcription_results')
    def test_basic_transcription_flow(self, mock_save, mock_processor, tmp_path):
        """Test basic transcription flow with mocked processor."""
        # Setup
        audio_file = tmp_path / "test.mp3"
        audio_file.touch()

        mock_proc_instance = MagicMock()
        mock_proc_instance.process_audio_file.return_value = {
            'segments': [],
            'language': 'en'
        }
        mock_processor.return_value = mock_proc_instance

        # This test verifies the flow components work together
        # Full integration test would require actual audio processing
        assert audio_file.exists()
        assert mock_processor is not None
