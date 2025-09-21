"""
Frame extraction functionality with threading support.
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np


class WorkerSignals(QObject):
    """Signals for background workers"""

    result = Signal(QPixmap, int, str)  # pixmap, timestamp, file_path
    error = Signal(str)  # error message
    finished = Signal()


class FrameExtractionWorker(QRunnable):
    """Background worker for frame extraction"""

    def __init__(self, frame: QVideoFrame, timestamp: int, file_path: str = ""):
        super().__init__()
        self.frame = frame
        self.timestamp = timestamp
        self.file_path = file_path
        self.signals = WorkerSignals()

    def run(self) -> None:
        """Process frame in background"""
        try:
            # Map frame for reading
            if not self.frame.map(QVideoFrame.ReadOnly):
                self.signals.error.emit("Failed to map video frame")
                return

            # Convert QVideoFrame to QImage
            qimg = self.frame.toImage()
            if qimg.isNull():
                self.signals.error.emit("Failed to convert frame to image")
                return

            # Create pixmap from image
            pixmap = QPixmap.fromImage(qimg)
            if pixmap.isNull():
                self.signals.error.emit("Failed to create pixmap from image")
                return

            # Emit result
            self.signals.result.emit(pixmap, self.timestamp, self.file_path)

        except Exception as e:
            self.signals.error.emit(f"Frame extraction error: {str(e)}")
        finally:
            # Unmap frame
            self.frame.unmap()
            self.signals.finished.emit()


class ThumbnailGenerationWorker(QRunnable):
    """Background worker for thumbnail generation"""

    def __init__(self, pixmap: QPixmap, timestamp: int, thumbnail_size: tuple = (160, 120)):
        super().__init__()
        self.pixmap = pixmap
        self.timestamp = timestamp
        self.thumbnail_size = thumbnail_size
        self.signals = WorkerSignals()

    def run(self) -> None:
        """Generate thumbnail in background"""
        try:
            # Scale pixmap to thumbnail size while maintaining aspect ratio
            scaled_pixmap = self.pixmap.scaled(
                self.thumbnail_size[0],
                self.thumbnail_size[1],
                aspectRatioMode=1,  # Qt.KeepAspectRatio
                transformMode=1,  # Qt.SmoothTransformation
            )

            self.signals.result.emit(scaled_pixmap, self.timestamp, "")

        except Exception as e:
            self.signals.error.emit(f"Thumbnail generation error: {str(e)}")
        finally:
            self.signals.finished.emit()


class FrameExtractor(QObject):
    """Extract and process video frames with threading"""

    frameExtracted = Signal(QPixmap, int, str)  # pixmap, timestamp, file_path
    thumbnailGenerated = Signal(QPixmap, int)  # thumbnail, timestamp
    errorOccurred = Signal(str)  # error message

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.thumbnail_size = (160, 120)

    @Slot(QVideoFrame, int, str)
    def extract_frame(self, frame: QVideoFrame, timestamp: int, file_path: str = "") -> None:
        """Extract frame in background thread"""
        if not frame.isValid():
            self.errorOccurred.emit("Invalid video frame")
            return

        worker = FrameExtractionWorker(frame, timestamp, file_path)
        worker.signals.result.connect(self.frameExtracted)
        worker.signals.error.connect(self.errorOccurred)
        self.thread_pool.start(worker)

    @Slot(QPixmap, int)
    def generate_thumbnail(self, pixmap: QPixmap, timestamp: int) -> None:
        """Generate thumbnail in background thread"""
        if pixmap.isNull():
            self.errorOccurred.emit("Invalid pixmap for thumbnail generation")
            return

        worker = ThumbnailGenerationWorker(pixmap, timestamp, self.thumbnail_size)
        worker.signals.result.connect(self._on_thumbnail_ready)
        worker.signals.error.connect(self.errorOccurred)
        self.thread_pool.start(worker)

    @Slot(QPixmap, int, str)
    def _on_thumbnail_ready(self, thumbnail: QPixmap, timestamp: int, _: str) -> None:
        """Handle thumbnail generation completion"""
        self.thumbnailGenerated.emit(thumbnail, timestamp)

    def set_thumbnail_size(self, width: int, height: int) -> None:
        """Set the size for generated thumbnails"""
        self.thumbnail_size = (width, height)

    def get_thumbnail_size(self) -> tuple:
        """Get current thumbnail size"""
        return self.thumbnail_size


def qframe_to_cv2(qframe: QVideoFrame) -> Optional[np.ndarray]:
    """Convert QVideoFrame to OpenCV numpy array"""
    try:
        if not qframe.map(QVideoFrame.ReadOnly):
            return None

        # Convert to QImage first
        qimg = qframe.toImage()
        if qimg.isNull():
            qframe.unmap()
            return None

        # Get image data
        width = qimg.width()
        height = qimg.height()
        ptr = qimg.constBits()

        # Convert to numpy array
        if qimg.format() == QImage.Format_RGB32:
            arr = np.array(ptr).reshape(height, width, 4)  # ARGB
            bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        elif qimg.format() == QImage.Format_RGB888:
            arr = np.array(ptr).reshape(height, width, 3)  # RGB
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        else:
            # Convert to RGB32 first
            qimg = qimg.convertToFormat(QImage.Format_RGB32)
            ptr = qimg.constBits()
            arr = np.array(ptr).reshape(height, width, 4)  # ARGB
            bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

        qframe.unmap()
        return bgr

    except Exception:
        qframe.unmap()
        return None


def cv2_to_qpixmap(cv_img: np.ndarray) -> QPixmap:
    """Convert OpenCV image to QPixmap"""
    try:
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width

        # Create QImage
        qimg = QImage(
            rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888
        )

        # Convert to QPixmap
        return QPixmap.fromImage(qimg)

    except Exception:
        return QPixmap()