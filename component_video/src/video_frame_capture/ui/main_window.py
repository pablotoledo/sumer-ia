"""
Main application window with dockable panels.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QVBoxLayout,
    QWidget,
    QMenuBar,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, QSettings, Signal, Slot
from PySide6.QtGui import QAction, QKeySequence, QDropEvent, QDragEnterEvent
from PySide6.QtMultimedia import QVideoFrame

from .video_display import VideoDisplayWidget
from .timeline_widget import TimelineWidget
from .thumbnail_gallery import ThumbnailGalleryWidget
from .controls_panel import ControlsPanel
from ..core.video_player import VideoPlayer
from ..core.timeline_controller import TimelineController
from ..core.frame_extractor import FrameExtractor
from ..core.memory_manager import MemoryManager


class MainWindow(QMainWindow):
    """Main application window with dockable panels"""

    # Signals
    fileLoaded = Signal(str)  # File path loaded
    framesCaptured = Signal(int)  # Number of frames captured
    exportCompleted = Signal(str)  # Export file path

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Frame Capture")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)

        # Accept drops
        self.setAcceptDrops(True)

        # Core components
        self.video_player = VideoPlayer()
        self.timeline_controller = TimelineController(self.video_player)
        self.frame_extractor = FrameExtractor()
        self.memory_manager = MemoryManager()

        # Settings
        self.settings = QSettings("VideoFrameCapture", "MainWindow")


        self.setup_ui()
        self.setup_docks()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.connect_signals()
        self.restore_settings()

    def setup_ui(self) -> None:
        """Setup central widget and basic UI"""
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Video display
        self.video_display = VideoDisplayWidget(self.video_player)
        layout.addWidget(self.video_display)

        self.setCentralWidget(central_widget)

    def setup_docks(self) -> None:
        """Setup dockable panels"""
        # Timeline dock
        self.timeline_dock = QDockWidget("Timeline", self)
        self.timeline_dock.setObjectName("TimelineDock")
        self.timeline_widget = TimelineWidget(self.timeline_controller)
        self.timeline_dock.setWidget(self.timeline_widget)
        self.timeline_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.timeline_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(Qt.BottomDockWidgetArea, self.timeline_dock)

        # Controls dock
        self.controls_dock = QDockWidget("Controls", self)
        self.controls_dock.setObjectName("ControlsDock")
        self.controls_panel = ControlsPanel(
            self.video_player, self.timeline_controller, self.frame_extractor
        )
        self.controls_dock.setWidget(self.controls_panel)
        self.controls_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.controls_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self.controls_dock)

        # Thumbnail gallery dock
        self.gallery_dock = QDockWidget("Captured Frames", self)
        self.gallery_dock.setObjectName("GalleryDock")
        self.thumbnail_gallery = ThumbnailGalleryWidget(self.memory_manager)
        self.gallery_dock.setWidget(self.thumbnail_gallery)
        self.gallery_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.gallery_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetClosable
            | QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.gallery_dock)

        # Enable dock nesting
        self.setDockNestingEnabled(True)

    def setup_menu_bar(self) -> None:
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Open action
        open_action = QAction("&Open Video...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("Open a video file")
        open_action.triggered.connect(self.open_video_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Export action
        export_action = QAction("&Export Frames...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setStatusTip("Export captured frames as ZIP")
        export_action.triggered.connect(self.export_frames)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        # Clear frames action
        clear_action = QAction("&Clear All Frames", self)
        clear_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        clear_action.setStatusTip("Clear all captured frames")
        clear_action.triggered.connect(self.clear_all_frames)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Show/hide docks
        view_menu.addAction(self.timeline_dock.toggleViewAction())
        view_menu.addAction(self.controls_dock.toggleViewAction())
        view_menu.addAction(self.gallery_dock.toggleViewAction())

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self) -> None:
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def connect_signals(self) -> None:
        """Connect component signals"""
        # Video player signals
        self.video_player.mediaLoaded.connect(self._on_media_loaded)
        self.video_player.errorOccurred.connect(self._on_player_error)

        # Timeline signals
        self.timeline_controller.positionChanged.connect(self._on_position_changed)
        self.timeline_controller.durationChanged.connect(self._on_duration_changed)

        # Frame extractor signals
        self.frame_extractor.frameExtracted.connect(self._on_frame_extracted)
        self.frame_extractor.errorOccurred.connect(self._on_extractor_error)

        # Controls panel signals
        self.controls_panel.frameCaptured.connect(lambda: self.capture_current_frame())

        # Gallery signals
        self.thumbnail_gallery.exportRequested.connect(self.export_selected_frames)
        self.thumbnail_gallery.captureRequested.connect(self.capture_current_frame)

        # Memory manager signals
        self.memory_manager.memoryStatusChanged.connect(self._on_memory_status_changed)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".wmv")):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                self.load_video(file_path)
                event.acceptProposedAction()

    @Slot()
    def open_video_file(self) -> None:
        """Open video file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)",
        )

        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path: str) -> None:
        """Load video file"""
        try:
            self.video_player.load_video(file_path)
            self.status_bar.showMessage(f"Loading: {file_path}")
            # Enable frame capture once video is loaded
            self.controls_panel.capture_group.update_capture_readiness(True)
            self.fileLoaded.emit(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load video: {str(e)}")

    @Slot()
    def export_frames(self) -> None:
        """Export all captured frames"""
        frame_count = self.thumbnail_gallery.get_frame_count()
        if frame_count == 0:
            QMessageBox.information(
                self, "No Frames", "No frames have been captured to export."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Frames", "", "ZIP Files (*.zip);;All Files (*)"
        )

        if file_path:
            self.thumbnail_gallery.export_all_frames(file_path)

    @Slot()
    def export_selected_frames(self) -> None:
        """Export selected frames"""
        selected_count = self.thumbnail_gallery.get_selected_count()
        if selected_count == 0:
            QMessageBox.information(
                self, "No Selection", "No frames are selected for export."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Selected Frames", "", "ZIP Files (*.zip);;All Files (*)"
        )

        if file_path:
            self.thumbnail_gallery.export_selected_frames(file_path)

    @Slot()
    def clear_all_frames(self) -> None:
        """Clear all captured frames"""
        reply = QMessageBox.question(
            self,
            "Clear Frames",
            "Are you sure you want to clear all captured frames?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.thumbnail_gallery.clear_all_frames()
            self.memory_manager.clear_all_caches()

    @Slot()
    def show_about(self) -> None:
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Video Frame Capture",
            "Video Frame Capture v0.1.0\n\n"
            "A professional desktop application for video frame capture and export.\n\n"
            "Built with PySide6 and OpenCV.",
        )

    @Slot()
    def _on_media_loaded(self) -> None:
        """Handle media loaded"""
        video_path = self.video_player.get_current_video_path()
        if video_path:
            self.status_bar.showMessage(f"Loaded: {video_path}")

    @Slot(str)
    def _on_player_error(self, error: str) -> None:
        """Handle player errors"""
        self.status_bar.showMessage(f"Error: {error}")
        QMessageBox.critical(self, "Video Player Error", error)


    @Slot('qint64')
    def _on_position_changed(self, position: int) -> None:
        """Handle position changes"""
        formatted_time = self.timeline_controller.format_time(position)
        duration = self.timeline_controller.get_duration()
        formatted_duration = self.timeline_controller.format_time(duration)
        self.status_bar.showMessage(f"Time: {formatted_time} / {formatted_duration}")

    @Slot('qint64')
    def _on_duration_changed(self, duration: int) -> None:
        """Handle duration changes"""
        pass  # Handled in position changed

    @Slot(object, int, str)
    def _on_frame_extracted(self, pixmap, timestamp: int, file_path: str) -> None:
        """Handle frame extraction"""
        self.thumbnail_gallery.add_frame(pixmap, timestamp, file_path)

    @Slot(str)
    def _on_extractor_error(self, error: str) -> None:
        """Handle extractor errors"""
        self.status_bar.showMessage(f"Frame extraction error: {error}")

    @Slot(int)
    def _on_frame_captured(self, timestamp: int) -> None:
        """Handle frame capture"""
        self.framesCaptured.emit(timestamp)

    def capture_current_frame(self) -> None:
        """Capture current video frame"""
        current_position = self.timeline_controller.get_current_position()
        video_path = self.video_player.get_current_video_path()

        if video_path and current_position >= 0:
            self.status_bar.showMessage(f"Capturing frame at {current_position}ms...")

            # Capturar frame usando el nuevo método
            pixmap = self.video_player.capture_current_frame()

            if pixmap and not pixmap.isNull():
                # Añadir a la galería
                self.thumbnail_gallery.add_frame(
                    pixmap, current_position, video_path
                )

                # Notificar al controls panel que la captura fue exitosa
                self.controls_panel.capture_group._on_frame_extracted(
                    pixmap, current_position, video_path
                )

                self.status_bar.showMessage(
                    f"Frame captured at {current_position}ms"
                )
            else:
                self.status_bar.showMessage("No valid frame available")

    @Slot(dict)
    def _on_memory_status_changed(self, status: dict) -> None:
        """Handle memory status changes"""
        # Could update a memory indicator in the status bar
        pass

    def save_settings(self) -> None:
        """Save window settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def restore_settings(self) -> None:
        """Restore window settings"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)

    def closeEvent(self, event) -> None:
        """Handle close event"""
        self.save_settings()
        self.memory_manager.clear_all_caches()
        event.accept()