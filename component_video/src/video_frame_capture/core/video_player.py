"""
Core video player implementation using QMediaPlayer and QVideoSink.
"""

from typing import Optional
from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class VideoPlayer(QObject):
    """Core video playback with frame extraction capabilities"""

    # Signals
    positionChanged = Signal('qint64')  # Position in milliseconds
    durationChanged = Signal('qint64')  # Duration in milliseconds
    frameReady = Signal()  # Frame available for capture
    stateChanged = Signal('QMediaPlayer::PlaybackState')  # Playback state
    mediaLoaded = Signal()  # Media successfully loaded
    errorOccurred = Signal(str)  # Error message
    volumeChanged = Signal('float')  # Volume changed (0.0 to 1.0)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_video_path: Optional[str] = None
        self.setup_player()

    def setup_player(self) -> None:
        """Initialize QMediaPlayer with QVideoWidget and QAudioOutput"""
        self.player = QMediaPlayer(self)
        self.video_widget = QVideoWidget()

        # Setup audio output
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.7)  # Default volume 70%

        # Debug audio device
        print(f"Audio device: {self.audio_output.device().description()}")
        print(f"Audio volume: {self.audio_output.volume()}")
        print(f"Audio muted: {self.audio_output.isMuted()}")

        # Connect player to outputs - video widget for display and audio
        self.player.setVideoOutput(self.video_widget)
        self.player.setAudioOutput(self.audio_output)

        # Connect signals
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_error_occurred)


        # Connect audio signals
        self.audio_output.volumeChanged.connect(self.volumeChanged)

    @Slot(str)
    def load_video(self, file_path: str) -> None:
        """Load video file"""
        try:
            url = QUrl.fromLocalFile(file_path)
            self._current_video_path = file_path
            self.player.setSource(url)
        except Exception as e:
            self.errorOccurred.emit(f"Failed to load video: {str(e)}")

    @Slot()
    def play(self) -> None:
        """Start playback"""
        if self.player.playbackState() != QMediaPlayer.PlayingState:
            self.player.play()

    @Slot()
    def pause(self) -> None:
        """Pause playback"""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()

    @Slot()
    def stop(self) -> None:
        """Stop playback"""
        self.player.stop()

    @Slot(int)
    def seek(self, position: int) -> None:
        """Seek to position in milliseconds"""
        if self.player.isSeekable():
            self.player.setPosition(position)

    def get_video_widget(self) -> QVideoWidget:
        """Get the video widget for display"""
        return self.video_widget

    def get_current_position(self) -> int:
        """Get current playback position in milliseconds"""
        return self.player.position()

    def get_duration(self) -> int:
        """Get video duration in milliseconds"""
        return self.player.duration()

    def get_current_video_path(self) -> Optional[str]:
        """Get the path of currently loaded video"""
        return self._current_video_path

    def is_playing(self) -> bool:
        """Check if video is currently playing"""
        return self.player.playbackState() == QMediaPlayer.PlayingState

    def is_seekable(self) -> bool:
        """Check if video is seekable"""
        return self.player.isSeekable()

    def set_volume(self, volume: float) -> None:
        """Set audio volume (0.0 to 1.0)"""
        if self.audio_output:
            volume = max(0.0, min(1.0, volume))  # Clamp to valid range
            self.audio_output.setVolume(volume)

    def get_volume(self) -> float:
        """Get current audio volume (0.0 to 1.0)"""
        if self.audio_output:
            return self.audio_output.volume()
        return 0.0

    def set_muted(self, muted: bool) -> None:
        """Set audio muted state"""
        if self.audio_output:
            self.audio_output.setMuted(muted)

    def is_muted(self) -> bool:
        """Check if audio is muted"""
        if self.audio_output:
            return self.audio_output.isMuted()
        return False

    def get_audio_output(self) -> QAudioOutput:
        """Get the audio output device"""
        return self.audio_output

    def capture_current_frame(self):
        """Capture current frame using OpenCV at current position"""
        try:
            if not self._current_video_path:
                return None

            import cv2
            from PySide6.QtGui import QPixmap, QImage

            # Get current position in milliseconds
            current_position_ms = self.player.position()

            # Open video with OpenCV
            cap = cv2.VideoCapture(self._current_video_path)
            if not cap.isOpened():
                return None

            # Set position (OpenCV uses milliseconds)
            cap.set(cv2.CAP_PROP_POS_MSEC, current_position_ms)

            # Read frame
            ret, frame = cap.read()
            cap.release()

            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame_rgb.shape
                bytes_per_line = 3 * width

                # Create QImage and convert to QPixmap
                qimage = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                return pixmap

            return None
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None


    @Slot('qint64')
    def _on_position_changed(self, position: int) -> None:
        """Handle position changes from QMediaPlayer"""
        self.positionChanged.emit(position)

    @Slot('qint64')
    def _on_duration_changed(self, duration: int) -> None:
        """Handle duration changes from QMediaPlayer"""
        self.durationChanged.emit(duration)

    @Slot('QMediaPlayer::PlaybackState')
    def _on_state_changed(self, state) -> None:
        """Handle state changes from QMediaPlayer"""
        self.stateChanged.emit(state)

    @Slot(int)
    def _on_media_status_changed(self, status: int) -> None:
        """Handle media status changes"""
        if status == QMediaPlayer.LoadedMedia:
            self.mediaLoaded.emit()

    @Slot(int, str)
    def _on_error_occurred(self, error: int, error_string: str) -> None:
        """Handle player errors"""
        self.errorOccurred.emit(f"Player error: {error_string}")