"""
Controls panel for video playback and frame capture.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QSpinBox,
    QGroupBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtMultimedia import QMediaPlayer

from ..core.video_player import VideoPlayer
from ..core.timeline_controller import TimelineController
from ..core.frame_extractor import FrameExtractor


class PlaybackControlsGroup(QGroupBox):
    """Playback control buttons"""

    def __init__(self, video_player: VideoPlayer, parent: Optional[QWidget] = None):
        super().__init__("Playback", parent)
        self.video_player = video_player
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Setup playback controls"""
        layout = QVBoxLayout(self)

        # Main playback buttons
        main_buttons_layout = QHBoxLayout()

        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setMinimumSize(60, 40)
        self.play_pause_btn.setMaximumSize(60, 40)
        font = QFont()
        font.setPointSize(16)
        self.play_pause_btn.setFont(font)
        self.play_pause_btn.setToolTip("Play/Pause (Space)")
        main_buttons_layout.addWidget(self.play_pause_btn)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setMinimumSize(40, 40)
        self.stop_btn.setMaximumSize(40, 40)
        self.stop_btn.setFont(font)
        self.stop_btn.setToolTip("Stop")
        main_buttons_layout.addWidget(self.stop_btn)

        layout.addLayout(main_buttons_layout)

        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setToolTip("Volume Control")
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("70%")
        self.volume_label.setMinimumWidth(35)
        volume_layout.addWidget(self.volume_label)

        layout.addLayout(volume_layout)

    def connect_signals(self) -> None:
        """Connect signals"""
        self.play_pause_btn.clicked.connect(self._toggle_playback)
        self.stop_btn.clicked.connect(self.video_player.stop)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.video_player.stateChanged.connect(self._on_state_changed)

    @Slot()
    def _toggle_playback(self) -> None:
        """Toggle play/pause"""
        if self.video_player.is_playing():
            self.video_player.pause()
        else:
            self.video_player.play()

    @Slot(int)
    def _on_volume_changed(self, value: int) -> None:
        """Handle volume changes"""
        self.volume_label.setText(f"{value}%")
        # Convert percentage to 0.0-1.0 range
        volume = value / 100.0
        self.video_player.set_volume(volume)

    @Slot(int)
    def _on_state_changed(self, state: int) -> None:
        """Handle playback state changes"""
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setText("⏸")
            self.play_pause_btn.setToolTip("Pause (Space)")
        else:
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setToolTip("Play (Space)")


class FrameCaptureGroup(QGroupBox):
    """Frame capture controls"""

    frameCaptured = Signal(int)  # timestamp

    def __init__(
        self,
        video_player: VideoPlayer,
        timeline_controller: TimelineController,
        frame_extractor: FrameExtractor,
        parent: Optional[QWidget] = None,
    ):
        super().__init__("Frame Capture", parent)
        self.video_player = video_player
        self.timeline_controller = timeline_controller
        self.frame_extractor = frame_extractor

        # Auto-capture timer
        from PySide6.QtCore import QTimer
        self.auto_capture_timer = QTimer(self)
        self.auto_capture_timer.timeout.connect(self._auto_capture_frame)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Setup frame capture controls"""
        layout = QVBoxLayout(self)

        # Capture button
        self.capture_btn = QPushButton("📸 Capture Current Frame")
        self.capture_btn.setMinimumHeight(40)
        self.capture_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """
        )
        self.capture_btn.setToolTip("Capture current frame (C)")
        layout.addWidget(self.capture_btn)

        # Auto-capture controls
        auto_layout = QHBoxLayout()
        auto_layout.addWidget(QLabel("Auto-capture every:"))

        self.auto_interval_spinbox = QSpinBox()
        self.auto_interval_spinbox.setRange(1, 60)
        self.auto_interval_spinbox.setValue(5)
        self.auto_interval_spinbox.setSuffix(" sec")
        auto_layout.addWidget(self.auto_interval_spinbox)

        self.auto_capture_btn = QPushButton("Start Auto")
        self.auto_capture_btn.setCheckable(True)
        auto_layout.addWidget(self.auto_capture_btn)

        layout.addLayout(auto_layout)

        # Capture info
        self.capture_info_label = QLabel("Ready to capture")
        self.capture_info_label.setStyleSheet("color: #666; font-size: 12px;")
        self.capture_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.capture_info_label)

    def connect_signals(self) -> None:
        """Connect signals"""
        self.capture_btn.clicked.connect(self._capture_current_frame)
        self.auto_capture_btn.toggled.connect(self._toggle_auto_capture)
        # Frame readiness will be handled differently now
        self.frame_extractor.frameExtracted.connect(self._on_frame_extracted)

    @Slot()
    def _capture_current_frame(self) -> None:
        """Capture current video frame"""
        current_position = self.timeline_controller.get_current_position()
        video_path = self.video_player.get_current_video_path()

        if video_path:
            # Visual feedback - change button style temporarily
            self.capture_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                """
            )
            self.capture_info_label.setText("Capturing frame...")

            # Emit capture signal
            self.frameCaptured.emit(current_position)

            # Reset button style after a short delay
            from PySide6.QtCore import QTimer
            QTimer.singleShot(200, self._reset_capture_button_style)

    @Slot(bool)
    def _toggle_auto_capture(self, enabled: bool) -> None:
        """Toggle auto-capture mode"""
        if enabled:
            self.auto_capture_btn.setText("Stop Auto")
            # Start auto-capture timer
            interval_seconds = self.auto_interval_spinbox.value()
            self.auto_capture_timer.start(interval_seconds * 1000)  # Convert to milliseconds
            self.capture_info_label.setText(f"Auto-capturing every {interval_seconds}s")
        else:
            self.auto_capture_btn.setText("Start Auto")
            # Stop auto-capture timer
            self.auto_capture_timer.stop()
            self.capture_info_label.setText("Ready to capture")

    @Slot()
    def _auto_capture_frame(self) -> None:
        """Auto-capture frame at timer interval"""
        if self.video_player.is_playing():
            self._capture_current_frame()

    def _reset_capture_button_style(self) -> None:
        """Reset capture button to original style"""
        self.capture_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            """
        )

    def update_capture_readiness(self, ready: bool) -> None:
        """Update capture button state"""
        self.capture_btn.setEnabled(ready)
        if ready:
            self.capture_info_label.setText("Ready to capture")
        else:
            self.capture_info_label.setText("No frame available")

    @Slot(object, int, str)
    def _on_frame_extracted(self, pixmap, timestamp: int, file_path: str) -> None:
        """Handle successful frame extraction"""
        # Show success message
        seconds = timestamp / 1000
        self.capture_info_label.setText(f"✅ Frame captured at {seconds:.1f}s")

        # Reset to ready state after 2 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.capture_info_label.setText("Ready to capture"))


class VideoInfoGroup(QGroupBox):
    """Video information display"""

    def __init__(self, video_player: VideoPlayer, parent: Optional[QWidget] = None):
        super().__init__("Video Info", parent)
        self.video_player = video_player
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Setup video info display"""
        layout = QVBoxLayout(self)

        # File info
        self.file_label = QLabel("No video loaded")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.file_label)

        # Video properties
        self.resolution_label = QLabel("Resolution: --")
        layout.addWidget(self.resolution_label)

        self.duration_label = QLabel("Duration: --")
        layout.addWidget(self.duration_label)

        self.fps_label = QLabel("Frame Rate: --")
        layout.addWidget(self.fps_label)

    def connect_signals(self) -> None:
        """Connect signals"""
        self.video_player.mediaLoaded.connect(self._on_media_loaded)
        self.video_player.durationChanged.connect(self._on_duration_changed)

    @Slot()
    def _on_media_loaded(self) -> None:
        """Handle media loaded"""
        video_path = self.video_player.get_current_video_path()
        if video_path:
            # Extract filename
            filename = video_path.split("/")[-1] if "/" in video_path else video_path
            filename = video_path.split("\\")[-1] if "\\" in video_path else filename
            self.file_label.setText(filename)

            # Note: Additional video metadata would be extracted here
            # This would require additional video analysis capabilities
            self.resolution_label.setText("Resolution: Loading...")
            self.fps_label.setText("Frame Rate: Loading...")

    @Slot('qint64')
    def _on_duration_changed(self, duration: int) -> None:
        """Handle duration changes"""
        if duration > 0:
            seconds = duration / 1000
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            self.duration_label.setText(f"Duration: {minutes:02d}:{seconds:02d}")


class ControlsPanel(QWidget):
    """Main controls panel widget"""

    frameCaptured = Signal(int)  # timestamp

    def __init__(
        self,
        video_player: VideoPlayer,
        timeline_controller: TimelineController,
        frame_extractor: FrameExtractor,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.video_player = video_player
        self.timeline_controller = timeline_controller
        self.frame_extractor = frame_extractor

        self.setMinimumWidth(250)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Setup the controls panel"""
        layout = QVBoxLayout(self)

        # Playback controls
        self.playback_group = PlaybackControlsGroup(self.video_player)
        layout.addWidget(self.playback_group)

        # Frame capture controls
        self.capture_group = FrameCaptureGroup(
            self.video_player, self.timeline_controller, self.frame_extractor
        )
        layout.addWidget(self.capture_group)

        # Video info
        self.info_group = VideoInfoGroup(self.video_player)
        layout.addWidget(self.info_group)

        # Stretch to push everything to top
        layout.addStretch()

    def connect_signals(self) -> None:
        """Connect signals"""
        self.capture_group.frameCaptured.connect(self.frameCaptured)

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts"""
        key = event.key()

        if key == Qt.Key_Space:
            self.playback_group._toggle_playback()
        elif key == Qt.Key_C:
            self.capture_group._capture_current_frame()
        else:
            super().keyPressEvent(event)