"""
Video display widget for video playback.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPixmap, QPainter, QFont, QPen, QBrush
from PySide6.QtMultimediaWidgets import QVideoWidget

from ..core.video_player import VideoPlayer


class VideoDisplayWidget(QWidget):
    """Widget for displaying video content with overlay information"""

    # Signals
    clicked = Signal()  # Widget clicked
    doubleClicked = Signal()  # Widget double-clicked

    def __init__(self, video_player: VideoPlayer, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.video_player = video_player
        self.setMinimumSize(640, 480)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Overlay settings
        self.show_overlay = True
        self.overlay_opacity = 0.7

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Get video widget from player
        self.video_widget = self.video_player.get_video_widget()
        self.video_widget.setAspectRatioMode(Qt.KeepAspectRatio)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.video_widget)

        # Placeholder for when no video is loaded
        self.placeholder_label = QLabel("Drop a video file here or use File > Open Video")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(
            """
            QLabel {
                color: #888;
                font-size: 16px;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                background-color: #f9f9f9;
            }
        """
        )
        self.placeholder_label.hide()
        layout.addWidget(self.placeholder_label)

    def connect_signals(self) -> None:
        """Connect video player signals"""
        self.video_player.mediaLoaded.connect(self._on_media_loaded)
        self.video_player.errorOccurred.connect(self._on_error_occurred)

    @Slot()
    def _on_media_loaded(self) -> None:
        """Handle media loaded"""
        self.placeholder_label.hide()
        self.video_widget.show()

    @Slot(str)
    def _on_error_occurred(self, error: str) -> None:
        """Handle player errors"""
        self.video_widget.hide()
        self.placeholder_label.setText(f"Error loading video: {error}")
        self.placeholder_label.show()

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """Handle mouse double-click events"""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)

    def sizeHint(self) -> QSize:
        """Return preferred size"""
        return QSize(800, 600)

    def minimumSizeHint(self) -> QSize:
        """Return minimum size"""
        return QSize(320, 240)

    def set_overlay_visible(self, visible: bool) -> None:
        """Set overlay visibility"""
        self.show_overlay = visible
        self.update()

    def set_overlay_opacity(self, opacity: float) -> None:
        """Set overlay opacity (0.0 to 1.0)"""
        self.overlay_opacity = max(0.0, min(1.0, opacity))
        self.update()

    def paintEvent(self, event) -> None:
        """Paint overlay information"""
        super().paintEvent(event)

        if not self.show_overlay:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set up overlay style
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        pen = QPen(Qt.white)
        painter.setPen(pen)

        # Semi-transparent background for text
        brush = QBrush(Qt.black)
        painter.setBrush(brush)
        painter.setOpacity(self.overlay_opacity)

        # Draw video information if available
        video_path = self.video_player.get_current_video_path()
        if video_path:
            # Extract filename
            filename = video_path.split("/")[-1] if "/" in video_path else video_path
            filename = video_path.split("\\")[-1] if "\\" in video_path else filename

            # Draw filename in top-left corner
            text_rect = painter.fontMetrics().boundingRect(filename)
            text_rect.adjust(-5, -2, 5, 2)
            text_rect.moveTo(10, 10)

            painter.drawRect(text_rect)
            painter.setOpacity(1.0)
            painter.drawText(text_rect, Qt.AlignCenter, filename)

            # Draw playback status in top-right corner
            if self.video_player.is_playing():
                status_text = "▶ Playing"
            else:
                status_text = "⏸ Paused"

            status_rect = painter.fontMetrics().boundingRect(status_text)
            status_rect.adjust(-5, -2, 5, 2)
            status_rect.moveTo(self.width() - status_rect.width() - 10, 10)

            painter.setOpacity(self.overlay_opacity)
            painter.drawRect(status_rect)
            painter.setOpacity(1.0)
            painter.drawText(status_rect, Qt.AlignCenter, status_text)

        painter.end()


class VideoPreviewWidget(QLabel):
    """Simple widget for displaying video frame previews"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumSize(160, 120)
        self.setMaximumSize(320, 240)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            """
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
        """
        )

    def set_frame(self, pixmap: QPixmap) -> None:
        """Set the frame to display"""
        if not pixmap.isNull():
            # Scale pixmap to fit widget while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
        else:
            self.clear()

    def clear_frame(self) -> None:
        """Clear the displayed frame"""
        self.clear()
        self.setText("No Preview")