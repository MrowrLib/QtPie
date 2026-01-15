"""ReactiveTableModel - QAbstractTableModel backed by ObservableList."""

from collections.abc import Callable, Sequence
from dataclasses import fields, is_dataclass
from typing import Any, cast, override

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

        # With checkable bool columns (auto-detected or explicit)
        model = ReactiveTableModel(dogs, checkable=["active"])  # Explicit
        model = ReactiveTableModel(dogs, checkable=None)  # Auto-detect bool fields
        model = ReactiveTableModel(dogs, checkable=False)  # Disable checkboxes
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        parent: QObject | None = None,
        *,
        columns: Sequence[str | int] | None = None,
        headers: dict[str | int, str] | None = None,
        format_fns: dict[str | int, Callable[[Any], str]] | None = None,
        checkable: list[str] | bool | None = None,
        checkable_text: str | dict[str, str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._headers: dict[str | int, str] = headers or {}
        self._format_fns = format_fns or {}
        self._checkable = checkable  # None=auto-detect, list=explicit, False=none
        self._checkable_text = checkable_text  # None=no text, str=all columns, dict=per-column

        # Determine columns - explicit or auto-detect from first item or dataclass
        self._columns_explicit = columns is not None
        self._columns: list[str | int]
        if columns is not None:
            self._columns = list(columns)
        else:
            self._columns = self._auto_detect_columns()

        # Resolve checkable columns after columns are known
        self._checkable_columns: set[str] = self._resolve_checkable_columns()

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

    def _auto_detect_columns(self) -> list[str | int]:
        """Auto-detect columns from dataclass type or first item."""
        # Try to get from first item
        if len(self._obs_list) > 0:
            item = self._obs_list[0]
            if is_dataclass(item) and not isinstance(item, type):
                return [f.name for f in fields(item)]
            # Handle tuples/sequences (e.g., dict items converted to (key, value) tuples)
            if isinstance(item, tuple):
                return list(range(len(cast(tuple[Any, ...], item))))  # [0, 1] for 2-tuple, etc.
            # For regular objects, use public attributes that aren't methods
            return [attr for attr in dir(item) if not attr.startswith("_") and not callable(getattr(item, attr, None))]
        return []

    def _resolve_checkable_columns(self) -> set[str]:
        """Resolve which columns should be checkable (have checkboxes)."""
        if self._checkable is False:
            return set()
        if isinstance(self._checkable, list):
            return set(self._checkable)
        # Auto-detect: find bool fields from first item
        if len(self._obs_list) > 0:
            item = self._obs_list[0]
            if is_dataclass(item) and not isinstance(item, type):
                return {f.name for f in fields(item) if f.type is bool or f.type == "bool"}
        return set()

    def _get_checkable_text_format(self, column_name: str) -> str | None:
        """Get the text format for a checkable column."""
        if self._checkable_text is None:
            return None
        if isinstance(self._checkable_text, str):
            return self._checkable_text  # Same format for all
        # At this point, it must be dict[str, str]
        return self._checkable_text.get(column_name)

    def _format_checkable_text(self, format_str: str, item: T, row: int, column_name: str) -> str:
        """Format checkable text using expression evaluator."""
        from qtpie.bindings.format_binding import create_item_formatter_with_context

        # Get the bool value for this column
        value = getattr(item, column_name, False)

        # Create formatter with additional context for #index and #value
        formatter = create_item_formatter_with_context(format_str)
        return formatter(item, {"index": row, "value": value})

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
            # Handle checkable columns
            if column_name in self._checkable_columns:
                text_format = self._get_checkable_text_format(column_name)
                if text_format is None:
                    return ""  # Checkbox only, no text
                return self._format_checkable_text(text_format, item, row, column_name)

            # Get the attribute value
            # Handle both string attributes (getattr) and integer indices (item[i])
            value: Any
            if isinstance(column_name, int):
                # Integer column = index access (for tuples/lists)
                try:
                    value = item[column_name]  # type: ignore[index]
                except (IndexError, KeyError, TypeError):
                    value = None
            else:
                # String column = attribute access
                value = getattr(item, column_name, None)

            # Apply format function if available
            if column_name in self._format_fns:
                return self._format_fns[column_name](value)

            return str(cast(Any, value)) if value is not None else ""

        elif role == Qt.ItemDataRole.CheckStateRole:
            # Return check state for checkable columns
            if column_name in self._checkable_columns:
                value = getattr(item, column_name, False)
                return Qt.CheckState.Checked if value else Qt.CheckState.Unchecked
            return None

        elif role == Qt.ItemDataRole.UserRole:
            # Return the actual item for programmatic access
            return item

        return None

    @override
    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        """Set data for the given index (handles checkbox state changes)."""
        if not index.isValid():
            return False

        if role == Qt.ItemDataRole.CheckStateRole:
            row = index.row()
            col = index.column()

            if row < 0 or row >= len(self._obs_list):
                return False
            if col < 0 or col >= len(self._columns):
                return False

            column_name = self._columns[col]
            if column_name not in self._checkable_columns:
                return False

            item = self._obs_list[row]
            # Qt.CheckState.Checked.value is 2, Unchecked.value is 0
            new_value = value == Qt.CheckState.Checked.value
            setattr(item, column_name, new_value)
            self.dataChanged.emit(index, index, [role])
            return True

        return False

    @override
    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        """Return flags for the given index."""
        base_flags = super().flags(index)
        if not index.isValid():
            return base_flags

        col = index.column()
        if col < 0 or col >= len(self._columns):
            return base_flags

        column_name = self._columns[col]
        if column_name in self._checkable_columns:
            return base_flags | Qt.ItemFlag.ItemIsUserCheckable
        return base_flags

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
                # Use custom header if provided
                if column_name in self._headers:
                    return self._headers.get(column_name)
                # Default: capitalize the field name (only for string columns)
                if isinstance(column_name, str):
                    return column_name.replace("_", " ").title()
                # Integer columns with no header - use "Column N"
                return f"Column {column_name}"

        elif orientation == Qt.Orientation.Vertical:
            return str(section + 1)

        return None

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        # Re-detect columns if we had none and columns weren't explicit
        if not self._columns_explicit and not self._columns:
            new_columns = self._auto_detect_columns()
            if new_columns:
                self.beginResetModel()
                self._columns = new_columns
                # Set default headers for tuple columns (from dict bindings)
                if isinstance(item, tuple) and len(cast(tuple[Any, ...], item)) == 2 and not self._headers:
                    self._headers = {0: "Key", 1: "Value"}
                self.endResetModel()
                return  # Reset already handles the insert
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
    def columns(self) -> list[str | int]:
        """Get the list of column names."""
        return self._columns.copy()
