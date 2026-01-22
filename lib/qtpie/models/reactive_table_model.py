"""ReactiveTableModel - QAbstractTableModel backed by ObservableList."""

from collections.abc import Callable, Sequence
from dataclasses import fields, is_dataclass
from typing import Any, cast, override

from observant import ObservableDict, ObservableList, ObservableProxy
from qtpy.QtCore import QAbstractTableModel, QModelIndex, QObject, QPersistentModelIndex, Qt

from .dict_sync import DictToTupleListSync

# Custom role for getting the ObservableProxy wrapper for an item
# This enables dirty/valid state tracking per-item
TABLE_PROXY_ROLE = Qt.ItemDataRole.UserRole + 1

# Special column name for dict key access
DICT_KEY_COLUMN = "#key"


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

        # Dict binding with #key column
        model = ReactiveTableModel(
            obs_list,  # List of (key, value) tuples
            columns=["#key", "value", "enabled"],  # #key accesses dict key
            dict_sync=DictToTupleListSync(source_dict),  # For editing support
        )
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
        editable: list[str | int] | bool | None = None,
        source_dict: ObservableDict[Any, Any] | dict[Any, Any] | None = None,
        dict_sync: DictToTupleListSync[Any, Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._headers: dict[str | int, str] = headers or {}
        self._format_fns = format_fns or {}
        self._checkable = checkable  # None=auto-detect, list=explicit, False=none
        self._checkable_text = checkable_text  # None=no text, str=all columns, dict=per-column
        self._editable = editable  # None/False=none, True=all, list=specific columns
        self._source_dict: ObservableDict[Any, Any] | dict[Any, Any] | None = source_dict  # For dict bindings
        self._dict_sync: DictToTupleListSync[Any, Any] | None = dict_sync  # For #key column support

        # Determine columns - explicit or auto-detect from first item or dataclass
        self._columns_explicit = columns is not None
        self._columns: list[str | int]
        if columns is not None:
            self._columns = list(columns)
        else:
            self._columns = self._auto_detect_columns()

        # Resolve checkable columns after columns are known
        self._checkable_columns: set[str] = self._resolve_checkable_columns()
        # Resolve editable columns
        self._editable_columns: set[str | int] = self._resolve_editable_columns()

        # Cache of ObservableProxy per item (keyed by id(item))
        # This enables per-item dirty/valid state tracking
        self._item_proxies: dict[int, ObservableProxy[T]] = {}

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
            # BUT: Variable fields are callable (have __call__), so check for Variable-like objects
            # Exclude State-specific attributes that shouldn't be columns
            excluded_attrs = {"state_parent"}

            def is_data_attr(attr: str) -> bool:
                if attr in excluded_attrs:
                    return False
                val = getattr(item, attr, None)
                # Variable-like objects (have .value and .observable) ARE data fields
                if hasattr(val, "value") and hasattr(val, "observable"):
                    return True
                # Exclude Event objects (have .emit but no .value)
                if hasattr(val, "emit") and not hasattr(val, "value"):
                    return False
                # Exclude callables (methods/functions)
                return not callable(val)

            return [attr for attr in dir(item) if not attr.startswith("_") and is_data_attr(attr)]
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

    def _resolve_editable_columns(self) -> set[str | int]:
        """Resolve which columns should be editable."""
        if self._editable is None or self._editable is False:
            return set()
        if self._editable is True:
            # All columns editable
            return set(self._columns)
        if isinstance(self._editable, list):  # pyright: ignore[reportUnnecessaryIsInstance]
            return set(self._editable)
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

    def _is_dict_binding(self) -> bool:
        """Check if this is a dict binding (items are key-value tuples)."""
        return self._source_dict is not None or self._dict_sync is not None

    def _get_value_from_tuple(self, item: Any, column_name: str | int) -> Any:
        """Get a value from a (key, value) tuple item for dict bindings.

        For dict bindings, items are (key, value) tuples. This method handles:
        - "#key" -> returns the key (item[0])
        - integer -> direct index access (item[column])
        - string -> attribute access on the value object (item[1].column)
        """
        if not isinstance(item, tuple) or len(item) < 2:  # pyright: ignore[reportUnknownArgumentType]
            return None

        key, value_obj = item[0], item[1]  # pyright: ignore[reportUnknownVariableType]

        if column_name == DICT_KEY_COLUMN:
            return key  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(column_name, int):
            # Direct tuple index access
            try:
                return item[column_name]  # pyright: ignore[reportUnknownVariableType]
            except (IndexError, TypeError):
                return None
        else:
            # String column = attribute access on value object
            attr_value = getattr(value_obj, column_name, None)  # pyright: ignore[reportUnknownArgumentType]
            # Unwrap Variable to get its value
            if attr_value is not None and hasattr(attr_value, "value") and hasattr(attr_value, "observable"):
                attr_value = attr_value.value  # pyright: ignore[reportUnknownMemberType]
            return attr_value

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

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            # Handle checkable columns (DisplayRole only)
            if role == Qt.ItemDataRole.DisplayRole and column_name in self._checkable_columns:
                text_format = self._get_checkable_text_format(column_name)
                if text_format is None:
                    return ""  # Checkbox only, no text
                # For dict bindings with checkable, get the value object for formatting
                if self._is_dict_binding() and isinstance(item, tuple) and len(item) >= 2:  # pyright: ignore[reportUnknownArgumentType]
                    return self._format_checkable_text(text_format, item[1], row, column_name)  # pyright: ignore[reportUnknownArgumentType]
                return self._format_checkable_text(text_format, item, row, column_name)  # pyright: ignore[reportUnknownArgumentType]

            # Get the attribute value
            value: Any

            # Dict binding: handle #key column and value object properties
            if self._is_dict_binding() and isinstance(item, tuple):
                value = self._get_value_from_tuple(item, column_name)
            elif isinstance(column_name, int):
                # Integer column = index access (for tuples/lists)
                try:
                    value = item[column_name]  # type: ignore[index]
                except (IndexError, KeyError, TypeError):
                    value = None
            else:
                # String column = attribute access
                value = getattr(item, column_name, None)
                # Unwrap Variable to get its value (for State objects with Variable fields)
                if hasattr(value, "value") and hasattr(value, "observable"):
                    value = value.value

            # For EditRole, return raw value (for editor to use)
            if role == Qt.ItemDataRole.EditRole:
                return str(cast(Any, value)) if value is not None else ""

            # For DisplayRole, apply format function if available
            if column_name in self._format_fns:
                return self._format_fns[column_name](value)

            return str(cast(Any, value)) if value is not None else ""

        elif role == Qt.ItemDataRole.CheckStateRole:
            # Return check state for checkable columns
            if column_name in self._checkable_columns:
                # For dict bindings, get value from value object
                if self._is_dict_binding() and isinstance(item, tuple) and len(item) >= 2:  # pyright: ignore[reportUnknownArgumentType]
                    value = getattr(item[1], column_name, False)  # pyright: ignore[reportUnknownArgumentType]
                else:
                    value = getattr(item, column_name, False)  # pyright: ignore[reportUnknownArgumentType]
                # Unwrap Variable to get its value (for State objects with Variable fields)
                if hasattr(value, "value") and hasattr(value, "observable"):
                    value = value.value
                return Qt.CheckState.Checked if value else Qt.CheckState.Unchecked
            return None

        elif role == Qt.ItemDataRole.UserRole:
            # Return the actual item for programmatic access
            # For dict bindings, return the value object (not the tuple)
            if self._is_dict_binding() and isinstance(item, tuple) and len(item) >= 2:  # pyright: ignore[reportUnknownArgumentType]
                return item[1]  # pyright: ignore[reportUnknownVariableType]
            return item  # pyright: ignore[reportUnknownVariableType]
        elif role == TABLE_PROXY_ROLE:
            # Return the ObservableProxy for this item (creates one if needed)
            # For dict bindings, proxy the value object
            if self._is_dict_binding() and isinstance(item, tuple) and len(item) >= 2:  # pyright: ignore[reportUnknownArgumentType]
                return self.proxy_for_item(item[1])  # pyright: ignore[reportUnknownArgumentType]
            return self.proxy_for_item(item)  # pyright: ignore[reportUnknownArgumentType]

        return None

    @override
    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        """Set data for the given index (handles checkbox and edit changes)."""
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()

        if row < 0 or row >= len(self._obs_list):
            return False
        if col < 0 or col >= len(self._columns):
            return False

        column_name = self._columns[col]
        item = self._obs_list[row]

        if role == Qt.ItemDataRole.CheckStateRole:
            if column_name not in self._checkable_columns:
                return False

            # Qt.CheckState.Checked.value is 2, Unchecked.value is 0
            new_value = value == Qt.CheckState.Checked.value

            # For dict bindings, set on value object
            if self._is_dict_binding() and isinstance(item, tuple) and len(item) >= 2:  # pyright: ignore[reportUnknownArgumentType]
                setattr(item[1], column_name, new_value)  # pyright: ignore[reportUnknownArgumentType]
            else:
                setattr(item, column_name, new_value)  # pyright: ignore[reportUnknownArgumentType]
            self.dataChanged.emit(index, index, [role])
            return True

        elif role == Qt.ItemDataRole.EditRole:
            if column_name not in self._editable_columns:
                return False

            # Dict binding with #key column or value properties
            if self._is_dict_binding() and isinstance(item, tuple) and len(item) >= 2:  # pyright: ignore[reportUnknownArgumentType]
                tuple_item = cast(tuple[Any, Any], item)
                old_key = tuple_item[0]
                value_obj = tuple_item[1]

                if column_name == DICT_KEY_COLUMN:
                    # Rename key using dict_sync if available
                    new_key = str(value)
                    if new_key == old_key:
                        return True  # No change needed

                    # Check for key collision
                    source = self._dict_sync.source if self._dict_sync else self._source_dict
                    if source is not None and new_key in source:
                        return False  # Key already exists, reject edit

                    if self._dict_sync:
                        # Use sync adapter for rename
                        success = self._dict_sync.rename_key(old_key, new_key)
                        if not success:
                            return False
                    elif self._source_dict is not None:
                        # Direct dict manipulation
                        del self._source_dict[old_key]
                        self._source_dict[new_key] = value_obj
                        self._obs_list[row] = (new_key, value_obj)  # type: ignore[assignment]

                    self.dataChanged.emit(index, index, [role])
                    return True

                elif isinstance(column_name, int):
                    # Integer column = old-style tuple index (0=key, 1=value as string)
                    if column_name == 0:
                        # Same as #key
                        new_key = str(value)
                        if new_key != old_key:
                            if self._source_dict is not None:
                                del self._source_dict[old_key]
                                self._source_dict[new_key] = value_obj
                            self._obs_list[row] = (new_key, value_obj)  # type: ignore[assignment]
                    elif column_name == 1:
                        # Update entire value (only works for simple values)
                        new_val = str(value)
                        if self._source_dict is not None:
                            self._source_dict[old_key] = new_val  # type: ignore[assignment]
                        self._obs_list[row] = (old_key, new_val)  # type: ignore[assignment]
                    self.dataChanged.emit(index, index, [role])
                    return True

                else:
                    # String column = property on value object
                    setattr(value_obj, column_name, value)  # pyright: ignore[reportUnknownArgumentType]
                    self.dataChanged.emit(index, index, [role])
                    return True

            # For regular objects/dataclasses - use setattr
            if isinstance(column_name, str):
                setattr(item, column_name, value)  # pyright: ignore[reportUnknownArgumentType]
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
        result_flags = base_flags

        if column_name in self._checkable_columns:
            result_flags = result_flags | Qt.ItemFlag.ItemIsUserCheckable

        if column_name in self._editable_columns:
            result_flags = result_flags | Qt.ItemFlag.ItemIsEditable

        return result_flags

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
                # Special handling for #key column
                if column_name == DICT_KEY_COLUMN:
                    return "Key"
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

    def proxy_for_item(self, item: T) -> ObservableProxy[T]:
        """Get or create an ObservableProxy for an item.

        This enables per-item dirty/valid state tracking. The proxy is cached
        so the same proxy is returned for the same item (by identity).

        When used with selectedItem binding, the Variable swaps its wrapper
        to use this proxy, ensuring dirty state is tracked per-item.

        Args:
            item: The item to wrap.

        Returns:
            The ObservableProxy wrapping the item.
        """
        item_id = id(item)
        if item_id not in self._item_proxies:
            self._item_proxies[item_id] = ObservableProxy(item)
        return self._item_proxies[item_id]

    def proxy_at(self, row: int) -> ObservableProxy[T] | None:
        """Get the ObservableProxy for the item at a given row.

        Args:
            row: The row index.

        Returns:
            The ObservableProxy for the item, or None if row is invalid.
        """
        item = self.item_at(row)
        if item is None:
            return None
        return self.proxy_for_item(item)
