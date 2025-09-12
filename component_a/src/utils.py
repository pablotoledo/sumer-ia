"""Utility functions for WhisperX Streamlit application."""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import time


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('whisperx_app.log')
        ]
    )
    
    return logging.getLogger(__name__)


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed.
    
    Returns:
        Dictionary mapping package names to availability status
    """
    dependencies = {
        'torch': False,
        'whisperx': False,
        'streamlit': False,
        'librosa': False,
        'transformers': False,
        'ffmpeg': False
    }
    
    # Check Python packages
    for package in ['torch', 'whisperx', 'streamlit', 'librosa', 'transformers']:
        try:
            __import__(package)
            dependencies[package] = True
        except ImportError:
            dependencies[package] = False
    
    # Check ffmpeg system dependency
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        dependencies['ffmpeg'] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        dependencies['ffmpeg'] = False
    
    return dependencies


def validate_cuda_setup() -> Dict[str, Any]:
    """Validate CUDA setup for GPU acceleration.
    
    Returns:
        Dictionary with CUDA validation results
    """
    cuda_info = {
        'cuda_available': False,
        'cuda_version': None,
        'gpu_count': 0,
        'gpu_names': [],
        'gpu_memory': [],
        'recommendations': []
    }
    
    try:
        import torch
        
        cuda_info['cuda_available'] = torch.cuda.is_available()
        
        if cuda_info['cuda_available']:
            cuda_info['cuda_version'] = torch.version.cuda
            cuda_info['gpu_count'] = torch.cuda.device_count()
            
            for i in range(cuda_info['gpu_count']):
                props = torch.cuda.get_device_properties(i)
                cuda_info['gpu_names'].append(props.name)
                cuda_info['gpu_memory'].append(props.total_memory / (1024**3))  # GB
            
            # Generate recommendations based on GPU memory
            total_memory = sum(cuda_info['gpu_memory'])
            if total_memory >= 16:
                cuda_info['recommendations'].append("High-end GPU detected. Use large models with high batch sizes.")
            elif total_memory >= 8:
                cuda_info['recommendations'].append("Mid-range GPU detected. Use medium models with moderate batch sizes.")
            else:
                cuda_info['recommendations'].append("Limited GPU memory. Consider using base model with small batch sizes.")
        else:
            cuda_info['recommendations'].append("CUDA not available. Processing will use CPU (slower).")
            
    except ImportError:
        cuda_info['recommendations'].append("PyTorch not installed. Cannot check CUDA status.")
    
    return cuda_info


def get_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA256 hash string
    """
    hash_sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    
    return hash_sha256.hexdigest()


def estimate_audio_duration(file_path: str) -> Optional[float]:
    """Estimate audio duration without loading the full file.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Duration in seconds, or None if cannot determine
    """
    try:
        import librosa
        duration = librosa.get_duration(path=file_path)
        return duration
    except Exception:
        # Fallback using ffmpeg if librosa fails
        try:
            cmd = [
                'ffprobe', '-i', file_path,
                '-show_entries', 'format=duration',
                '-v', 'quiet', '-of', 'csv=p=0'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            return None


def clean_temp_files(temp_dir: Optional[str] = None) -> int:
    """Clean up temporary files created during processing.
    
    Args:
        temp_dir: Specific temporary directory to clean, or None for default
        
    Returns:
        Number of files cleaned
    """
    import tempfile
    import glob
    
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
    
    # Look for whisperx-related temp files
    patterns = [
        'whisperx_*',
        'tmp_audio_*',
        '*.tmp',
        'streamlit_*'
    ]
    
    files_cleaned = 0
    
    for pattern in patterns:
        search_pattern = os.path.join(temp_dir, pattern)
        for file_path in glob.glob(search_pattern):
            try:
                # Only delete files older than 1 hour
                if os.path.isfile(file_path):
                    file_age = time.time() - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
                        files_cleaned += 1
            except Exception as e:
                logging.warning(f"Could not delete temp file {file_path}: {e}")
    
    return files_cleaned


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_hf_token(token: str) -> Tuple[bool, str]:
    """Validate HuggingFace token format and accessibility.
    
    Args:
        token: HuggingFace API token
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not token:
        return False, "Token is empty"
    
    if not token.startswith('hf_'):
        return False, "Token should start with 'hf_'"
    
    if len(token) < 20:
        return False, "Token appears to be too short"
    
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        # Test token by getting user info
        user_info = api.whoami(token=token)
        if user_info:
            return True, f"Valid token for user: {user_info.get('name', 'Unknown')}"
    except Exception as e:
        return False, f"Token validation failed: {str(e)}"
    
    return True, "Token appears valid"


def get_optimal_batch_size(gpu_memory_gb: float, model_name: str) -> int:
    """Calculate optimal batch size based on available GPU memory.
    
    Args:
        gpu_memory_gb: Available GPU memory in GB
        model_name: WhisperX model name
        
    Returns:
        Recommended batch size
    """
    # Base memory requirements per batch for different models (approximate)
    model_memory_per_batch = {
        "base": 0.1,
        "small": 0.15,
        "medium": 0.25,
        "large-v2": 0.4,
        "large-v3": 0.5
    }
    
    memory_per_batch = model_memory_per_batch.get(model_name, 0.25)
    
    # Reserve 20% of GPU memory for other operations
    available_memory = gpu_memory_gb * 0.8
    
    # Calculate optimal batch size
    optimal_batch = int(available_memory / memory_per_batch)
    
    # Clamp to reasonable range
    return max(1, min(optimal_batch, 32))


def create_processing_summary(result: Dict[str, Any], processing_time: float, 
                            config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a comprehensive processing summary.
    
    Args:
        result: WhisperX processing result
        processing_time: Total processing time in seconds
        config: Processing configuration used
        
    Returns:
        Processing summary dictionary
    """
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'processing_time_seconds': processing_time,
        'processing_time_formatted': format_duration(processing_time),
        'configuration': config,
        'audio_stats': {},
        'model_performance': {}
    }
    
    # Extract audio statistics
    segments = result.get('segments', [])
    if segments:
        total_duration = max(seg.get('end', 0) for seg in segments)
        total_words = sum(len(seg.get('text', '').split()) for seg in segments)
        
        summary['audio_stats'] = {
            'duration_seconds': total_duration,
            'duration_formatted': format_duration(total_duration),
            'total_segments': len(segments),
            'total_words': total_words,
            'language': result.get('language', 'unknown')
        }
        
        # Calculate performance metrics
        if processing_time > 0 and total_duration > 0:
            realtime_factor = processing_time / total_duration
            words_per_second = total_words / processing_time if processing_time > 0 else 0
            
            summary['model_performance'] = {
                'realtime_factor': round(realtime_factor, 2),
                'words_per_second': round(words_per_second, 2),
                'segments_per_second': round(len(segments) / processing_time, 2)
            }
    
    return summary


def format_duration(seconds: float) -> str:
    """Format duration in human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}m {seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours}h {minutes}m {seconds:.1f}s"


class PerformanceProfiler:
    """Simple performance profiler for tracking processing steps."""
    
    def __init__(self):
        """Initialize profiler."""
        self.steps = []
        self.start_time = None
    
    def start(self, step_name: str):
        """Start timing a processing step.
        
        Args:
            step_name: Name of the processing step
        """
        self.start_time = time.time()
        self.current_step = step_name
    
    def end(self):
        """End timing the current step."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.steps.append({
                'step': self.current_step,
                'duration': duration,
                'duration_formatted': format_duration(duration)
            })
            self.start_time = None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get profiling summary.
        
        Returns:
            Profiling summary dictionary
        """
        total_time = sum(step['duration'] for step in self.steps)
        
        return {
            'total_time': total_time,
            'total_time_formatted': format_duration(total_time),
            'steps': self.steps,
            'step_count': len(self.steps)
        }