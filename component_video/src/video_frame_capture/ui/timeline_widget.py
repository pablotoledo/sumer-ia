"""
Custom timeline widget with precise seeking and bookmarks.
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSlider,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, Slot, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QColor, QMouseEvent

from ..core.timeline_controller import TimelineController


class TimelineSlider(QSlider):
    """Custom slider with click-to-seek and bookmark display"""

    positionClicked = Signal(int)  # Position clicked in milliseconds
    hoverChanged = Signal(int)  # Hover position changed

    def __init__(self, orientation=Qt.Horizontal, parent: Optional[QWidget] = None):
        super().__init__(orientation, parent)
        self.setMinimum(0)
        self.setMaximum(0)
        self.bookmarks: List[int] = []
        self.hover_position = -1
        self.setMouseTracking(True)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for click-to-seek"""
        if event.button() == Qt.LeftButton:
            # Calculate position based on click
            value = self._position_from_click(event.position().toPoint())
            if 0 <= value <= self.maximum():
                self.setValue(value)
                self.positionClicked.emit(value)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for hover effects"""
        self.hover_position = self._position_from_click(event.position().toPoint())
        self.hoverChanged.emit(self.hover_position)
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave"""
        self.hover_position = -1
        self.update()
        super().leaveEvent(event)

    def _position_from_click(self, click_pos: QPoint) -> int:
        """Calculate slider value from click position"""
        if self.orientation() == Qt.Horizontal:
            groove_rect = self._get_groove_rect()
            if groove_rect.width() > 0:
                relative_pos = (click_pos.x() - groove_rect.left()) / groove_rect.width()
                return int(self.minimum() + relative_pos * (self.maximum() - self.minimum()))
        return self.value()

    def _get_groove_rect(self) -> QRect:
        """Get the groove rectangle"""
        # Simplified groove calculation
        margin = 10
        return QRect(margin, self.height() // 2 - 2, self.width() - 2 * margin, 4)

    def paintEvent(self, event) -> None:
        """Custom paint with bookmarks and hover"""
        super().paintEvent(event)

        if self.maximum() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        groove_rect = self._get_groove_rect()

        # Draw bookmarks
        if self.bookmarks:
            painter.setPen(QPen(QColor(255, 165, 0), 2))  # Orange
            for bookmark in self.bookmarks:
                if self.minimum() <= bookmark <= self.maximum():
                    pos_ratio = (bookmark - self.minimum()) / (self.maximum() - self.minimum())
                    x = groove_rect.left() + int(pos_ratio * groove_rect.width())
                    painter.drawLine(x, groove_rect.top() - 5, x, groove_rect.bottom() + 5)

        # Draw hover indicator
        if self.hover_position >= 0:
            painter.setPen(QPen(QColor(100, 150, 255, 128), 1))  # Semi-transparent blue
            pos_ratio = (self.hover_position - self.minimum()) / (self.maximum() - self.minimum())
            x = groove_rect.left() + int(pos_ratio * groove_rect.width())
            painter.drawLine(x, groove_rect.top() - 8, x, groove_rect.bottom() + 8)

        painter.end()

    def set_bookmarks(self, bookmarks: List[int]) -> None:
        """Set bookmark positions"""
        self.bookmarks = bookmarks.copy()
        self.update()

    def add_bookmark(self, position: int) -> None:
        """Add bookmark at position"""
        if position not in self.bookmarks:
            self.bookmarks.append(position)
            self.bookmarks.sort()
            self.update()

    def remove_bookmark(self, position: int) -> None:
        """Remove bookmark at position"""
        if position in self.bookmarks:
            self.bookmarks.remove(position)
            self.update()


class TimelineWidget(QWidget):
    """Timeline widget with controls and time display"""

    # Signals
    positionChanged = Signal(int)  # Position changed by user
    bookmarkToggled = Signal(int)  # Bookmark toggled at position

    def __init__(self, timeline_controller: TimelineController, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.timeline_controller = timeline_controller
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Time display row
        time_layout = QHBoxLayout()

        # Current time
        self.current_time_label = QLabel("00:00.000")
        self.current_time_label.setMinimumWidth(80)
        self.current_time_label.setAlignment(Qt.AlignCenter)
        self.current_time_label.setStyleSheet("font-family: monospace; font-weight: bold;")
        time_layout.addWidget(self.current_time_label)

        # Timeline slider
        self.timeline_slider = TimelineSlider()
        self.timeline_slider.setMinimumHeight(30)
        time_layout.addWidget(self.timeline_slider)

        # Duration time
        self.duration_label = QLabel("00:00.000")
        self.duration_label.setMinimumWidth(80)
        self.duration_label.setAlignment(Qt.AlignCenter)
        self.duration_label.setStyleSheet("font-family: monospace; font-weight: bold;")
        time_layout.addWidget(self.duration_label)

        layout.addLayout(time_layout)

        # Controls row
        controls_layout = QHBoxLayout()

        # Previous frame button
        self.prev_frame_btn = QPushButton("◀◀")
        self.prev_frame_btn.setMaximumWidth(40)
        self.prev_frame_btn.setToolTip("Previous Frame (Left Arrow)")
        controls_layout.addWidget(self.prev_frame_btn)

        # Skip backward button
        self.skip_back_btn = QPushButton("⏮")
        self.skip_back_btn.setMaximumWidth(40)
        self.skip_back_btn.setToolTip("Skip Backward 10s (Shift+Left)")
        controls_layout.addWidget(self.skip_back_btn)

        # Bookmark button
        self.bookmark_btn = QPushButton("📌")
        self.bookmark_btn.setMaximumWidth(40)
        self.bookmark_btn.setToolTip("Toggle Bookmark (B)")
        controls_layout.addWidget(self.bookmark_btn)

        # Frame info
        self.frame_info_label = QLabel("Frame: 0 / 0")
        self.frame_info_label.setAlignment(Qt.AlignCenter)
        self.frame_info_label.setStyleSheet("font-family: monospace;")
        controls_layout.addWidget(self.frame_info_label)

        # Skip forward button
        self.skip_forward_btn = QPushButton("⏭")
        self.skip_forward_btn.setMaximumWidth(40)
        self.skip_forward_btn.setToolTip("Skip Forward 10s (Shift+Right)")
        controls_layout.addWidget(self.skip_forward_btn)

        # Next frame button
        self.next_frame_btn = QPushButton("▶▶")
        self.next_frame_btn.setMaximumWidth(40)
        self.next_frame_btn.setToolTip("Next Frame (Right Arrow)")
        controls_layout.addWidget(self.next_frame_btn)

        layout.addLayout(controls_layout)

    def connect_signals(self) -> None:
        """Connect signals"""
        # Timeline controller signals
        self.timeline_controller.positionChanged.connect(self._on_position_changed)
        self.timeline_controller.durationChanged.connect(self._on_duration_changed)
        self.timeline_controller.bookmarkAdded.connect(self._on_bookmark_added)
        self.timeline_controller.bookmarkRemoved.connect(self._on_bookmark_removed)

        # Timeline slider signals
        self.timeline_slider.positionClicked.connect(self._on_slider_clicked)
        self.timeline_slider.valueChanged.connect(self._on_slider_changed)

        # Button signals
        self.prev_frame_btn.clicked.connect(self.timeline_controller.seek_to_previous_frame)
        self.next_frame_btn.clicked.connect(self.timeline_controller.seek_to_next_frame)
        self.skip_back_btn.clicked.connect(lambda: self.timeline_controller.seek_relative(-10000))
        self.skip_forward_btn.clicked.connect(lambda: self.timeline_controller.seek_relative(10000))
        self.bookmark_btn.clicked.connect(self._toggle_bookmark)

    @Slot('qint64')
    def _on_position_changed(self, position: int) -> None:
        """Handle position changes from timeline controller"""
        # Update slider without triggering signals
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(position)
        self.timeline_slider.blockSignals(False)

        # Update time display
        formatted_time = self.timeline_controller.format_time(position)
        self.current_time_label.setText(formatted_time)

        # Update frame info
        current_frame = self.timeline_controller.get_current_frame_number()
        total_frames = self.timeline_controller.get_total_frames()
        self.frame_info_label.setText(f"Frame: {current_frame} / {total_frames}")

    @Slot('qint64')
    def _on_duration_changed(self, duration: int) -> None:
        """Handle duration changes"""
        self.timeline_slider.setMaximum(duration)
        formatted_duration = self.timeline_controller.format_time(duration)
        self.duration_label.setText(formatted_duration)

    @Slot(int)
    def _on_bookmark_added(self, position: int) -> None:
        """Handle bookmark added"""
        self.timeline_slider.add_bookmark(position)

    @Slot(int)
    def _on_bookmark_removed(self, position: int) -> None:
        """Handle bookmark removed"""
        self.timeline_slider.remove_bookmark(position)

    @Slot(int)
    def _on_slider_clicked(self, position: int) -> None:
        """Handle slider click"""
        self.timeline_controller.seek_to_position(position)
        self.positionChanged.emit(position)

    @Slot(int)
    def _on_slider_changed(self, position: int) -> None:
        """Handle slider value change (dragging)"""
        if not self.timeline_slider.isSliderDown():
            return  # Only respond to direct value changes, not dragging

        self.timeline_controller.seek_to_position(position)
        self.positionChanged.emit(position)

    @Slot()
    def _toggle_bookmark(self) -> None:
        """Toggle bookmark at current position"""
        current_position = self.timeline_controller.get_current_position()
        bookmarks = self.timeline_controller.get_bookmarks()

        if current_position in bookmarks:
            self.timeline_controller.remove_bookmark(current_position)
        else:
            self.timeline_controller.add_bookmark(current_position)

        self.bookmarkToggled.emit(current_position)

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts"""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Left:
            if modifiers & Qt.ShiftModifier:
                self.timeline_controller.seek_relative(-10000)  # 10 seconds
            else:
                self.timeline_controller.seek_to_previous_frame()
        elif key == Qt.Key_Right:
            if modifiers & Qt.ShiftModifier:
                self.timeline_controller.seek_relative(10000)  # 10 seconds
            else:
                self.timeline_controller.seek_to_next_frame()
        elif key == Qt.Key_B:
            self._toggle_bookmark()
        else:
            super().keyPressEvent(event)

    def set_frame_rate(self, fps: float) -> None:
        """Set video frame rate for accurate frame navigation"""
        self.timeline_controller.set_frame_rate(fps)