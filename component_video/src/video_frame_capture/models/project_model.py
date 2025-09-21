"""
Project state management model.
"""

from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal, QSettings
import json
import os
from datetime import datetime


class ProjectModel(QObject):
    """Manages project state and settings"""

    # Signals
    projectChanged = Signal()  # Project data changed
    videoLoaded = Signal(str)  # Video file loaded
    settingsChanged = Signal(dict)  # Settings changed

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        # Project data
        self._current_video_path: Optional[str] = None
        self._project_name: str = "Untitled Project"
        self._project_directory: Optional[str] = None
        self._creation_time: Optional[datetime] = None
        self._last_modified: Optional[datetime] = None

        # Settings
        self._settings = QSettings("VideoFrameCapture", "Project")
        self._user_preferences = self._load_preferences()

        # Captured frames metadata
        self._captured_frames: List[Dict[str, Any]] = []

        # Video metadata
        self._video_metadata: Dict[str, Any] = {}

    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from settings"""
        default_prefs = {
            "thumbnail_size": (160, 120),
            "export_format": "PNG",
            "export_quality": 95,
            "auto_save_project": True,
            "remember_window_state": True,
            "default_export_directory": os.path.expanduser("~/Downloads"),
            "frame_naming_pattern": "frame_{timestamp}ms",
            "max_cache_size_mb": 500,
            "enable_hardware_acceleration": True,
        }

        preferences = {}
        for key, default_value in default_prefs.items():
            value = self._settings.value(f"preferences/{key}", default_value)
            preferences[key] = value

        return preferences

    def save_preferences(self) -> None:
        """Save current preferences to settings"""
        for key, value in self._user_preferences.items():
            self._settings.setValue(f"preferences/{key}", value)

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference value"""
        return self._user_preferences.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        """Set user preference value"""
        if self._user_preferences.get(key) != value:
            self._user_preferences[key] = value
            self.save_preferences()
            self.settingsChanged.emit(self._user_preferences.copy())

    def create_new_project(self, project_name: str, project_directory: str) -> None:
        """Create a new project"""
        self._project_name = project_name
        self._project_directory = project_directory
        self._creation_time = datetime.now()
        self._last_modified = self._creation_time
        self._current_video_path = None
        self._captured_frames.clear()
        self._video_metadata.clear()

        # Create project directory if it doesn't exist
        os.makedirs(project_directory, exist_ok=True)

        self.projectChanged.emit()

    def load_project(self, project_file_path: str) -> bool:
        """Load project from file"""
        try:
            with open(project_file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            self._project_name = project_data.get("name", "Untitled Project")
            self._project_directory = os.path.dirname(project_file_path)
            self._current_video_path = project_data.get("video_path")
            self._captured_frames = project_data.get("captured_frames", [])
            self._video_metadata = project_data.get("video_metadata", {})

            # Parse timestamps
            creation_str = project_data.get("creation_time")
            if creation_str:
                self._creation_time = datetime.fromisoformat(creation_str)

            modified_str = project_data.get("last_modified")
            if modified_str:
                self._last_modified = datetime.fromisoformat(modified_str)

            self.projectChanged.emit()
            return True

        except Exception as e:
            print(f"Failed to load project: {e}")
            return False

    def save_project(self, project_file_path: Optional[str] = None) -> bool:
        """Save project to file"""
        if not project_file_path and self._project_directory:
            project_file_path = os.path.join(
                self._project_directory, f"{self._project_name}.vfc"
            )

        if not project_file_path:
            return False

        try:
            self._last_modified = datetime.now()

            project_data = {
                "name": self._project_name,
                "video_path": self._current_video_path,
                "captured_frames": self._captured_frames,
                "video_metadata": self._video_metadata,
                "creation_time": self._creation_time.isoformat() if self._creation_time else None,
                "last_modified": self._last_modified.isoformat(),
                "version": "1.0",
            }

            with open(project_file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Failed to save project: {e}")
            return False

    def set_video_path(self, video_path: str) -> None:
        """Set current video file path"""
        if self._current_video_path != video_path:
            self._current_video_path = video_path
            self._last_modified = datetime.now()
            self.videoLoaded.emit(video_path)
            self.projectChanged.emit()

    def get_video_path(self) -> Optional[str]:
        """Get current video file path"""
        return self._current_video_path

    def set_video_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set video metadata"""
        self._video_metadata = metadata.copy()
        self._last_modified = datetime.now()
        self.projectChanged.emit()

    def get_video_metadata(self) -> Dict[str, Any]:
        """Get video metadata"""
        return self._video_metadata.copy()

    def add_captured_frame(self, frame_data: Dict[str, Any]) -> None:
        """Add captured frame metadata"""
        frame_entry = {
            "timestamp": frame_data.get("timestamp", 0),
            "file_path": frame_data.get("file_path", ""),
            "capture_time": datetime.now().isoformat(),
            "width": frame_data.get("width", 0),
            "height": frame_data.get("height", 0),
            "size_bytes": frame_data.get("size_bytes", 0),
        }

        self._captured_frames.append(frame_entry)
        self._last_modified = datetime.now()
        self.projectChanged.emit()

    def remove_captured_frame(self, timestamp: int) -> bool:
        """Remove captured frame by timestamp"""
        for i, frame in enumerate(self._captured_frames):
            if frame.get("timestamp") == timestamp:
                del self._captured_frames[i]
                self._last_modified = datetime.now()
                self.projectChanged.emit()
                return True
        return False

    def clear_captured_frames(self) -> None:
        """Clear all captured frames"""
        if self._captured_frames:
            self._captured_frames.clear()
            self._last_modified = datetime.now()
            self.projectChanged.emit()

    def get_captured_frames(self) -> List[Dict[str, Any]]:
        """Get captured frames metadata"""
        return self._captured_frames.copy()

    def get_project_info(self) -> Dict[str, Any]:
        """Get comprehensive project information"""
        return {
            "name": self._project_name,
            "directory": self._project_directory,
            "video_path": self._current_video_path,
            "creation_time": self._creation_time.isoformat() if self._creation_time else None,
            "last_modified": self._last_modified.isoformat() if self._last_modified else None,
            "frame_count": len(self._captured_frames),
            "video_metadata": self._video_metadata.copy(),
            "has_unsaved_changes": self._has_unsaved_changes(),
        }

    def _has_unsaved_changes(self) -> bool:
        """Check if project has unsaved changes"""
        # Simple check based on modification time
        # In a real implementation, you might track changes more precisely
        return True  # Simplified for now

    def get_project_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        if not self._captured_frames:
            return {
                "frame_count": 0,
                "total_size_bytes": 0,
                "timestamp_range": (0, 0),
                "average_frame_size": 0,
            }

        timestamps = [f.get("timestamp", 0) for f in self._captured_frames]
        sizes = [f.get("size_bytes", 0) for f in self._captured_frames]

        return {
            "frame_count": len(self._captured_frames),
            "total_size_bytes": sum(sizes),
            "timestamp_range": (min(timestamps), max(timestamps)) if timestamps else (0, 0),
            "average_frame_size": sum(sizes) / len(sizes) if sizes else 0,
            "earliest_capture": min(
                (f.get("capture_time", "") for f in self._captured_frames), default=""
            ),
            "latest_capture": max(
                (f.get("capture_time", "") for f in self._captured_frames), default=""
            ),
        }

    def export_project_summary(self) -> str:
        """Export project summary as text"""
        info = self.get_project_info()
        stats = self.get_project_statistics()

        summary = f"""
Project Summary
===============

Project Name: {info['name']}
Directory: {info['directory'] or 'Not set'}
Video File: {info['video_path'] or 'Not loaded'}
Created: {info['creation_time'] or 'Unknown'}
Last Modified: {info['last_modified'] or 'Unknown'}

Statistics
----------
Captured Frames: {stats['frame_count']}
Total Size: {stats['total_size_bytes'] / (1024*1024):.2f} MB
Time Range: {stats['timestamp_range'][0]}ms - {stats['timestamp_range'][1]}ms
Average Frame Size: {stats['average_frame_size'] / 1024:.2f} KB

Video Information
-----------------
"""

        for key, value in self._video_metadata.items():
            summary += f"{key}: {value}\n"

        return summary.strip()

    def set_project_name(self, name: str) -> None:
        """Set project name"""
        if self._project_name != name:
            self._project_name = name
            self._last_modified = datetime.now()
            self.projectChanged.emit()

    def get_project_name(self) -> str:
        """Get project name"""
        return self._project_name

    def set_project_directory(self, directory: str) -> None:
        """Set project directory"""
        if self._project_directory != directory:
            self._project_directory = directory
            self._last_modified = datetime.now()
            self.projectChanged.emit()

    def get_project_directory(self) -> Optional[str]:
        """Get project directory"""
        return self._project_directory