"""
Timeline controller for precise video navigation and frame management.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from .video_player import VideoPlayer


class TimelineController(QObject):
    """Manages video timeline navigation and frame tracking"""

    # Signals
    positionChanged = Signal('qint64')  # Current position in milliseconds
    durationChanged = Signal('qint64')  # Video duration in milliseconds
    frameRateChanged = Signal(float)  # Video frame rate
    timelineClicked = Signal(int)  # Position clicked on timeline
    bookmarkAdded = Signal(int)  # Bookmark position added
    bookmarkRemoved = Signal(int)  # Bookmark position removed

    def __init__(self, video_player: VideoPlayer, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.video_player = video_player
        self._duration = 0
        self._current_position = 0
        self._frame_rate = 30.0  # Default frame rate
        self._bookmarks: List[int] = []  # Bookmarked positions
        self._is_seeking = False

        # Timer for smooth position updates
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.setInterval(33)  # ~30 FPS updates

        self._connect_video_player()

    def _connect_video_player(self) -> None:
        """Connect to video player signals"""
        self.video_player.positionChanged.connect(self._on_position_changed)
        self.video_player.durationChanged.connect(self._on_duration_changed)
        self.video_player.stateChanged.connect(self._on_state_changed)

    @Slot('qint64')
    def _on_position_changed(self, position: int) -> None:
        """Handle position changes from video player"""
        if not self._is_seeking:
            self._current_position = position
            self.positionChanged.emit(position)

    @Slot('qint64')
    def _on_duration_changed(self, duration: int) -> None:
        """Handle duration changes from video player"""
        self._duration = duration
        self.durationChanged.emit(duration)

    @Slot(int)
    def _on_state_changed(self, state: int) -> None:
        """Handle playback state changes"""
        if state == 1:  # Playing
            self.position_timer.start()
        else:
            self.position_timer.stop()

    @Slot()
    def _update_position(self) -> None:
        """Update position from video player"""
        if not self._is_seeking:
            position = self.video_player.get_current_position()
            if position != self._current_position:
                self._current_position = position
                self.positionChanged.emit(position)

    @Slot(int)
    def seek_to_position(self, position: int) -> None:
        """Seek to specific position"""
        if 0 <= position <= self._duration:
            self._is_seeking = True
            self._current_position = position
            self.video_player.seek(position)
            self.positionChanged.emit(position)

            # Reset seeking flag after a short delay
            QTimer.singleShot(100, self._reset_seeking_flag)

    def _reset_seeking_flag(self) -> None:
        """Reset the seeking flag"""
        self._is_seeking = False

    @Slot(float)
    def seek_to_percentage(self, percentage: float) -> None:
        """Seek to position by percentage (0.0 to 1.0)"""
        if self._duration > 0:
            position = int(self._duration * max(0.0, min(1.0, percentage)))
            self.seek_to_position(position)

    @Slot(int)
    def seek_relative(self, milliseconds: int) -> None:
        """Seek relative to current position"""
        new_position = self._current_position + milliseconds
        self.seek_to_position(new_position)

    @Slot()
    def seek_to_next_frame(self) -> None:
        """Seek to next frame"""
        if self._frame_rate > 0:
            frame_duration = int(1000 / self._frame_rate)
            self.seek_relative(frame_duration)

    @Slot()
    def seek_to_previous_frame(self) -> None:
        """Seek to previous frame"""
        if self._frame_rate > 0:
            frame_duration = int(1000 / self._frame_rate)
            self.seek_relative(-frame_duration)

    @Slot(int)
    def add_bookmark(self, position: Optional[int] = None) -> None:
        """Add bookmark at position (current position if None)"""
        if position is None:
            position = self._current_position

        if position not in self._bookmarks:
            self._bookmarks.append(position)
            self._bookmarks.sort()
            self.bookmarkAdded.emit(position)

    @Slot(int)
    def remove_bookmark(self, position: int) -> None:
        """Remove bookmark at position"""
        if position in self._bookmarks:
            self._bookmarks.remove(position)
            self.bookmarkRemoved.emit(position)

    @Slot()
    def seek_to_next_bookmark(self) -> None:
        """Seek to next bookmark"""
        next_bookmarks = [b for b in self._bookmarks if b > self._current_position]
        if next_bookmarks:
            self.seek_to_position(min(next_bookmarks))

    @Slot()
    def seek_to_previous_bookmark(self) -> None:
        """Seek to previous bookmark"""
        prev_bookmarks = [b for b in self._bookmarks if b < self._current_position]
        if prev_bookmarks:
            self.seek_to_position(max(prev_bookmarks))

    def get_current_position(self) -> int:
        """Get current timeline position in milliseconds"""
        return self._current_position

    def get_duration(self) -> int:
        """Get video duration in milliseconds"""
        return self._duration

    def get_current_percentage(self) -> float:
        """Get current position as percentage (0.0 to 1.0)"""
        if self._duration > 0:
            return self._current_position / self._duration
        return 0.0

    def get_bookmarks(self) -> List[int]:
        """Get list of bookmark positions"""
        return self._bookmarks.copy()

    def set_frame_rate(self, fps: float) -> None:
        """Set video frame rate for frame-accurate seeking"""
        self._frame_rate = fps
        self.frameRateChanged.emit(fps)

    def get_frame_rate(self) -> float:
        """Get current frame rate"""
        return self._frame_rate

    def get_current_frame_number(self) -> int:
        """Get current frame number based on position and frame rate"""
        if self._frame_rate > 0:
            return int((self._current_position / 1000.0) * self._frame_rate)
        return 0

    def get_total_frames(self) -> int:
        """Get total number of frames in video"""
        if self._frame_rate > 0 and self._duration > 0:
            return int((self._duration / 1000.0) * self._frame_rate)
        return 0

    def seek_to_frame_number(self, frame_number: int) -> None:
        """Seek to specific frame number"""
        if self._frame_rate > 0:
            position = int((frame_number / self._frame_rate) * 1000)
            self.seek_to_position(position)

    def format_time(self, milliseconds: int) -> str:
        """Format time in milliseconds to MM:SS.mmm"""
        total_seconds = milliseconds / 1000.0
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        ms = int((total_seconds % 1) * 1000)
        return f"{minutes:02d}:{seconds:02d}.{ms:03d}"

    def get_timeline_info(self) -> Dict[str, Any]:
        """Get comprehensive timeline information"""
        return {
            "current_position": self._current_position,
            "duration": self._duration,
            "percentage": self.get_current_percentage(),
            "frame_rate": self._frame_rate,
            "current_frame": self.get_current_frame_number(),
            "total_frames": self.get_total_frames(),
            "bookmarks": self._bookmarks.copy(),
            "formatted_time": self.format_time(self._current_position),
            "formatted_duration": self.format_time(self._duration),
        }