"""
Main application entry point for Video Frame Capture.
"""

import sys
import os
from typing import Optional
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer, QThread, QLoggingCategory
from PySide6.QtGui import QPixmap, QIcon, QFont

# Import application components
from video_frame_capture.ui.main_window import MainWindow
from video_frame_capture.core.video_player import VideoPlayer
from video_frame_capture.core.frame_extractor import FrameExtractor
from video_frame_capture.core.memory_manager import MemoryManager
from video_frame_capture.utils.file_manager import FileManager


class VideoFrameCaptureApp(QApplication):
    """Main application class with initialization and error handling"""

    def __init__(self, argv):
        super().__init__(argv)

        # Application metadata
        self.setApplicationName("Video Frame Capture")
        self.setApplicationVersion("0.1.0")
        self.setOrganizationName("Video Frame Capture Team")
        self.setOrganizationDomain("videoframecapture.app")

        # Set application icon if available
        self.setup_application_icon()

        # Setup logging
        self.setup_logging()

        # Initialize application
        self.main_window: Optional[MainWindow] = None
        self.splash_screen: Optional[QSplashScreen] = None

        # Connect to aboutToQuit signal for cleanup
        self.aboutToQuit.connect(self.cleanup)

    def setup_application_icon(self) -> None:
        """Setup application icon"""
        try:
            # Try to load application icon
            icon_path = os.path.join(
                os.path.dirname(__file__),
                "resources", "icons", "app_icon.png"
            )
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
        except Exception:
            # Icon loading is optional
            pass

    def setup_logging(self) -> None:
        """Setup application logging"""
        # Disable Qt logging for cleaner output in development
        QLoggingCategory.setFilterRules("qt.qpa.xcb.warning=false")

    def show_splash_screen(self) -> None:
        """Show splash screen during startup"""
        try:
            # Create a simple splash screen
            splash_pixmap = QPixmap(400, 300)
            splash_pixmap.fill(Qt.white)

            self.splash_screen = QSplashScreen(splash_pixmap)
            self.splash_screen.setWindowFlags(
                Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
            )

            # Show splash with loading message
            self.splash_screen.show()
            self.splash_screen.showMessage(
                "Loading Video Frame Capture...",
                Qt.AlignHCenter | Qt.AlignBottom,
                Qt.black
            )

            # Process events to show splash
            self.processEvents()

        except Exception as e:
            print(f"Could not show splash screen: {e}")

    def hide_splash_screen(self) -> None:
        """Hide splash screen"""
        if self.splash_screen:
            self.splash_screen.finish(self.main_window)
            self.splash_screen = None

    def initialize_application(self) -> bool:
        """Initialize the main application components"""
        try:
            # Show splash screen
            self.show_splash_screen()

            if self.splash_screen:
                self.splash_screen.showMessage(
                    "Initializing components...",
                    Qt.AlignHCenter | Qt.AlignBottom,
                    Qt.black
                )
            self.processEvents()

            # Create main window
            self.main_window = MainWindow()

            if self.splash_screen:
                self.splash_screen.showMessage(
                    "Setting up user interface...",
                    Qt.AlignHCenter | Qt.AlignBottom,
                    Qt.black
                )
            self.processEvents()

            # Connect application-level signals
            self.connect_signals()

            if self.splash_screen:
                self.splash_screen.showMessage(
                    "Ready!",
                    Qt.AlignHCenter | Qt.AlignBottom,
                    Qt.black
                )
            self.processEvents()

            # Small delay to show "Ready!" message
            QTimer.singleShot(500, self.show_main_window)

            return True

        except Exception as e:
            self.show_error_message("Initialization Error", str(e))
            return False

    def show_main_window(self) -> None:
        """Show the main window and hide splash screen"""
        if self.main_window:
            self.main_window.show()
            self.hide_splash_screen()

    def connect_signals(self) -> None:
        """Connect application-level signals"""
        if self.main_window:
            # Handle file loading from command line arguments
            self.main_window.fileLoaded.connect(self.on_file_loaded)

            # Handle application errors
            self.main_window.video_player.errorOccurred.connect(self.on_video_error)

    def on_file_loaded(self, file_path: str) -> None:
        """Handle file loaded signal"""
        print(f"File loaded: {file_path}")

    def on_video_error(self, error_message: str) -> None:
        """Handle video player errors"""
        self.show_error_message("Video Player Error", error_message)

    def show_error_message(self, title: str, message: str) -> None:
        """Show error message dialog"""
        QMessageBox.critical(None, title, message)

    def process_command_line_args(self) -> None:
        """Process command line arguments"""
        args = self.arguments()

        # Skip the first argument (executable path)
        for arg in args[1:]:
            if os.path.isfile(arg) and FileManager.is_video_file(arg):
                # Load video file
                if self.main_window:
                    QTimer.singleShot(1000, lambda: self.main_window.load_video(arg))
                break

    def cleanup(self) -> None:
        """Cleanup application resources"""
        try:
            if self.main_window:
                # Save window state
                self.main_window.save_settings()

                # Clean up memory manager
                if hasattr(self.main_window, 'memory_manager'):
                    self.main_window.memory_manager.clear_all_caches()

            # Clean up temporary files
            FileManager.clean_temp_directory()

        except Exception as e:
            print(f"Cleanup error: {e}")

    def run(self) -> int:
        """Run the application"""
        try:
            # Initialize application
            if not self.initialize_application():
                return 1

            # Process command line arguments
            self.process_command_line_args()

            # Enter event loop
            return self.exec()

        except Exception as e:
            self.show_error_message("Application Error", str(e))
            return 1


def setup_high_dpi_support() -> None:
    """Setup high DPI support for the application"""
    try:
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        # High DPI support is optional
        pass


def setup_style() -> None:
    """Setup application style"""
    try:
        app = QApplication.instance()
        if app:
            # Set a modern style if available
            app.setStyle("Fusion")

            # Set default font
            font = QFont("Segoe UI", 9)
            app.setFont(font)

    except Exception:
        # Style setup is optional
        pass


def check_dependencies() -> bool:
    """Check if required dependencies are available"""
    try:
        import cv2
        import numpy
        from PySide6 import QtMultimedia
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False


def main() -> int:
    """Main entry point"""
    try:
        # Setup high DPI support before creating QApplication
        setup_high_dpi_support()

        # Check dependencies
        if not check_dependencies():
            print("Error: Missing required dependencies")
            print("Please install: pip install PySide6 opencv-python numpy")
            return 1

        # Create and run application
        app = VideoFrameCaptureApp(sys.argv)

        # Setup application style
        setup_style()

        # Run application
        return app.run()

    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


# Entry point for direct execution
if __name__ == "__main__":
    sys.exit(main())


# Additional utilities for development and deployment
def create_desktop_shortcut():
    """Create desktop shortcut (for installers)"""
    # This would be implemented for deployment
    pass


def register_file_associations():
    """Register file associations (for installers)"""
    # This would be implemented for deployment
    pass


def get_application_info() -> dict:
    """Get application information"""
    return {
        "name": "Video Frame Capture",
        "version": "0.1.0",
        "description": "Desktop application for video frame capture and export",
        "author": "Video Frame Capture Team",
        "license": "MIT",
        "python_requires": ">=3.9",
        "dependencies": [
            "PySide6>=6.6.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
            "Pillow>=10.0.0",
        ],
    }