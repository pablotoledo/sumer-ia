"""
Data model for thumbnail gallery with selection support.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, Signal, QSize
from PySide6.QtGui import QPixmap


class ThumbnailModel(QAbstractListModel):
    """Custom model for thumbnail gallery with lazy loading and selection"""

    # Signals
    selectionChanged = Signal()  # Selection state changed

    def __init__(self, parent: Optional[QAbstractListModel] = None):
        super().__init__(parent)
        self._thumbnails: List[Dict[str, Any]] = []
        self._selected_indices: set = set()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of thumbnails"""
        return len(self._thumbnails)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return data for given index and role"""
        if not index.isValid() or index.row() >= len(self._thumbnails):
            return None

        thumbnail = self._thumbnails[index.row()]

        if role == Qt.DecorationRole:
            # Return the pixmap for display
            pixmap = thumbnail.get("pixmap")
            if pixmap and not pixmap.isNull():
                # Si el pixmap es muy grande, escalarlo aquí también
                if pixmap.width() > 160 or pixmap.height() > 120:
                    return pixmap.scaled(160, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                return pixmap
            return None

        elif role == Qt.DisplayRole:
            # Return timestamp as display text
            timestamp = thumbnail.get("timestamp", 0)
            # Formatear mejor el timestamp
            seconds = timestamp / 1000.0
            return f"{seconds:.1f}s"

        elif role == Qt.CheckStateRole:
            # Return selection state
            return Qt.Checked if index.row() in self._selected_indices else Qt.Unchecked

        elif role == Qt.UserRole:
            # Return complete thumbnail data
            return thumbnail

        elif role == Qt.SizeHintRole:
            # Return preferred size for item
            return QSize(160, 140)

        elif role == Qt.ToolTipRole:
            # Return tooltip text
            timestamp = thumbnail.get("timestamp", 0)
            file_path = thumbnail.get("file_path", "Unknown")
            original_pixmap = thumbnail.get("original_pixmap")
            display_pixmap = thumbnail.get("pixmap")

            filename = file_path.split("/")[-1] if "/" in file_path else file_path
            filename = file_path.split("\\")[-1] if "\\" in file_path else filename

            if original_pixmap:
                size_text = f"{original_pixmap.width()}x{original_pixmap.height()} (original)"
            elif display_pixmap:
                size_text = f"{display_pixmap.width()}x{display_pixmap.height()}"
            else:
                size_text = "Unknown"

            return f"Timestamp: {timestamp}ms\nSource: {filename}\nSize: {size_text}"

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """Set data for given index and role"""
        if not index.isValid() or index.row() >= len(self._thumbnails):
            return False

        if role == Qt.CheckStateRole:
            # Handle selection state changes
            if value == Qt.Checked:
                self._selected_indices.add(index.row())
            else:
                self._selected_indices.discard(index.row())

            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            self.selectionChanged.emit()
            return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return item flags"""
        if not index.isValid():
            return Qt.NoItemFlags

        return (
            Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
            | Qt.ItemIsUserCheckable
        )

    def add_thumbnail(self, display_pixmap: QPixmap, original_pixmap: QPixmap, timestamp: int, file_path: str) -> None:
        """Add new thumbnail to model with both display and original versions"""
        row = len(self._thumbnails)

        self.beginInsertRows(QModelIndex(), row, row)
        self._thumbnails.append({
            "pixmap": display_pixmap,          # Para mostrar en la UI (thumbnail)
            "original_pixmap": original_pixmap, # Para exportar (tamaño completo)
            "timestamp": timestamp,
            "file_path": file_path,
            "capture_time": None,  # Could store when frame was captured
        })
        self.endInsertRows()

    def remove_thumbnail(self, row: int) -> bool:
        """Remove thumbnail at given row"""
        if 0 <= row < len(self._thumbnails):
            self.beginRemoveRows(QModelIndex(), row, row)

            # Remove from thumbnails list
            del self._thumbnails[row]

            # Update selected indices (remove and adjust)
            new_selected = set()
            for idx in self._selected_indices:
                if idx < row:
                    new_selected.add(idx)
                elif idx > row:
                    new_selected.add(idx - 1)
                # Skip idx == row (it's being removed)

            self._selected_indices = new_selected

            self.endRemoveRows()
            self.selectionChanged.emit()
            return True

        return False

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Remove single row (required by QAbstractItemModel)"""
        return self.remove_thumbnail(row)

    def clear_all(self) -> None:
        """Clear all thumbnails"""
        if self._thumbnails:
            self.beginResetModel()
            self._thumbnails.clear()
            self._selected_indices.clear()
            self.endResetModel()
            self.selectionChanged.emit()

    def get_selected_thumbnails(self) -> List[Dict[str, Any]]:
        """Get all selected thumbnail data"""
        return [self._thumbnails[i] for i in sorted(self._selected_indices)
                if i < len(self._thumbnails)]

    def get_all_thumbnails(self) -> List[Dict[str, Any]]:
        """Get all thumbnail data"""
        return self._thumbnails.copy()

    def select_all(self) -> None:
        """Select all thumbnails"""
        if not self._thumbnails:
            return

        self._selected_indices = set(range(len(self._thumbnails)))

        # Emit dataChanged for all items
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._thumbnails) - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [Qt.CheckStateRole])
        self.selectionChanged.emit()

    def select_none(self) -> None:
        """Deselect all thumbnails"""
        if not self._selected_indices:
            return

        selected_rows = list(self._selected_indices)
        self._selected_indices.clear()

        # Emit dataChanged for previously selected items
        for row in selected_rows:
            if row < len(self._thumbnails):
                idx = self.index(row, 0)
                self.dataChanged.emit(idx, idx, [Qt.CheckStateRole])

        self.selectionChanged.emit()

    def toggle_selection(self, row: int) -> bool:
        """Toggle selection state of thumbnail at row"""
        if 0 <= row < len(self._thumbnails):
            index = self.index(row, 0)
            current_state = self.data(index, Qt.CheckStateRole)
            new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
            return self.setData(index, new_state, Qt.CheckStateRole)
        return False

    def get_selection_count(self) -> int:
        """Get number of selected thumbnails"""
        return len(self._selected_indices)

    def is_selected(self, row: int) -> bool:
        """Check if thumbnail at row is selected"""
        return row in self._selected_indices

    def get_thumbnail_at(self, row: int) -> Optional[Dict[str, Any]]:
        """Get thumbnail data at specific row"""
        if 0 <= row < len(self._thumbnails):
            return self._thumbnails[row]
        return None

    def find_thumbnail_by_timestamp(self, timestamp: int) -> int:
        """Find thumbnail row by timestamp (returns -1 if not found)"""
        for i, thumbnail in enumerate(self._thumbnails):
            if thumbnail.get("timestamp") == timestamp:
                return i
        return -1

    def get_statistics(self) -> Dict[str, Any]:
        """Get model statistics"""
        if not self._thumbnails:
            return {
                "total_count": 0,
                "selected_count": 0,
                "timestamp_range": (0, 0),
                "total_memory_estimate": 0,
            }

        timestamps = [t.get("timestamp", 0) for t in self._thumbnails]

        # Estimate memory usage (rough calculation)
        total_memory = 0
        for thumbnail in self._thumbnails:
            # Count both original and display pixmaps
            original_pixmap = thumbnail.get("original_pixmap")
            display_pixmap = thumbnail.get("pixmap")

            if original_pixmap:
                total_memory += original_pixmap.width() * original_pixmap.height() * 4
            if display_pixmap:
                total_memory += display_pixmap.width() * display_pixmap.height() * 4

        return {
            "total_count": len(self._thumbnails),
            "selected_count": len(self._selected_indices),
            "timestamp_range": (min(timestamps), max(timestamps)),
            "total_memory_estimate": total_memory,
        }