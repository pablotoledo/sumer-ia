"""
WhisperX Streamlit Application

A professional-grade audio transcription application using WhisperX
with speaker diarization and comprehensive output formats.
"""

__version__ = "0.1.0"
__author__ = "Pablo Toledo"
__description__ = "WhisperX Streamlit application for long audio transcription"

from .config import HardwareConfig, ProcessingConfig, OutputConfig
from .whisperx_processor import WhisperXProcessor
from .format_converters import TranscriptionFormatConverter, TranscriptionSummary
from .memory_manager import MemoryManager, MemoryMonitor

__all__ = [
    "HardwareConfig",
    "ProcessingConfig", 
    "OutputConfig",
    "WhisperXProcessor",
    "TranscriptionFormatConverter",
    "TranscriptionSummary",
    "MemoryManager",
    "MemoryMonitor",
]