"""ReactiveTableModel - QAbstractTableModel backed by ObservableList."""

from collections.abc import Callable, Sequence
from dataclasses import fields, is_dataclass
from typing import Any, override

from observant import ObservableList
from qtpy.QtCore import QAbstractTableModel, QModelIndex, QObject, QPersistentModelIndex, Qt


class ReactiveTableModel[T](QAbstractTableModel):
    """QAbstractTableModel backed by ObservableList[T].

    Emits proper Qt model signals when the ObservableList changes:
    - on_insert -> beginInsertRows/endInsertRows
    - on_remove -> beginRemoveRows/endRemoveRows
    - on_replace -> dataChanged
    - on_clear -> beginResetModel/endResetModel

    Usage:
        # Auto-detect columns from dataclass fields
        dogs = ObservableList([Dog("Fido", 3), Dog("Rex", 5)])
        model = ReactiveTableModel(dogs)
        table.setModel(model)

        # Explicit columns
        model = ReactiveTableModel(dogs, columns=["name", "age"])

        # With custom formatters per column
        model = ReactiveTableModel(dogs, columns=["name", "age"], format_fns={"age": lambda x: f"{x} years"})
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        parent: QObject | None = None,
        *,
        columns: Sequence[str] | None = None,
        headers: dict[str, str] | None = None,
        format_fns: dict[str, Callable[[Any], str]] | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._headers = headers or {}
        self._format_fns = format_fns or {}

        # Determine columns - explicit or auto-detect from first item or dataclass
        if columns is not None:
            self._columns = list(columns)
        else:
            self._columns = self._auto_detect_columns()

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

    def _auto_detect_columns(self) -> list[str]:
        """Auto-detect columns from dataclass type or first item."""
        # Try to get from first item
        if len(self._obs_list) > 0:
            item = self._obs_list[0]
            if is_dataclass(item) and not isinstance(item, type):
                return [f.name for f in fields(item)]
            # For regular objects, use public attributes that aren't methods
            return [attr for attr in dir(item) if not attr.startswith("_") and not callable(getattr(item, attr, None))]
        return []

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        """Return number of rows in the model."""
        if parent is not None and parent.isValid():
            return 0
        return len(self._obs_list)

    @override
    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        """Return number of columns in the model."""
        if parent is not None and parent.isValid():
            return 0
        return len(self._columns)

    @override
    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._obs_list):
            return None
        if col < 0 or col >= len(self._columns):
            return None

        item = self._obs_list[row]
        column_name = self._columns[col]

        if role == Qt.ItemDataRole.DisplayRole:
            # Get the attribute value
            value = getattr(item, column_name, None)

            # Apply format function if available
            if column_name in self._format_fns:
                return self._format_fns[column_name](value)

            return str(value) if value is not None else ""

        elif role == Qt.ItemDataRole.UserRole:
            # Return the actual item for programmatic access
            return item

        return None

    @override
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return header data for the given section."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._columns):
                column_name = self._columns[section]
                # Use custom header if provided, otherwise capitalize the field name
                return self._headers.get(column_name, column_name.replace("_", " ").title())

        elif orientation == Qt.Orientation.Vertical:
            return str(section + 1)

        return None

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        self.beginInsertRows(QModelIndex(), index, index)
        self.endInsertRows()

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        self.beginRemoveRows(QModelIndex(), index, index)
        self.endRemoveRows()

    def _on_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle item replacement."""
        top_left = self.index(index, 0)
        bottom_right = self.index(index, len(self._columns) - 1)
        self.dataChanged.emit(top_left, bottom_right)

    def _on_clear(self, items: list[T]) -> None:
        """Handle list clear."""
        self.beginResetModel()
        self.endResetModel()

    # Convenience methods

    def item_at(self, row: int) -> T | None:
        """Get the item at a given row."""
        if 0 <= row < len(self._obs_list):
            return self._obs_list[row]
        return None

    def index_of(self, item: T) -> int:
        """Find the row index of an item, returns -1 if not found."""
        try:
            return list(self._obs_list).index(item)
        except ValueError:
            return -1

    @property
    def columns(self) -> list[str]:
        """Get the list of column names."""
        return self._columns.copy()
