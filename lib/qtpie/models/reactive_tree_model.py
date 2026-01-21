"""ReactiveTreeModel - QAbstractItemModel backed by hierarchical ObservableList."""

from collections.abc import Callable
from dataclasses import fields, is_dataclass
from typing import Any, override

from observant import ObservableList, ObservableProxy
from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, QPersistentModelIndex, Qt

_INVALID_INDEX = QModelIndex()

# Custom role for getting the ObservableProxy wrapper for an item
# This enables dirty/valid state tracking per-item
TREE_PROXY_ROLE = Qt.ItemDataRole.UserRole + 1


class ReactiveTreeModel[T](QAbstractItemModel):
    """QAbstractItemModel backed by hierarchical ObservableList[T].

    Each item in the list can have children accessed via a configurable attribute.

    Usage:
        @dataclass
        class TreeNode:
            name: str
            children: list[TreeNode] = field(default_factory=list)

        nodes = ObservableList([TreeNode("Root", [TreeNode("Child")])])
        model = ReactiveTreeModel(nodes, children_attr="children")
        tree_view.setModel(model)

    Args:
        observable_list: The root items.
        children_attr: Attribute name for accessing children (default: "children").
        format_fn: Optional function to format display text.
        checkable: Checkbox support for tree nodes.
            - None/False: no checkboxes (default)
            - str without braces: two-way binding to bool field name
            - str with braces "{expr}": one-way expression (read-only checkbox)
        editable: Inline editing support for tree nodes.
            - None/False: no editing (default)
            - str: field name to edit (supports nested paths like "info.title")
            - True: edit the item itself (for simple types like str)
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        parent: QObject | None = None,
        *,
        children_attr: str = "children",
        format_fn: Callable[[T], str] | None = None,
        checkable: str | bool | None = None,
        editable: str | bool | None = None,
        on_edited: Callable[[T, Any, Any], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._children_attr = children_attr
        self._format_fn = format_fn
        self._checkable = checkable
        self._checkable_is_expression = checkable is not None and isinstance(checkable, str) and "{" in checkable
        self._editable = editable
        self._on_edited = on_edited

        # Cache of ObservableProxy per item (keyed by id(item))
        # This enables per-item dirty/valid state tracking
        self._item_proxies: dict[int, ObservableProxy[T]] = {}

        # Track subscribed children lists to avoid duplicate subscriptions
        self._subscribed_children: set[int] = set()

        # Subscribe to root list changes
        observable_list.on_insert(self._on_root_insert)
        observable_list.on_remove(self._on_root_remove)
        observable_list.on_replace(self._on_root_replace)
        observable_list.on_clear(self._on_root_clear)

        # Subscribe to existing items' children lists
        for item in observable_list:
            self._subscribe_to_children(item)

    def _get_children(self, item: T) -> list[T]:
        """Get children of an item."""
        children = getattr(item, self._children_attr, None)
        if children is None:
            return []
        # Unwrap Variable to get its value (for State objects with Variable fields)
        if hasattr(children, "value") and hasattr(children, "observable"):
            children = children.value
            if children is None:
                return []
        # Handle ObservableList or regular list
        if isinstance(children, ObservableList):
            return list(children)  # pyright: ignore[reportUnknownArgumentType]
        return list(children) if children else []

    @override
    def index(self, row: int, column: int, parent: QModelIndex | QPersistentModelIndex | None = None) -> QModelIndex:
        """Create model index for the given row/column under parent."""
        if parent is None:
            parent = _INVALID_INDEX
        if not self.hasIndex(row, column, parent):
            return _INVALID_INDEX

        if not parent.isValid():
            # Root level
            if row < len(self._obs_list):
                return self.createIndex(row, column, self._obs_list[row])
        else:
            # Child level
            parent_item = parent.internalPointer()
            children = self._get_children(parent_item)
            if row < len(children):
                return self.createIndex(row, column, children[row])

        return _INVALID_INDEX

    @override
    def parent(self, index: QModelIndex | QPersistentModelIndex | None = None) -> QModelIndex:  # type: ignore[override]
        """Get parent index of the given index."""
        if index is None:
            index = _INVALID_INDEX
        if not index.isValid():
            return _INVALID_INDEX

        child_item = index.internalPointer()

        # Search for parent in the tree
        parent_item = self._find_parent(child_item)
        if parent_item is None:
            return _INVALID_INDEX

        # Find row of parent
        row = self._find_row(parent_item)
        if row < 0:
            return _INVALID_INDEX

        return self.createIndex(row, 0, parent_item)

    def _find_parent(self, child: T, items: list[T] | None = None, parent: T | None = None) -> T | None:
        """Find the parent of a child item by searching the tree."""
        if items is None:
            items = list(self._obs_list)

        for item in items:
            children = self._get_children(item)
            if child in children:
                return item
            # Recurse into children
            found = self._find_parent(child, children, item)
            if found is not None:
                return found
        return None

    def _find_row(self, item: T, items: list[T] | None = None) -> int:
        """Find the row index of an item within its parent's children."""
        # Check root level first
        try:
            return list(self._obs_list).index(item)
        except ValueError:
            pass

        # Search in all children
        if items is None:
            items = list(self._obs_list)

        for parent_item in items:
            children = self._get_children(parent_item)
            try:
                return children.index(item)
            except ValueError:
                pass
            # Recurse
            row = self._find_row(item, children)
            if row >= 0:
                return row

        return -1

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        """Return number of rows under the given parent."""
        if parent is None:
            parent = _INVALID_INDEX
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            return len(self._obs_list)

        parent_item = parent.internalPointer()
        return len(self._get_children(parent_item))

    @override
    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        """Return number of columns (always 1 for tree)."""
        return 1

    @override
    def data(self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        item = index.internalPointer()
        if item is None:
            return None

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
            # Return check state for checkable nodes
            if isinstance(self._checkable, str):
                checked = self._evaluate_checkable(item)
                return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            return None
        elif role == Qt.ItemDataRole.UserRole:
            return item
        elif role == TREE_PROXY_ROLE:
            # Return the ObservableProxy for this item (creates one if needed)
            return self.proxy_for_item(item)

        return None

    @override
    def hasChildren(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> bool:
        """Return True if parent has children."""
        if parent is None:
            parent = _INVALID_INDEX
        if not parent.isValid():
            return len(self._obs_list) > 0
        parent_item = parent.internalPointer()
        return len(self._get_children(parent_item)) > 0

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

        item = index.internalPointer()
        if item is None:
            return False

        if role == Qt.ItemDataRole.EditRole:
            if self._editable is True:
                # Simple type - replace item in list
                row = index.row()
                parent_index = self.parent(index)
                old_value = item  # The item itself is the old value
                if parent_index.isValid():
                    # Child item - find parent's children list
                    parent_item = parent_index.internalPointer()
                    children = getattr(parent_item, self._children_attr, None)
                    if children is not None and 0 <= row < len(children):
                        children[row] = value
                        self.dataChanged.emit(index, index, [role])
                        self._invoke_on_edited(item, old_value, value)
                        return True
                else:
                    # Root item
                    if 0 <= row < len(self._obs_list):
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
            # Strip braces and evaluate
            expr = self._checkable[1:-1]  # Remove { }
            # Build context from item attributes
            if is_dataclass(item) and not isinstance(item, type):
                context = {f.name: getattr(item, f.name, None) for f in fields(item)}
            else:
                context = {attr: getattr(item, attr, None) for attr in dir(item) if not attr.startswith("_")}
            try:
                # Limited builtins for safe evaluation
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

    # Children list subscription

    def _subscribe_to_children(self, item: T) -> None:
        """Subscribe to an item's children ObservableList for updates."""
        children_raw = getattr(item, self._children_attr, None)
        # Unwrap Variable to get its observable (for State objects with Variable fields)
        if children_raw is not None and hasattr(children_raw, "value") and hasattr(children_raw, "observable"):
            # For Variable[list[...]], the observable is an ObservableList
            unwrapped = children_raw.observable
            if unwrapped is not None:
                children_raw = unwrapped
        if children_raw is None or not isinstance(children_raw, ObservableList):
            return

        # Cast to proper type for pyright
        from typing import cast

        children: ObservableList[T] = cast(ObservableList[T], children_raw)

        children_id = id(children)
        if children_id in self._subscribed_children:
            return
        self._subscribed_children.add(children_id)

        # Create handlers that find the parent index and emit proper signals
        def on_child_insert(child_index: int, child_item: T) -> None:
            parent_index = self._find_index_for_item(item)
            if parent_index.isValid():
                self.beginInsertRows(parent_index, child_index, child_index)
                self.endInsertRows()
            # Also subscribe to the new child's children if it has any
            self._subscribe_to_children(child_item)

        def on_child_remove(child_index: int, _child_item: T) -> None:
            parent_index = self._find_index_for_item(item)
            if parent_index.isValid():
                self.beginRemoveRows(parent_index, child_index, child_index)
                self.endRemoveRows()

        def on_child_replace(child_index: int, _old_item: T, new_item: T) -> None:
            parent_index = self._find_index_for_item(item)
            if parent_index.isValid():
                child_model_index = self.index(child_index, 0, parent_index)
                self.dataChanged.emit(child_model_index, child_model_index)
            # Subscribe to the new item's children
            self._subscribe_to_children(new_item)

        def on_child_clear(_items: list[T]) -> None:
            parent_index = self._find_index_for_item(item)
            if parent_index.isValid():
                self.beginResetModel()
                self.endResetModel()

        children.on_insert(on_child_insert)
        children.on_remove(on_child_remove)
        children.on_replace(on_child_replace)
        children.on_clear(on_child_clear)

        # Recursively subscribe to existing children's children
        for child in children:
            self._subscribe_to_children(child)

    # Root list change handlers

    def _on_root_insert(self, index: int, item: T) -> None:
        """Handle root item insertion."""
        self.beginInsertRows(QModelIndex(), index, index)
        self.endInsertRows()
        # Subscribe to the new item's children
        self._subscribe_to_children(item)

    def _on_root_remove(self, index: int, item: T) -> None:
        """Handle root item removal."""
        self.beginRemoveRows(QModelIndex(), index, index)
        self.endRemoveRows()

    def _on_root_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle root item replacement."""
        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index)
        # Subscribe to the new item's children
        self._subscribe_to_children(new_item)

    def _on_root_clear(self, items: list[T]) -> None:
        """Handle root list clear."""
        self.beginResetModel()
        self.endResetModel()

    # Convenience methods

    def item_at(self, index: QModelIndex) -> T | None:
        """Get the item at a given model index."""
        if not index.isValid():
            return None
        return index.internalPointer()  # type: ignore[return-value]

    def refresh(self) -> None:
        """Force a full model refresh."""
        self.beginResetModel()
        self.endResetModel()

    def notify_item_changed(self, item: T) -> None:
        """Notify that an item's data has changed (e.g., a property was modified).

        This finds the item in the tree and emits dataChanged so the view updates.

        Args:
            item: The item whose data changed.
        """
        index = self._find_index_for_item(item)
        if index.isValid():
            self.dataChanged.emit(index, index)

    def _find_index_for_item(self, item: T, parent: QModelIndex | None = None) -> QModelIndex:
        """Find the QModelIndex for an item by searching the tree."""
        if parent is None:
            parent = _INVALID_INDEX

        # Get items at this level
        if not parent.isValid():
            items = list(self._obs_list)
        else:
            parent_item = parent.internalPointer()
            items = self._get_children(parent_item)

        # Check each item at this level
        for row, current_item in enumerate(items):
            if current_item is item:
                return self.index(row, 0, parent)

            # Recurse into children
            current_index = self.index(row, 0, parent)
            found = self._find_index_for_item(item, current_index)
            if found.isValid():
                return found

        return _INVALID_INDEX

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

    def proxy_for_index(self, index: QModelIndex) -> ObservableProxy[T] | None:
        """Get the ObservableProxy for the item at a given index.

        Args:
            index: The model index.

        Returns:
            The ObservableProxy for the item, or None if index is invalid.
        """
        if not index.isValid():
            return None
        item = index.internalPointer()
        if item is None:
            return None
        return self.proxy_for_item(item)  # type: ignore[arg-type]
