"""Unit tests for configuration management module."""

from __future__ import annotations

from dataclasses import replace
from typing import Dict

import pytest

import config
from config import (
    HardwareConfig,
    ProcessingConfig,
    OutputConfig,
    ConfigValidator,
    get_memory_requirements,
)


class TestHardwareConfigDetection:
    """Tests around hardware auto detection and configuration helpers."""

    def test_auto_detect_prefers_first_supported_backend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Auto detection should return configuration from the first successful detector."""

        # Simulate NVIDIA hardware being reported by the generic detector.
        hardware_report = {
            "type": "nvidia_cuda",
            "name": "NVIDIA RTX 4090",
            "memory_gb": 24.0,
        }
        monkeypatch.setattr(config, "detect_hardware", lambda: hardware_report)

        detected = HardwareConfig.auto_detect()

        assert detected.device == "cuda"
        assert detected.hardware_type == "NVIDIA RTX 40xx"
        assert detected.hardware_name == "NVIDIA RTX 4090"
        assert detected.batch_size == 64  # highest preset for large memory GPUs
        assert detected.expected_speedup == 15.0

    def test_auto_detect_falls_back_to_cpu_on_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If all detection attempts fail we should receive a safe CPU configuration."""

        # Every detector will raise causing the chain to progress to the CPU fallback.

        def raise_detect() -> Dict[str, str]:  # type: ignore[return-type]
            raise RuntimeError("hardware detection failed")

        monkeypatch.setattr(config, "detect_hardware", raise_detect)

        detected = HardwareConfig.auto_detect()

        assert detected.device == "cpu"
        assert detected.hardware_type == "CPU"
        assert detected.hardware_name == "CPU (Fallback)"
        assert detected.batch_size == 4

    @pytest.mark.parametrize(
        "gpu_name,memory_gb,expected",
        [
            ("NVIDIA RTX 3090", 24.0, {"batch_size": 32, "speedup": 10.0, "type": "NVIDIA RTX 30xx"}),
            ("NVIDIA RTX 2080", 8.0, {"batch_size": 16, "speedup": 6.0, "type": "NVIDIA RTX 20xx"}),
            ("NVIDIA GTX 1080 Ti", 11.0, {"batch_size": 8, "speedup": 4.0, "type": "NVIDIA GTX"}),
        ],
    )
    def test_configure_nvidia_cuda_profiles(self, gpu_name: str, memory_gb: float, expected: Dict[str, object]) -> None:
        """Verify the NVIDIA helper picks correct presets for different GPU families."""

        hw_info = {"name": gpu_name, "memory_gb": memory_gb}

        cfg = HardwareConfig._configure_nvidia_cuda(hw_info)

        assert cfg.device == "cuda"
        assert cfg.hardware_type == expected["type"]
        assert cfg.batch_size == expected["batch_size"]
        assert cfg.expected_speedup == expected["speedup"]


class TestProcessingOutputConfig:
    """Tests for processing and output configuration helpers."""

    def test_processing_preset_balanced(self) -> None:
        cfg = ProcessingConfig.get_preset("balanced")

        assert cfg.model_name == "small"
        assert cfg.enable_diarization is True
        assert cfg.min_speakers == 2
        assert cfg.segment_length_hours == 2.0

    def test_processing_preset_default(self) -> None:
        cfg = ProcessingConfig.get_preset("does_not_exist")

        # Unknown presets should fall back to the balanced profile.
        assert cfg.model_name == "small"
        assert cfg.enable_diarization is True

    def test_output_config_default(self) -> None:
        cfg = OutputConfig.default()

        assert cfg.formats == ["JSON", "SRT"]
        assert cfg.include_word_timestamps is True
        assert cfg.include_confidence_scores is True
        assert cfg.speaker_labels is True


class TestConfigValidators:
    """Validation related tests."""

    def test_validate_hardware_config_respects_torch_capabilities(self, monkeypatch: pytest.MonkeyPatch) -> None:
        hw_cfg = HardwareConfig(
            device="cuda",
            batch_size=8,
            compute_type="float16",
            memory_threshold_gb=8.0,
            hardware_type="NVIDIA",
            hardware_name="Test GPU",
            expected_speedup=5.0,
        )

        monkeypatch.setattr(config.torch.cuda, "is_available", lambda: True)

        is_valid, message = ConfigValidator.validate_hardware_config(hw_cfg)

        assert is_valid is True
        assert message == "Valid configuration"

    def test_validate_hardware_config_rejects_unavailable_cuda(self, monkeypatch: pytest.MonkeyPatch) -> None:
        hw_cfg = HardwareConfig(
            device="cuda",
            batch_size=8,
            compute_type="float16",
            memory_threshold_gb=8.0,
            hardware_type="NVIDIA",
            hardware_name="Test GPU",
            expected_speedup=5.0,
        )

        monkeypatch.setattr(config.torch.cuda, "is_available", lambda: False)

        is_valid, message = ConfigValidator.validate_hardware_config(hw_cfg)

        assert is_valid is False
        assert "CUDA requested but not available" in message

    def test_validate_processing_config_errors(self) -> None:
        invalid_cfg = replace(ProcessingConfig.get_preset("fast"), model_name="unknown_model")

        is_valid, message = ConfigValidator.validate_processing_config(invalid_cfg)

        assert is_valid is False
        assert "Unsupported model" in message

    def test_validate_output_config_requires_known_formats(self) -> None:
        invalid = OutputConfig(formats=["JSON", "DOCX"], include_word_timestamps=True,
                               include_confidence_scores=True, speaker_labels=True)

        is_valid, message = ConfigValidator.validate_output_config(invalid)

        assert is_valid is False
        assert "Unsupported output format" in message

    def test_get_memory_requirements_scales_with_batch_and_precision(self) -> None:
        base = get_memory_requirements("base", batch_size=1, compute_type="float32")
        larger = get_memory_requirements("base", batch_size=4, compute_type="int8")

        assert larger["gpu_memory_gb"] > base["gpu_memory_gb"] * 0.5  # scaled by batch size
        assert larger["ram_gb"] == pytest.approx(larger["gpu_memory_gb"] * 1.5, rel=1e-6)
