# Video Frame Capture

A professional desktop application for video frame capture and export using PySide6.

## Features

- **Video Playback**: Load and play MP4, AVI, MOV, MKV, and other video formats
- **Timeline Navigation**: Precise seeking with frame-accurate positioning
- **Frame Capture**: Capture frames at any video position with one click
- **Thumbnail Gallery**: Visual gallery of captured frames with selection support
- **Batch Export**: Export selected frames as ZIP archives
- **Memory Management**: Intelligent caching with memory optimization
- **Drag & Drop**: Simple drag and drop video file loading
- **Professional UI**: Dockable panels with customizable layout

## Requirements

- Python 3.9 or higher
- PySide6 6.6.0+
- OpenCV 4.8.0+
- NumPy 1.24.0+
- Pillow 10.0.0+

## Installation

### Using Poetry (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd video_frame_capture
```

2. Install dependencies:
```bash
poetry install
```

3. Run the application:
```bash
poetry run video-frame-capture
```

### Using pip

1. Clone the repository:
```bash
git clone <repository-url>
cd video_frame_capture
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python -m src.video_frame_capture.main
```

## Usage

### Loading Videos

- **Drag & Drop**: Drag a video file directly onto the application window
- **File Menu**: Use File > Open Video to browse and select a video file
- **Command Line**: Pass a video file path as a command line argument

### Capturing Frames

1. Load a video file
2. Navigate to the desired position using the timeline controls
3. Click the "📸 Capture Current Frame" button
4. The captured frame will appear in the thumbnail gallery

### Timeline Navigation

- **Play/Pause**: Click the play button or press Space
- **Seeking**: Click anywhere on the timeline to jump to that position
- **Frame Navigation**: Use the ◀◀ and ▶▶ buttons for frame-by-frame movement
- **Keyboard Shortcuts**:
  - `Space`: Play/Pause
  - `Left Arrow`: Previous frame
  - `Right Arrow`: Next frame
  - `Shift + Left`: Skip backward 10 seconds
  - `Shift + Right`: Skip forward 10 seconds
  - `B`: Toggle bookmark at current position

### Managing Captured Frames

- **Selection**: Use checkboxes to select frames for export
- **Select All**: Use the "Select All" checkbox to select/deselect all frames
- **Context Menu**: Right-click frames for additional options
- **Clear**: Use the "🗑 Clear All" button to remove all captured frames

### Exporting Frames

1. Select the frames you want to export using checkboxes
2. Click "📤 Export Selected" or use File > Export Frames
3. Choose a location and filename for the ZIP file
4. The export will include:
   - Individual frame images (PNG format)
   - Metadata JSON file with frame information
   - Text summary of the export

## Architecture

### Core Components

- **VideoPlayer**: QMediaPlayer wrapper with QVideoSink integration
- **FrameExtractor**: Background frame processing with threading
- **TimelineController**: Precise timeline navigation and bookmarks
- **MemoryManager**: LRU caching with memory monitoring

### UI Components

- **MainWindow**: Dockable interface with drag & drop support
- **VideoDisplay**: Video playback with overlay information
- **TimelineWidget**: Custom timeline with seeking and bookmarks
- **ThumbnailGallery**: Grid view of captured frames with selection
- **ControlsPanel**: Playback and capture controls

### Data Models

- **ThumbnailModel**: QAbstractListModel for thumbnail display
- **ProjectModel**: Project state and settings management
- **CaptureModel**: Captured frame data and metadata

### Threading Workers

- **FrameCaptureWorker**: Background frame extraction
- **ThumbnailWorker**: Thumbnail generation
- **ExportWorker**: ZIP file creation and export

## Configuration

The application stores settings in platform-appropriate locations:
- **Windows**: `%APPDATA%/VideoFrameCapture/`
- **macOS**: `~/Library/Application Support/VideoFrameCapture/`
- **Linux**: `~/.local/share/VideoFrameCapture/`

### Settings Include

- Window geometry and dock layout
- Cache size and memory limits
- Export preferences
- Thumbnail size settings

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open video file |
| `Ctrl+E` | Export frames |
| `Ctrl+Shift+C` | Clear all frames |
| `Space` | Play/Pause |
| `C` | Capture current frame |
| `B` | Toggle bookmark |
| `Left Arrow` | Previous frame |
| `Right Arrow` | Next frame |
| `Shift+Left` | Skip backward 10s |
| `Shift+Right` | Skip forward 10s |

## Development

### Project Structure

```
src/video_frame_capture/
├── core/                 # Core video processing
│   ├── video_player.py
│   ├── frame_extractor.py
│   ├── timeline_controller.py
│   └── memory_manager.py
├── ui/                   # User interface
│   ├── main_window.py
│   ├── video_display.py
│   ├── timeline_widget.py
│   ├── thumbnail_gallery.py
│   └── controls_panel.py
├── models/               # Data models
│   ├── thumbnail_model.py
│   ├── project_model.py
│   └── capture_model.py
├── workers/              # Background workers
│   ├── frame_capture_worker.py
│   ├── thumbnail_worker.py
│   └── export_worker.py
└── utils/                # Utilities
    ├── opencv_bridge.py
    ├── file_manager.py
    └── cache_manager.py
```

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black src/
poetry run flake8 src/
```

### Type Checking

```bash
poetry run mypy src/
```

## Building for Distribution

### PyInstaller

```bash
poetry run pyinstaller --windowed --onefile src/video_frame_capture/main.py
```

### Briefcase

```bash
poetry run briefcase create
poetry run briefcase build
poetry run briefcase package
```

## Troubleshooting

### Common Issues

**Video won't load**
- Ensure the video format is supported
- Check that the file isn't corrupted
- Verify codec compatibility

**Poor performance**
- Reduce cache size in settings
- Close other resource-intensive applications
- Check available system memory

**Export fails**
- Ensure sufficient disk space
- Check write permissions for export directory
- Verify frames are selected for export

**Application crashes**
- Check console output for error messages
- Ensure all dependencies are installed correctly
- Try running with `--debug` flag for verbose output

### Debug Mode

Run with debug information:
```bash
python -m src.video_frame_capture.main --debug
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

## Changelog

### v0.1.0
- Initial release
- Basic video playback and frame capture
- Timeline navigation with bookmarks
- Thumbnail gallery with selection
- ZIP export functionality
- Memory management and caching
- Drag & drop support