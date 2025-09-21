"""
Background worker for thumbnail generation.
"""

from typing import Optional, List, Tuple
from PySide6.QtCore import QObject, QRunnable, Signal, QSize
from PySide6.QtGui import QPixmap, QImage
import time


class ThumbnailSignals(QObject):
    """Signals for thumbnail worker"""

    thumbnailReady = Signal(QPixmap, int, str)  # thumbnail, timestamp, original_path
    progress = Signal(int, str)  # percentage, status_message
    error = Signal(str)  # error_message
    finished = Signal()  # completed


class ThumbnailWorker(QRunnable):
    """Worker for generating thumbnails from pixmaps"""

    def __init__(
        self,
        source_pixmap: QPixmap,
        timestamp: int,
        thumbnail_size: QSize = QSize(160, 120),
        quality_settings: Optional[dict] = None,
        original_path: str = "",
    ):
        super().__init__()
        self.source_pixmap = source_pixmap
        self.timestamp = timestamp
        self.thumbnail_size = thumbnail_size
        self.quality_settings = quality_settings or {}
        self.original_path = original_path
        self.signals = ThumbnailSignals()
        self._is_cancelled = False

    def run(self) -> None:
        """Generate thumbnail from source pixmap"""
        try:
            self.signals.progress.emit(0, "Starting thumbnail generation...")

            if self._is_cancelled or self.source_pixmap.isNull():
                return

            self.signals.progress.emit(25, "Scaling image...")

            # Get quality settings
            smooth_scaling = self.quality_settings.get("smooth_scaling", True)
            keep_aspect_ratio = self.quality_settings.get("keep_aspect_ratio", True)
            background_color = self.quality_settings.get("background_color", None)

            if self._is_cancelled:
                return

            # Choose transformation mode
            transform_mode = 1 if smooth_scaling else 0  # Qt.SmoothTransformation : Qt.FastTransformation

            # Choose aspect ratio mode
            aspect_mode = 1 if keep_aspect_ratio else 0  # Qt.KeepAspectRatio : Qt.IgnoreAspectRatio

            self.signals.progress.emit(50, "Applying scaling transformation...")

            # Scale the pixmap
            scaled_pixmap = self.source_pixmap.scaled(
                self.thumbnail_size,
                aspectRatioMode=aspect_mode,
                transformMode=transform_mode
            )

            if self._is_cancelled:
                return

            self.signals.progress.emit(75, "Finalizing thumbnail...")

            # Apply background color if needed and aspect ratio was kept
            if background_color and keep_aspect_ratio:
                scaled_pixmap = self._add_background(scaled_pixmap, background_color)

            # Apply any additional processing
            final_thumbnail = self._apply_post_processing(scaled_pixmap)

            if self._is_cancelled:
                return

            self.signals.progress.emit(100, "Thumbnail generation complete")

            # Emit the result
            self.signals.thumbnailReady.emit(final_thumbnail, self.timestamp, self.original_path)

        except Exception as e:
            self.signals.error.emit(f"Thumbnail generation error: {str(e)}")

        finally:
            self.signals.finished.emit()

    def cancel(self) -> None:
        """Cancel thumbnail generation"""
        self._is_cancelled = True

    def _add_background(self, pixmap: QPixmap, background_color) -> QPixmap:
        """Add background color to pixmap to fill target size"""
        # Create a new pixmap with the target size and background color
        background_pixmap = QPixmap(self.thumbnail_size)
        background_pixmap.fill(background_color)

        # Calculate position to center the scaled pixmap
        x = (self.thumbnail_size.width() - pixmap.width()) // 2
        y = (self.thumbnail_size.height() - pixmap.height()) // 2

        # Draw the scaled pixmap on the background
        from PySide6.QtGui import QPainter
        painter = QPainter(background_pixmap)
        painter.drawPixmap(x, y, pixmap)
        painter.end()

        return background_pixmap

    def _apply_post_processing(self, pixmap: QPixmap) -> QPixmap:
        """Apply any post-processing effects"""
        # Apply sharpening if requested
        if self.quality_settings.get("sharpen", False):
            # Basic sharpening could be implemented here
            pass

        # Apply border if requested
        border_width = self.quality_settings.get("border_width", 0)
        if border_width > 0:
            border_color = self.quality_settings.get("border_color", "#cccccc")
            pixmap = self._add_border(pixmap, border_width, border_color)

        return pixmap

    def _add_border(self, pixmap: QPixmap, width: int, color) -> QPixmap:
        """Add border to pixmap"""
        from PySide6.QtGui import QPainter, QPen
        from PySide6.QtCore import Qt

        # Create a copy to draw on
        bordered_pixmap = QPixmap(pixmap)
        painter = QPainter(bordered_pixmap)

        # Set up pen for border
        pen = QPen(color, width)
        painter.setPen(pen)

        # Draw border rectangle
        rect = bordered_pixmap.rect().adjusted(
            width // 2, width // 2, -width // 2, -width // 2
        )
        painter.drawRect(rect)
        painter.end()

        return bordered_pixmap


class BatchThumbnailSignals(QObject):
    """Signals for batch thumbnail worker"""

    thumbnailReady = Signal(QPixmap, int, str)  # thumbnail, timestamp, path
    batchProgress = Signal(int, int, str)  # current, total, status
    error = Signal(str)  # error_message
    finished = Signal(int)  # total_processed


class BatchThumbnailWorker(QRunnable):
    """Worker for generating multiple thumbnails in batch"""

    def __init__(
        self,
        pixmap_data_list: List[Tuple[QPixmap, int, str]],  # (pixmap, timestamp, path)
        thumbnail_size: QSize = QSize(160, 120),
        quality_settings: Optional[dict] = None,
    ):
        super().__init__()
        self.pixmap_data_list = pixmap_data_list
        self.thumbnail_size = thumbnail_size
        self.quality_settings = quality_settings or {}
        self.signals = BatchThumbnailSignals()
        self._is_cancelled = False
        self._processed_count = 0

    def run(self) -> None:
        """Generate thumbnails for all pixmaps in batch"""
        total_count = len(self.pixmap_data_list)

        try:
            for i, (pixmap, timestamp, path) in enumerate(self.pixmap_data_list):
                if self._is_cancelled:
                    break

                self.signals.batchProgress.emit(
                    i, total_count, f"Generating thumbnail {i+1} of {total_count}"
                )

                # Generate individual thumbnail
                success = self._generate_single_thumbnail(pixmap, timestamp, path)
                if success:
                    self._processed_count += 1

                # Small delay to prevent overwhelming the system
                time.sleep(0.005)  # 5ms delay

        except Exception as e:
            self.signals.error.emit(f"Batch thumbnail generation error: {str(e)}")

        finally:
            self.signals.finished.emit(self._processed_count)

    def cancel(self) -> None:
        """Cancel batch thumbnail generation"""
        self._is_cancelled = True

    def _generate_single_thumbnail(self, pixmap: QPixmap, timestamp: int, path: str) -> bool:
        """Generate a single thumbnail"""
        try:
            if pixmap.isNull():
                return False

            # Get quality settings
            smooth_scaling = self.quality_settings.get("smooth_scaling", True)
            keep_aspect_ratio = self.quality_settings.get("keep_aspect_ratio", True)

            # Choose modes
            transform_mode = 1 if smooth_scaling else 0
            aspect_mode = 1 if keep_aspect_ratio else 0

            # Scale the pixmap
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_size,
                aspectRatioMode=aspect_mode,
                transformMode=transform_mode
            )

            # Apply post-processing
            final_thumbnail = self._apply_post_processing(scaled_pixmap)

            # Emit result
            self.signals.thumbnailReady.emit(final_thumbnail, timestamp, path)
            return True

        except Exception as e:
            self.signals.error.emit(f"Single thumbnail error: {str(e)}")
            return False

    def _apply_post_processing(self, pixmap: QPixmap) -> QPixmap:
        """Apply post-processing effects (same as ThumbnailWorker)"""
        border_width = self.quality_settings.get("border_width", 0)
        if border_width > 0:
            border_color = self.quality_settings.get("border_color", "#cccccc")
            return self._add_border(pixmap, border_width, border_color)
        return pixmap

    def _add_border(self, pixmap: QPixmap, width: int, color) -> QPixmap:
        """Add border to pixmap (same as ThumbnailWorker)"""
        from PySide6.QtGui import QPainter, QPen

        bordered_pixmap = QPixmap(pixmap)
        painter = QPainter(bordered_pixmap)

        pen = QPen(color, width)
        painter.setPen(pen)

        rect = bordered_pixmap.rect().adjusted(
            width // 2, width // 2, -width // 2, -width // 2
        )
        painter.drawRect(rect)
        painter.end()

        return bordered_pixmap


class ThumbnailCache:
    """Simple cache for thumbnails to avoid regeneration"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = {}  # key -> (pixmap, timestamp)
        self._access_order = []  # LRU tracking

    def get(self, key: str) -> Optional[QPixmap]:
        """Get thumbnail from cache"""
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key][0]
        return None

    def put(self, key: str, pixmap: QPixmap, timestamp: int) -> None:
        """Add thumbnail to cache"""
        # Remove oldest if at capacity
        while len(self._cache) >= self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]

        # Add new item
        self._cache[key] = (pixmap, timestamp)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def remove(self, key: str) -> bool:
        """Remove thumbnail from cache"""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cached thumbnails"""
        self._cache.clear()
        self._access_order.clear()

    def get_size(self) -> int:
        """Get number of cached thumbnails"""
        return len(self._cache)