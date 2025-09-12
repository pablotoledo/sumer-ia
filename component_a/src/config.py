"""Configuration management for WhisperX Streamlit application."""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List, Any
import torch
import logging


@dataclass
class HardwareConfig:
    """Hardware-specific configuration settings."""
    device: str
    batch_size: int
    compute_type: str
    memory_threshold_gb: float
    hardware_type: str
    hardware_name: str
    expected_speedup: float
    
    @classmethod
    def auto_detect(cls) -> 'HardwareConfig':
        """Auto-detect optimal hardware configuration with smart fallback system."""
        return cls._detect_with_fallback()
    
    @classmethod
    def _detect_with_fallback(cls) -> 'HardwareConfig':
        """Cascading hardware detection with intelligent fallback."""
        detection_chain = [
            ("Apple MPS", cls._try_apple_mps),
            ("NVIDIA CUDA", cls._try_nvidia_cuda),
            ("AMD ROCm", cls._try_amd_rocm),
            ("Intel XPU", cls._try_intel_xpu),
            ("CPU Fallback", cls._try_cpu_fallback)
        ]
        
        last_error = None
        
        for hardware_type, detection_func in detection_chain:
            try:
                config = detection_func()
                if config is not None:
                    return config
            except Exception as e:
                last_error = e
                continue
        
        # If all detection methods fail, return safe CPU config
        return cls._configure_cpu_fallback()
    
    @classmethod
    def _try_apple_mps(cls) -> Optional['HardwareConfig']:
        """Try to detect and configure Apple MPS."""
        try:
            hardware_info = detect_hardware()
            if hardware_info["type"] == "apple_mps":
                return cls._configure_apple_mps(hardware_info)
        except Exception:
            pass
        return None
    
    @classmethod
    def _try_nvidia_cuda(cls) -> Optional['HardwareConfig']:
        """Try to detect and configure NVIDIA CUDA."""
        try:
            hardware_info = detect_hardware()
            if hardware_info["type"] == "nvidia_cuda":
                return cls._configure_nvidia_cuda(hardware_info)
        except Exception:
            pass
        return None
    
    @classmethod
    def _try_amd_rocm(cls) -> Optional['HardwareConfig']:
        """Try to detect and configure AMD ROCm."""
        try:
            hardware_info = detect_hardware()
            if hardware_info["type"] == "amd_rocm":
                return cls._configure_amd_rocm(hardware_info)
        except Exception:
            pass
        return None
    
    @classmethod
    def _try_intel_xpu(cls) -> Optional['HardwareConfig']:
        """Try to detect and configure Intel XPU."""
        try:
            hardware_info = detect_hardware()
            if hardware_info["type"] == "intel_xpu":
                return cls._configure_intel_xpu(hardware_info)
        except Exception:
            pass
        return None
    
    @classmethod 
    def _try_cpu_fallback(cls) -> 'HardwareConfig':
        """Always-working CPU fallback configuration."""
        return cls._configure_cpu_fallback()
    
    @classmethod
    def _configure_apple_mps(cls, hw_info: Dict) -> 'HardwareConfig':
        """Configure for Apple Silicon (M1/M2/M3/M4) with MPS."""
        # M4 Pro optimization
        if "M4" in hw_info["name"]:
            return cls(
                device="mps",
                batch_size=32,
                compute_type="float16",
                memory_threshold_gb=16.0,
                hardware_type="Apple Silicon",
                hardware_name=hw_info["name"],
                expected_speedup=8.5
            )
        elif "M3" in hw_info["name"]:
            return cls(
                device="mps",
                batch_size=24,
                compute_type="float16", 
                memory_threshold_gb=14.0,
                hardware_type="Apple Silicon",
                hardware_name=hw_info["name"],
                expected_speedup=7.0
            )
        elif "M2" in hw_info["name"]:
            return cls(
                device="mps",
                batch_size=16,
                compute_type="float16",
                memory_threshold_gb=12.0,
                hardware_type="Apple Silicon", 
                hardware_name=hw_info["name"],
                expected_speedup=5.5
            )
        else:  # M1 or unknown
            return cls(
                device="mps",
                batch_size=12,
                compute_type="float16",
                memory_threshold_gb=10.0,
                hardware_type="Apple Silicon",
                hardware_name=hw_info["name"],
                expected_speedup=4.0
            )
    
    @classmethod
    def _configure_nvidia_cuda(cls, hw_info: Dict) -> 'HardwareConfig':
        """Configure for NVIDIA CUDA GPUs."""
        gpu_memory_gb = hw_info["memory_gb"]
        gpu_name = hw_info["name"]
        
        # RTX 40xx series (Ada Lovelace)
        if any(model in gpu_name for model in ["RTX 4090", "RTX 4080", "RTX 4070"]):
            return cls(
                device="cuda",
                batch_size=64 if gpu_memory_gb >= 16 else 32,
                compute_type="float16",
                memory_threshold_gb=gpu_memory_gb * 0.85,
                hardware_type="NVIDIA RTX 40xx",
                hardware_name=gpu_name,
                expected_speedup=15.0 if gpu_memory_gb >= 16 else 12.0
            )
        # RTX 30xx series (Ampere)
        elif any(model in gpu_name for model in ["RTX 3090", "RTX 3080", "RTX 3070"]):
            return cls(
                device="cuda",
                batch_size=32 if gpu_memory_gb >= 12 else 16,
                compute_type="float16",
                memory_threshold_gb=gpu_memory_gb * 0.8,
                hardware_type="NVIDIA RTX 30xx",
                hardware_name=gpu_name,
                expected_speedup=10.0 if gpu_memory_gb >= 12 else 8.0
            )
        # RTX 20xx series (Turing)
        elif any(model in gpu_name for model in ["RTX 2080", "RTX 2070", "RTX 2060"]):
            return cls(
                device="cuda",
                batch_size=16,
                compute_type="float16",
                memory_threshold_gb=gpu_memory_gb * 0.75,
                hardware_type="NVIDIA RTX 20xx",
                hardware_name=gpu_name,
                expected_speedup=6.0
            )
        # GTX series (older)
        else:
            return cls(
                device="cuda",
                batch_size=8,
                compute_type="int8",
                memory_threshold_gb=gpu_memory_gb * 0.7,
                hardware_type="NVIDIA GTX",
                hardware_name=gpu_name,
                expected_speedup=4.0
            )
    
    @classmethod  
    def _configure_amd_rocm(cls, hw_info: Dict) -> 'HardwareConfig':
        """Configure for AMD GPUs with ROCm."""
        return cls(
            device="cuda",  # ROCm uses CUDA compatibility layer
            batch_size=16,
            compute_type="float16", 
            memory_threshold_gb=hw_info["memory_gb"] * 0.8,
            hardware_type="AMD Radeon",
            hardware_name=hw_info["name"],
            expected_speedup=6.0
        )
    
    @classmethod
    def _configure_intel_xpu(cls, hw_info: Dict) -> 'HardwareConfig':
        """Configure for Intel Arc GPUs."""
        return cls(
            device="xpu",
            batch_size=12,
            compute_type="float16",
            memory_threshold_gb=hw_info["memory_gb"] * 0.8,
            hardware_type="Intel Arc",
            hardware_name=hw_info["name"], 
            expected_speedup=3.5
        )
    
    @classmethod
    def _configure_cpu_fallback(cls) -> 'HardwareConfig':
        """Fallback to CPU configuration."""
        return cls(
            device="cpu",
            batch_size=4,
            compute_type="int8",
            memory_threshold_gb=8.0,
            hardware_type="CPU",
            hardware_name="CPU (Fallback)",
            expected_speedup=1.0
        )


@dataclass
class ProcessingConfig:
    """Processing pipeline configuration."""
    model_name: str
    language: Optional[str]
    enable_diarization: bool
    min_speakers: int
    max_speakers: int
    segment_length_hours: float
    
    @classmethod
    def get_preset(cls, preset_name: str) -> 'ProcessingConfig':
        """Get predefined configuration presets."""
        presets = {
            "fast": cls(
                model_name="base",
                language="en",
                enable_diarization=False,
                min_speakers=1,
                max_speakers=1,
                segment_length_hours=4.0
            ),
            "balanced": cls(
                model_name="small",
                language=None,
                enable_diarization=True,
                min_speakers=2,
                max_speakers=4,
                segment_length_hours=2.0
            ),
            "accurate": cls(
                model_name="large-v2",
                language=None,
                enable_diarization=True,
                min_speakers=2,
                max_speakers=6,
                segment_length_hours=1.5
            ),
            "long_audio": cls(
                model_name="base",
                language="en",
                enable_diarization=False,
                min_speakers=1,
                max_speakers=1,
                segment_length_hours=1.0
            )
        }
        return presets.get(preset_name, presets["balanced"])


@dataclass
class OutputConfig:
    """Output format configuration."""
    formats: List[str]
    include_word_timestamps: bool
    include_confidence_scores: bool
    speaker_labels: bool
    
    @classmethod
    def default(cls) -> 'OutputConfig':
        """Default output configuration."""
        return cls(
            formats=["JSON", "SRT"],
            include_word_timestamps=True,
            include_confidence_scores=True,
            speaker_labels=True
        )


class ConfigValidator:
    """Validates configuration settings."""
    
    SUPPORTED_MODELS = ["base", "small", "medium", "large-v2", "large-v3"]
    SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "ja", "zh", "auto"]
    SUPPORTED_FORMATS = ["JSON", "SRT", "VTT", "TXT"]
    SUPPORTED_DEVICES = ["cuda", "cpu", "mps", "xpu"]
    SUPPORTED_COMPUTE_TYPES = ["float16", "float32", "int8"]
    
    @classmethod
    def validate_hardware_config(cls, config: HardwareConfig) -> Tuple[bool, str]:
        """Validate hardware configuration."""
        if config.device not in cls.SUPPORTED_DEVICES:
            return False, f"Unsupported device: {config.device}"
        
        if config.device == "cuda" and not torch.cuda.is_available():
            return False, "CUDA requested but not available"
        
        if config.compute_type not in cls.SUPPORTED_COMPUTE_TYPES:
            return False, f"Unsupported compute type: {config.compute_type}"
        
        if config.batch_size < 1 or config.batch_size > 64:
            return False, "Batch size must be between 1 and 64"
        
        return True, "Valid configuration"
    
    @classmethod
    def validate_processing_config(cls, config: ProcessingConfig) -> Tuple[bool, str]:
        """Validate processing configuration."""
        if config.model_name not in cls.SUPPORTED_MODELS:
            return False, f"Unsupported model: {config.model_name}"
        
        if config.language and config.language not in cls.SUPPORTED_LANGUAGES:
            return False, f"Unsupported language: {config.language}"
        
        if config.min_speakers < 1 or config.max_speakers > 20:
            return False, "Speaker count must be between 1 and 20"
        
        if config.min_speakers > config.max_speakers:
            return False, "Min speakers cannot exceed max speakers"
        
        if config.segment_length_hours <= 0 or config.segment_length_hours > 8:
            return False, "Segment length must be between 0 and 8 hours"
        
        return True, "Valid configuration"
    
    @classmethod
    def validate_output_config(cls, config: OutputConfig) -> Tuple[bool, str]:
        """Validate output configuration."""
        if not config.formats:
            return False, "At least one output format must be selected"
        
        for fmt in config.formats:
            if fmt not in cls.SUPPORTED_FORMATS:
                return False, f"Unsupported output format: {fmt}"
        
        return True, "Valid configuration"


def detect_hardware() -> Dict[str, Any]:
    """Detect available hardware with comprehensive fallback support."""
    import platform
    import subprocess
    
    # Hardware detection priority order with safety checks
    hardware_detectors = [
        _detect_apple_mps,
        _detect_nvidia_cuda, 
        _detect_amd_rocm,
        _detect_intel_xpu
    ]
    
    # Try each detector in order
    for detector in hardware_detectors:
        try:
            result = detector()
            if result is not None:
                return result
        except Exception:
            continue
    
    # Final CPU fallback
    return _detect_cpu_fallback()


def _detect_apple_mps() -> Optional[Dict[str, Any]]:
    """Detect Apple Silicon with MPS backend."""
    try:
        # Check if MPS is available and functional
        if not (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
            return None
            
        # Test MPS functionality
        test_tensor = torch.tensor([1.0], device='mps')
        _ = test_tensor + 1  # Simple operation test
        
        # Get chip information
        import subprocess
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True, timeout=3)
            chip_name = result.stdout.strip()
            
            # Determine memory based on chip type
            if 'M4' in chip_name:
                memory_gb = 18.0
            elif 'M3' in chip_name:
                memory_gb = 16.0
            elif 'M2' in chip_name:
                memory_gb = 12.0
            else:
                memory_gb = 10.0
                
            return {
                "type": "apple_mps",
                "name": chip_name,
                "memory_gb": memory_gb,
                "compute_units": "Neural Engine + GPU"
            }
        except:
            # Fallback for unknown Apple Silicon
            return {
                "type": "apple_mps",
                "name": "Apple Silicon (Unknown)",
                "memory_gb": 8.0,
                "compute_units": "Unknown"
            }
    except Exception:
        return None


def _detect_nvidia_cuda() -> Optional[Dict[str, Any]]:
    """Detect NVIDIA CUDA GPUs with functionality test."""
    try:
        if not torch.cuda.is_available():
            return None
            
        # Test CUDA functionality
        test_tensor = torch.tensor([1.0], device='cuda')
        _ = test_tensor + 1
        
        device_props = torch.cuda.get_device_properties(0)
        gpu_name = device_props.name
        gpu_memory_gb = device_props.total_memory / (1024**3)
        
        return {
            "type": "nvidia_cuda",
            "name": gpu_name,
            "memory_gb": gpu_memory_gb,
            "compute_capability": f"{device_props.major}.{device_props.minor}",
            "multiprocessors": device_props.multi_processor_count
        }
    except Exception:
        return None


def _detect_amd_rocm() -> Optional[Dict[str, Any]]:
    """Detect AMD ROCm support."""
    try:
        import subprocess
        result = subprocess.run(['rocm-smi', '--showproduct'], 
                              capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and 'AMD' in result.stdout:
            return {
                "type": "amd_rocm",
                "name": "AMD Radeon (ROCm)",
                "memory_gb": 8.0,
                "driver": "ROCm"
            }
    except Exception:
        pass
    return None


def _detect_intel_xpu() -> Optional[Dict[str, Any]]:
    """Detect Intel XPU (Arc GPU) support."""
    try:
        import intel_extension_for_pytorch  # type: ignore
        if hasattr(torch, 'xpu') and torch.xpu.is_available():
            # Test XPU functionality 
            test_tensor = torch.tensor([1.0], device='xpu')
            _ = test_tensor + 1
            
            return {
                "type": "intel_xpu",
                "name": "Intel Arc GPU",
                "memory_gb": 8.0,
                "driver": "Intel XPU"
            }
    except Exception:
        pass
    return None


def _detect_cpu_fallback() -> Dict[str, Any]:
    """CPU fallback detection - always works."""
    import platform
    
    try:
        cpu_info = platform.processor()
        if not cpu_info:
            cpu_info = platform.machine()
    except:
        cpu_info = "Unknown CPU"
        
    return {
        "type": "cpu",
        "name": f"{cpu_info} CPU",
        "cores": torch.get_num_threads(),
        "memory_gb": 8.0
    }


def get_available_hardware_options() -> List[Dict[str, Any]]:
    """Get all available hardware acceleration options."""
    options = []
    
    # Always include CPU
    options.append({
        "id": "cpu",
        "name": "CPU Only",
        "description": "Universal compatibility, slower performance",
        "available": True,
        "speedup": 1.0
    })
    
    # Check Apple MPS
    try:
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            hw_info = detect_hardware()
            if hw_info["type"] == "apple_mps":
                options.append({
                    "id": "mps",
                    "name": f"Apple Silicon ({hw_info['name']})",
                    "description": "Optimized for M-series chips with Neural Engine",
                    "available": True,
                    "speedup": 8.5 if "M4" in hw_info["name"] else 7.0
                })
    except:
        pass
    
    # Check NVIDIA CUDA
    try:
        if torch.cuda.is_available():
            device_props = torch.cuda.get_device_properties(0)
            gpu_name = device_props.name
            speedup = 15.0 if "RTX 40" in gpu_name else 10.0 if "RTX 30" in gpu_name else 6.0
            
            options.append({
                "id": "cuda",
                "name": f"NVIDIA CUDA ({gpu_name})",
                "description": "High-performance GPU acceleration",
                "available": True,
                "speedup": speedup
            })
    except:
        pass
    
    # Check AMD ROCm
    try:
        import subprocess
        result = subprocess.run(['rocm-smi', '--showproduct'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            options.append({
                "id": "rocm",
                "name": "AMD Radeon (ROCm)",
                "description": "AMD GPU acceleration (experimental)",
                "available": True,
                "speedup": 6.0
            })
    except:
        pass
    
    # Check Intel XPU
    try:
        import intel_extension_for_pytorch  # type: ignore
        if hasattr(torch, 'xpu') and torch.xpu.is_available():
            options.append({
                "id": "xpu", 
                "name": "Intel Arc GPU",
                "description": "Intel Arc GPU acceleration (experimental)",
                "available": True,
                "speedup": 3.5
            })
    except:
        pass
    
    return options


def get_memory_requirements(model_name: str, batch_size: int, compute_type: str) -> Dict[str, float]:
    """Estimate memory requirements for given configuration."""
    
    # Base memory requirements in GB (approximate)
    base_requirements = {
        "base": 1.0,
        "small": 2.0,
        "medium": 5.0,
        "large-v2": 10.0,
        "large-v3": 12.0
    }
    
    # Compute type multipliers
    compute_multipliers = {
        "float32": 1.0,
        "float16": 0.6,
        "int8": 0.4
    }
    
    # Batch size scaling (approximate)
    batch_multiplier = 1.0 + (batch_size - 1) * 0.1
    
    base_memory = base_requirements.get(model_name, 5.0)
    compute_multiplier = compute_multipliers.get(compute_type, 1.0)
    
    estimated_gpu_memory = base_memory * compute_multiplier * batch_multiplier
    estimated_ram = estimated_gpu_memory * 1.5  # RAM is typically 1.5x GPU memory
    
    return {
        "gpu_memory_gb": estimated_gpu_memory,
        "ram_gb": estimated_ram,
        "disk_cache_gb": 2.0  # For model downloads and temporary files
    }


class PerformanceBenchmarker:
    """Benchmarks hardware performance and provides optimization recommendations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def quick_benchmark(self, hardware_config: HardwareConfig) -> Dict[str, float]:
        """Run a quick benchmark to estimate hardware performance."""
        import time
        
        benchmark_results = {
            "tensor_ops_per_sec": 0.0,
            "memory_bandwidth_gbps": 0.0,
            "model_load_time_sec": 0.0,
            "relative_performance": 1.0
        }
        
        try:
            device = hardware_config.device
            
            # Tensor operations benchmark
            start_time = time.time()
            test_tensor = torch.randn(1000, 1000, device=device, dtype=torch.float16)
            operations = 0
            
            for _ in range(10):
                result = torch.matmul(test_tensor, test_tensor.T)
                result = torch.relu(result)
                result = torch.sum(result)
                operations += 3
            
            if device != "cpu":
                if device == "cuda":
                    torch.cuda.synchronize()
                elif device == "mps":
                    torch.mps.synchronize()
            
            end_time = time.time()
            benchmark_results["tensor_ops_per_sec"] = operations / (end_time - start_time)
            
            # Memory bandwidth test
            start_time = time.time()
            large_tensor = torch.randn(5000, 5000, device=device)
            copied_tensor = large_tensor.clone()
            data_size_gb = large_tensor.element_size() * large_tensor.numel() / (1024**3)
            end_time = time.time()
            
            benchmark_results["memory_bandwidth_gbps"] = (data_size_gb * 2) / (end_time - start_time)
            
            # Relative performance calculation
            baseline_scores = {
                "cpu": 100,
                "mps": 800,     # Apple M4 Pro estimate
                "cuda": 1000,   # NVIDIA RTX estimate
                "xpu": 400      # Intel Arc estimate
            }
            
            device_key = device if device in baseline_scores else "cpu"
            benchmark_results["relative_performance"] = benchmark_results["tensor_ops_per_sec"] / baseline_scores[device_key]
            
            self.logger.info(f"Benchmark completed for {device}: {benchmark_results['tensor_ops_per_sec']:.1f} ops/sec")
            
        except Exception as e:
            self.logger.warning(f"Benchmark failed: {e}")
            
        return benchmark_results
    
    def get_optimization_preset(self, hardware_config: HardwareConfig, 
                              benchmark_results: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Get optimized preset based on hardware and benchmarks."""
        
        if benchmark_results is None:
            benchmark_results = self.quick_benchmark(hardware_config)
        
        # Base presets by hardware type
        presets = {
            "apple_mps_m4_pro": {
                "name": "Apple M4 Pro Optimized",
                "description": "Tuned for M4 Pro with 18GB unified memory",
                "batch_size": 32,
                "compute_type": "float16", 
                "memory_threshold_gb": 16.0,
                "segment_length_hours": 2.0,
                "enable_aggressive_caching": True,
                "expected_speedup": 8.5,
                "model_recommendations": {
                    "fast_processing": "base",
                    "balanced": "small", 
                    "high_accuracy": "medium"
                }
            },
            "apple_mps_general": {
                "name": "Apple Silicon Optimized",
                "description": "General optimization for Apple M-series chips",
                "batch_size": 24,
                "compute_type": "float16",
                "memory_threshold_gb": 12.0,
                "segment_length_hours": 2.5,
                "enable_aggressive_caching": True,
                "expected_speedup": 6.0,
                "model_recommendations": {
                    "fast_processing": "base",
                    "balanced": "small",
                    "high_accuracy": "small"
                }
            },
            "nvidia_rtx_40xx": {
                "name": "NVIDIA RTX 40xx Optimized",
                "description": "Optimized for RTX 4090/4080/4070 series",
                "batch_size": 64,
                "compute_type": "float16",
                "memory_threshold_gb": 20.0,
                "segment_length_hours": 3.0,
                "enable_tensor_cores": True,
                "expected_speedup": 15.0,
                "model_recommendations": {
                    "fast_processing": "small",
                    "balanced": "medium",
                    "high_accuracy": "large-v2"
                }
            },
            "nvidia_rtx_30xx": {
                "name": "NVIDIA RTX 30xx Optimized", 
                "description": "Optimized for RTX 3090/3080/3070 series",
                "batch_size": 32,
                "compute_type": "float16",
                "memory_threshold_gb": 16.0,
                "segment_length_hours": 2.5,
                "enable_tensor_cores": True,
                "expected_speedup": 10.0,
                "model_recommendations": {
                    "fast_processing": "base",
                    "balanced": "small",
                    "high_accuracy": "medium"
                }
            },
            "cpu_optimized": {
                "name": "CPU Optimized",
                "description": "Maximum efficiency for CPU-only processing",
                "batch_size": 4,
                "compute_type": "int8",
                "memory_threshold_gb": 8.0,
                "segment_length_hours": 1.0,
                "enable_quantization": True,
                "expected_speedup": 1.0,
                "model_recommendations": {
                    "fast_processing": "base",
                    "balanced": "base", 
                    "high_accuracy": "small"
                }
            }
        }
        
        # Select best preset based on hardware
        preset_key = self._select_optimal_preset(hardware_config, benchmark_results)
        optimal_preset = presets.get(preset_key, presets["cpu_optimized"])
        
        # Adjust based on actual benchmark performance
        if benchmark_results["relative_performance"] > 1.2:
            # Hardware is performing better than expected
            optimal_preset["batch_size"] = min(64, int(optimal_preset["batch_size"] * 1.2))
            optimal_preset["expected_speedup"] *= 1.1
        elif benchmark_results["relative_performance"] < 0.8:
            # Hardware is underperforming
            optimal_preset["batch_size"] = max(1, int(optimal_preset["batch_size"] * 0.8))
            optimal_preset["expected_speedup"] *= 0.9
        
        return optimal_preset
    
    def _select_optimal_preset(self, hardware_config: HardwareConfig, 
                             benchmark_results: Dict[str, float]) -> str:
        """Select the best preset key based on hardware characteristics."""
        
        if hardware_config.hardware_type == "Apple Silicon":
            if "M4" in hardware_config.hardware_name:
                return "apple_mps_m4_pro"
            else:
                return "apple_mps_general"
        
        elif hardware_config.hardware_type.startswith("NVIDIA"):
            if "RTX 40" in hardware_config.hardware_name:
                return "nvidia_rtx_40xx"
            elif "RTX 30" in hardware_config.hardware_name:
                return "nvidia_rtx_30xx"
            else:
                return "nvidia_rtx_30xx"  # Default to 30xx settings
        
        else:
            return "cpu_optimized"


def get_performance_recommendations(hardware_config: HardwareConfig) -> Dict[str, Any]:
    """Get comprehensive performance recommendations."""
    benchmarker = PerformanceBenchmarker()
    benchmark_results = benchmarker.quick_benchmark(hardware_config)
    optimization_preset = benchmarker.get_optimization_preset(hardware_config, benchmark_results)
    
    return {
        "benchmark_results": benchmark_results,
        "optimization_preset": optimization_preset,
        "hardware_summary": {
            "device": hardware_config.device,
            "hardware_name": hardware_config.hardware_name,
            "expected_speedup": hardware_config.expected_speedup,
            "memory_threshold": hardware_config.memory_threshold_gb
        },
        "recommendations": {
            "model_size": optimization_preset["model_recommendations"]["balanced"],
            "batch_size": optimization_preset["batch_size"],
            "precision": optimization_preset["compute_type"],
            "segment_length": optimization_preset["segment_length_hours"]
        }
    }