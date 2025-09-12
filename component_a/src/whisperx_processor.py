"""Core WhisperX processing pipeline for audio transcription and speaker diarization."""

import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Tuple
import time
import math

try:
    import whisperx
    import torch
    import librosa
    import numpy as np
    
    # Fix PyTorch 2.6+ weights_only issue for WhisperX compatibility
    # Monkey patch torch.load to use weights_only=False by default for WhisperX
    original_torch_load = torch.load
    def safe_torch_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    torch.load = safe_torch_load
    
except ImportError as e:
    raise ImportError(f"Required packages not installed: {e}")

try:
    from config import HardwareConfig, ProcessingConfig, OutputConfig
    from memory_manager import MemoryManager, MemoryMonitor, configure_memory_efficient_torch
except ImportError:
    from .config import HardwareConfig, ProcessingConfig, OutputConfig
    from .memory_manager import MemoryManager, MemoryMonitor, configure_memory_efficient_torch


class WhisperXProcessor:
    """Main processor for WhisperX transcription pipeline."""
    
    def __init__(self, 
                 hardware_config: HardwareConfig,
                 processing_config: ProcessingConfig,
                 output_config: OutputConfig):
        """Initialize WhisperX processor.
        
        Args:
            hardware_config: Hardware configuration settings
            processing_config: Processing pipeline configuration
            output_config: Output format configuration
        """
        self.hardware_config = hardware_config
        self.processing_config = processing_config
        self.output_config = output_config
        
        self.memory_manager = MemoryManager(hardware_config.memory_threshold_gb)
        self.memory_monitor = MemoryMonitor(self.memory_manager)
        
        self.logger = logging.getLogger(__name__)
        
        # Configure PyTorch for memory efficiency
        configure_memory_efficient_torch()
        
        # Initialize models as None
        self.whisper_model = None
        self.alignment_model = None
        self.alignment_metadata = None
        self.diarization_model = None
        
        # Processing state
        self.current_language = None
        self.processing_segments = []
        
    def load_whisper_model(self) -> bool:
        """Load WhisperX transcription model with intelligent fallback.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            self.logger.info(f"Loading WhisperX model: {self.processing_config.model_name}")
            self.memory_monitor.log_memory_status("before_whisper_model_load")
            
            # Try with original device first
            self.whisper_model = whisperx.load_model(
                self.processing_config.model_name,
                self.hardware_config.device,
                compute_type=self.hardware_config.compute_type,
                language=self.processing_config.language
            )
            
            self.memory_monitor.log_memory_status("after_whisper_model_load")
            self.logger.info(f"WhisperX model loaded successfully on {self.hardware_config.device}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to load WhisperX model on {self.hardware_config.device}: {e}")
            
            # Intelligent fallback system
            if self.hardware_config.device == "mps":
                return self._fallback_mps_to_cpu()
            elif self.hardware_config.device == "xpu":
                return self._fallback_xpu_to_cpu()
            else:
                self.logger.error(f"No fallback available for device: {self.hardware_config.device}")
                return False
    
    def _fallback_mps_to_cpu(self) -> bool:
        """Fallback from MPS to CPU when MPS is not supported by WhisperX."""
        try:
            self.logger.info("🔄 Falling back from MPS to CPU (WhisperX MPS compatibility)")
            
            # Update hardware config for CPU fallback
            original_device = self.hardware_config.device
            self.hardware_config.device = "cpu"
            self.hardware_config.compute_type = "int8"  # CPU works better with int8
            self.hardware_config.batch_size = min(8, self.hardware_config.batch_size)
            
            # Try loading with CPU
            self.whisper_model = whisperx.load_model(
                self.processing_config.model_name,
                "cpu",
                compute_type="int8",
                language=self.processing_config.language
            )
            
            self.memory_monitor.log_memory_status("after_whisper_model_load_cpu_fallback")
            self.logger.info("✅ WhisperX model loaded successfully with CPU fallback")
            self.logger.info("💡 Note: Using CPU fallback. Processing will be slower but compatible")
            
            return True
            
        except Exception as fallback_error:
            self.logger.error(f"CPU fallback also failed: {fallback_error}")
            return False
    
    def _fallback_xpu_to_cpu(self) -> bool:
        """Fallback from Intel XPU to CPU when XPU is not supported."""
        try:
            self.logger.info("🔄 Falling back from Intel XPU to CPU")
            
            # Update hardware config for CPU fallback
            self.hardware_config.device = "cpu"
            self.hardware_config.compute_type = "int8"
            self.hardware_config.batch_size = min(8, self.hardware_config.batch_size)
            
            self.whisper_model = whisperx.load_model(
                self.processing_config.model_name,
                "cpu",
                compute_type="int8",
                language=self.processing_config.language
            )
            
            self.logger.info("✅ WhisperX model loaded successfully with CPU fallback")
            return True
            
        except Exception as fallback_error:
            self.logger.error(f"CPU fallback also failed: {fallback_error}")
            return False
    
    def load_alignment_model(self, language_code: str) -> bool:
        """Load alignment model for word-level timestamps.
        
        Args:
            language_code: Language code for alignment model
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            self.logger.info(f"Loading alignment model for language: {language_code}")
            self.memory_monitor.log_memory_status("before_alignment_model_load")
            
            self.alignment_model, self.alignment_metadata = whisperx.load_align_model(
                language_code=language_code,
                device=self.hardware_config.device
            )
            
            self.memory_monitor.log_memory_status("after_alignment_model_load")
            self.logger.info("Alignment model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load alignment model: {e}")
            return False
    
    def load_diarization_model(self, hf_token: str) -> bool:
        """Load diarization model for speaker identification.
        
        Args:
            hf_token: HuggingFace API token
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if not self.processing_config.enable_diarization:
                return True
                
            self.logger.info("Loading diarization model")
            self.memory_monitor.log_memory_status("before_diarization_model_load")
            
            self.diarization_model = whisperx.DiarizationPipeline(
                use_auth_token=hf_token,
                device=self.hardware_config.device
            )
            
            self.memory_monitor.log_memory_status("after_diarization_model_load")
            self.logger.info("Diarization model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load diarization model: {e}")
            return False
    
    def cleanup_models(self):
        """Clean up all loaded models from memory."""
        self.logger.info("Cleaning up models from memory")
        
        if self.whisper_model:
            self.memory_manager.cleanup_model(self.whisper_model)
            self.whisper_model = None
            
        if self.alignment_model:
            self.memory_manager.cleanup_model(self.alignment_model)
            self.alignment_model = None
            self.alignment_metadata = None
            
        if self.diarization_model:
            self.memory_manager.cleanup_model(self.diarization_model)
            self.diarization_model = None
        
        self.memory_manager.full_cleanup()
        self.memory_monitor.log_memory_status("after_model_cleanup")
    
    def load_and_segment_audio(self, audio_path: str) -> Tuple[Any, List[Dict[str, Any]]]:
        """Load audio and create segments if needed for memory management.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, segment_info_list)
        """
        self.logger.info(f"Loading audio from: {audio_path}")
        
        # Load audio using whisperx
        audio = whisperx.load_audio(audio_path)
        
        # Calculate duration in hours
        duration_seconds = len(audio) / 16000  # WhisperX uses 16kHz sample rate
        duration_hours = duration_seconds / 3600
        
        self.logger.info(f"Audio duration: {duration_hours:.2f} hours ({duration_seconds:.1f} seconds)")
        
        # Check if segmentation is needed
        if self.memory_manager.should_segment_audio(
            duration_hours, 
            self.processing_config.model_name,
            self.hardware_config.batch_size
        ):
            segment_length_hours = self.processing_config.segment_length_hours
            if segment_length_hours > duration_hours:
                segment_length_hours = duration_hours
                
            segments = self._create_audio_segments(audio, segment_length_hours)
            self.logger.info(f"Created {len(segments)} audio segments of {segment_length_hours:.2f}h each")
            return audio, segments
        else:
            # Process as single segment
            segments = [{
                'start_time': 0.0,
                'end_time': duration_hours,
                'audio_data': audio,
                'segment_id': 0
            }]
            return audio, segments
    
    def _create_audio_segments(self, audio: np.ndarray, segment_length_hours: float) -> List[Dict[str, Any]]:
        """Create audio segments for processing.
        
        Args:
            audio: Full audio data
            segment_length_hours: Length of each segment in hours
            
        Returns:
            List of segment information dictionaries
        """
        segment_length_samples = int(segment_length_hours * 3600 * 16000)  # 16kHz sample rate
        segments = []
        
        for i, start_sample in enumerate(range(0, len(audio), segment_length_samples)):
            end_sample = min(start_sample + segment_length_samples, len(audio))
            
            # Add slight overlap to prevent word cutting
            if i > 0:
                start_sample = max(0, start_sample - 800)  # 50ms overlap
            if end_sample < len(audio):
                end_sample = min(len(audio), end_sample + 800)  # 50ms overlap
            
            segment_audio = audio[start_sample:end_sample]
            
            segments.append({
                'start_time': start_sample / 16000 / 3600,  # Convert to hours
                'end_time': end_sample / 16000 / 3600,
                'audio_data': segment_audio,
                'segment_id': i,
                'start_sample': start_sample,
                'end_sample': end_sample
            })
        
        return segments
    
    def transcribe_audio(self, audio: np.ndarray, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Transcribe audio using WhisperX.
        
        Args:
            audio: Audio data to transcribe
            progress_callback: Optional callback for progress updates
            
        Returns:
            Transcription result dictionary
        """
        if not self.whisper_model:
            raise RuntimeError("WhisperX model not loaded")
        
        self.logger.info("Starting transcription")
        self.memory_monitor.log_memory_status("before_transcription")
        
        if progress_callback:
            progress_callback(0.1, "Transcribing audio...")
        
        try:
            result = self.whisper_model.transcribe(
                audio, 
                batch_size=self.hardware_config.batch_size
            )
            
            self.current_language = result.get("language", "en")
            self.logger.info(f"Transcription completed. Detected language: {self.current_language}")
            
            if progress_callback:
                progress_callback(0.4, f"Transcription completed (language: {self.current_language})")
            
            self.memory_monitor.log_memory_status("after_transcription")
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise
    
    def align_transcription(self, result: Dict[str, Any], audio: np.ndarray, 
                          progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Align transcription for word-level timestamps.
        
        Args:
            result: Transcription result from WhisperX
            audio: Original audio data
            progress_callback: Optional callback for progress updates
            
        Returns:
            Aligned transcription result
        """
        if not result.get("segments"):
            self.logger.warning("No segments to align")
            return result
        
        language_code = self.current_language or result.get("language", "en")
        
        if not self.alignment_model:
            if not self.load_alignment_model(language_code):
                self.logger.warning("Alignment model not available, skipping alignment")
                return result
        
        self.logger.info("Starting alignment")
        self.memory_monitor.log_memory_status("before_alignment")
        
        if progress_callback:
            progress_callback(0.6, "Aligning word timestamps...")
        
        try:
            aligned_result = whisperx.align(
                result["segments"],
                self.alignment_model,
                self.alignment_metadata,
                audio,
                self.hardware_config.device,
                return_char_alignments=False
            )
            
            # Update the result with aligned segments
            result.update(aligned_result)
            
            self.logger.info("Alignment completed")
            if progress_callback:
                progress_callback(0.8, "Word alignment completed")
            
            self.memory_monitor.log_memory_status("after_alignment")
            return result
            
        except Exception as e:
            self.logger.error(f"Alignment failed: {e}")
            # Return original result if alignment fails
            return result
    
    def perform_diarization(self, result: Dict[str, Any], audio: np.ndarray,
                          hf_token: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Perform speaker diarization.
        
        Args:
            result: Aligned transcription result
            audio: Original audio data
            hf_token: HuggingFace API token
            progress_callback: Optional callback for progress updates
            
        Returns:
            Result with speaker labels
        """
        if not self.processing_config.enable_diarization:
            return result
        
        if not self.diarization_model:
            if not self.load_diarization_model(hf_token):
                self.logger.warning("Diarization model not available, skipping diarization")
                return result
        
        self.logger.info("Starting speaker diarization")
        self.memory_monitor.log_memory_status("before_diarization")
        
        if progress_callback:
            progress_callback(0.9, "Performing speaker diarization...")
        
        try:
            # Perform diarization
            diarization_segments = self.diarization_model(
                audio,
                min_speakers=self.processing_config.min_speakers,
                max_speakers=self.processing_config.max_speakers
            )
            
            # Assign speakers to words
            result = whisperx.assign_word_speakers(diarization_segments, result)
            
            self.logger.info("Diarization completed")
            if progress_callback:
                progress_callback(1.0, "Speaker diarization completed")
            
            self.memory_monitor.log_memory_status("after_diarization")
            return result
            
        except Exception as e:
            self.logger.error(f"Diarization failed: {e}")
            # Return result without speaker labels if diarization fails
            return result
    
    def process_audio_file(self, audio_path: str, hf_token: Optional[str] = None,
                          progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process complete audio file through WhisperX pipeline.
        
        Args:
            audio_path: Path to audio file
            hf_token: HuggingFace API token (required for diarization)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete processing result
        """
        start_time = time.time()
        
        try:
            # Load models
            if progress_callback:
                progress_callback(0.05, "Loading models...")
            
            if not self.load_whisper_model():
                raise RuntimeError("Failed to load WhisperX model")
            
            # Load and segment audio
            if progress_callback:
                progress_callback(0.08, "Loading audio...")
            
            full_audio, segments = self.load_and_segment_audio(audio_path)
            
            # Process segments
            all_results = []
            total_segments = len(segments)
            
            for i, segment in enumerate(segments):
                segment_start_time = time.time()
                
                if progress_callback:
                    base_progress = 0.1 + (i / total_segments) * 0.8
                    progress_callback(base_progress, f"Processing segment {i+1}/{total_segments}")
                
                # Create segment progress callback
                def segment_progress(progress, message):
                    if progress_callback:
                        segment_progress_val = base_progress + (progress * 0.8 / total_segments)
                        progress_callback(segment_progress_val, f"Segment {i+1}: {message}")
                
                # Transcribe segment
                result = self.transcribe_audio(segment['audio_data'], segment_progress)
                
                # Align segment
                result = self.align_transcription(result, segment['audio_data'], segment_progress)
                
                # Diarize segment (if enabled)
                if hf_token:
                    result = self.perform_diarization(result, segment['audio_data'], hf_token, segment_progress)
                
                # Adjust timestamps for segment offset
                if i > 0:  # Not the first segment
                    offset_seconds = segment['start_time'] * 3600
                    self._adjust_segment_timestamps(result, offset_seconds)
                
                all_results.append({
                    'segment_id': i,
                    'result': result,
                    'processing_time': time.time() - segment_start_time
                })
                
                # Cleanup between segments to manage memory
                if i < total_segments - 1:  # Not the last segment
                    self.memory_manager.full_cleanup()
            
            # Merge all segment results
            if progress_callback:
                progress_callback(0.95, "Merging segment results...")
            
            final_result = self._merge_segment_results(all_results)
            
            # Final cleanup
            self.cleanup_models()
            
            processing_time = time.time() - start_time
            final_result['processing_info'] = {
                'total_processing_time': processing_time,
                'segments_processed': total_segments,
                'memory_report': self.memory_monitor.get_memory_report()
            }
            
            if progress_callback:
                progress_callback(1.0, f"Processing completed in {processing_time:.1f} seconds")
            
            self.logger.info(f"Audio processing completed in {processing_time:.2f} seconds")
            return final_result
            
        except Exception as e:
            self.cleanup_models()
            self.logger.error(f"Audio processing failed: {e}")
            raise
    
    def _adjust_segment_timestamps(self, result: Dict[str, Any], offset_seconds: float):
        """Adjust timestamps in result for segment offset.
        
        Args:
            result: Transcription result to adjust
            offset_seconds: Offset to add to timestamps
        """
        if 'segments' not in result:
            return
        
        for segment in result['segments']:
            segment['start'] += offset_seconds
            segment['end'] += offset_seconds
            
            if 'words' in segment:
                for word in segment['words']:
                    if 'start' in word:
                        word['start'] += offset_seconds
                    if 'end' in word:
                        word['end'] += offset_seconds
    
    def _merge_segment_results(self, segment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple audio segments.
        
        Args:
            segment_results: List of segment processing results
            
        Returns:
            Merged result dictionary
        """
        if not segment_results:
            return {'segments': [], 'language': 'unknown'}
        
        # Start with the first result as base
        merged_result = segment_results[0]['result'].copy()
        merged_segments = list(merged_result.get('segments', []))
        
        # Add segments from remaining results
        for segment_data in segment_results[1:]:
            result = segment_data['result']
            if 'segments' in result:
                merged_segments.extend(result['segments'])
        
        merged_result['segments'] = merged_segments
        
        # Add processing metadata
        total_processing_time = sum(sr['processing_time'] for sr in segment_results)
        merged_result['segment_processing_info'] = {
            'total_segments': len(segment_results),
            'total_segment_processing_time': total_processing_time,
            'segment_details': [
                {
                    'segment_id': sr['segment_id'],
                    'processing_time': sr['processing_time']
                }
                for sr in segment_results
            ]
        }
        
        return merged_result