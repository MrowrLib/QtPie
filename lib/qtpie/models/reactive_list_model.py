"""ReactiveListModel - QAbstractListModel backed by ObservableList."""

from collections.abc import Callable
from dataclasses import fields, is_dataclass
from typing import Any, override

from observant import ObservableList, ObservableProxy
from qtpy.QtCore import QAbstractListModel, QModelIndex, QObject, QPersistentModelIndex, Qt

# Custom role for getting the ObservableProxy wrapper for an item
# This enables dirty/valid state tracking per-item
PROXY_ROLE = Qt.ItemDataRole.UserRole + 1


class ReactiveListModel[T](QAbstractListModel):
    """QAbstractListModel backed by ObservableList[T].

    Emits proper Qt model signals when the ObservableList changes:
    - on_insert -> beginInsertRows/endInsertRows
    - on_remove -> beginRemoveRows/endRemoveRows
    - on_replace -> dataChanged
    - on_clear -> beginResetModel/endResetModel

    Usage:
        obs_list = ObservableList(["A", "B", "C"])
        model = ReactiveListModel(obs_list)
        combo.setModel(model)

        # Changes to obs_list automatically update the view
        obs_list.append("D")  # Emits rowsInserted
        obs_list.remove("A")  # Emits rowsRemoved

        # With custom formatting for complex objects:
        dogs = ObservableList([Dog("Fido", 3), Dog("Rex", 5)])
        model = ReactiveListModel(dogs, format_fn=lambda d: f"{d.name} ({d.age})")

        # With checkboxes:
        model = ReactiveListModel(tasks, checkable="done")  # Two-way binding
        model = ReactiveListModel(tasks, checkable="{len(title) > 10}")  # Read-only expression

        # With inline editing:
        model = ReactiveListModel(tasks, editable="title")  # Two-way binding to field
        model = ReactiveListModel(strings, editable=True)  # Edit simple types directly
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        parent: QObject | None = None,
        *,
        format_fn: Callable[[T], str] | None = None,
        checkable: str | bool | None = None,
        editable: str | bool | None = None,
        on_edited: Callable[[T, Any, Any], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._format_fn = format_fn
        self._checkable = checkable
        self._checkable_is_expression = checkable is not None and isinstance(checkable, str) and "{" in checkable
        self._editable = editable
        self._on_edited = on_edited

        # Cache of ObservableProxy per item (keyed by id(item))
        # This enables per-item dirty/valid state tracking
        self._item_proxies: dict[int, ObservableProxy[T]] = {}

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        """Return number of rows in the model."""
        if parent is not None and parent.isValid():
            return 0
        return len(self._obs_list)

    @override
    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        """Return flags for the given index."""
        base_flags = super().flags(index)
        if not index.isValid():
            return base_flags

        result_flags = base_flags

        if isinstance(self._checkable, str):
            result_flags = result_flags | Qt.ItemFlag.ItemIsUserCheckable

        if self._editable is True or isinstance(self._editable, str):
            result_flags = result_flags | Qt.ItemFlag.ItemIsEditable

        return result_flags

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
        if row < 0 or row >= len(self._obs_list):
            return False

        item = self._obs_list[row]

        if role == Qt.ItemDataRole.EditRole:
            if self._editable is True:
                # Simple type - replace item in list
                old_value = item  # The item itself is the old value
                self._obs_list[row] = value
                self.dataChanged.emit(index, index, [role])
                self._invoke_on_edited(item, old_value, value)
                return True
            elif isinstance(self._editable, str):
                # Field name - set the field value (supports nested paths)
                old_value = self._get_nested_attr(item, self._editable)
                if self._set_nested_attr(item, self._editable, value):
                    self.dataChanged.emit(index, index, [role])
                    self._invoke_on_edited(item, old_value, value)
                    return True
            return False

        if role == Qt.ItemDataRole.CheckStateRole:
            # Only allow editing for field names (not expressions)
            if isinstance(self._checkable, str) and not self._checkable_is_expression:
                new_value = value == Qt.CheckState.Checked.value
                if self._set_nested_attr(item, self._checkable, new_value):
                    self.dataChanged.emit(index, index, [role])
                    return True
        return False

    def _invoke_on_edited(self, item: T, old_value: Any, new_value: Any) -> None:
        """Invoke the on_edited callback if set."""
        if self._on_edited is not None:
            try:
                self._on_edited(item, old_value, new_value)
            except Exception:
                pass  # Don't let callback errors break the edit

    def _evaluate_checkable(self, item: T) -> bool:
        """Evaluate the checkable field/expression for an item."""
        if not isinstance(self._checkable, str):
            return False
        if self._checkable_is_expression:
            # Expression: evaluate with item context
            expr = self._checkable[1:-1]  # Remove { }
            # Build context from item attributes
            if is_dataclass(item) and not isinstance(item, type):
                context = {f.name: getattr(item, f.name, None) for f in fields(item)}
            else:
                context = {attr: getattr(item, attr, None) for attr in dir(item) if not attr.startswith("_")}
            try:
                safe_builtins = {"len": len, "str": str, "int": int, "bool": bool, "float": float}
                return bool(eval(expr, {"__builtins__": safe_builtins}, context))  # noqa: S307
            except Exception:
                return False
        else:
            # Field name: get attribute (supports nested paths)
            return bool(self._get_nested_attr(item, self._checkable, False))

    def _get_nested_attr(self, obj: Any, path: str, default: Any = None) -> Any:
        """Get nested attribute value supporting dotted paths like 'info.title'."""
        current = obj
        for part in path.split("."):
            if current is None:
                return default
            current = getattr(current, part, None)
        return current if current is not None else default

    def _set_nested_attr(self, obj: Any, path: str, value: Any) -> bool:
        """Set nested attribute value supporting dotted paths like 'info.title'.

        Uses ObservableProxy to ensure reactive updates propagate to all bindings.
        """
        # Get or create proxy for the item to ensure reactive updates
        proxy = self.proxy_for_item(obj)

        parts = path.split(".")
        current: Any = proxy
        for part in parts[:-1]:
            current = getattr(current, part, None)
            if current is None:
                return False
        # Setting through the proxy triggers reactive notifications
        setattr(current, parts[-1], value)
        return True

    @override
    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        row = index.row()
        if row < 0 or row >= len(self._obs_list):
            return None

        item = self._obs_list[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if self._format_fn is not None:
                return self._format_fn(item)
            return str(item)
        elif role == Qt.ItemDataRole.EditRole:
            # Return the editable value for pre-populating the editor
            if self._editable is True:
                # Simple type - return the item itself
                return item
            elif isinstance(self._editable, str):
                # Field name - return the field value (supports nested paths)
                return self._get_nested_attr(item, self._editable)
            return None
        elif role == Qt.ItemDataRole.CheckStateRole:
            # Return check state for checkable items
            if isinstance(self._checkable, str):
                checked = self._evaluate_checkable(item)
                return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            return None
        elif role == Qt.ItemDataRole.UserRole:
            # Return the actual item for programmatic access
            return item
        elif role == PROXY_ROLE:
            # Return the ObservableProxy for this item (creates one if needed)
            return self.proxy_for_item(item)

        return None

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        self.beginInsertRows(QModelIndex(), index, index)
        self.endInsertRows()

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        self.beginRemoveRows(QModelIndex(), index, index)
        self.endRemoveRows()
        # Clean up proxy cache for removed item
        item_id = id(item)
        if item_id in self._item_proxies:
            del self._item_proxies[item_id]

    def _on_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle item replacement."""
        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index)
        # Clean up proxy cache for old item
        old_id = id(old_item)
        if old_id in self._item_proxies:
            del self._item_proxies[old_id]

    def _on_clear(self, items: list[T]) -> None:
        """Handle list clear."""
        self.beginResetModel()
        self.endResetModel()
        # Clean up all proxy caches
        self._item_proxies.clear()

    # Convenience methods

    def item_at(self, index: int) -> T | None:
        """Get the item at a given index."""
        if 0 <= index < len(self._obs_list):
            return self._obs_list[index]
        return None

    def index_of(self, item: T) -> int:
        """Find the index of an item, returns -1 if not found."""
        try:
            return list(self._obs_list).index(item)
        except ValueError:
            return -1

    def notify_item_changed(self, item: T) -> None:
        """Notify that an item's data has changed (e.g., a property was modified).

        This finds the item in the list and emits dataChanged so the view updates.

        Args:
            item: The item whose data changed.
        """
        idx = self.index_of(item)
        if idx >= 0:
            model_index = self.index(idx, 0)
            self.dataChanged.emit(model_index, model_index)

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

    def proxy_at(self, index: int) -> ObservableProxy[T] | None:
        """Get the ObservableProxy for the item at a given index.

        Args:
            index: The row index.

        Returns:
            The ObservableProxy for the item, or None if index is invalid.
        """
        item = self.item_at(index)
        if item is None:
            return None
        return self.proxy_for_item(item)
