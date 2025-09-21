"""
File management utilities for video frame capture application.
"""

import os
import shutil
import tempfile
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import json
from datetime import datetime
from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QPixmap


class FileManager:
    """Manages file operations for the application"""

    # Supported video formats
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4': 'MP4 Video',
        '.avi': 'AVI Video',
        '.mov': 'QuickTime Video',
        '.mkv': 'Matroska Video',
        '.wmv': 'Windows Media Video',
        '.m4v': 'MPEG-4 Video',
        '.flv': 'Flash Video',
        '.webm': 'WebM Video',
    }

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = {
        '.png': 'PNG Image',
        '.jpg': 'JPEG Image',
        '.jpeg': 'JPEG Image',
        '.bmp': 'Bitmap Image',
        '.tiff': 'TIFF Image',
        '.gif': 'GIF Image',
    }

    @staticmethod
    def get_app_data_directory() -> Path:
        """Get application data directory"""
        app_data = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        app_dir = Path(app_data) / "VideoFrameCapture"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    @staticmethod
    def get_temp_directory() -> Path:
        """Get temporary directory for the application"""
        temp_dir = Path(tempfile.gettempdir()) / "VideoFrameCapture"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    @staticmethod
    def get_documents_directory() -> Path:
        """Get user documents directory"""
        return Path(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation))

    @staticmethod
    def get_downloads_directory() -> Path:
        """Get user downloads directory"""
        return Path(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation))

    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """Check if file is a supported video format"""
        return Path(file_path).suffix.lower() in FileManager.SUPPORTED_VIDEO_FORMATS

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """Check if file is a supported image format"""
        return Path(file_path).suffix.lower() in FileManager.SUPPORTED_IMAGE_FORMATS

    @staticmethod
    def get_video_format_filter() -> str:
        """Get file dialog filter for video files"""
        extensions = list(FileManager.SUPPORTED_VIDEO_FORMATS.keys())
        filter_parts = []

        # All supported videos
        all_extensions = " ".join(f"*{ext}" for ext in extensions)
        filter_parts.append(f"Video Files ({all_extensions})")

        # Individual formats
        for ext, desc in FileManager.SUPPORTED_VIDEO_FORMATS.items():
            filter_parts.append(f"{desc} (*{ext})")

        # All files
        filter_parts.append("All Files (*)")

        return ";;".join(filter_parts)

    @staticmethod
    def get_image_format_filter() -> str:
        """Get file dialog filter for image files"""
        extensions = list(FileManager.SUPPORTED_IMAGE_FORMATS.keys())
        filter_parts = []

        # All supported images
        all_extensions = " ".join(f"*{ext}" for ext in extensions)
        filter_parts.append(f"Image Files ({all_extensions})")

        # Individual formats
        for ext, desc in FileManager.SUPPORTED_IMAGE_FORMATS.items():
            filter_parts.append(f"{desc} (*{ext})")

        return ";;".join(filter_parts)

    @staticmethod
    def get_export_format_filter() -> str:
        """Get file dialog filter for export files"""
        return "ZIP Archive (*.zip);;All Files (*)"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext

        return filename

    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """Ensure directory exists, create if necessary"""
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        try:
            path = Path(file_path)
            stat = path.stat()

            return {
                "name": path.name,
                "stem": path.stem,
                "suffix": path.suffix,
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "exists": path.exists(),
                "parent": str(path.parent),
                "absolute_path": str(path.absolute()),
            }
        except Exception:
            return {
                "name": "",
                "stem": "",
                "suffix": "",
                "size_bytes": 0,
                "size_mb": 0,
                "modified_time": None,
                "created_time": None,
                "is_file": False,
                "is_directory": False,
                "exists": False,
                "parent": "",
                "absolute_path": file_path,
            }

    @staticmethod
    def copy_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """Copy file from source to destination"""
        try:
            dest_path = Path(destination)

            if dest_path.exists() and not overwrite:
                return False

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source, destination)
            return True
        except Exception:
            return False

    @staticmethod
    def move_file(source: str, destination: str, overwrite: bool = False) -> bool:
        """Move file from source to destination"""
        try:
            dest_path = Path(destination)

            if dest_path.exists() and not overwrite:
                return False

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(source, destination)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file"""
        try:
            Path(file_path).unlink()
            return True
        except Exception:
            return False

    @staticmethod
    def clean_temp_directory() -> None:
        """Clean up temporary files"""
        try:
            temp_dir = FileManager.get_temp_directory()
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    @staticmethod
    def save_pixmap(pixmap: QPixmap, file_path: str, format: str = "PNG", quality: int = 95) -> bool:
        """Save QPixmap to file"""
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Save pixmap
            format_upper = format.upper()
            if format_upper == "JPG":
                format_upper = "JPEG"

            return pixmap.save(file_path, format_upper, quality)
        except Exception:
            return False

    @staticmethod
    def load_pixmap(file_path: str) -> Optional[QPixmap]:
        """Load QPixmap from file"""
        try:
            pixmap = QPixmap(file_path)
            return pixmap if not pixmap.isNull() else None
        except Exception:
            return None


class ProjectFileManager:
    """Manages project file operations"""

    PROJECT_EXTENSION = ".vfc"
    PROJECT_VERSION = "1.0"

    @staticmethod
    def save_project(project_data: Dict[str, Any], file_path: str) -> bool:
        """Save project data to file"""
        try:
            # Ensure .vfc extension
            if not file_path.endswith(ProjectFileManager.PROJECT_EXTENSION):
                file_path += ProjectFileManager.PROJECT_EXTENSION

            # Add metadata
            project_data["_metadata"] = {
                "version": ProjectFileManager.PROJECT_VERSION,
                "saved_at": datetime.now().isoformat(),
                "application": "Video Frame Capture",
            }

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    @staticmethod
    def load_project(file_path: str) -> Optional[Dict[str, Any]]:
        """Load project data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # Validate project file
            if not ProjectFileManager._validate_project_data(project_data):
                return None

            return project_data
        except Exception:
            return None

    @staticmethod
    def _validate_project_data(project_data: Dict[str, Any]) -> bool:
        """Validate project data structure"""
        try:
            # Check for required fields
            required_fields = ["name", "video_path", "captured_frames"]
            for field in required_fields:
                if field not in project_data:
                    return False

            # Check metadata version if present
            metadata = project_data.get("_metadata", {})
            version = metadata.get("version")
            if version and version != ProjectFileManager.PROJECT_VERSION:
                # Could handle version migration here
                pass

            return True
        except Exception:
            return False

    @staticmethod
    def get_project_filter() -> str:
        """Get file dialog filter for project files"""
        return f"Video Frame Capture Projects (*{ProjectFileManager.PROJECT_EXTENSION});;All Files (*)"

    @staticmethod
    def create_backup(project_file_path: str) -> Optional[str]:
        """Create backup of project file"""
        try:
            path = Path(project_file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.stem}_backup_{timestamp}{path.suffix}"
            backup_path = path.parent / backup_name

            shutil.copy2(project_file_path, backup_path)
            return str(backup_path)
        except Exception:
            return None


class ExportManager:
    """Manages export operations"""

    @staticmethod
    def generate_export_filename(
        base_name: str = "frames_export",
        timestamp: Optional[datetime] = None
    ) -> str:
        """Generate export filename with timestamp"""
        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp_str}.zip"

    @staticmethod
    def get_available_export_path(directory: str, filename: str) -> str:
        """Get available export path, adding suffix if file exists"""
        base_path = Path(directory) / filename

        if not base_path.exists():
            return str(base_path)

        # File exists, add suffix
        stem = base_path.stem
        suffix = base_path.suffix
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = base_path.parent / new_name
            if not new_path.exists():
                return str(new_path)
            counter += 1

    @staticmethod
    def estimate_export_size(frame_count: int, average_frame_size: int) -> Dict[str, Any]:
        """Estimate export file size"""
        # Rough estimation including ZIP compression (~20% reduction)
        uncompressed_size = frame_count * average_frame_size
        compressed_size = int(uncompressed_size * 0.8)  # Assume 20% compression

        return {
            "frame_count": frame_count,
            "uncompressed_bytes": uncompressed_size,
            "compressed_bytes": compressed_size,
            "uncompressed_mb": uncompressed_size / (1024 * 1024),
            "compressed_mb": compressed_size / (1024 * 1024),
            "compression_ratio": 0.8,
        }


class PathUtils:
    """Path manipulation utilities"""

    @staticmethod
    def make_relative_path(full_path: str, base_path: str) -> str:
        """Make path relative to base path"""
        try:
            return str(Path(full_path).relative_to(Path(base_path)))
        except ValueError:
            return full_path

    @staticmethod
    def resolve_relative_path(relative_path: str, base_path: str) -> str:
        """Resolve relative path against base path"""
        return str(Path(base_path) / relative_path)

    @staticmethod
    def get_common_path(paths: List[str]) -> str:
        """Get common parent path for list of paths"""
        if not paths:
            return ""

        try:
            return str(Path(os.path.commonpath(paths)))
        except ValueError:
            return ""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize path separators for current platform"""
        return str(Path(path).resolve())

    @staticmethod
    def split_path_components(path: str) -> List[str]:
        """Split path into components"""
        return list(Path(path).parts)

    @staticmethod
    def get_unique_filename(directory: str, basename: str, extension: str) -> str:
        """Get unique filename in directory"""
        counter = 0
        while True:
            if counter == 0:
                filename = f"{basename}{extension}"
            else:
                filename = f"{basename}_{counter}{extension}"

            full_path = Path(directory) / filename
            if not full_path.exists():
                return filename
            counter += 1