# Video Frame Capture - Architecture Documentation

## Overview

This document describes the architectural design and implementation patterns of the Video Frame Capture application, built with PySide6 and following modern Qt6 multimedia practices.

## Core Architecture Principles

### 1. Separation of Concerns
- **Core Layer**: Video processing, frame extraction, timeline management
- **UI Layer**: User interface components and interactions
- **Data Layer**: Models for state management and data persistence
- **Worker Layer**: Background processing and threading
- **Utility Layer**: Helper functions and cross-cutting concerns

### 2. Signal-Slot Communication
All components communicate through Qt's signal-slot mechanism, ensuring:
- Loose coupling between components
- Thread-safe communication
- Event-driven architecture
- Easy testing and mocking

### 3. Thread Safety
- Main UI thread handles user interactions
- Background workers process video frames
- QThreadPool manages concurrent operations
- Memory-safe frame passing between threads

## Component Architecture

### Core Components

#### VideoPlayer (`core/video_player.py`)
**Purpose**: Wraps QMediaPlayer with QVideoSink for frame extraction

**Key Features**:
- QMediaPlayer integration for video playback
- QVideoSink for direct frame access
- Signal emission for frame changes
- Error handling and state management

**Architecture Pattern**: Facade Pattern
```python
QMediaPlayer + QVideoSink → VideoPlayer → Signals
```

#### FrameExtractor (`core/frame_extractor.py`)
**Purpose**: Extracts video frames with background processing

**Key Features**:
- QVideoFrame to QPixmap conversion
- Background threading with QRunnable
- OpenCV integration for image processing
- Memory-efficient frame handling

**Architecture Pattern**: Worker Pattern
```python
QVideoFrame → FrameExtractionWorker → QPixmap + Signals
```

#### TimelineController (`core/timeline_controller.py`)
**Purpose**: Manages video timeline navigation and bookmarks

**Key Features**:
- Frame-accurate seeking
- Bookmark management
- Time formatting utilities
- Position tracking and updates

**Architecture Pattern**: Controller Pattern
```python
VideoPlayer ← TimelineController → UI Components
```

#### MemoryManager (`core/memory_manager.py`)
**Purpose**: Intelligent memory management with LRU caching

**Key Features**:
- Multi-level LRU caches (frames, thumbnails, metadata)
- Memory pressure monitoring
- Automatic cleanup and optimization
- Statistics and monitoring

**Architecture Pattern**: Strategy Pattern
```python
LRUCache + MemoryMonitor → MemoryManager → Cache Operations
```

### UI Components

#### MainWindow (`ui/main_window.py`)
**Purpose**: Main application window with dockable interface

**Key Features**:
- QDockWidget-based layout
- Drag & drop video loading
- Menu and toolbar management
- Settings persistence

**Architecture Pattern**: Composite Pattern
```python
QMainWindow + QDockWidgets → Integrated Interface
```

#### VideoDisplay (`ui/video_display.py`)
**Purpose**: Video playback widget with overlay information

**Key Features**:
- QVideoWidget integration
- Custom overlay painting
- Click and double-click handling
- Placeholder for empty state

**Architecture Pattern**: Decorator Pattern
```python
QVideoWidget + Overlay → Enhanced Video Display
```

#### TimelineWidget (`ui/timeline_widget.py`)
**Purpose**: Custom timeline with precise seeking

**Key Features**:
- Custom QSlider with click-to-seek
- Bookmark visualization
- Hover effects and tooltips
- Keyboard navigation

**Architecture Pattern**: Custom Widget Pattern
```python
QSlider + Custom Paint → Interactive Timeline
```

#### ThumbnailGallery (`ui/thumbnail_gallery.py`)
**Purpose**: Grid display of captured frames with selection

**Key Features**:
- QListView with custom model
- Multiple selection support
- Context menus and actions
- Export functionality

**Architecture Pattern**: Model-View Pattern
```python
ThumbnailModel + QListView → Gallery Interface
```

### Data Models

#### ThumbnailModel (`models/thumbnail_model.py`)
**Purpose**: QAbstractListModel for thumbnail display

**Key Features**:
- Lazy loading of thumbnails
- Selection state management
- Efficient data access
- Statistical information

**Architecture Pattern**: Model Pattern (MVC)
```python
QAbstractListModel → Custom Data Operations
```

#### ProjectModel (`models/project_model.py`)
**Purpose**: Project state and settings management

**Key Features**:
- Project file I/O
- Settings persistence
- Metadata tracking
- Change notifications

**Architecture Pattern**: Repository Pattern
```python
Data Persistence ← ProjectModel → Application State
```

### Threading Architecture

#### Background Workers
All heavy processing is moved to background threads:

**FrameCaptureWorker**:
- Video frame processing
- Image format conversion
- Memory-safe operations

**ThumbnailWorker**:
- Thumbnail generation
- Image scaling and effects
- Batch processing support

**ExportWorker**:
- ZIP file creation
- Progress reporting
- Error handling

**Architecture Pattern**: Producer-Consumer
```python
Main Thread → QThreadPool → Worker Threads → Results via Signals
```

## Memory Management Strategy

### Multi-Level Caching
1. **Frame Cache**: Full-resolution video frames (LRU, 300MB limit)
2. **Thumbnail Cache**: Scaled thumbnails (LRU, 100MB limit)
3. **Metadata Cache**: Video and frame metadata (LRU, 50MB limit)

### Memory Monitoring
- Real-time memory usage tracking
- Automatic cache pruning under pressure
- Garbage collection integration
- Memory leak prevention

### Cache Optimization
```python
Memory Pressure → Cache Reduction → Garbage Collection
```

## Threading Model

### Thread Safety Patterns

#### Signal-Slot Communication
```python
Worker Thread: emit signal → Main Thread: slot execution
```

#### Frame Passing
```python
QVideoFrame.map() → Copy Data → QVideoFrame.unmap()
```

#### Cache Access
```python
Threading.RLock → Cache Operation → Release Lock
```

## Error Handling Strategy

### Hierarchical Error Handling
1. **Component Level**: Local error recovery
2. **Application Level**: User notification
3. **System Level**: Graceful degradation

### Error Types
- **Video Loading Errors**: Format support, codec issues
- **Processing Errors**: Memory exhaustion, threading issues
- **Export Errors**: File system, permissions
- **UI Errors**: Widget state, event handling

## Performance Optimization

### Video Processing
- Hardware acceleration where available
- Efficient pixel format handling
- Minimal memory copying
- Frame dropping under load

### UI Responsiveness
- Non-blocking operations
- Progressive loading
- Lazy initialization
- Efficient repainting

### Memory Efficiency
- LRU cache eviction
- Weak references where appropriate
- Explicit resource cleanup
- Memory pool reuse

## Extensibility Points

### Plugin Architecture (Future)
- Video codec plugins
- Export format plugins
- Processing effect plugins
- UI theme plugins

### Configuration System
- User preferences
- Plugin settings
- Performance tuning
- Feature toggles

## Testing Architecture

### Unit Testing
- Component isolation
- Mock dependencies
- Signal/slot testing
- Memory leak detection

### Integration Testing
- End-to-end workflows
- UI automation
- Performance benchmarks
- Memory profiling

### Test Structure
```python
tests/
├── test_core/          # Core component tests
├── test_ui/            # UI component tests
├── test_models/        # Data model tests
├── test_workers/       # Threading tests
└── test_integration/   # Integration tests
```

## Deployment Architecture

### Distribution Formats
- **Standalone Executable**: PyInstaller packaging
- **Native Package**: Platform-specific installers
- **Portable**: Self-contained directory

### Dependency Management
- **Core Dependencies**: PySide6, OpenCV, NumPy
- **Optional Dependencies**: Hardware acceleration libraries
- **Platform Dependencies**: OS-specific multimedia codecs

### Update Mechanism (Future)
- Incremental updates
- Automatic dependency checking
- Rollback capabilities
- Delta patching

## Security Considerations

### Input Validation
- Video file format validation
- Path traversal prevention
- Memory bounds checking
- Resource limit enforcement

### Data Protection
- Temporary file cleanup
- Memory scrubbing
- Secure file operations
- Privacy-preserving exports

## Monitoring and Diagnostics

### Performance Metrics
- Frame processing rate
- Memory usage patterns
- Cache hit ratios
- Thread utilization

### Diagnostic Information
- Application logs
- Error reporting
- Performance profiling
- Memory analysis

This architecture ensures scalability, maintainability, and performance while providing a robust foundation for video frame capture operations.