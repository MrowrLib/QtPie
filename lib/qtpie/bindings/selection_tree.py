"""Selection bindings for QTreeView."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


def setup_tree_selection_bindings(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTreeModel
    selected_item_path: str | None,
    selected_items_path: str | None,
    resolve_or_create_variable_fn: Any = None,  # Callable to resolve/create variables
) -> None:
    """Set up selection bindings for QTreeView.

    Args:
        host: The Widget/Window instance containing the Variables
        widget: The QTreeView widget
        model: The ReactiveTreeModel backing the widget
        selected_item_path: Variable path for single item binding (e.g., "_selected_node")
        selected_items_path: Variable path for multi-item binding (e.g., "_selected_nodes")
        resolve_or_create_variable_fn: Function to resolve/create variables (injected from apply.py)
    """
    if selected_item_path is None and selected_items_path is None:
        return

    from qtpy.QtCore import QTimer

    from qtpie.variable import Variable as VarType

    # Resolve Variables - may be None initially if widget isn't parented yet
    item_var: VarType[Any] | None = None
    items_var: VarType[list[Any]] | None = None

    if selected_item_path is not None:
        source = resolve_or_create_variable_fn(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_items_path is not None:
        source = resolve_or_create_variable_fn(host, selected_items_path, None)
        if isinstance(source, VarType):
            items_var = source  # pyright: ignore[reportUnknownVariableType]

    # If we didn't find the Variables yet, the widget might not be parented.
    # Schedule a deferred retry after the event loop processes parenting.
    if (selected_item_path is not None and item_var is None) or (selected_items_path is not None and items_var is None):

        def retry_binding() -> None:
            # Re-attempt resolution after parenting
            nonlocal item_var, items_var
            if selected_item_path is not None and item_var is None:
                source = resolve_or_create_variable_fn(host, selected_item_path, None)
                if isinstance(source, VarType):
                    item_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_items_path is not None and items_var is None:
                source = resolve_or_create_variable_fn(host, selected_items_path, None)
                if isinstance(source, VarType):
                    items_var = source  # pyright: ignore[reportUnknownVariableType]
            # If we found them now, set up the actual bindings
            if item_var is not None or items_var is not None:
                _setup_tree_selection_bindings_impl(host, widget, model, item_var, items_var)

        QTimer.singleShot(0, retry_binding)
        return

    # Set up bindings immediately if Variables were found
    _setup_tree_selection_bindings_impl(host, widget, model, item_var, items_var)


def _setup_tree_selection_bindings_impl(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTreeModel
    item_var: Any | None,  # Variable[Any] | None
    items_var: Any | None,  # Variable[list[Any]] | None
) -> None:
    """Implementation of tree selection bindings (called after Variables are resolved)."""
    from qtpy.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Get selection model
    selection_model = widget.selectionModel()  # type: ignore[attr-defined]
    if selection_model is None:
        return

    # Helper to get item at model index
    def get_item_at_index(index: QModelIndex) -> Any:
        if not index.isValid():
            return None
        return model.data(index, Qt.ItemDataRole.UserRole)

    # Helper to get current item
    def get_current_item() -> Any:
        current = selection_model.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        return get_item_at_index(current)  # pyright: ignore[reportUnknownArgumentType]

    # Helper to get all selected items
    def get_selected_items() -> list[Any]:
        indexes = selection_model.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        items: list[Any] = []
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            item = get_item_at_index(idx)  # pyright: ignore[reportUnknownArgumentType]
            if item is not None and item not in items:
                items.append(item)
        return items

    # Helper to find model index for an item (searches entire tree)
    def find_index_for_item(item: Any, parent: QModelIndex | None = None) -> QModelIndex:
        if parent is None:
            parent = QModelIndex()
        for row in range(model.rowCount(parent)):
            idx = model.index(row, 0, parent)
            if get_item_at_index(idx) == item:
                return idx
            # Search children recursively
            child_result = find_index_for_item(item, idx)
            if child_result.isValid():
                return child_result
        return QModelIndex()

    # Initialize from current state or Variable defaults
    if item_var is not None:
        initial_item = item_var.value
        if initial_item is not None:
            # Try to select the item in the tree
            idx = find_index_for_item(initial_item)
            if idx.isValid():
                selection_model.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
                    idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
                )
        else:
            # Sync Variable to current selection
            item_var.value = get_current_item()

    if items_var is not None:
        initial_items = items_var.value
        if initial_items is None or not initial_items:  # pyright: ignore[reportUnnecessaryComparison]
            items_var.value = get_selected_items()

    # Variable → Widget binding (single item)
    if item_var is not None:

        def on_item_var_change(*_args: Any) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                new_item = item_var.value  # type: ignore[union-attr]
                if new_item is not None:
                    idx = find_index_for_item(new_item)
                    if idx.isValid():
                        selection_model.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
                            idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
                        )
            finally:
                updating["flag"] = False

        item_var.on_change(on_item_var_change)

    # Widget → Variable binding
    if item_var is not None or items_var is not None:

        def on_current_changed(current: QModelIndex, _previous: QModelIndex) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                if item_var is not None:
                    item_var.value = get_item_at_index(current)
            finally:
                updating["flag"] = False

        def on_selection_changed(_selected: QItemSelection, _deselected: QItemSelection) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                if items_var is not None:
                    items_var.value = get_selected_items()
            finally:
                updating["flag"] = False

        selection_model.currentChanged.connect(on_current_changed)  # pyright: ignore[reportUnknownMemberType]
        selection_model.selectionChanged.connect(on_selection_changed)  # pyright: ignore[reportUnknownMemberType]
