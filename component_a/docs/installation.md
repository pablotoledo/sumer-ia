# Installation Guide

This guide provides detailed installation instructions for the WhisperX Streamlit application.

## System Requirements

### Operating System Support
- **Linux**: Ubuntu 20.04+ (recommended), Debian 11+, CentOS 8+
- **macOS**: 10.15+ (Catalina or newer)
- **Windows**: 10/11 (with WSL2 recommended for best performance)

### Hardware Requirements

#### Minimum System Requirements
- **CPU**: 4-core modern processor (Intel i5/AMD Ryzen 5 equivalent)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space (5GB for models, 5GB for processing)
- **Network**: Internet connection for model downloads

#### GPU Requirements (Optional but Recommended)
- **NVIDIA GPU**: GTX 1060 6GB / RTX 2060 or better
- **CUDA**: Version 11.8 or 12.1
- **cuDNN**: Version 8.x
- **VRAM**: 
  - Base/Small models: 4GB+
  - Medium model: 6GB+
  - Large models: 8GB+

#### Performance Expectations

| Hardware Configuration | 1-hour Audio Processing Time | Recommended Model |
|------------------------|------------------------------|-------------------|
| CPU Only (8-core)     | 30-60 minutes               | base              |
| GTX 1060 6GB          | 3-8 minutes                 | small             |
| RTX 3070 8GB          | 2-5 minutes                 | large-v2          |
| RTX 4090 24GB         | 1-3 minutes                 | large-v3          |

## Installation Methods

### Method 1: uv Package Manager (Recommended)

uv is a fast Python package and project manager that provides the most reliable installation.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone the repository
git clone <repository-url>
cd whisperx-streamlit

# Set Python version
uv python pin 3.10

# Install all dependencies
uv sync

# Run the application
uv run streamlit run src/app.py
```

### Method 2: pip with Virtual Environment

```bash
# Clone repository
git clone <repository-url>
cd whisperx-streamlit

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support (if GPU available)
pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install -e .

# Run the application
streamlit run src/app.py
```

### Method 3: Conda Environment

```bash
# Clone repository
git clone <repository-url>
cd whisperx-streamlit

# Create conda environment
conda create -n whisperx python=3.10
conda activate whisperx

# Install PyTorch with CUDA
conda install pytorch==2.0.0 torchaudio==2.0.0 pytorch-cuda=11.8 -c pytorch -c nvidia

# Install WhisperX and dependencies
pip install git+https://github.com/m-bain/whisperX.git
pip install streamlit librosa transformers pyannote.audio speechbrain huggingface-hub

# Run the application
streamlit run src/app.py
```

## System-Specific Installation

### Ubuntu/Debian Linux

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    ffmpeg \
    git \
    curl \
    build-essential

# Install NVIDIA drivers (if GPU available)
sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit

# Install cuDNN (for GPU acceleration)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install -y libcudnn8 libcudnn8-dev

# Reboot after NVIDIA installation
sudo reboot

# Verify CUDA installation
nvidia-smi
nvcc --version

# Continue with uv or pip installation
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 ffmpeg git

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Continue with uv installation method
```

### Windows 10/11

#### Option A: WSL2 (Recommended)
```bash
# Enable WSL2
wsl --install Ubuntu-22.04

# Inside WSL2, follow Ubuntu instructions above
```

#### Option B: Native Windows
```powershell
# Install Python 3.10 from python.org
# Download and install Git for Windows
# Download and install FFmpeg

# Install uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Open PowerShell and continue with uv installation
```

## GPU Setup (NVIDIA CUDA)

### CUDA Installation

#### Linux (Ubuntu/Debian)
```bash
# Download CUDA 11.8
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run

# Install CUDA
sudo sh cuda_11.8.0_520.61.05_linux.run

# Add to PATH (add to ~/.bashrc)
export PATH=/usr/local/cuda-11.8/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH
```

#### Windows
1. Download CUDA 11.8 from NVIDIA Developer website
2. Run the installer
3. Verify installation: `nvcc --version`

#### macOS
CUDA is not supported on macOS. Use CPU processing or consider alternatives.

### Verify GPU Setup

```python
# Test CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA devices: {torch.cuda.device_count()}')"

# Test WhisperX with GPU
python -c "import whisperx; print('WhisperX imported successfully')"
```

## Dependency Installation Issues

### Common PyTorch Issues

#### CUDA Version Mismatch
```bash
# Check CUDA version
nvcc --version
nvidia-smi

# Install compatible PyTorch version
# For CUDA 11.8:
pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1:
pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cu121
```

#### CPU-Only Installation
```bash
pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cpu
```

### WhisperX Installation Issues

#### Install from GitHub
```bash
# Install specific version
pip install git+https://github.com/m-bain/whisperX.git@v3.1.5

# Install development version
pip install git+https://github.com/m-bain/whisperX.git

# Force reinstall
pip install --force-reinstall git+https://github.com/m-bain/whisperX.git
```

#### Compilation Issues
```bash
# Install build tools (Ubuntu)
sudo apt install -y build-essential python3-dev

# Install build tools (macOS)
xcode-select --install

# Upgrade build tools
pip install --upgrade setuptools wheel pip
```

### FFmpeg Installation Issues

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Windows
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH
4. Restart command prompt/PowerShell

## Model Downloads

Models are downloaded automatically on first use. To pre-download:

```python
import whisperx

# Pre-download Whisper models
whisperx.load_model("base", "cpu")
whisperx.load_model("small", "cpu")
whisperx.load_model("large-v2", "cpu")

# Pre-download alignment models
whisperx.load_align_model(language_code="en", device="cpu")
whisperx.load_align_model(language_code="es", device="cpu")
```

### Model Storage Locations
- **Linux/macOS**: `~/.cache/whisperx/`
- **Windows**: `%USERPROFILE%\.cache\whisperx\`

## Environment Variables

Set these environment variables for optimal performance:

```bash
# For GPU users
export CUDA_VISIBLE_DEVICES=0
export TORCH_CUDA_ARCH_LIST="6.0;6.1;7.0;7.5;8.0;8.6"

# For memory optimization
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# For HuggingFace cache
export HUGGINGFACE_HUB_CACHE=/path/to/cache

# Add to ~/.bashrc or ~/.zshrc for persistence
```

## Verification Script

Create a verification script to test installation:

```python
# verify_installation.py
import sys
import subprocess

def check_dependency(name, import_name=None):
    if import_name is None:
        import_name = name
    
    try:
        __import__(import_name)
        print(f"✅ {name} is available")
        return True
    except ImportError:
        print(f"❌ {name} is NOT available")
        return False

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        print("✅ FFmpeg is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg is NOT available")
        return False

def check_cuda():
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA is available ({torch.cuda.device_count()} device(s))")
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"   GPU {i}: {props.name} ({props.total_memory/1024**3:.1f}GB)")
            return True
        else:
            print("⚠️  CUDA is not available (CPU-only mode)")
            return False
    except ImportError:
        print("❌ PyTorch is not available")
        return False

if __name__ == "__main__":
    print("🔍 Verifying WhisperX Streamlit Installation...")
    print("=" * 50)
    
    dependencies = [
        ("Python 3.10+", lambda: sys.version_info >= (3, 10)),
        ("torch", "torch"),
        ("whisperx", "whisperx"),
        ("streamlit", "streamlit"),
        ("librosa", "librosa"),
        ("transformers", "transformers"),
    ]
    
    results = []
    
    for name, check in dependencies:
        if callable(check):
            results.append(check())
        else:
            results.append(check_dependency(name, check))
    
    results.append(check_ffmpeg())
    cuda_available = check_cuda()
    
    print("\n" + "=" * 50)
    if all(results[:6]):  # All main dependencies
        print("🎉 Installation verification successful!")
        if cuda_available:
            print("🚀 GPU acceleration is available")
        else:
            print("💻 Running in CPU-only mode")
        
        print("\n📋 Next steps:")
        print("1. Run: streamlit run src/app.py")
        print("2. Open browser to: http://localhost:8501")
        if not cuda_available:
            print("3. Consider GPU setup for faster processing")
    else:
        print("❌ Installation verification failed!")
        print("Please fix the missing dependencies above")
        sys.exit(1)
```

Run verification:
```bash
python verify_installation.py
```

## Troubleshooting

### Permission Issues (Linux/macOS)
```bash
# Fix pip permissions
pip install --user <package>

# Or use sudo (not recommended)
sudo pip install <package>
```

### Port Already in Use
```bash
# Find process using port 8501
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run src/app.py --server.port 8502
```

### Module Not Found Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall package
pip install --force-reinstall <package>
```

### Memory Issues During Installation
```bash
# Increase pip cache
pip install --no-cache-dir <package>

# Use swap file (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Getting Help

If you encounter issues:

1. **Check the logs**: Look for error messages in the terminal
2. **Verify system requirements**: Ensure your system meets minimum requirements
3. **Check GitHub Issues**: Search for similar problems
4. **Update dependencies**: Try updating to latest versions
5. **Clean installation**: Remove virtual environment and reinstall

### Useful Commands for Debugging

```bash
# Check Python version
python --version

# Check pip version
pip --version

# List installed packages
pip list

# Check CUDA version
nvidia-smi
nvcc --version

# Check available disk space
df -h

# Check memory usage
free -h  # Linux
vm_stat  # macOS
```

For additional help, please create an issue on GitHub with:
- Your operating system and version
- Python version
- Complete error message
- Steps to reproduce the issue