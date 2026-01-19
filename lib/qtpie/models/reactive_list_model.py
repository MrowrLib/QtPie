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
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        parent: QObject | None = None,
        *,
        format_fn: Callable[[T], str] | None = None,
        checkable: str | bool | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._format_fn = format_fn
        self._checkable = checkable
        self._checkable_is_expression = checkable is not None and isinstance(checkable, str) and "{" in checkable

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
        if isinstance(self._checkable, str):
            return base_flags | Qt.ItemFlag.ItemIsUserCheckable
        return base_flags

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
            # Only allow editing for field names (not expressions)
            if isinstance(self._checkable, str) and not self._checkable_is_expression:
                row = index.row()
                if row < 0 or row >= len(self._obs_list):
                    return False
                item = self._obs_list[row]
                new_value = value == Qt.CheckState.Checked.value
                setattr(item, self._checkable, new_value)
                self.dataChanged.emit(index, index, [role])
                return True
        return False

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
            # Field name: get attribute
            return bool(getattr(item, self._checkable, False))

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
