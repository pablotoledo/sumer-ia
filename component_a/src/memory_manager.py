"""Memory management utilities for WhisperX processing."""

import gc
import os
import psutil
import torch
from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass
from enum import Enum


class HardwareType(Enum):
    """Supported hardware types for memory optimization."""
    APPLE_MPS = "apple_mps"
    NVIDIA_CUDA = "nvidia_cuda" 
    AMD_ROCM = "amd_rocm"
    INTEL_XPU = "intel_xpu"
    CPU = "cpu"


@dataclass
class HardwareMemoryProfile:
    """Memory profile for specific hardware type."""
    hardware_type: HardwareType
    unified_memory: bool  # Whether GPU and RAM share memory
    memory_efficiency: float  # Memory usage efficiency factor
    cache_strategy: str  # Caching strategy to use
    batch_size_factor: float  # Batch size scaling factor
    preferred_precision: str  # Preferred compute precision


class MemoryManager:
    """Manages memory usage during WhisperX processing with hardware-specific optimizations."""
    
    def __init__(self, memory_threshold_gb: float = 8.0, hardware_type: Optional[HardwareType] = None):
        """Initialize memory manager.
        
        Args:
            memory_threshold_gb: Maximum memory usage threshold in GB
            hardware_type: Hardware type for specialized optimizations
        """
        self.memory_threshold_gb = memory_threshold_gb
        self.hardware_type = hardware_type or self._detect_hardware_type()
        self.hardware_profile = self._get_hardware_profile(self.hardware_type)
        self.logger = logging.getLogger(__name__)
    
    def _detect_hardware_type(self) -> HardwareType:
        """Auto-detect current hardware type."""
        try:
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return HardwareType.APPLE_MPS
            elif torch.cuda.is_available():
                return HardwareType.NVIDIA_CUDA
            elif hasattr(torch, 'xpu') and torch.xpu.is_available():
                return HardwareType.INTEL_XPU
            else:
                return HardwareType.CPU
        except:
            return HardwareType.CPU
    
    def _get_hardware_profile(self, hardware_type: HardwareType) -> HardwareMemoryProfile:
        """Get memory profile for hardware type."""
        profiles = {
            HardwareType.APPLE_MPS: HardwareMemoryProfile(
                hardware_type=HardwareType.APPLE_MPS,
                unified_memory=True,
                memory_efficiency=0.85,  # Apple Silicon has efficient unified memory
                cache_strategy="aggressive_clear",
                batch_size_factor=1.3,  # Can handle larger batches due to unified memory
                preferred_precision="float16"
            ),
            HardwareType.NVIDIA_CUDA: HardwareMemoryProfile(
                hardware_type=HardwareType.NVIDIA_CUDA,
                unified_memory=False,
                memory_efficiency=0.75,  # Separate GPU/RAM memory
                cache_strategy="smart_reserve",
                batch_size_factor=1.0,
                preferred_precision="float16"
            ),
            HardwareType.AMD_ROCM: HardwareMemoryProfile(
                hardware_type=HardwareType.AMD_ROCM,
                unified_memory=False,
                memory_efficiency=0.70,  # Experimental ROCm support
                cache_strategy="conservative",
                batch_size_factor=0.8,
                preferred_precision="float16"
            ),
            HardwareType.INTEL_XPU: HardwareMemoryProfile(
                hardware_type=HardwareType.INTEL_XPU,
                unified_memory=False,
                memory_efficiency=0.72,  # Intel Arc GPUs
                cache_strategy="moderate",
                batch_size_factor=0.9,
                preferred_precision="float16"
            ),
            HardwareType.CPU: HardwareMemoryProfile(
                hardware_type=HardwareType.CPU,
                unified_memory=True,
                memory_efficiency=0.60,  # CPU-only processing is less efficient
                cache_strategy="minimal",
                batch_size_factor=0.5,
                preferred_precision="int8"
            )
        }
        return profiles.get(hardware_type, profiles[HardwareType.CPU])
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics with hardware-specific details.
        
        Returns:
            Dictionary with RAM and GPU/MPS memory usage in GB
        """
        # RAM usage
        process = psutil.Process(os.getpid())
        ram_usage_gb = process.memory_info().rss / (1024**3)
        
        # Hardware-specific GPU memory usage
        gpu_usage_gb = 0.0
        gpu_reserved_gb = 0.0
        
        if self.hardware_type == HardwareType.APPLE_MPS:
            try:
                # For Apple MPS, memory is unified - estimate GPU usage
                if hasattr(torch.backends, 'mps'):
                    # MPS doesn't have direct memory querying, estimate based on tensors
                    gpu_usage_gb = self._estimate_mps_memory_usage()
            except:
                pass
        elif self.hardware_type == HardwareType.NVIDIA_CUDA:
            if torch.cuda.is_available():
                gpu_usage_gb = torch.cuda.memory_allocated() / (1024**3)
                gpu_reserved_gb = torch.cuda.memory_reserved() / (1024**3)
        elif self.hardware_type == HardwareType.INTEL_XPU:
            try:
                if hasattr(torch, 'xpu') and torch.xpu.is_available():
                    gpu_usage_gb = torch.xpu.memory_allocated() / (1024**3)
            except:
                pass
        
        # For unified memory systems, adjust total calculation
        if self.hardware_profile.unified_memory:
            total_gb = max(ram_usage_gb, gpu_usage_gb)  # Memory is shared
        else:
            total_gb = ram_usage_gb + gpu_usage_gb
        
        return {
            "ram_gb": ram_usage_gb,
            "gpu_gb": gpu_usage_gb,
            "gpu_reserved_gb": gpu_reserved_gb,
            "total_gb": total_gb,
            "hardware_type": self.hardware_type.value,
            "unified_memory": self.hardware_profile.unified_memory
        }
    
    def _estimate_mps_memory_usage(self) -> float:
        """Estimate MPS memory usage (Apple Silicon)."""
        # This is an approximation since MPS doesn't expose memory stats directly
        try:
            # Count tensors on MPS device
            mps_tensors = 0
            estimated_size = 0.0
            
            # This is a rough estimation - in practice, you'd need to track tensors
            # For now, return a conservative estimate
            return 0.5  # 500MB estimate
        except:
            return 0.0
    
    def check_memory_threshold(self) -> bool:
        """Check if memory usage is below threshold.
        
        Returns:
            True if memory usage is acceptable, False otherwise
        """
        usage = self.get_memory_usage()
        return usage["total_gb"] < self.memory_threshold_gb
    
    def cleanup_torch_cache(self):
        """Clean up PyTorch cache with hardware-specific optimizations."""
        if self.hardware_type == HardwareType.NVIDIA_CUDA:
            if torch.cuda.is_available():
                if self.hardware_profile.cache_strategy == "smart_reserve":
                    # For NVIDIA, keep some cache for performance
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                else:
                    # Aggressive cleanup
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.synchronize()
                self.logger.info("Cleared CUDA cache")
        
        elif self.hardware_type == HardwareType.APPLE_MPS:
            if hasattr(torch.backends, 'mps'):
                if self.hardware_profile.cache_strategy == "aggressive_clear":
                    # Apple MPS benefits from aggressive cleanup due to unified memory
                    torch.mps.empty_cache()
                    self.logger.info("Cleared MPS cache")
        
        elif self.hardware_type == HardwareType.INTEL_XPU:
            try:
                if hasattr(torch, 'xpu') and torch.xpu.is_available():
                    torch.xpu.empty_cache()
                    torch.xpu.synchronize()
                    self.logger.info("Cleared Intel XPU cache")
            except:
                pass
        
        # Always run Python garbage collection after cache cleanup
        self.cleanup_python_garbage()
    
    def cleanup_python_garbage(self):
        """Force Python garbage collection."""
        collected = gc.collect()
        self.logger.info(f"Garbage collected {collected} objects")
    
    def cleanup_model(self, model: Any):
        """Safely cleanup a model from memory.
        
        Args:
            model: Model object to cleanup
        """
        if model is not None:
            del model
            self.cleanup_python_garbage()
            self.cleanup_torch_cache()
    
    def full_cleanup(self):
        """Perform comprehensive memory cleanup."""
        self.cleanup_python_garbage()
        self.cleanup_torch_cache()
        
        usage_after = self.get_memory_usage()
        self.logger.info(f"Memory after cleanup: {usage_after['total_gb']:.2f}GB")
    
    def estimate_processing_memory(self, audio_duration_hours: float, 
                                 model_name: str, batch_size: int) -> float:
        """Estimate memory requirements for processing.
        
        Args:
            audio_duration_hours: Duration of audio in hours
            model_name: WhisperX model name
            batch_size: Processing batch size
            
        Returns:
            Estimated memory usage in GB
        """
        # Base model memory requirements
        model_memory = {
            "base": 1.0,
            "small": 2.0, 
            "medium": 5.0,
            "large-v2": 10.0,
            "large-v3": 12.0
        }.get(model_name, 5.0)
        
        # Audio processing memory (approximately 100MB per hour)
        audio_memory = audio_duration_hours * 0.1
        
        # Batch processing memory
        batch_memory = batch_size * 0.1
        
        # Alignment and diarization overhead
        alignment_memory = audio_duration_hours * 0.5
        
        total_memory = model_memory + audio_memory + batch_memory + alignment_memory
        
        return total_memory
    
    def should_segment_audio(self, audio_duration_hours: float, 
                           model_name: str, batch_size: int) -> bool:
        """Determine if audio should be segmented for processing.
        
        Args:
            audio_duration_hours: Duration of audio in hours
            model_name: WhisperX model name
            batch_size: Processing batch size
            
        Returns:
            True if audio should be segmented
        """
        estimated_memory = self.estimate_processing_memory(
            audio_duration_hours, model_name, batch_size
        )
        
        return estimated_memory > self.memory_threshold_gb
    
    def get_optimal_segment_length(self, audio_duration_hours: float,
                                 model_name: str, batch_size: int) -> float:
        """Calculate optimal segment length for memory constraints.
        
        Args:
            audio_duration_hours: Total audio duration in hours
            model_name: WhisperX model name
            batch_size: Processing batch size
            
        Returns:
            Optimal segment length in hours
        """
        if not self.should_segment_audio(audio_duration_hours, model_name, batch_size):
            return audio_duration_hours
        
        # Start with 1-hour segments and adjust based on memory
        target_segment_hours = 1.0
        
        while target_segment_hours > 0.25:  # Minimum 15-minute segments
            estimated_memory = self.estimate_processing_memory(
                target_segment_hours, model_name, batch_size
            )
            
            if estimated_memory <= self.memory_threshold_gb * 0.8:  # 80% threshold
                break
                
            target_segment_hours *= 0.8
        
        return max(target_segment_hours, 0.25)
    
    def get_optimal_batch_size(self, base_batch_size: int, available_memory_gb: float) -> int:
        """Calculate optimal batch size based on hardware and available memory."""
        # Apply hardware-specific batch size factor
        hardware_adjusted = int(base_batch_size * self.hardware_profile.batch_size_factor)
        
        # Memory-based adjustment
        if self.hardware_profile.unified_memory:
            # For unified memory (Apple Silicon, CPU), be more conservative
            memory_factor = min(1.0, available_memory_gb / 8.0)
        else:
            # For discrete GPU memory, can be more aggressive
            memory_factor = min(1.5, available_memory_gb / 4.0)
        
        optimal_batch_size = max(1, int(hardware_adjusted * memory_factor))
        
        # Hardware-specific limits
        if self.hardware_type == HardwareType.APPLE_MPS:
            optimal_batch_size = min(optimal_batch_size, 64)  # M4 Pro can handle large batches
        elif self.hardware_type == HardwareType.NVIDIA_CUDA:
            optimal_batch_size = min(optimal_batch_size, 32)  # Conservative for CUDA
        elif self.hardware_type == HardwareType.CPU:
            optimal_batch_size = min(optimal_batch_size, 8)   # CPU has limited parallelism
        
        return optimal_batch_size
    
    def get_hardware_recommendations(self) -> Dict[str, Any]:
        """Get hardware-specific processing recommendations."""
        return {
            "hardware_type": self.hardware_type.value,
            "unified_memory": self.hardware_profile.unified_memory,
            "memory_efficiency": self.hardware_profile.memory_efficiency,
            "preferred_precision": self.hardware_profile.preferred_precision,
            "cache_strategy": self.hardware_profile.cache_strategy,
            "batch_size_factor": self.hardware_profile.batch_size_factor,
            "optimizations": self._get_hardware_optimizations()
        }
    
    def _get_hardware_optimizations(self) -> Dict[str, str]:
        """Get hardware-specific optimization tips."""
        optimizations = {
            HardwareType.APPLE_MPS: {
                "memory": "Unified memory allows larger batches and aggressive caching",
                "precision": "float16 provides excellent performance with Neural Engine",
                "batch": "Can handle 32+ batch sizes efficiently due to unified memory",
                "tips": "Use MPS backend for 5-8x speedup over CPU on M-series chips"
            },
            HardwareType.NVIDIA_CUDA: {
                "memory": "Separate GPU memory requires careful memory management",
                "precision": "float16 enables Tensor Core acceleration on RTX cards",
                "batch": "Moderate batch sizes (16-32) work best for most GPUs",
                "tips": "Enable mixed precision and CUDA memory fractions for optimal performance"
            },
            HardwareType.AMD_ROCM: {
                "memory": "ROCm compatibility layer may have higher overhead",
                "precision": "float16 supported but may have compatibility issues",
                "batch": "Conservative batch sizes recommended for stability",
                "tips": "Experimental support - monitor for stability issues"
            },
            HardwareType.INTEL_XPU: {
                "memory": "Intel Arc GPUs have moderate memory capacity",
                "precision": "float16 provides good performance-memory balance",
                "batch": "Medium batch sizes (12-24) typically optimal",
                "tips": "Intel Extension for PyTorch required for XPU acceleration"
            },
            HardwareType.CPU: {
                "memory": "Limited by system RAM and lacks parallelism",
                "precision": "int8 quantization essential for reasonable performance",
                "batch": "Small batch sizes (4-8) prevent memory exhaustion", 
                "tips": "Consider upgrading to GPU acceleration for significant speedup"
            }
        }
        return optimizations.get(self.hardware_type, optimizations[HardwareType.CPU])


class MemoryMonitor:
    """Real-time memory monitoring during processing."""
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize memory monitor.
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        self.peak_usage = {"ram_gb": 0.0, "gpu_gb": 0.0, "total_gb": 0.0}
        self.logger = logging.getLogger(__name__)
    
    def update_peak_usage(self):
        """Update peak memory usage statistics."""
        current_usage = self.memory_manager.get_memory_usage()
        
        for key in self.peak_usage:
            if current_usage[key] > self.peak_usage[key]:
                self.peak_usage[key] = current_usage[key]
    
    def check_oom_risk(self) -> tuple[bool, str]:
        """Check for out-of-memory risk.
        
        Returns:
            Tuple of (is_at_risk, warning_message)
        """
        usage = self.memory_manager.get_memory_usage()
        threshold = self.memory_manager.memory_threshold_gb
        
        if usage["total_gb"] > threshold * 0.9:
            return True, f"Critical memory usage: {usage['total_gb']:.2f}GB / {threshold:.2f}GB"
        elif usage["total_gb"] > threshold * 0.8:
            return True, f"High memory usage: {usage['total_gb']:.2f}GB / {threshold:.2f}GB"
        
        return False, ""
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report.
        
        Returns:
            Dictionary with current and peak memory usage
        """
        self.update_peak_usage()
        current = self.memory_manager.get_memory_usage()
        
        return {
            "current": current,
            "peak": self.peak_usage.copy(),
            "threshold_gb": self.memory_manager.memory_threshold_gb,
            "usage_percentage": (current["total_gb"] / self.memory_manager.memory_threshold_gb) * 100
        }
    
    def log_memory_status(self, step: str):
        """Log current memory status for a processing step.
        
        Args:
            step: Name of the current processing step
        """
        usage = self.memory_manager.get_memory_usage()
        self.logger.info(
            f"Memory usage at {step}: "
            f"RAM={usage['ram_gb']:.2f}GB, "
            f"GPU={usage['gpu_gb']:.2f}GB, "
            f"Total={usage['total_gb']:.2f}GB"
        )
        
        at_risk, warning = self.check_oom_risk()
        if at_risk:
            self.logger.warning(f"Memory warning at {step}: {warning}")


def configure_memory_efficient_torch():
    """Configure PyTorch for memory-efficient operation."""
    if torch.cuda.is_available():
        # Enable memory fraction allocation
        torch.cuda.set_per_process_memory_fraction(0.8)
        
        # Enable CUDA memory pool for better management
        if hasattr(torch.cuda, 'memory_pool_set_fraction'):
            torch.cuda.memory_pool_set_fraction(0.8)
    
    # Set PyTorch threading for better memory usage
    torch.set_num_threads(min(4, torch.get_num_threads()))


def get_system_memory_info() -> Dict[str, float]:
    """Get system memory information.
    
    Returns:
        Dictionary with system memory statistics in GB
    """
    virtual_memory = psutil.virtual_memory()
    
    memory_info = {
        "total_ram_gb": virtual_memory.total / (1024**3),
        "available_ram_gb": virtual_memory.available / (1024**3),
        "used_ram_gb": virtual_memory.used / (1024**3),
        "ram_usage_percent": virtual_memory.percent
    }
    
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory
        memory_info.update({
            "total_gpu_gb": gpu_memory / (1024**3),
            "allocated_gpu_gb": torch.cuda.memory_allocated() / (1024**3),
            "cached_gpu_gb": torch.cuda.memory_reserved() / (1024**3)
        })
    
    return memory_info