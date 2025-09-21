"""
Model for managing captured frame data and metadata.
"""

from typing import List, Dict, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap
from datetime import datetime
import hashlib


class FrameData:
    """Container for frame data and metadata"""

    def __init__(
        self,
        pixmap: QPixmap,
        timestamp: int,
        video_path: str,
        capture_time: Optional[datetime] = None,
    ):
        self.pixmap = pixmap
        self.timestamp = timestamp
        self.video_path = video_path
        self.capture_time = capture_time or datetime.now()
        self._hash = None

    @property
    def width(self) -> int:
        """Get frame width"""
        return self.pixmap.width()

    @property
    def height(self) -> int:
        """Get frame height"""
        return self.pixmap.height()

    @property
    def size_bytes(self) -> int:
        """Estimate frame size in bytes"""
        # Rough estimation: width * height * 4 (RGBA)
        return self.width * self.height * 4

    @property
    def hash(self) -> str:
        """Get frame hash for deduplication"""
        if self._hash is None:
            # Create hash from timestamp and video path
            hasher = hashlib.md5()
            hasher.update(f"{self.timestamp}_{self.video_path}".encode())
            self._hash = hasher.hexdigest()
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "timestamp": self.timestamp,
            "video_path": self.video_path,
            "capture_time": self.capture_time.isoformat(),
            "width": self.width,
            "height": self.height,
            "size_bytes": self.size_bytes,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], pixmap: QPixmap) -> "FrameData":
        """Create from dictionary representation"""
        capture_time = datetime.fromisoformat(data["capture_time"])
        return cls(
            pixmap=pixmap,
            timestamp=data["timestamp"],
            video_path=data["video_path"],
            capture_time=capture_time,
        )


class CaptureModel(QObject):
    """Model for managing captured frame data"""

    # Signals
    frameAdded = Signal(object)  # FrameData added
    frameRemoved = Signal(str)  # Frame hash removed
    framesCleared = Signal()  # All frames cleared
    selectionChanged = Signal(list)  # Selected frame hashes
    statisticsChanged = Signal(dict)  # Statistics updated

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._frames: Dict[str, FrameData] = {}  # hash -> FrameData
        self._selected_hashes: set = set()
        self._frame_order: List[str] = []  # Maintains insertion order

    def add_frame(self, frame_data: FrameData) -> bool:
        """Add a captured frame"""
        frame_hash = frame_data.hash

        # Check for duplicates
        if frame_hash in self._frames:
            return False  # Frame already exists

        self._frames[frame_hash] = frame_data
        self._frame_order.append(frame_hash)

        self.frameAdded.emit(frame_data)
        self._update_statistics()
        return True

    def remove_frame(self, frame_hash: str) -> bool:
        """Remove a frame by hash"""
        if frame_hash in self._frames:
            del self._frames[frame_hash]
            self._frame_order.remove(frame_hash)
            self._selected_hashes.discard(frame_hash)

            self.frameRemoved.emit(frame_hash)
            self._update_statistics()
            self._update_selection()
            return True
        return False

    def remove_frame_by_timestamp(self, timestamp: int, video_path: str) -> bool:
        """Remove frame by timestamp and video path"""
        for frame_hash, frame_data in self._frames.items():
            if frame_data.timestamp == timestamp and frame_data.video_path == video_path:
                return self.remove_frame(frame_hash)
        return False

    def clear_all_frames(self) -> None:
        """Clear all captured frames"""
        if self._frames:
            self._frames.clear()
            self._frame_order.clear()
            self._selected_hashes.clear()

            self.framesCleared.emit()
            self._update_statistics()
            self._update_selection()

    def get_frame(self, frame_hash: str) -> Optional[FrameData]:
        """Get frame data by hash"""
        return self._frames.get(frame_hash)

    def get_all_frames(self) -> List[FrameData]:
        """Get all frame data in insertion order"""
        return [self._frames[hash] for hash in self._frame_order if hash in self._frames]

    def get_selected_frames(self) -> List[FrameData]:
        """Get selected frame data"""
        return [
            self._frames[hash]
            for hash in self._selected_hashes
            if hash in self._frames
        ]

    def get_frame_count(self) -> int:
        """Get total number of frames"""
        return len(self._frames)

    def get_selected_count(self) -> int:
        """Get number of selected frames"""
        return len(self._selected_hashes)

    def select_frame(self, frame_hash: str) -> bool:
        """Select a frame"""
        if frame_hash in self._frames:
            self._selected_hashes.add(frame_hash)
            self._update_selection()
            return True
        return False

    def deselect_frame(self, frame_hash: str) -> bool:
        """Deselect a frame"""
        if frame_hash in self._selected_hashes:
            self._selected_hashes.remove(frame_hash)
            self._update_selection()
            return True
        return False

    def toggle_frame_selection(self, frame_hash: str) -> bool:
        """Toggle frame selection state"""
        if frame_hash in self._selected_hashes:
            return self.deselect_frame(frame_hash)
        else:
            return self.select_frame(frame_hash)

    def select_all_frames(self) -> None:
        """Select all frames"""
        self._selected_hashes = set(self._frames.keys())
        self._update_selection()

    def deselect_all_frames(self) -> None:
        """Deselect all frames"""
        if self._selected_hashes:
            self._selected_hashes.clear()
            self._update_selection()

    def is_frame_selected(self, frame_hash: str) -> bool:
        """Check if frame is selected"""
        return frame_hash in self._selected_hashes

    def get_frames_by_video(self, video_path: str) -> List[FrameData]:
        """Get all frames from specific video"""
        return [
            frame for frame in self.get_all_frames()
            if frame.video_path == video_path
        ]

    def get_frames_in_time_range(
        self, start_time: int, end_time: int, video_path: Optional[str] = None
    ) -> List[FrameData]:
        """Get frames within time range"""
        frames = []
        for frame in self.get_all_frames():
            if start_time <= frame.timestamp <= end_time:
                if video_path is None or frame.video_path == video_path:
                    frames.append(frame)
        return frames

    def find_nearest_frame(self, timestamp: int, video_path: str) -> Optional[FrameData]:
        """Find frame closest to given timestamp"""
        video_frames = self.get_frames_by_video(video_path)
        if not video_frames:
            return None

        # Find frame with minimum time difference
        nearest_frame = min(
            video_frames,
            key=lambda f: abs(f.timestamp - timestamp)
        )
        return nearest_frame

    def get_statistics(self) -> Dict[str, Any]:
        """Get capture statistics"""
        if not self._frames:
            return {
                "total_frames": 0,
                "selected_frames": 0,
                "total_size_bytes": 0,
                "average_size_bytes": 0,
                "unique_videos": 0,
                "time_range": (0, 0),
                "capture_time_range": ("", ""),
            }

        frames = list(self._frames.values())
        sizes = [frame.size_bytes for frame in frames]
        timestamps = [frame.timestamp for frame in frames]
        capture_times = [frame.capture_time for frame in frames]

        unique_videos = len(set(frame.video_path for frame in frames))

        return {
            "total_frames": len(self._frames),
            "selected_frames": len(self._selected_hashes),
            "total_size_bytes": sum(sizes),
            "average_size_bytes": sum(sizes) / len(sizes) if sizes else 0,
            "unique_videos": unique_videos,
            "time_range": (min(timestamps), max(timestamps)) if timestamps else (0, 0),
            "capture_time_range": (
                min(capture_times).isoformat() if capture_times else "",
                max(capture_times).isoformat() if capture_times else "",
            ),
        }

    def export_metadata(self) -> List[Dict[str, Any]]:
        """Export all frame metadata"""
        return [frame.to_dict() for frame in self.get_all_frames()]

    def export_selected_metadata(self) -> List[Dict[str, Any]]:
        """Export selected frame metadata"""
        return [frame.to_dict() for frame in self.get_selected_frames()]

    def get_video_statistics(self, video_path: str) -> Dict[str, Any]:
        """Get statistics for specific video"""
        video_frames = self.get_frames_by_video(video_path)

        if not video_frames:
            return {
                "frame_count": 0,
                "total_size_bytes": 0,
                "time_range": (0, 0),
            }

        timestamps = [frame.timestamp for frame in video_frames]
        sizes = [frame.size_bytes for frame in video_frames]

        return {
            "frame_count": len(video_frames),
            "total_size_bytes": sum(sizes),
            "time_range": (min(timestamps), max(timestamps)),
            "average_size_bytes": sum(sizes) / len(sizes),
        }

    def _update_selection(self) -> None:
        """Emit selection changed signal"""
        self.selectionChanged.emit(list(self._selected_hashes))

    def _update_statistics(self) -> None:
        """Emit statistics changed signal"""
        self.statisticsChanged.emit(self.get_statistics())

    def sort_frames_by_timestamp(self, ascending: bool = True) -> None:
        """Sort frames by timestamp"""
        self._frame_order.sort(
            key=lambda h: self._frames[h].timestamp if h in self._frames else 0,
            reverse=not ascending
        )

    def sort_frames_by_capture_time(self, ascending: bool = True) -> None:
        """Sort frames by capture time"""
        self._frame_order.sort(
            key=lambda h: self._frames[h].capture_time if h in self._frames else datetime.min,
            reverse=not ascending
        )

    def group_frames_by_video(self) -> Dict[str, List[FrameData]]:
        """Group frames by video file"""
        groups = {}
        for frame in self.get_all_frames():
            video_path = frame.video_path
            if video_path not in groups:
                groups[video_path] = []
            groups[video_path].append(frame)
        return groups