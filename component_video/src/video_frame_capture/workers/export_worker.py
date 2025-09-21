"""
Background worker for exporting frames to ZIP archives.
"""

import os
import zipfile
import tempfile
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, QRunnable, Signal
from PySide6.QtGui import QPixmap
import time
from datetime import datetime


class ExportSignals(QObject):
    """Signals for export worker"""

    progress = Signal(int, str)  # percentage, status_message
    fileProcessed = Signal(str, int)  # filename, size_bytes
    error = Signal(str)  # error_message
    finished = Signal(str)  # export_file_path


class ExportWorker(QRunnable):
    """Worker for exporting captured frames to ZIP file"""

    def __init__(
        self,
        frame_data_list: List[Dict[str, Any]],
        export_file_path: str,
        export_options: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.frame_data_list = frame_data_list
        self.export_file_path = export_file_path
        self.export_options = export_options or {}
        self.signals = ExportSignals()
        self._is_cancelled = False

        # Default export options
        self.image_format = self.export_options.get("format", "PNG")
        self.image_quality = self.export_options.get("quality", 95)
        self.include_metadata = self.export_options.get("include_metadata", True)
        self.compression_level = self.export_options.get("compression_level", 6)
        self.filename_pattern = self.export_options.get(
            "filename_pattern", "frame_{timestamp:06d}ms"
        )

    def run(self) -> None:
        """Export frames to ZIP file"""
        try:
            self.signals.progress.emit(0, "Starting export process...")

            if not self.frame_data_list:
                self.signals.error.emit("No frames to export")
                return

            # Ensure export directory exists
            export_dir = os.path.dirname(self.export_file_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)

            total_frames = len(self.frame_data_list)
            processed_files = []

            # Create ZIP file
            with zipfile.ZipFile(
                self.export_file_path, 'w',
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=self.compression_level
            ) as zip_file:

                # Export each frame
                for i, frame_data in enumerate(self.frame_data_list):
                    if self._is_cancelled:
                        break

                    progress = int((i / total_frames) * 85)  # Reserve 15% for metadata
                    self.signals.progress.emit(
                        progress, f"Exporting frame {i+1} of {total_frames}"
                    )

                    # Process individual frame
                    success, file_info = self._export_single_frame(frame_data, zip_file, i)
                    if success and file_info:
                        processed_files.append(file_info)
                        self.signals.fileProcessed.emit(file_info['filename'], file_info['size'])

                # Add metadata if requested
                if self.include_metadata and not self._is_cancelled:
                    self.signals.progress.emit(85, "Generating metadata...")
                    self._add_metadata_to_zip(zip_file, processed_files)

                self.signals.progress.emit(95, "Finalizing ZIP file...")

            if not self._is_cancelled:
                self.signals.progress.emit(100, "Export completed successfully")
                self.signals.finished.emit(self.export_file_path)

        except Exception as e:
            # Clean up partial file if export failed
            if os.path.exists(self.export_file_path):
                try:
                    os.remove(self.export_file_path)
                except:
                    pass
            self.signals.error.emit(f"Export failed: {str(e)}")

    def cancel(self) -> None:
        """Cancel the export process"""
        self._is_cancelled = True

    def _export_single_frame(
        self, frame_data: Dict[str, Any], zip_file: zipfile.ZipFile, index: int
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Export a single frame to the ZIP file"""
        try:
            pixmap = frame_data.get("pixmap")
            timestamp = frame_data.get("timestamp", 0)

            if not pixmap or pixmap.isNull():
                return False, None

            # Generate filename
            filename = self._generate_filename(timestamp, index)

            # Convert pixmap to bytes
            image_bytes = self._pixmap_to_bytes(pixmap)
            if not image_bytes:
                return False, None

            # Add to ZIP
            zip_file.writestr(filename, image_bytes)

            # Return file info
            file_info = {
                "filename": filename,
                "timestamp": timestamp,
                "size": len(image_bytes),
                "width": pixmap.width(),
                "height": pixmap.height(),
                "format": self.image_format,
                "original_path": frame_data.get("file_path", ""),
            }

            return True, file_info

        except Exception as e:
            self.signals.error.emit(f"Failed to export frame at {timestamp}ms: {str(e)}")
            return False, None

    def _generate_filename(self, timestamp: int, index: int) -> str:
        """Generate filename for the frame"""
        try:
            # Use the filename pattern
            filename = self.filename_pattern.format(
                timestamp=timestamp,
                index=index,
                format=self.image_format.lower()
            )

            # Ensure proper extension
            if not filename.lower().endswith(f".{self.image_format.lower()}"):
                filename += f".{self.image_format.lower()}"

            # Sanitize filename
            filename = self._sanitize_filename(filename)

            return filename

        except Exception:
            # Fallback to simple naming
            return f"frame_{timestamp:06d}ms.{self.image_format.lower()}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext

        return filename

    def _pixmap_to_bytes(self, pixmap: QPixmap) -> Optional[bytes]:
        """Convert QPixmap to bytes in specified format"""
        try:
            from PySide6.QtCore import QBuffer, QIODevice

            # Create a buffer to store the image data
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)

            # Save pixmap to buffer
            format_str = self.image_format.upper()
            if format_str == "JPG":
                format_str = "JPEG"

            success = pixmap.save(buffer, format_str, self.image_quality)
            if not success:
                return None

            # Get bytes data
            image_bytes = buffer.data().data()
            buffer.close()

            return image_bytes

        except Exception as e:
            self.signals.error.emit(f"Failed to convert pixmap to bytes: {str(e)}")
            return None

    def _add_metadata_to_zip(
        self, zip_file: zipfile.ZipFile, file_info_list: List[Dict[str, Any]]
    ) -> None:
        """Add metadata file to ZIP archive"""
        try:
            metadata = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_frames": len(file_info_list),
                    "format": self.image_format,
                    "quality": self.image_quality,
                    "compression_level": self.compression_level,
                },
                "frames": file_info_list,
                "statistics": self._calculate_export_statistics(file_info_list),
            }

            # Convert to JSON
            import json
            metadata_json = json.dumps(metadata, indent=2)

            # Add to ZIP
            zip_file.writestr("export_metadata.json", metadata_json)

            # Also add a simple text summary
            summary_text = self._generate_text_summary(metadata)
            zip_file.writestr("export_summary.txt", summary_text)

        except Exception as e:
            # Don't fail the entire export if metadata fails
            self.signals.error.emit(f"Failed to add metadata: {str(e)}")

    def _calculate_export_statistics(self, file_info_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for the exported frames"""
        if not file_info_list:
            return {}

        total_size = sum(info.get("size", 0) for info in file_info_list)
        timestamps = [info.get("timestamp", 0) for info in file_info_list]
        widths = [info.get("width", 0) for info in file_info_list]
        heights = [info.get("height", 0) for info in file_info_list]

        return {
            "total_files": len(file_info_list),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "average_file_size_bytes": total_size / len(file_info_list),
            "timestamp_range": {
                "min": min(timestamps) if timestamps else 0,
                "max": max(timestamps) if timestamps else 0,
                "span_ms": max(timestamps) - min(timestamps) if timestamps else 0,
            },
            "resolution_info": {
                "min_width": min(widths) if widths else 0,
                "max_width": max(widths) if widths else 0,
                "min_height": min(heights) if heights else 0,
                "max_height": max(heights) if heights else 0,
            },
        }

    def _generate_text_summary(self, metadata: Dict[str, Any]) -> str:
        """Generate human-readable text summary"""
        export_info = metadata.get("export_info", {})
        stats = metadata.get("statistics", {})

        summary = f"""Video Frame Export Summary
========================

Export Details:
- Export Date: {export_info.get('timestamp', 'Unknown')}
- Total Frames: {export_info.get('total_frames', 0)}
- Image Format: {export_info.get('format', 'Unknown')}
- Image Quality: {export_info.get('quality', 0)}%
- Compression Level: {export_info.get('compression_level', 0)}

Statistics:
- Total Size: {stats.get('total_size_mb', 0):.2f} MB
- Average File Size: {stats.get('average_file_size_bytes', 0) / 1024:.2f} KB
- Time Range: {stats.get('timestamp_range', {}).get('min', 0)}ms - {stats.get('timestamp_range', {}).get('max', 0)}ms
- Duration Span: {stats.get('timestamp_range', {}).get('span_ms', 0)}ms

Resolution Range:
- Width: {stats.get('resolution_info', {}).get('min_width', 0)} - {stats.get('resolution_info', {}).get('max_width', 0)} pixels
- Height: {stats.get('resolution_info', {}).get('min_height', 0)} - {stats.get('resolution_info', {}).get('max_height', 0)} pixels

Generated by Video Frame Capture Application
"""
        return summary


class QuickExportWorker(QRunnable):
    """Simplified worker for quick single-frame exports"""

    def __init__(self, pixmap: QPixmap, file_path: str, format: str = "PNG", quality: int = 95):
        super().__init__()
        self.pixmap = pixmap
        self.file_path = file_path
        self.format = format
        self.quality = quality
        self.signals = ExportSignals()

    def run(self) -> None:
        """Export single frame to file"""
        try:
            self.signals.progress.emit(0, "Starting quick export...")

            if self.pixmap.isNull():
                self.signals.error.emit("Invalid pixmap for export")
                return

            # Ensure directory exists
            export_dir = os.path.dirname(self.file_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)

            self.signals.progress.emit(50, "Saving image file...")

            # Save pixmap directly to file
            format_str = self.format.upper()
            if format_str == "JPG":
                format_str = "JPEG"

            success = self.pixmap.save(self.file_path, format_str, self.quality)

            if success:
                self.signals.progress.emit(100, "Export completed")
                self.signals.finished.emit(self.file_path)
            else:
                self.signals.error.emit("Failed to save image file")

        except Exception as e:
            self.signals.error.emit(f"Quick export failed: {str(e)}")