"""Tests for configuration management module."""

import pytest
from unittest.mock import patch, Mock
from src.config import (
    HardwareConfig, ProcessingConfig, OutputConfig, 
    ConfigValidator, get_memory_requirements
)


class TestHardwareConfig:
    """Test hardware configuration functionality."""
    
    def test_hardware_config_creation(self):
        """Test creating hardware configuration."""
        config = HardwareConfig(
            device="cuda",
            batch_size=16,
            compute_type="float16",
            memory_threshold_gb=8.0
        )
        
        assert config.device == "cuda"
        assert config.batch_size == 16
        assert config.compute_type == "float16"
        assert config.memory_threshold_gb == 8.0
    
    @patch('src.config.torch')
    def test_auto_detect_cuda_available_high_memory(self, mock_torch):
        """Test auto-detection with high GPU memory."""
        mock_torch.cuda.is_available.return_value = True
        mock_props = Mock()
        mock_props.total_memory = 16 * 1024**3  # 16GB
        mock_torch.cuda.get_device_properties.return_value = mock_props
        
        config = HardwareConfig.auto_detect()
        
        assert config.device == "cuda"
        assert config.batch_size == 32
        assert config.compute_type == "float16"
        assert config.memory_threshold_gb == 16 * 0.8
    
    @patch('src.config.torch')
    def test_auto_detect_cuda_available_medium_memory(self, mock_torch):
        """Test auto-detection with medium GPU memory."""
        mock_torch.cuda.is_available.return_value = True
        mock_props = Mock()
        mock_props.total_memory = 8 * 1024**3  # 8GB
        mock_torch.cuda.get_device_properties.return_value = mock_props
        
        config = HardwareConfig.auto_detect()
        
        assert config.device == "cuda"
        assert config.batch_size == 16
        assert config.compute_type == "float16"
        assert config.memory_threshold_gb == 8 * 0.8
    
    @patch('src.config.torch')
    def test_auto_detect_cuda_available_low_memory(self, mock_torch):
        """Test auto-detection with low GPU memory."""
        mock_torch.cuda.is_available.return_value = True
        mock_props = Mock()
        mock_props.total_memory = 4 * 1024**3  # 4GB
        mock_torch.cuda.get_device_properties.return_value = mock_props
        
        config = HardwareConfig.auto_detect()
        
        assert config.device == "cuda"
        assert config.batch_size == 8
        assert config.compute_type == "int8"
        assert config.memory_threshold_gb == 4 * 0.8
    
    @patch('src.config.torch')
    def test_auto_detect_no_cuda(self, mock_torch):
        """Test auto-detection without CUDA."""
        mock_torch.cuda.is_available.return_value = False
        
        config = HardwareConfig.auto_detect()
        
        assert config.device == "cpu"
        assert config.batch_size == 4
        assert config.compute_type == "int8"
        assert config.memory_threshold_gb == 8.0


class TestProcessingConfig:
    """Test processing configuration functionality."""
    
    def test_processing_config_creation(self):
        """Test creating processing configuration."""
        config = ProcessingConfig(
            model_name="large-v2",
            language="en",
            enable_diarization=True,
            min_speakers=2,
            max_speakers=4,
            segment_length_hours=2.0
        )
        
        assert config.model_name == "large-v2"
        assert config.language == "en"
        assert config.enable_diarization is True
        assert config.min_speakers == 2
        assert config.max_speakers == 4
        assert config.segment_length_hours == 2.0
    
    def test_get_preset_fast(self):
        """Test fast preset configuration."""
        config = ProcessingConfig.get_preset("fast")
        
        assert config.model_name == "base"
        assert config.language == "en"
        assert config.enable_diarization is False
        assert config.segment_length_hours == 4.0
    
    def test_get_preset_balanced(self):
        """Test balanced preset configuration."""
        config = ProcessingConfig.get_preset("balanced")
        
        assert config.model_name == "small"
        assert config.language is None
        assert config.enable_diarization is True
        assert config.min_speakers == 2
        assert config.max_speakers == 4
    
    def test_get_preset_accurate(self):
        """Test accurate preset configuration."""
        config = ProcessingConfig.get_preset("accurate")
        
        assert config.model_name == "large-v2"
        assert config.enable_diarization is True
        assert config.max_speakers == 6
    
    def test_get_preset_long_audio(self):
        """Test long audio preset configuration."""
        config = ProcessingConfig.get_preset("long_audio")
        
        assert config.model_name == "base"
        assert config.enable_diarization is False
        assert config.segment_length_hours == 1.0
    
    def test_get_preset_unknown(self):
        """Test unknown preset returns balanced."""
        config = ProcessingConfig.get_preset("unknown_preset")
        
        # Should return balanced as default
        assert config.model_name == "small"


class TestOutputConfig:
    """Test output configuration functionality."""
    
    def test_output_config_creation(self):
        """Test creating output configuration."""
        config = OutputConfig(
            formats=["JSON", "SRT", "VTT"],
            include_word_timestamps=True,
            include_confidence_scores=True,
            speaker_labels=True
        )
        
        assert "JSON" in config.formats
        assert "SRT" in config.formats
        assert "VTT" in config.formats
        assert config.include_word_timestamps is True
        assert config.include_confidence_scores is True
        assert config.speaker_labels is True
    
    def test_default_output_config(self):
        """Test default output configuration."""
        config = OutputConfig.default()
        
        assert "JSON" in config.formats
        assert "SRT" in config.formats
        assert config.include_word_timestamps is True
        assert config.include_confidence_scores is True
        assert config.speaker_labels is True


class TestConfigValidator:
    """Test configuration validation functionality."""
    
    @patch('src.config.torch')
    def test_validate_hardware_config_valid_cuda(self, mock_torch):
        """Test validating valid CUDA hardware config."""
        mock_torch.cuda.is_available.return_value = True
        
        config = HardwareConfig(
            device="cuda",
            batch_size=16,
            compute_type="float16",
            memory_threshold_gb=8.0
        )
        
        is_valid, message = ConfigValidator.validate_hardware_config(config)
        
        assert is_valid is True
        assert message == "Valid configuration"
    
    @patch('src.config.torch')
    def test_validate_hardware_config_cuda_not_available(self, mock_torch):
        """Test validating CUDA config when CUDA not available."""
        mock_torch.cuda.is_available.return_value = False
        
        config = HardwareConfig(
            device="cuda",
            batch_size=16,
            compute_type="float16",
            memory_threshold_gb=8.0
        )
        
        is_valid, message = ConfigValidator.validate_hardware_config(config)
        
        assert is_valid is False
        assert "CUDA requested but not available" in message
    
    def test_validate_hardware_config_invalid_device(self):
        """Test validating invalid device."""
        config = HardwareConfig(
            device="invalid_device",
            batch_size=16,
            compute_type="float16",
            memory_threshold_gb=8.0
        )
        
        is_valid, message = ConfigValidator.validate_hardware_config(config)
        
        assert is_valid is False
        assert "Unsupported device" in message
    
    def test_validate_hardware_config_invalid_batch_size(self):
        """Test validating invalid batch size."""
        config = HardwareConfig(
            device="cpu",
            batch_size=100,  # Too large
            compute_type="float16",
            memory_threshold_gb=8.0
        )
        
        is_valid, message = ConfigValidator.validate_hardware_config(config)
        
        assert is_valid is False
        assert "Batch size must be between 1 and 64" in message
    
    def test_validate_processing_config_valid(self):
        """Test validating valid processing config."""
        config = ProcessingConfig(
            model_name="large-v2",
            language="en",
            enable_diarization=True,
            min_speakers=2,
            max_speakers=4,
            segment_length_hours=2.0
        )
        
        is_valid, message = ConfigValidator.validate_processing_config(config)
        
        assert is_valid is True
        assert message == "Valid configuration"
    
    def test_validate_processing_config_invalid_model(self):
        """Test validating invalid model name."""
        config = ProcessingConfig(
            model_name="invalid_model",
            language="en",
            enable_diarization=False,
            min_speakers=1,
            max_speakers=1,
            segment_length_hours=2.0
        )
        
        is_valid, message = ConfigValidator.validate_processing_config(config)
        
        assert is_valid is False
        assert "Unsupported model" in message
    
    def test_validate_processing_config_invalid_speakers(self):
        """Test validating invalid speaker configuration."""
        config = ProcessingConfig(
            model_name="base",
            language="en",
            enable_diarization=True,
            min_speakers=5,  # Greater than max
            max_speakers=4,
            segment_length_hours=2.0
        )
        
        is_valid, message = ConfigValidator.validate_processing_config(config)
        
        assert is_valid is False
        assert "Min speakers cannot exceed max speakers" in message
    
    def test_validate_output_config_valid(self):
        """Test validating valid output config."""
        config = OutputConfig(
            formats=["JSON", "SRT"],
            include_word_timestamps=True,
            include_confidence_scores=True,
            speaker_labels=True
        )
        
        is_valid, message = ConfigValidator.validate_output_config(config)
        
        assert is_valid is True
        assert message == "Valid configuration"
    
    def test_validate_output_config_no_formats(self):
        """Test validating output config with no formats."""
        config = OutputConfig(
            formats=[],
            include_word_timestamps=True,
            include_confidence_scores=True,
            speaker_labels=True
        )
        
        is_valid, message = ConfigValidator.validate_output_config(config)
        
        assert is_valid is False
        assert "At least one output format must be selected" in message
    
    def test_validate_output_config_invalid_format(self):
        """Test validating output config with invalid format."""
        config = OutputConfig(
            formats=["JSON", "INVALID_FORMAT"],
            include_word_timestamps=True,
            include_confidence_scores=True,
            speaker_labels=True
        )
        
        is_valid, message = ConfigValidator.validate_output_config(config)
        
        assert is_valid is False
        assert "Unsupported output format" in message


class TestMemoryRequirements:
    """Test memory requirements estimation."""
    
    def test_get_memory_requirements_base_model(self):
        """Test memory requirements for base model."""
        requirements = get_memory_requirements("base", 16, "float16")
        
        assert "gpu_memory_gb" in requirements
        assert "ram_gb" in requirements
        assert "disk_cache_gb" in requirements
        assert requirements["gpu_memory_gb"] > 0
        assert requirements["ram_gb"] > requirements["gpu_memory_gb"]
    
    def test_get_memory_requirements_large_model(self):
        """Test memory requirements for large model."""
        requirements = get_memory_requirements("large-v2", 16, "float16")
        
        # Large model should require more memory than base
        base_requirements = get_memory_requirements("base", 16, "float16")
        
        assert requirements["gpu_memory_gb"] > base_requirements["gpu_memory_gb"]
        assert requirements["ram_gb"] > base_requirements["ram_gb"]
    
    def test_get_memory_requirements_different_compute_types(self):
        """Test memory requirements with different compute types."""
        float16_req = get_memory_requirements("small", 16, "float16")
        int8_req = get_memory_requirements("small", 16, "int8")
        
        # int8 should require less memory than float16
        assert int8_req["gpu_memory_gb"] < float16_req["gpu_memory_gb"]
    
    def test_get_memory_requirements_different_batch_sizes(self):
        """Test memory requirements with different batch sizes."""
        small_batch = get_memory_requirements("small", 8, "float16")
        large_batch = get_memory_requirements("small", 32, "float16")
        
        # Larger batch should require more memory
        assert large_batch["gpu_memory_gb"] > small_batch["gpu_memory_gb"]
    
    def test_get_memory_requirements_unknown_model(self):
        """Test memory requirements for unknown model."""
        requirements = get_memory_requirements("unknown_model", 16, "float16")
        
        # Should fall back to default (medium model equivalent)
        assert requirements["gpu_memory_gb"] > 0
        assert requirements["ram_gb"] > 0


if __name__ == "__main__":
    pytest.main([__file__])