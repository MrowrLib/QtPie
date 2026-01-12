"""ReactiveTreeModel - QAbstractItemModel backed by hierarchical ObservableList."""

from collections.abc import Callable
from typing import Any, override

from observant import ObservableList
from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, QPersistentModelIndex, Qt

_INVALID_INDEX = QModelIndex()


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
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        parent: QObject | None = None,
        *,
        children_attr: str = "children",
        format_fn: Callable[[T], str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._obs_list = observable_list
        self._children_attr = children_attr
        self._format_fn = format_fn

        # Subscribe to root list changes
        observable_list.on_insert(self._on_root_insert)
        observable_list.on_remove(self._on_root_remove)
        observable_list.on_replace(self._on_root_replace)
        observable_list.on_clear(self._on_root_clear)

    def _get_children(self, item: T) -> list[T]:
        """Get children of an item."""
        children = getattr(item, self._children_attr, None)
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
        elif role == Qt.ItemDataRole.UserRole:
            return item

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

    # Root list change handlers

    def _on_root_insert(self, index: int, item: T) -> None:
        """Handle root item insertion."""
        self.beginInsertRows(QModelIndex(), index, index)
        self.endInsertRows()

    def _on_root_remove(self, index: int, item: T) -> None:
        """Handle root item removal."""
        self.beginRemoveRows(QModelIndex(), index, index)
        self.endRemoveRows()

    def _on_root_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle root item replacement."""
        model_index = self.index(index, 0)
        self.dataChanged.emit(model_index, model_index)

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
