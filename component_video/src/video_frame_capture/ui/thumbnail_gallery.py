"""
Thumbnail gallery widget with selection and export capabilities.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListView,
    QPushButton,
    QLabel,
    QCheckBox,
    QProgressBar,
    QMessageBox,
    QMenu,
    QSizePolicy,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QApplication,
    QStyle,
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QModelIndex, QThread, QRect, QEvent
from PySide6.QtGui import QAction, QContextMenuEvent, QPainter, QFontMetrics, QMouseEvent

from ..models.thumbnail_model import ThumbnailModel
from ..core.memory_manager import MemoryManager
from ..workers.export_worker import ExportWorker


class ThumbnailItemDelegate(QStyledItemDelegate):
    """Custom delegate for thumbnail items with checkbox overlay"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Custom paint method"""
        painter.save()

        # Get data
        pixmap = index.data(Qt.DecorationRole)
        text = index.data(Qt.DisplayRole)
        is_checked = index.data(Qt.CheckStateRole) == Qt.Checked

        # Calculate rects
        rect = option.rect
        pixmap_rect = QRect(rect.x() + 10, rect.y() + 10, 160, 120)
        text_rect = QRect(rect.x(), pixmap_rect.bottom() + 5, rect.width(), 20)
        checkbox_rect = QRect(rect.x() + 5, rect.y() + 5, 20, 20)

        # Draw selection background
        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        # Draw pixmap if available
        if pixmap and not pixmap.isNull():
            # Scale pixmap to fit
            scaled_pixmap = pixmap.scaled(160, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Center the pixmap
            pixmap_x = pixmap_rect.x() + (pixmap_rect.width() - scaled_pixmap.width()) // 2
            pixmap_y = pixmap_rect.y() + (pixmap_rect.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(pixmap_x, pixmap_y, scaled_pixmap)

            # Draw border around pixmap
            painter.setPen(Qt.lightGray)
            painter.drawRect(pixmap_x, pixmap_y, scaled_pixmap.width(), scaled_pixmap.height())

        # Draw checkbox
        from PySide6.QtWidgets import QStyleOptionButton
        checkbox_option = QStyleOptionButton()
        checkbox_option.rect = checkbox_rect
        checkbox_option.state = QStyle.State_Enabled
        if is_checked:
            checkbox_option.state |= QStyle.State_On
        else:
            checkbox_option.state |= QStyle.State_Off

        style = QApplication.style()
        style.drawPrimitive(QStyle.PE_IndicatorCheckBox, checkbox_option, painter)

        # Draw text
        if text:
            painter.setPen(option.palette.text().color())
            painter.drawText(text_rect, Qt.AlignCenter, text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Return size hint for item"""
        return QSize(180, 160)

    def editorEvent(self, event, model, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """Handle checkbox clicks"""
        if event.type() == QEvent.MouseButtonPress:
            checkbox_rect = QRect(option.rect.x() + 5, option.rect.y() + 5, 20, 20)
            if checkbox_rect.contains(event.pos()):
                # Toggle checkbox
                current_state = index.data(Qt.CheckStateRole)
                new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                return model.setData(index, new_state, Qt.CheckStateRole)
        return False


class ThumbnailListView(QListView):
    """Custom list view for thumbnails with context menu"""

    contextMenuRequested = Signal(QModelIndex, object)  # index, global_pos

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setSelectionMode(QListView.ExtendedSelection)
        self.setMovement(QListView.Static)
        self.setSpacing(10)
        self.setGridSize(QSize(180, 160))
        self.setUniformItemSizes(True)

        # Set custom delegate
        self.setItemDelegate(ThumbnailItemDelegate(self))

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Handle context menu requests"""
        index = self.indexAt(event.pos())
        self.contextMenuRequested.emit(index, event.globalPos())


class ThumbnailGalleryWidget(QWidget):
    """Widget for displaying and managing captured frame thumbnails"""

    # Signals
    frameSelected = Signal(object)  # Selected frame data
    exportRequested = Signal()  # Export requested
    exportProgress = Signal(int, str)  # Progress percentage, status message
    exportCompleted = Signal(str)  # Export file path
    captureRequested = Signal()  # Capture frame requested

    def __init__(self, memory_manager: MemoryManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.memory_manager = memory_manager
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Data model
        self.thumbnail_model = ThumbnailModel()

        # Export worker
        self.export_worker = None
        self.export_thread = None

        # Control flags
        self._updating_select_all = False

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Header with title and count
        header_layout = QHBoxLayout()

        self.title_label = QLabel("Captured Frames")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.count_label = QLabel("0 frames")
        self.count_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.count_label)

        layout.addLayout(header_layout)

        # Selection controls
        selection_layout = QHBoxLayout()

        self.select_all_checkbox = QCheckBox("Select All")
        selection_layout.addWidget(self.select_all_checkbox)

        selection_layout.addStretch()

        self.selected_count_label = QLabel("0 selected")
        self.selected_count_label.setStyleSheet("color: #666; font-size: 12px;")
        selection_layout.addWidget(self.selected_count_label)

        layout.addLayout(selection_layout)

        # Thumbnail list view
        self.thumbnail_list = ThumbnailListView()
        self.thumbnail_list.setModel(self.thumbnail_model)
        layout.addWidget(self.thumbnail_list)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Action buttons
        button_layout = QHBoxLayout()

        self.capture_btn = QPushButton("📸 Capture Current Frame")
        self.capture_btn.setMinimumHeight(35)
        button_layout.addWidget(self.capture_btn)

        self.export_selected_btn = QPushButton("📤 Export Selected")
        self.export_selected_btn.setMinimumHeight(35)
        self.export_selected_btn.setEnabled(False)
        button_layout.addWidget(self.export_selected_btn)

        self.clear_btn = QPushButton("🗑 Clear All")
        self.clear_btn.setMinimumHeight(35)
        button_layout.addWidget(self.clear_btn)

        layout.addLayout(button_layout)

    def connect_signals(self) -> None:
        """Connect signals"""
        # Model signals
        self.thumbnail_model.dataChanged.connect(self._on_selection_changed)
        self.thumbnail_model.selectionChanged.connect(self._on_selection_changed)
        self.thumbnail_model.rowsInserted.connect(self._on_frame_count_changed)
        self.thumbnail_model.rowsRemoved.connect(self._on_frame_count_changed)

        # List view signals
        self.thumbnail_list.clicked.connect(self._on_thumbnail_clicked)
        self.thumbnail_list.contextMenuRequested.connect(self._show_context_menu)

        # Control signals
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        self.capture_btn.clicked.connect(self._request_frame_capture)
        self.export_selected_btn.clicked.connect(self._export_selected)
        self.clear_btn.clicked.connect(self._clear_all)

    def add_frame(self, pixmap, timestamp: int, file_path: str) -> None:
        """Add a captured frame to the gallery"""
        # Crear thumbnail para visualización
        thumbnail_size = QSize(160, 120)
        thumbnail_pixmap = pixmap.scaled(
            thumbnail_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # Cache el thumbnail para visualización
        cache_key = f"thumbnail_{timestamp}_{file_path}"
        thumbnail_size_bytes = thumbnail_pixmap.width() * thumbnail_pixmap.height() * 4
        self.memory_manager.cache_thumbnail(cache_key, thumbnail_pixmap, thumbnail_size_bytes)

        # Guardar AMBAS versiones en el modelo: thumbnail para mostrar y original para exportar
        self.thumbnail_model.add_thumbnail(
            display_pixmap=thumbnail_pixmap,  # Para mostrar en la UI
            original_pixmap=pixmap,           # Para exportar en tamaño completo
            timestamp=timestamp,
            file_path=file_path
        )

        # Update UI
        self._update_frame_count()

    def get_frame_count(self) -> int:
        """Get total number of captured frames"""
        return self.thumbnail_model.rowCount()

    def get_selected_count(self) -> int:
        """Get number of selected frames"""
        return len(self.thumbnail_model.get_selected_thumbnails())

    def export_all_frames(self, file_path: str) -> None:
        """Export all frames to ZIP file"""
        all_thumbnails = []
        for i in range(self.thumbnail_model.rowCount()):
            index = self.thumbnail_model.index(i, 0)
            thumbnail_data = self.thumbnail_model.data(index, Qt.UserRole)
            if thumbnail_data:
                all_thumbnails.append(thumbnail_data)

        if all_thumbnails:
            # Convertir thumbnails para usar imágenes originales para exportación
            export_data = []
            for thumbnail in all_thumbnails:
                export_frame = thumbnail.copy()
                # Usar la imagen original en lugar del thumbnail para exportar
                export_frame["pixmap"] = thumbnail.get("original_pixmap", thumbnail.get("pixmap"))
                export_data.append(export_frame)

            self._start_export(export_data, file_path)

    def export_selected_frames(self, file_path: str) -> None:
        """Export selected frames to ZIP file"""
        selected_thumbnails = self.thumbnail_model.get_selected_thumbnails()
        if selected_thumbnails:
            # Convertir thumbnails para usar imágenes originales para exportación
            export_data = []
            for thumbnail in selected_thumbnails:
                export_frame = thumbnail.copy()
                # Usar la imagen original en lugar del thumbnail para exportar
                export_frame["pixmap"] = thumbnail.get("original_pixmap", thumbnail.get("pixmap"))
                export_data.append(export_frame)

            self._start_export(export_data, file_path)

    def clear_all_frames(self) -> None:
        """Clear all captured frames"""
        self.thumbnail_model.clear_all()
        self.memory_manager.clear_thumbnail_cache()
        self._update_frame_count()

    def _start_export(self, thumbnails: List[Dict[str, Any]], file_path: str) -> None:
        """Start export process in background thread"""
        if self.export_worker and self.export_thread:
            return  # Export already in progress

        # Create worker and thread
        self.export_worker = ExportWorker(thumbnails, file_path)
        self.export_thread = QThread()

        # Connect signals from worker.signals (not worker directly)
        self.export_worker.signals.progress.connect(self._on_export_progress)
        self.export_worker.signals.finished.connect(self._on_export_finished)
        self.export_worker.signals.error.connect(self._on_export_error)

        # Use thread pool instead of moveToThread
        from PySide6.QtCore import QThreadPool
        self.progress_bar.setVisible(True)
        self.export_selected_btn.setEnabled(False)

        # Run in thread pool
        QThreadPool.globalInstance().start(self.export_worker)

    @Slot(QModelIndex)
    def _on_thumbnail_clicked(self, index: QModelIndex) -> None:
        """Handle thumbnail click"""
        if index.isValid():
            thumbnail_data = self.thumbnail_model.data(index, Qt.UserRole)
            if thumbnail_data:
                self.frameSelected.emit(thumbnail_data)

    @Slot(QModelIndex, object)
    def _show_context_menu(self, index: QModelIndex, global_pos) -> None:
        """Show context menu for thumbnail"""
        if not index.isValid():
            return

        menu = QMenu(self)

        # Remove action
        remove_action = QAction("Remove Frame", self)
        remove_action.triggered.connect(lambda: self._remove_frame(index))
        menu.addAction(remove_action)

        # Show frame info action
        info_action = QAction("Frame Info", self)
        info_action.triggered.connect(lambda: self._show_frame_info(index))
        menu.addAction(info_action)

        menu.exec(global_pos)

    def _remove_frame(self, index: QModelIndex) -> None:
        """Remove a specific frame"""
        if index.isValid():
            self.thumbnail_model.removeRow(index.row())
            self._update_frame_count()

    def _show_frame_info(self, index: QModelIndex) -> None:
        """Show frame information"""
        if index.isValid():
            thumbnail_data = self.thumbnail_model.data(index, Qt.UserRole)
            if thumbnail_data:
                timestamp = thumbnail_data.get("timestamp", 0)
                file_path = thumbnail_data.get("file_path", "Unknown")
                original_pixmap = thumbnail_data.get("original_pixmap")
                display_pixmap = thumbnail_data.get("pixmap")

                # Usar imagen original para mostrar el tamaño real
                if original_pixmap:
                    size_text = f"{original_pixmap.width()}x{original_pixmap.height()} pixels (original)"
                elif display_pixmap:
                    size_text = f"{display_pixmap.width()}x{display_pixmap.height()} pixels"
                else:
                    size_text = "Unknown"

                info_text = f"""
Frame Information:
- Timestamp: {timestamp}ms
- Source: {file_path}
- Size: {size_text}
- Display thumbnail: {display_pixmap.width() if display_pixmap else 0}x{display_pixmap.height() if display_pixmap else 0} pixels
                """.strip()

                QMessageBox.information(self, "Frame Info", info_text)

    @Slot(int)
    def _on_select_all_changed(self, state: int) -> None:
        """Handle select all checkbox"""
        # Evitar loops cuando el checkbox se actualiza automáticamente
        if hasattr(self, '_updating_select_all') and self._updating_select_all:
            return

        # Determinar si debe seleccionar o deseleccionar todo
        if state == Qt.Checked.value:
            # Seleccionar todos
            for i in range(self.thumbnail_model.rowCount()):
                index = self.thumbnail_model.index(i, 0)
                self.thumbnail_model.setData(index, Qt.Checked, Qt.CheckStateRole)
        elif state == Qt.Unchecked.value:
            # Deseleccionar todos
            for i in range(self.thumbnail_model.rowCount()):
                index = self.thumbnail_model.index(i, 0)
                self.thumbnail_model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
        # No hacer nada para Qt.PartiallyChecked

    @Slot()
    def _on_selection_changed(self) -> None:
        """Handle selection changes"""
        selected_count = self.get_selected_count()
        total_count = self.get_frame_count()

        # Update UI labels and buttons
        self.selected_count_label.setText(f"{selected_count} selected")
        self.export_selected_btn.setEnabled(selected_count > 0)

        # Update select all checkbox (evitar loops)
        self._updating_select_all = True
        try:
            if selected_count == 0:
                self.select_all_checkbox.setCheckState(Qt.Unchecked)
            elif selected_count == total_count and total_count > 0:
                self.select_all_checkbox.setCheckState(Qt.Checked)
            else:
                self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
        finally:
            self._updating_select_all = False

    @Slot()
    def _on_frame_count_changed(self) -> None:
        """Handle frame count changes"""
        self._update_frame_count()

    def _update_frame_count(self) -> None:
        """Update frame count display"""
        count = self.get_frame_count()
        self.count_label.setText(f"{count} frames")
        self.capture_btn.setEnabled(True)  # Always allow capture
        self.clear_btn.setEnabled(count > 0)

    @Slot()
    def _request_frame_capture(self) -> None:
        """Request frame capture from current video position"""
        # Emit signal to request frame capture
        # The main window will handle the actual capture
        self.captureRequested.emit()

    @Slot()
    def _export_selected(self) -> None:
        """Export selected frames"""
        self.exportRequested.emit()

    @Slot()
    def _clear_all(self) -> None:
        """Clear all frames with confirmation"""
        reply = QMessageBox.question(
            self,
            "Clear All Frames",
            "Are you sure you want to remove all captured frames?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.clear_all_frames()

    @Slot(int, str)
    def _on_export_progress(self, percentage: int, message: str) -> None:
        """Handle export progress updates"""
        self.progress_bar.setValue(percentage)
        self.exportProgress.emit(percentage, message)

    @Slot(str)
    def _on_export_finished(self, file_path: str) -> None:
        """Handle export completion"""
        self.progress_bar.setVisible(False)
        self.export_selected_btn.setEnabled(self.get_selected_count() > 0)
        self.export_worker = None
        self.export_thread = None
        self.exportCompleted.emit(file_path)

        QMessageBox.information(self, "Export Complete", f"Frames exported to:\n{file_path}")
        print(f"DEBUG: Export completed successfully to: {file_path}")

    @Slot(str)
    def _on_export_error(self, error_message: str) -> None:
        """Handle export errors"""
        self.progress_bar.setVisible(False)
        self.export_selected_btn.setEnabled(self.get_selected_count() > 0)
        self.export_worker = None
        self.export_thread = None

        print(f"DEBUG: Export error: {error_message}")
        QMessageBox.critical(self, "Export Error", f"Export failed:\n{error_message}")