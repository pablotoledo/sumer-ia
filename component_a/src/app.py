"""
WhisperX Streamlit Application for Audio Transcription with Speaker Diarization.

This application provides a user-friendly interface for transcribing long audio files
(3-4 hours) using WhisperX with word-level timestamps and speaker diarization.
"""

import streamlit as st
import tempfile
import zipfile
import io
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle imports - try absolute first, then relative
try:
    from config import (
        HardwareConfig, ProcessingConfig, OutputConfig, ConfigValidator, 
        get_memory_requirements, detect_hardware, get_available_hardware_options
    )
    from whisperx_processor import WhisperXProcessor
    from format_converters import TranscriptionFormatConverter, TranscriptionSummary
    from memory_manager import get_system_memory_info
except ImportError:
    # Try relative imports
    try:
        from .config import (
            HardwareConfig, ProcessingConfig, OutputConfig, ConfigValidator,
            get_memory_requirements, detect_hardware, get_available_hardware_options
        )
        from .whisperx_processor import WhisperXProcessor
        from .format_converters import TranscriptionFormatConverter, TranscriptionSummary
        from .memory_manager import get_system_memory_info
    except ImportError:
        # Add current directory to path and try again
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        
        from config import (
            HardwareConfig, ProcessingConfig, OutputConfig, ConfigValidator,
            get_memory_requirements, detect_hardware, get_available_hardware_options
        )
        from whisperx_processor import WhisperXProcessor
        from format_converters import TranscriptionFormatConverter, TranscriptionSummary
        from memory_manager import get_system_memory_info


# Page configuration
st.set_page_config(
    page_title="WhisperX Audio Transcription",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def display_system_info():
    """Display system information and requirements."""
    with st.sidebar.expander("💻 System Information"):
        try:
            memory_info = get_system_memory_info()
            
            st.write("**Memory:**")
            st.write(f"• RAM: {memory_info['available_ram_gb']:.1f}GB / {memory_info['total_ram_gb']:.1f}GB available")
            
            if 'total_gpu_gb' in memory_info:
                st.write(f"• GPU: {memory_info['total_gpu_gb']:.1f}GB total")
                st.write(f"• GPU Used: {memory_info['allocated_gpu_gb']:.1f}GB")
            else:
                st.write("• GPU: Not available")
            
        except Exception as e:
            st.error(f"Could not get system info: {e}")


def validate_audio_file(uploaded_file) -> tuple[bool, str]:
    """Validate uploaded audio file."""
    if not uploaded_file:
        return False, "No file uploaded"
    
    # Check file size (max 1GB)
    if uploaded_file.size > 1 * 1024 * 1024 * 1024:
        return False, "File size must be less than 1GB"
    
    # Check file extension
    allowed_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.mp4', '.ogg', '.wma'}
    file_extension = Path(uploaded_file.name).suffix.lower()
    
    if file_extension not in allowed_extensions:
        return False, f"Unsupported file format: {file_extension}"
    
    return True, "File is valid"


def estimate_processing_time(duration_minutes: float, model_name: str, enable_diarization: bool) -> str:
    """Estimate processing time based on audio duration and settings."""
    # Base processing rates (minutes of processing per minute of audio)
    base_rates = {
        "base": 0.05,
        "small": 0.08, 
        "medium": 0.15,
        "large-v2": 0.25,
        "large-v3": 0.30
    }
    
    base_rate = base_rates.get(model_name, 0.15)
    processing_minutes = duration_minutes * base_rate
    
    # Add diarization overhead (2-3x longer)
    if enable_diarization:
        processing_minutes *= 2.5
    
    if processing_minutes < 1:
        return f"~{int(processing_minutes * 60)} seconds"
    elif processing_minutes < 60:
        return f"~{int(processing_minutes)} minutes"
    else:
        hours = int(processing_minutes // 60)
        minutes = int(processing_minutes % 60)
        return f"~{hours}h {minutes}m"


def create_download_package(result: Dict[str, Any], formats: list, converter: TranscriptionFormatConverter) -> bytes:
    """Create ZIP package with all requested formats."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add transcription files
        if "JSON" in formats:
            json_content = converter.to_json(result)
            zip_file.writestr("transcription.json", json_content.encode('utf-8'))
        
        if "SRT" in formats:
            srt_content = converter.to_srt(result)
            zip_file.writestr("transcription.srt", srt_content.encode('utf-8'))
        
        if "VTT" in formats:
            vtt_content = converter.to_vtt(result)
            zip_file.writestr("transcription.vtt", vtt_content.encode('utf-8'))
        
        if "TXT" in formats:
            txt_content = converter.to_txt(result)
            zip_file.writestr("transcription.txt", txt_content.encode('utf-8'))
        
        if "CSV" in formats:
            csv_content = converter.to_csv(result)
            zip_file.writestr("transcription.csv", csv_content.encode('utf-8'))
        
        if "Word-level JSON" in formats:
            word_json = converter.to_word_level_json(result)
            zip_file.writestr("word_level.json", word_json.encode('utf-8'))
        
        # Add summary
        summary = TranscriptionSummary(result)
        summary_content = json.dumps(summary.get_full_summary(), indent=2, ensure_ascii=False)
        zip_file.writestr("summary.json", summary_content.encode('utf-8'))
    
    zip_buffer.seek(0)
    return zip_buffer.read()


def display_transcription_preview(result: Dict[str, Any], max_segments: int = 5):
    """Display a preview of the transcription results."""
    segments = result.get('segments', [])
    
    if not segments:
        st.warning("No transcription segments found.")
        return
    
    st.subheader("📝 Transcription Preview")
    
    # Show first few segments
    for i, segment in enumerate(segments[:max_segments]):
        start_time = segment.get('start', 0)
        end_time = segment.get('end', 0)
        text = segment.get('text', '').strip()
        speaker = segment.get('speaker', '')
        
        # Format timestamp
        start_min = int(start_time // 60)
        start_sec = int(start_time % 60)
        end_min = int(end_time // 60)
        end_sec = int(end_time % 60)
        
        timestamp = f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"
        
        # Display segment
        if speaker:
            st.write(f"**[{timestamp}] {speaker}:** {text}")
        else:
            st.write(f"**[{timestamp}]** {text}")
    
    if len(segments) > max_segments:
        remaining = len(segments) - max_segments
        st.info(f"... and {remaining} more segments")


def display_transcription_stats(result: Dict[str, Any]):
    """Display transcription statistics."""
    summary = TranscriptionSummary(result)
    stats = summary.get_full_summary()
    
    # Basic stats
    basic = stats['basic_stats']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Duration", basic['total_duration_formatted'])
    with col2:
        st.metric("Total Words", f"{basic['total_words']:,}")
    with col3:
        st.metric("Segments", f"{basic['total_segments']:,}")
    with col4:
        st.metric("Language", basic['language'].upper())
    
    # Speaker stats (if available)
    speaker_stats = stats['speaker_stats']
    if speaker_stats['speaker_count'] > 0:
        st.subheader("👥 Speaker Statistics")
        
        for speaker_data in speaker_stats['speakers']:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{speaker_data['speaker']}**")
            with col2:
                st.write(f"{speaker_data['duration_formatted']} ({speaker_data['percentage']}%)")
            with col3:
                st.write(f"{speaker_data['words']:,} words")
    
    # Confidence stats (if available)
    confidence = stats['confidence_stats']
    if confidence['has_confidence_scores']:
        st.subheader("📊 Confidence Scores")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average", f"{confidence['average_confidence']:.2f}")
        with col2:
            st.metric("High Confidence", f"{confidence['high_confidence_words']:,}")
        with col3:
            st.metric("Low Confidence", f"{confidence['low_confidence_words']:,}")


def main():
    """Main application function."""
    st.title("🎵 WhisperX Audio Transcription")
    st.markdown("*Advanced speech recognition with word-level timestamps and speaker diarization*")
    
    # System information
    display_system_info()
    
    # File upload
    st.header("📁 Upload Audio File")
    
    # Warning for large files
    with st.expander("⚠️ Important: Large File Upload Tips"):
        st.markdown("""
        **For files >200MB (like your 360MB WAV):**
        - ⏱️ Upload may take **5-15 minutes** depending on connection
        - 🔄 **Don't refresh** the page during upload
        - 📊 Progress bar may freeze temporarily - this is normal
        - 🚫 If you get "Network Error", **try again** - it often works on retry
        - 💡 Consider **compressing** to MP3 for faster upload
        """)
    
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['mp3', 'wav', 'flac', 'm4a', 'mp4', 'ogg', 'wma'],
        help="Supported formats: MP3, WAV, FLAC, M4A, MP4, OGG, WMA (max 1GB) - Large files may take several minutes to upload"
    )
    
    if uploaded_file:
        # Validate file
        is_valid, validation_message = validate_audio_file(uploaded_file)
        
        if not is_valid:
            st.error(validation_message)
            st.stop()
        
        # Display file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success(f"✅ File loaded: {uploaded_file.name} ({file_size_mb:.1f} MB)")
        
        with col2:
            # Estimate audio duration (rough)
            estimated_duration_hours = file_size_mb / 10  # Rough estimate: 10MB per hour
            st.info(f"⏱️ ~{estimated_duration_hours:.1f}h audio")
        
        # Configuration sidebar
        st.sidebar.header("⚙️ Configuration")
        
        # Hardware Acceleration Configuration
        st.sidebar.subheader("🚀 Hardware Acceleration")
        
        # Detect available hardware options
        available_hardware = get_available_hardware_options()
        detected_hw = detect_hardware()
        
        # Hardware acceleration mode selection
        acceleration_mode = st.sidebar.radio(
            "Acceleration Mode:",
            ["Auto-Optimize (Recommended)", "Manual Selection"],
            help="Auto-optimize detects your hardware and uses optimal settings"
        )
        
        if acceleration_mode == "Auto-Optimize (Recommended)":
            # Auto-detect and show results
            hardware_config = HardwareConfig.auto_detect()
            
            # Display detection results with performance info
            st.sidebar.success(
                f"🎯 **Detected: {hardware_config.hardware_name}**\n\n"
                f"• **Device**: {hardware_config.device.upper()}\n"
                f"• **Batch Size**: {hardware_config.batch_size}\n" 
                f"• **Precision**: {hardware_config.compute_type}\n"
                f"• **Expected Speedup**: {hardware_config.expected_speedup:.1f}x\n\n"
                f"*Your M4 Pro should process 360MB in ~3-4 minutes vs ~25 minutes on CPU!*"
            )
            
        else:
            # Manual hardware selection
            st.sidebar.write("**Available Hardware Options:**")
            
            # Create radio buttons for available hardware
            hw_options = []
            hw_labels = []
            recommended_idx = 0
            
            for i, option in enumerate(available_hardware):
                speedup_text = f"{option['speedup']:.1f}x faster" if option['speedup'] > 1 else "baseline"
                label = f"{option['name']} ({speedup_text})"
                hw_labels.append(label)
                hw_options.append(option)
                
                # Mark the fastest available as recommended
                if option['speedup'] > hw_options[recommended_idx]['speedup']:
                    recommended_idx = i
            
            # Add recommended marker
            if len(hw_options) > 1:
                hw_labels[recommended_idx] += " ⭐ Recommended"
            
            selected_hw_idx = st.sidebar.radio(
                "Select Hardware:",
                range(len(hw_labels)),
                format_func=lambda i: hw_labels[i],
                index=recommended_idx,
                help="⭐ marks the fastest option available on your system"
            )
            
            selected_option = hw_options[selected_hw_idx]
            
            # Show details about selected hardware
            with st.sidebar.expander(f"📊 {selected_option['name']} Details"):
                st.write(f"**Description**: {selected_option['description']}")
                st.write(f"**Expected Performance**: {selected_option['speedup']:.1f}x speedup")
                
                if selected_option['id'] == 'mps':
                    st.write("**Optimizations**: Neural Engine + Unified Memory")
                    st.write("**Best For**: M-series Mac users")
                elif selected_option['id'] == 'cuda':
                    st.write("**Optimizations**: Tensor Cores + CUDA")
                    st.write("**Best For**: NVIDIA RTX/GTX users")
                elif selected_option['id'] == 'cpu':
                    st.write("**Compatibility**: Universal")
                    st.write("**Best For**: Systems without GPU")
            
            # Advanced settings for manual mode
            with st.sidebar.expander("🔧 Advanced Settings"):
                if selected_option['id'] != 'cpu':
                    batch_size = st.slider(
                        "Batch Size", 
                        1, 64, 
                        32 if selected_option['id'] == 'mps' else 16,
                        help="Higher = faster but more memory usage"
                    )
                    compute_type = st.selectbox(
                        "Precision",
                        ["float16", "int8", "float32"],
                        index=0,
                        help="float16 = balanced, int8 = memory efficient, float32 = highest precision"
                    )
                else:
                    batch_size = 4
                    compute_type = "int8"
                    st.info("CPU mode uses optimized settings automatically")
            
            # Create hardware config based on manual selection
            if selected_option['id'] == 'mps':
                hardware_config = HardwareConfig(
                    device="mps",
                    batch_size=batch_size,
                    compute_type=compute_type,
                    memory_threshold_gb=16.0,
                    hardware_type="Apple Silicon",
                    hardware_name=detected_hw.get('name', 'Apple M-series'),
                    expected_speedup=selected_option['speedup']
                )
            elif selected_option['id'] == 'cuda':
                hardware_config = HardwareConfig(
                    device="cuda",
                    batch_size=batch_size,
                    compute_type=compute_type,
                    memory_threshold_gb=8.0,
                    hardware_type="NVIDIA GPU",
                    hardware_name=detected_hw.get('name', 'NVIDIA GPU'),
                    expected_speedup=selected_option['speedup']
                )
            else:  # CPU fallback
                hardware_config = HardwareConfig(
                    device="cpu",
                    batch_size=4,
                    compute_type="int8",
                    memory_threshold_gb=8.0,
                    hardware_type="CPU",
                    hardware_name="CPU (Universal)",
                    expected_speedup=1.0
                )
        
        # Processing configuration
        st.sidebar.subheader("Model Settings")
        
        preset = st.sidebar.selectbox(
            "Configuration Preset",
            ["fast", "balanced", "accurate", "long_audio", "custom"],
            index=1,
            help="Predefined settings for different use cases"
        )
        
        if preset == "custom":
            model_name = st.sidebar.selectbox(
                "Model Size",
                ["base", "small", "medium", "large-v2", "large-v3"],
                index=1,
                help="Larger models = better accuracy, more processing time"
            )
            
            language_mode = st.sidebar.radio("Language", ["Auto-detect", "Specify"])
            if language_mode == "Specify":
                language = st.sidebar.selectbox(
                    "Language Code",
                    ["en", "es", "fr", "de", "it", "pt", "ja", "zh"],
                    help="Specifying language improves accuracy and speed"
                )
            else:
                language = None
            
            enable_diarization = st.sidebar.checkbox(
                "Enable Speaker Diarization",
                value=True,
                help="Identify different speakers (requires HuggingFace token)"
            )
            
            if enable_diarization:
                st.sidebar.info("🎯 **Speaker Detection Settings**")
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    min_speakers = st.sidebar.number_input(
                        "Min Speakers", 
                        min_value=1, 
                        max_value=10, 
                        value=2,
                        help="Minimum number of speakers expected",
                        key="min_speakers_input"
                    )
                with col2:
                    max_speakers = st.sidebar.number_input(
                        "Max Speakers", 
                        min_value=1, 
                        max_value=10, 
                        value=4,
                        help="Maximum number of speakers expected",
                        key="max_speakers_input"
                    )
                
                # Validation
                if min_speakers > max_speakers:
                    st.sidebar.error("⚠️ Min speakers cannot be greater than max speakers!")
                    min_speakers = max_speakers
            else:
                min_speakers = max_speakers = 1
            
            processing_config = ProcessingConfig(
                model_name=model_name,
                language=language,
                enable_diarization=enable_diarization,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
                segment_length_hours=2.0
            )
        else:
            processing_config = ProcessingConfig.get_preset(preset)
            st.sidebar.info(f"Using {preset} preset: {processing_config.model_name} model")
        
        # HuggingFace token (if diarization enabled)
        hf_token = None
        if processing_config.enable_diarization:
            st.sidebar.markdown("---")
            st.sidebar.markdown("🔑 **Authentication Required**")
            
            hf_token = st.sidebar.text_input(
                "HuggingFace Token",
                type="password",
                placeholder="hf_xxxxxxxxxxxxx",
                help="Required for speaker diarization. Get token at https://huggingface.co/settings/tokens"
            )
            
            if not hf_token:
                st.sidebar.warning("⚠️ **HuggingFace token required for speaker diarization**")
                st.sidebar.markdown("""
                **Steps to get token:**
                1. Go to [HuggingFace](https://huggingface.co/join) and create account (free)
                2. Go to [Settings → Access Tokens](https://huggingface.co/settings/tokens)
                3. Create new token with 'read' access
                4. **Accept ALL model agreements** (click each link):
                   - ✅ [speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
                   - ✅ [segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
                   - ✅ [speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)
                5. Copy your token (starts with `hf_`) and paste it above
                """)
            else:
                if hf_token.startswith("hf_"):
                    st.sidebar.success("✅ Valid HuggingFace token format")
                else:
                    st.sidebar.error("❌ Invalid token format. Should start with 'hf_'")
                    hf_token = None
            
            if not hf_token:
                st.sidebar.error("HuggingFace token required for diarization")
        
        # Output configuration
        st.sidebar.subheader("Output Settings")
        
        output_formats = st.sidebar.multiselect(
            "Output Formats",
            ["JSON", "SRT", "VTT", "TXT", "CSV", "Word-level JSON"],
            default=["JSON", "SRT"],
            help="Select desired output formats"
        )
        
        include_word_timestamps = st.sidebar.checkbox("Include Word Timestamps", value=True)
        include_confidence = st.sidebar.checkbox("Include Confidence Scores", value=True)
        include_speakers = st.sidebar.checkbox("Include Speaker Labels", value=True)
        
        output_config = OutputConfig(
            formats=output_formats,
            include_word_timestamps=include_word_timestamps,
            include_confidence_scores=include_confidence,
            speaker_labels=include_speakers
        )
        
        # Validate configurations
        hw_valid, hw_msg = ConfigValidator.validate_hardware_config(hardware_config)
        proc_valid, proc_msg = ConfigValidator.validate_processing_config(processing_config)
        out_valid, out_msg = ConfigValidator.validate_output_config(output_config)
        
        if not (hw_valid and proc_valid and out_valid):
            st.error("Configuration validation failed:")
            if not hw_valid:
                st.error(f"Hardware: {hw_msg}")
            if not proc_valid:
                st.error(f"Processing: {proc_msg}")
            if not out_valid:
                st.error(f"Output: {out_msg}")
            st.stop()
        
        # Memory requirements estimation
        memory_req = get_memory_requirements(
            processing_config.model_name,
            hardware_config.batch_size,
            hardware_config.compute_type
        )
        
        st.sidebar.subheader("📊 Estimated Requirements")
        st.sidebar.write(f"**GPU Memory:** {memory_req['gpu_memory_gb']:.1f}GB")
        st.sidebar.write(f"**RAM:** {memory_req['ram_gb']:.1f}GB") 
        st.sidebar.write(f"**Processing Time:** {estimate_processing_time(file_size_mb / 10, processing_config.model_name, processing_config.enable_diarization)}")
        
        # Configuration Summary
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Current Configuration")
        if processing_config.enable_diarization:
            if hf_token:
                st.sidebar.success(f"✅ **Speaker Diarization:** ON ({processing_config.min_speakers}-{processing_config.max_speakers} speakers)")
            else:
                st.sidebar.error("❌ **Speaker Diarization:** Token Missing")
        else:
            st.sidebar.info("ℹ️ **Speaker Diarization:** OFF")
        
        st.sidebar.write(f"**Model:** {processing_config.model_name}")
        st.sidebar.write(f"**Device:** {hardware_config.device.upper()}")
        st.sidebar.write(f"**Output:** {', '.join(output_formats)}")
        
        # Processing summary in main area
        if output_formats:
            st.markdown("---")
            st.subheader("🎯 Ready to Process")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Model:** {processing_config.model_name}")
            with col2:
                if processing_config.enable_diarization and hf_token:
                    st.success(f"**Speakers:** {processing_config.min_speakers}-{processing_config.max_speakers}")
                else:
                    st.warning("**Speakers:** Not detected")
            with col3:
                st.info(f"**Outputs:** {len(output_formats)} formats")
        
        # Initialize session state
        if 'transcription_result' not in st.session_state:
            st.session_state.transcription_result = None
        if 'processing_completed' not in st.session_state:
            st.session_state.processing_completed = False
        if 'processing_time' not in st.session_state:
            st.session_state.processing_time = 0
        if 'output_formats' not in st.session_state:
            st.session_state.output_formats = []
        if 'converter_settings' not in st.session_state:
            st.session_state.converter_settings = {}

        # Processing button
        if st.button("🚀 Start Transcription", type="primary", disabled=not output_formats):
            if processing_config.enable_diarization and not hf_token:
                st.error("HuggingFace token is required for speaker diarization")
                st.stop()
            
            # Reset session state for new processing
            st.session_state.transcription_result = None
            st.session_state.processing_completed = False
            
            # Create progress containers
            progress_container = st.container()
            status_container = st.container()
            
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    temp_audio_path = tmp_file.name
                
                # Initialize processor
                processor = WhisperXProcessor(
                    hardware_config=hardware_config,
                    processing_config=processing_config,
                    output_config=output_config
                )
                
                # Progress callback
                def update_progress(progress: float, message: str):
                    progress_bar.progress(min(progress, 1.0))
                    status_text.text(message)
                
                # Process audio
                start_time = time.time()
                result = processor.process_audio_file(
                    temp_audio_path,
                    hf_token=hf_token,
                    progress_callback=update_progress
                )
                processing_time = time.time() - start_time
                
                # Clean up temporary file
                os.unlink(temp_audio_path)
                
                # Store results in session state
                st.session_state.transcription_result = result
                st.session_state.processing_completed = True
                st.session_state.processing_time = processing_time
                st.session_state.output_formats = output_formats
                st.session_state.converter_settings = {
                    'include_speaker_labels': include_speakers,
                    'include_word_timestamps': include_word_timestamps,
                    'include_confidence_scores': include_confidence
                }
                
                # Success message
                with status_container:
                    st.success(f"✅ Transcription completed in {processing_time:.1f} seconds!")
                
                st.rerun()  # Refresh to show results
                
            except Exception as e:
                with status_container:
                    st.error(f"❌ Processing failed: {str(e)}")
                    st.exception(e)
                
                # Clean up temporary file if it exists
                try:
                    if 'temp_audio_path' in locals():
                        os.unlink(temp_audio_path)
                except:
                    pass

        # Display results from session state (persistent across interactions)
        if st.session_state.processing_completed and st.session_state.transcription_result:
            st.markdown("---")
            st.success(f"✅ Transcription completed in {st.session_state.processing_time:.1f} seconds!")
            
            # Display results
            col1, col2 = st.columns([2, 1])
            
            with col1:
                display_transcription_preview(st.session_state.transcription_result)
            
            with col2:
                display_transcription_stats(st.session_state.transcription_result)
            
            # Create format converter with saved settings
            converter = TranscriptionFormatConverter(
                include_speaker_labels=st.session_state.converter_settings['include_speaker_labels'],
                include_word_timestamps=st.session_state.converter_settings['include_word_timestamps'],
                include_confidence_scores=st.session_state.converter_settings['include_confidence_scores']
            )
            
            # Generate download package
            download_data = create_download_package(
                st.session_state.transcription_result, 
                st.session_state.output_formats, 
                converter
            )
            
            # Download button
            st.download_button(
                label="📦 Download Results (ZIP)",
                data=download_data,
                file_name=f"transcription_{uploaded_file.name if uploaded_file else 'result'}.zip",
                mime="application/zip",
                type="primary"
            )
            
            # Individual format downloads
            st.subheader("📄 Individual Downloads")
            
            download_cols = st.columns(min(len(st.session_state.output_formats), 4))
            
            for i, format_name in enumerate(st.session_state.output_formats):
                col_idx = i % 4
                
                with download_cols[col_idx]:
                    if format_name == "JSON":
                        content = converter.to_json(st.session_state.transcription_result)
                        filename = f"transcription.json"
                    elif format_name == "SRT":
                        content = converter.to_srt(st.session_state.transcription_result)
                        filename = f"transcription.srt"
                    elif format_name == "VTT":
                        content = converter.to_vtt(st.session_state.transcription_result)
                        filename = f"transcription.vtt"
                    elif format_name == "TXT":
                        content = converter.to_txt(st.session_state.transcription_result)
                        filename = f"transcription.txt"
                    elif format_name == "CSV":
                        content = converter.to_csv(st.session_state.transcription_result)
                        filename = f"transcription.csv"
                    elif format_name == "Word-level JSON":
                        content = converter.to_word_level_json(st.session_state.transcription_result)
                        filename = f"word_level.json"
                    
                    st.download_button(
                        label=f"📄 {format_name}",
                        data=content.encode('utf-8'),
                        file_name=filename,
                        mime="text/plain",
                        key=f"download_{format_name}_{i}"
                    )
            
            # Clear results button
            if st.button("🗑️ Clear Results", type="secondary"):
                st.session_state.transcription_result = None
                st.session_state.processing_completed = False
                st.session_state.processing_time = 0
                st.session_state.output_formats = []
                st.session_state.converter_settings = {}
                st.rerun()
    
    else:
        # Instructions when no file is uploaded
        st.info("👆 Upload an audio file to get started")
        
        with st.expander("📖 Usage Instructions"):
            st.markdown("""
            ### How to use this application:
            
            1. **Upload Audio**: Choose an audio file (MP3, WAV, FLAC, etc.) up to 2GB
            2. **Configure Settings**: Select model size, enable diarization, choose output formats
            3. **Add HF Token**: If using diarization, provide your HuggingFace token
            4. **Process**: Click "Start Transcription" and wait for completion
            5. **Download**: Get your results in multiple formats
            
            ### Tips for best results:
            
            - **For speed**: Use "fast" preset with base model
            - **For accuracy**: Use "accurate" preset with large-v2 model  
            - **For long audio (3+ hours)**: Use "long_audio" preset
            - **Specify language**: If known, specify language for better accuracy
            - **GPU recommended**: CUDA GPU significantly speeds up processing
            
            ### About Speaker Diarization:
            
            Speaker diarization identifies "who spoke when" in the audio. It requires:
            - A HuggingFace account and token (free at [huggingface.co](https://huggingface.co/join))
            - Accept model agreements for these 3 models:
              - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
              - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
              - [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)
            - Additional processing time (2-3x longer)
            - More memory usage
            """)
        
        with st.expander("🔧 System Requirements"):
            st.markdown("""
            ### Minimum Requirements:
            - **CPU**: Modern multi-core processor
            - **RAM**: 8GB minimum, 16GB recommended
            - **Storage**: 5GB free space for models
            - **GPU**: Optional but highly recommended (NVIDIA with CUDA)
            
            ### GPU Requirements (for optimal performance):
            - **Base model**: 2GB VRAM
            - **Small model**: 4GB VRAM
            - **Large models**: 8GB+ VRAM
            
            ### Processing Time Estimates:
            - **1 hour audio + Base model**: ~3-5 minutes
            - **1 hour audio + Large model**: ~10-15 minutes
            - **With diarization**: 2-3x longer
            """)


if __name__ == "__main__":
    main()