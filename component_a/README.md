# WhisperX Streamlit Application

A professional-grade Streamlit application for audio transcription using WhisperX, featuring word-level timestamps, speaker diarization, and comprehensive output formats.

## 🚀 Features

- **Advanced Transcription**: WhisperX with 70x real-time performance
- **Speaker Diarization**: Identify "who spoke when" with pyannote.audio
- **Multiple Output Formats**: JSON, SRT, VTT, TXT, CSV, Word-level JSON
- **Memory Optimization**: Automatic segmentation for 3-4 hour audio files
- **Progress Tracking**: Real-time progress updates during processing
- **Hardware Auto-detection**: Optimal settings for your GPU/CPU setup
- **Configuration Presets**: Fast, balanced, accurate, and long-audio modes

## 📋 System Requirements

### Minimum Requirements
- **CPU**: Modern multi-core processor
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space for models
- **Python**: 3.10 or higher

### GPU Requirements (Recommended)
- **Base model**: 2GB VRAM
- **Small model**: 4GB VRAM  
- **Large models**: 8GB+ VRAM
- **NVIDIA GPU**: CUDA 11.8+ with cuDNN 8.x

### Processing Time Estimates
- **1 hour audio + Base model**: ~3-5 minutes
- **1 hour audio + Large model**: ~10-15 minutes
- **With speaker diarization**: 2-3x longer

## 🛠 Installation

### Prerequisites

#### System Dependencies
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install ffmpeg -y

# For macOS
brew install ffmpeg
```

#### NVIDIA CUDA and cuDNN Setup (Required for GPU acceleration)

**Note**: GPU acceleration significantly improves processing speed (5-10x faster than CPU).

1. **Install NVIDIA GPU drivers**:
```bash
# Check if drivers are installed
nvidia-smi

# If not installed, install NVIDIA drivers
sudo apt install nvidia-driver-535 -y
sudo reboot
```

2. **Add NVIDIA CUDA repository**:
```bash
# Download and install CUDA keyring
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
```

3. **Install CUDA and cuDNN**:
```bash
# Install CUDA toolkit
sudo apt install cuda-toolkit-11-8 -y

# Install cuDNN libraries
sudo apt install libcudnn8 libcudnn8-dev -y
```

4. **Verify installation**:
```bash
# Check CUDA version
nvcc --version
nvidia-smi

# Test PyTorch CUDA availability (after installation)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Alternative: CPU-only setup**
If you prefer to use CPU-only processing (no GPU requirements):
- No CUDA/cuDNN installation needed
- Processing will be slower but fully functional
- The application will automatically detect and use CPU mode

### Using uv Package Manager (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd whisperx-streamlit

# Install with uv
uv python pin 3.10
uv sync

# Run the application
uv run streamlit run src/app.py --server.maxUploadSize 1024
```

### Using pip
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run src/app.py
```

### Manual Installation
```bash
# Install PyTorch with CUDA support first
pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu118

# Install WhisperX from GitHub
pip install git+https://github.com/m-bain/whisperX.git

# Install other dependencies  
pip install streamlit librosa transformers pyannote.audio speechbrain
```

## 🎯 Quick Start

1. **Start the application** (with 1GB upload limit):
   ```bash
   # Option 1: Using the provided script (recommended)
   uv run python run_app.py
   
   # Option 2: Direct streamlit command with parameters
   cd src && uv run streamlit run app.py --server.maxUploadSize 1024
   ```

2. **Upload audio file**: Choose MP3, WAV, FLAC, M4A, or other supported formats

3. **Configure settings**:
   - Select configuration preset (fast/balanced/accurate)
   - Enable speaker diarization (requires HuggingFace token)
   - Choose output formats

4. **Add HuggingFace token** (for diarization):
   - Sign up at [huggingface.co](https://huggingface.co)
   - Get token from [settings/tokens](https://huggingface.co/settings/tokens)
   - Accept user agreements for diarization models

5. **Process and download**: Click "Start Transcription" and download results

## ⚙️ Configuration

### Configuration Presets

| Preset | Model | Speed | Accuracy | Memory | Use Case |
|--------|--------|-------|----------|---------|----------|
| **Fast** | base | ⚡⚡⚡ | ⭐⭐ | Low | Quick transcription |
| **Balanced** | small | ⚡⚡ | ⭐⭐⭐ | Medium | General purpose |
| **Accurate** | large-v2 | ⚡ | ⭐⭐⭐⭐⭐ | High | High accuracy needed |
| **Long Audio** | base | ⚡⚡ | ⭐⭐ | Optimized | 3+ hour files |

### Custom Configuration Options

#### Hardware Settings
- **Device**: CUDA (GPU) or CPU processing
- **Batch Size**: 1-32 (higher = faster, more memory)
- **Compute Type**: float16 (balanced), int8 (memory-efficient), float32 (highest precision)

#### Processing Settings
- **Model**: base, small, medium, large-v2, large-v3
- **Language**: Auto-detect or specify (en, es, fr, de, etc.)
- **Speaker Diarization**: Enable/disable speaker identification
- **Speaker Count**: Min/max number of speakers (1-20)

#### Output Settings
- **Formats**: JSON, SRT, VTT, TXT, CSV, Word-level JSON
- **Word Timestamps**: Include precise word timing
- **Confidence Scores**: Include transcription confidence
- **Speaker Labels**: Include speaker identification

## 📊 Output Formats

### JSON Format
```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.663,
      "end": 7.751,
      "text": "Welcome back. Here we go again.",
      "speaker": "SPEAKER_00",
      "words": [
        {
          "word": "Welcome",
          "start": 0.663,
          "end": 0.903,
          "confidence": 0.906,
          "speaker": "SPEAKER_00"
        }
      ]
    }
  ]
}
```

### SRT Format (Subtitles)
```srt
1
00:00:00,663 --> 00:00:07,751
[SPEAKER_00]: Welcome back. Here we go again.

2
00:00:08,184 --> 00:00:12,745
[SPEAKER_01]: This is the second speaker talking.
```

### VTT Format (WebVTT)
```vtt
WEBVTT

00:00:00.663 --> 00:00:07.751
[SPEAKER_00]: Welcome back. Here we go again.

00:00:08.184 --> 00:00:12.745
[SPEAKER_01]: This is the second speaker talking.
```

## 🔧 Advanced Usage

### Processing Long Audio Files (3-4 hours)

The application automatically handles long audio files by:
- **Automatic Segmentation**: Splits audio into manageable chunks
- **Memory Management**: Cleans up between segments
- **Result Merging**: Combines segments into final transcript
- **Progress Tracking**: Shows progress across all segments

### Memory Optimization

For memory-constrained systems:
1. Use **base** or **small** models
2. Reduce **batch size** to 4-8
3. Use **int8** compute type
4. Disable **diarization** for very long files
5. Enable **long_audio** preset

### GPU Optimization

For maximum performance:
1. Use **large-v2** or **large-v3** models
2. Increase **batch size** to 16-32
3. Use **float16** compute type
4. Ensure 8GB+ VRAM available

## 🐛 Troubleshooting

### Common Issues

#### CUDA Out of Memory
```bash
# Solution 1: Reduce batch size
batch_size = 4  # instead of 16

# Solution 2: Use int8 compute type
compute_type = "int8"  # instead of "float16"

# Solution 3: Use smaller model
model_name = "base"  # instead of "large-v2"
```

#### PyTorch Installation Issues
```bash
# Uninstall existing PyTorch
pip uninstall torch torchaudio

# Install specific version with CUDA
pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu118
```

#### WhisperX Installation Issues
```bash
# Install from GitHub directly
pip install git+https://github.com/m-bain/whisperX.git

# Or use specific commit
pip install git+https://github.com/m-bain/whisperX.git@<commit-hash>
```

#### HuggingFace Token Issues
1. Verify token starts with `hf_`
2. Check token permissions (read access required)
3. Accept user agreements for diarization models:
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

### Performance Issues

#### Slow Processing
- Use GPU instead of CPU
- Increase batch size if memory allows
- Disable diarization for faster results
- Use smaller model (base/small)

#### High Memory Usage
- Enable automatic segmentation
- Use int8 compute type
- Reduce batch size
- Monitor system memory

## 📚 API Reference

### Core Classes

#### `WhisperXProcessor`
Main processing class that handles the complete transcription pipeline.

```python
from src.whisperx_processor import WhisperXProcessor
from src.config import HardwareConfig, ProcessingConfig, OutputConfig

# Initialize processor
processor = WhisperXProcessor(
    hardware_config=HardwareConfig.auto_detect(),
    processing_config=ProcessingConfig.get_preset("balanced"),
    output_config=OutputConfig.default()
)

# Process audio file
result = processor.process_audio_file(
    "audio.mp3", 
    hf_token="hf_...",
    progress_callback=lambda p, m: print(f"{p:.1%}: {m}")
)
```

#### `TranscriptionFormatConverter`
Converts transcription results to various output formats.

```python
from src.format_converters import TranscriptionFormatConverter

converter = TranscriptionFormatConverter(
    include_speaker_labels=True,
    include_word_timestamps=True,
    include_confidence_scores=True
)

# Convert to different formats
json_output = converter.to_json(result)
srt_output = converter.to_srt(result)  
vtt_output = converter.to_vtt(result)
txt_output = converter.to_txt(result)
```

#### `MemoryManager`
Handles memory optimization and cleanup.

```python
from src.memory_manager import MemoryManager

memory_manager = MemoryManager(memory_threshold_gb=8.0)

# Check memory usage
usage = memory_manager.get_memory_usage()
print(f"Current memory: {usage['total_gb']:.2f}GB")

# Cleanup when needed
memory_manager.full_cleanup()
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_processor.py
```

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Issues**: Report bugs and request features via [GitHub Issues]
- **Documentation**: Check this README and code comments
- **WhisperX**: Visit [WhisperX GitHub](https://github.com/m-bain/whisperX) for model-specific issues

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the base model
- [WhisperX](https://github.com/m-bain/whisperX) for fast inference and alignment
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) for speaker diarization
- [Streamlit](https://streamlit.io/) for the web interface framework