"""
Background worker for frame capture processing.
"""

from typing import Optional, List, Any
from PySide6.QtCore import QObject, QRunnable, Signal, Slot, QMutex, QWaitCondition
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtGui import QPixmap, QImage
import time


class FrameCaptureSignals(QObject):
    """Signals for frame capture worker"""

    frameReady = Signal(QPixmap, int, str)  # pixmap, timestamp, file_path
    progress = Signal(int, str)  # percentage, status_message
    error = Signal(str)  # error_message
    finished = Signal()  # completed


class FrameCaptureWorker(QRunnable):
    """Worker for processing video frames in background"""

    def __init__(
        self,
        video_frame: QVideoFrame,
        timestamp: int,
        file_path: str = "",
        processing_options: Optional[dict] = None,
    ):
        super().__init__()
        self.video_frame = video_frame
        self.timestamp = timestamp
        self.file_path = file_path
        self.processing_options = processing_options or {}
        self.signals = FrameCaptureSignals()
        self._is_cancelled = False

    def run(self) -> None:
        """Process the video frame"""
        try:
            self.signals.progress.emit(0, "Starting frame processing...")

            if self._is_cancelled:
                return

            # Map the video frame for reading
            if not self.video_frame.map(QVideoFrame.ReadOnly):
                self.signals.error.emit("Failed to map video frame for reading")
                return

            self.signals.progress.emit(25, "Converting frame to image...")

            if self._is_cancelled:
                self.video_frame.unmap()
                return

            # Convert to QImage
            qimage = self.video_frame.toImage()
            if qimage.isNull():
                self.signals.error.emit("Failed to convert video frame to image")
                self.video_frame.unmap()
                return

            self.signals.progress.emit(50, "Processing image...")

            if self._is_cancelled:
                self.video_frame.unmap()
                return

            # Apply any processing options
            processed_image = self._apply_processing(qimage)

            self.signals.progress.emit(75, "Creating final pixmap...")

            if self._is_cancelled:
                self.video_frame.unmap()
                return

            # Convert to pixmap
            pixmap = QPixmap.fromImage(processed_image)
            if pixmap.isNull():
                self.signals.error.emit("Failed to create pixmap from processed image")
                self.video_frame.unmap()
                return

            self.signals.progress.emit(100, "Frame processing complete")

            # Emit the result
            self.signals.frameReady.emit(pixmap, self.timestamp, self.file_path)

        except Exception as e:
            self.signals.error.emit(f"Frame processing error: {str(e)}")

        finally:
            # Always unmap the frame
            self.video_frame.unmap()
            self.signals.finished.emit()

    def cancel(self) -> None:
        """Cancel the frame processing"""
        self._is_cancelled = True

    def _apply_processing(self, image: QImage) -> QImage:
        """Apply processing options to the image"""
        processed_image = image

        # Apply scaling if requested
        scale_factor = self.processing_options.get("scale_factor", 1.0)
        if scale_factor != 1.0:
            new_width = int(image.width() * scale_factor)
            new_height = int(image.height() * scale_factor)
            processed_image = processed_image.scaled(
                new_width, new_height,
                aspectRatioMode=1,  # Qt.KeepAspectRatio
                transformMode=1     # Qt.SmoothTransformation
            )

        # Apply format conversion if requested
        target_format = self.processing_options.get("format")
        if target_format and hasattr(QImage, f"Format_{target_format}"):
            format_enum = getattr(QImage, f"Format_{target_format}")
            processed_image = processed_image.convertToFormat(format_enum)

        return processed_image


class BatchFrameCaptureSignals(QObject):
    """Signals for batch frame capture worker"""

    frameProcessed = Signal(QPixmap, int, str)  # pixmap, timestamp, file_path
    batchProgress = Signal(int, int, str)  # current, total, status
    error = Signal(str)  # error_message
    finished = Signal(int)  # total_processed


class BatchFrameCaptureWorker(QRunnable):
    """Worker for processing multiple frames in batch"""

    def __init__(
        self,
        frame_data_list: List[dict],  # List of {frame, timestamp, file_path}
        processing_options: Optional[dict] = None,
    ):
        super().__init__()
        self.frame_data_list = frame_data_list
        self.processing_options = processing_options or {}
        self.signals = BatchFrameCaptureSignals()
        self._is_cancelled = False
        self._processed_count = 0

    def run(self) -> None:
        """Process all frames in batch"""
        total_frames = len(self.frame_data_list)

        try:
            for i, frame_data in enumerate(self.frame_data_list):
                if self._is_cancelled:
                    break

                self.signals.batchProgress.emit(
                    i, total_frames, f"Processing frame {i+1} of {total_frames}"
                )

                # Process individual frame
                success = self._process_single_frame(frame_data)
                if success:
                    self._processed_count += 1

                # Small delay to prevent overwhelming the system
                time.sleep(0.01)

        except Exception as e:
            self.signals.error.emit(f"Batch processing error: {str(e)}")

        finally:
            self.signals.finished.emit(self._processed_count)

    def cancel(self) -> None:
        """Cancel batch processing"""
        self._is_cancelled = True

    def _process_single_frame(self, frame_data: dict) -> bool:
        """Process a single frame from the batch"""
        try:
            video_frame = frame_data.get("frame")
            timestamp = frame_data.get("timestamp", 0)
            file_path = frame_data.get("file_path", "")

            if not video_frame or not video_frame.isValid():
                return False

            # Map frame
            if not video_frame.map(QVideoFrame.ReadOnly):
                return False

            # Convert to image
            qimage = video_frame.toImage()
            if qimage.isNull():
                video_frame.unmap()
                return False

            # Apply processing
            processed_image = self._apply_processing(qimage)

            # Create pixmap
            pixmap = QPixmap.fromImage(processed_image)
            if pixmap.isNull():
                video_frame.unmap()
                return False

            # Emit result
            self.signals.frameProcessed.emit(pixmap, timestamp, file_path)

            # Unmap frame
            video_frame.unmap()
            return True

        except Exception as e:
            self.signals.error.emit(f"Single frame processing error: {str(e)}")
            return False

    def _apply_processing(self, image: QImage) -> QImage:
        """Apply processing options to the image"""
        # Same implementation as FrameCaptureWorker
        processed_image = image

        scale_factor = self.processing_options.get("scale_factor", 1.0)
        if scale_factor != 1.0:
            new_width = int(image.width() * scale_factor)
            new_height = int(image.height() * scale_factor)
            processed_image = processed_image.scaled(
                new_width, new_height,
                aspectRatioMode=1,
                transformMode=1
            )

        target_format = self.processing_options.get("format")
        if target_format and hasattr(QImage, f"Format_{target_format}"):
            format_enum = getattr(QImage, f"Format_{target_format}")
            processed_image = processed_image.convertToFormat(format_enum)

        return processed_image


class AutoCaptureSignals(QObject):
    """Signals for auto-capture worker"""

    captureRequested = Signal(int)  # timestamp
    statusChanged = Signal(str)  # status_message
    intervalReached = Signal()  # capture interval reached


class AutoCaptureController(QObject):
    """Controller for automatic frame capture at intervals"""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.signals = AutoCaptureSignals()
        self._is_active = False
        self._interval_seconds = 5.0
        self._last_capture_time = 0
        self._mutex = QMutex()
        self._condition = QWaitCondition()

    @Slot(float)
    def set_interval(self, seconds: float) -> None:
        """Set auto-capture interval in seconds"""
        with self._mutex:
            self._interval_seconds = max(0.1, seconds)  # Minimum 100ms

    @Slot(bool)
    def set_active(self, active: bool) -> None:
        """Start or stop auto-capture"""
        with self._mutex:
            if self._is_active != active:
                self._is_active = active
                if active:
                    self.signals.statusChanged.emit("Auto-capture started")
                    self._last_capture_time = time.time()
                else:
                    self.signals.statusChanged.emit("Auto-capture stopped")

                self._condition.wakeAll()

    @Slot(int)
    def check_capture_time(self, current_timestamp: int) -> None:
        """Check if it's time to capture based on video timestamp"""
        if not self._is_active:
            return

        current_time = time.time()

        with self._mutex:
            if current_time - self._last_capture_time >= self._interval_seconds:
                self._last_capture_time = current_time
                self.signals.captureRequested.emit(current_timestamp)
                self.signals.intervalReached.emit()

    def is_active(self) -> bool:
        """Check if auto-capture is active"""
        return self._is_active

    def get_interval(self) -> float:
        """Get current auto-capture interval"""
        return self._interval_seconds