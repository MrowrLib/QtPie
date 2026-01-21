# pyright: reportPrivateUsage=false
"""QTreeView test helpers."""

from typing import Any

from qtpy.QtCore import QItemSelectionModel, QModelIndex, Qt
from qtpy.QtWidgets import QTreeView


def find_tree_index(
    tree: QTreeView,
    target: Any,
    parent: QModelIndex | None = None,
) -> QModelIndex:
    """Find the QModelIndex for a given item in a QTreeView.

    Searches the tree model recursively for an item matching `target`.
    QtPie stores actual data items at Qt.ItemDataRole.UserRole.

    Args:
        tree: The QTreeView to search
        target: The item to find (compared by identity)
        parent: Parent index to search from (None for root)

    Returns:
        The QModelIndex for the item, or invalid QModelIndex if not found
    """
    model = tree.model()
    if parent is None:
        parent = QModelIndex()

    for row in range(model.rowCount(parent)):
        idx = model.index(row, 0, parent)
        # QtPie stores the actual item at UserRole
        item = model.data(idx, Qt.ItemDataRole.UserRole)
        if item is target:
            return idx
        # Search children recursively
        child_result = find_tree_index(tree, target, idx)
        if child_result.isValid():
            return child_result
    return QModelIndex()


def click_tree_item(tree: QTreeView, idx: QModelIndex) -> None:
    """Click an item in a QTreeView.

    Simulates a user click by:
    1. Selecting the item (updates selectedItem= bindings)
    2. Emitting clicked signal (triggers clicked= handlers)

    Args:
        tree: The QTreeView widget
        idx: The QModelIndex of the item to click
    """
    selection_model = tree.selectionModel()
    selection_model.setCurrentIndex(idx, QItemSelectionModel.SelectionFlag.ClearAndSelect)
    tree.clicked.emit(idx)


def double_click_tree_item(tree: QTreeView, idx: QModelIndex) -> None:
    """Double-click an item in a QTreeView.

    Simulates a user double-click by:
    1. Selecting the item (updates selectedItem= bindings)
    2. Emitting doubleClicked signal (triggers doubleClicked= handlers)

    Args:
        tree: The QTreeView widget
        idx: The QModelIndex of the item to double-click
    """
    selection_model = tree.selectionModel()
    selection_model.setCurrentIndex(idx, QItemSelectionModel.SelectionFlag.ClearAndSelect)
    tree.doubleClicked.emit(idx)


def expand_to_index(tree: QTreeView, idx: QModelIndex) -> None:
    """Expand all parents to make an index visible.

    Args:
        tree: The QTreeView widget
        idx: The QModelIndex to make visible
    """
    parent = idx.parent()
    while parent.isValid():
        tree.expand(parent)
        parent = parent.parent()


def get_tree_item(tree: QTreeView, idx: QModelIndex) -> Any:
    """Get the data item at a QModelIndex.

    Args:
        tree: The QTreeView widget
        idx: The QModelIndex to get data from

    Returns:
        The item stored at UserRole, or None if invalid
    """
    if not idx.isValid():
        return None
    model = tree.model()
    return model.data(idx, Qt.ItemDataRole.UserRole)
