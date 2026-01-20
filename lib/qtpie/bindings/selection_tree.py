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
    selected_widget_path: str | None = None,
    resolve_or_create_variable_fn: Any = None,  # Callable to resolve/create variables
) -> None:
    """Set up selection bindings for QTreeView.

    Args:
        host: The Widget/Window instance containing the Variables
        widget: The QTreeView widget
        model: The ReactiveTreeModel backing the widget
        selected_item_path: Variable path for single item binding (e.g., "_selected_node")
        selected_items_path: Variable path for multi-item binding (e.g., "_selected_nodes")
        selected_widget_path: Variable path for embedded widget binding (e.g., "_selected_widget")
        resolve_or_create_variable_fn: Function to resolve/create variables (injected from apply.py)
    """
    if selected_item_path is None and selected_items_path is None and selected_widget_path is None:
        return

    from observant import Observable

    from qtpie.variable import Variable as VarType

    # Helper to check if source is Variable or Observable
    def is_var_or_obs(source: Any) -> bool:
        return isinstance(source, VarType) or isinstance(source, Observable)

    # Resolve Variables (or Observables for record field bindings)
    item_var: Any | None = None
    items_var: Any | None = None
    widget_var: Any | None = None

    if selected_item_path is not None:
        source = resolve_or_create_variable_fn(host, selected_item_path, None)
        if is_var_or_obs(source):
            item_var = source

    if selected_items_path is not None:
        source = resolve_or_create_variable_fn(host, selected_items_path, None)
        if is_var_or_obs(source):
            items_var = source

    if selected_widget_path is not None:
        source = resolve_or_create_variable_fn(host, selected_widget_path, None)
        if is_var_or_obs(source):
            widget_var = source

    # ALWAYS call _setup_tree_selection_bindings_impl to connect the signal handler early.
    # This ensures the selection binding handler is connected BEFORE user's signal handlers.
    # The handler uses a mutable container so it can access Variables resolved later.
    _setup_tree_selection_bindings_impl(host, widget, model, item_var, items_var, widget_var)


def _setup_tree_selection_bindings_impl(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTreeModel
    item_var: Any | None,  # Variable[Any] | None
    items_var: Any | None,  # Variable[list[Any]] | None
    widget_var: Any | None = None,  # Variable[QWidget | None] | None
) -> None:
    """Implementation of tree selection bindings (called after Variables are resolved)."""
    from observant import Observable
    from qtpy.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Use mutable container so handler closures can access updated values
    # (Variables may be resolved AFTER handler is connected)
    container: dict[str, Any] = {
        "model": model,
        "item_var": item_var,
        "items_var": items_var,
        "widget_var": widget_var,
        "selection_model": None,
    }

    # Helper to check if something is an Observable (from record fields)
    def is_observable(obj: Any) -> bool:
        return isinstance(obj, Observable)

    # Helper to get value from Variable or Observable
    def get_var_value(var: Any) -> Any:
        if var is None:
            return None
        if is_observable(var):
            return var.get()  # pyright: ignore[reportUnknownMemberType]
        return var.value  # pyright: ignore[reportUnknownMemberType]

    # Helper to set value on Variable or Observable
    def set_var_value(var: Any, value: Any, index: QModelIndex | None = None) -> None:
        """Set value on Variable or Observable, using replace_wrapper for complex objects.

        For Variables with ObservableProxy wrappers AND complex object values
        (dataclasses, custom classes), we use replace_wrapper() with the model's
        cached proxy to enable per-item dirty state tracking.

        Variable.replace_wrapper() preserves on_change callbacks by re-registering
        them on the new wrapper.
        """
        from dataclasses import is_dataclass
        from enum import Enum

        from observant import ObservableProxy

        from qtpie.models.reactive_tree_model import TREE_PROXY_ROLE

        if var is None:
            return
        if is_observable(var):
            var.set(value)  # pyright: ignore[reportUnknownMemberType]
        else:
            # Try to get the proxy from the model
            proxy: ObservableProxy[Any] | None = None
            if index is not None and index.isValid():
                m = container["model"]
                if m is not None:
                    try:
                        proxy = m.data(index, TREE_PROXY_ROLE)
                        if not isinstance(proxy, ObservableProxy):
                            proxy = None
                    except (RuntimeError, AttributeError):
                        proxy = None

            # Check if the value is a "complex object" that benefits from proxy sharing
            is_complex_object = False
            if value is not None:
                val_type = type(value)  # pyright: ignore[reportUnknownArgumentType,reportUnknownVariableType]
                is_dataclass_instance = is_dataclass(value) and not isinstance(value, type)
                is_enum = isinstance(value, Enum)
                is_builtin = val_type.__module__ == "builtins"
                has_dict = hasattr(value, "__dict__")
                is_complex_object = is_dataclass_instance or (has_dict and not is_enum and not is_builtin)

            current_wrapper = getattr(var, "_wrapper", None)
            if proxy is not None and is_complex_object and hasattr(var, "replace_wrapper") and isinstance(current_wrapper, ObservableProxy):
                var.replace_wrapper(proxy)
            else:
                var.value = value  # pyright: ignore[reportUnknownMemberType]

    # Helper to get item at model index
    def get_item_at_index(index: QModelIndex) -> Any:
        m = container["model"]
        if m is None or not index.isValid():
            return None
        return m.data(index, Qt.ItemDataRole.UserRole)

    # Helper to get current item
    def get_current_item() -> Any:
        sm = container["selection_model"]
        if sm is None:
            return None
        current = sm.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        return get_item_at_index(current)  # pyright: ignore[reportUnknownArgumentType]

    # Helper to get all selected items
    def get_selected_items() -> list[Any]:
        sm = container["selection_model"]
        if sm is None:
            return []
        indexes = sm.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        items: list[Any] = []
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            item = get_item_at_index(idx)  # pyright: ignore[reportUnknownArgumentType]
            if item is not None and item not in items:
                items.append(item)
        return items

    # Helper to find model index for an item (searches entire tree)
    def find_index_for_item(item: Any, parent: QModelIndex | None = None) -> QModelIndex:
        m = container["model"]
        if m is None:
            return QModelIndex()
        if parent is None:
            parent = QModelIndex()
        for row in range(m.rowCount(parent)):
            idx = m.index(row, 0, parent)
            if get_item_at_index(idx) == item:
                return idx
            # Search children recursively
            child_result = find_index_for_item(item, idx)
            if child_result.isValid():
                return child_result
        return QModelIndex()

    # Helper to get the embedded widget at an index (for selectedWidget binding)
    def get_widget_at_index(index: QModelIndex) -> Any:
        if not index.isValid():
            return None
        # QAbstractItemView.indexWidget() returns the widget for persistent editors
        return widget.indexWidget(index)  # type: ignore[attr-defined]

    # Widget → Variable binding handler (must be defined BEFORE connecting)
    def on_current_changed(current: QModelIndex, _previous: QModelIndex) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            iv = container["item_var"]
            if iv is not None:
                set_var_value(iv, get_item_at_index(current), current)
            wv = container["widget_var"]
            if wv is not None:
                set_var_value(wv, get_widget_at_index(current))
        finally:
            updating["flag"] = False

    def on_selection_changed(_selected: QItemSelection, _deselected: QItemSelection) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            isv = container["items_var"]
            if isv is not None:
                set_var_value(isv, get_selected_items())
        finally:
            updating["flag"] = False

    # Connect handler to selection model
    def connect_selection_handler() -> None:
        sm = widget.selectionModel()  # type: ignore[attr-defined]
        if sm is None:
            return
        old_sm = container["selection_model"]
        if old_sm is sm:
            return  # Same selection model, already connected
        container["selection_model"] = sm
        # Always connect handlers - they will check if vars are None
        sm.currentChanged.connect(on_current_changed)  # pyright: ignore[reportUnknownMemberType]
        sm.selectionChanged.connect(on_selection_changed)  # pyright: ignore[reportUnknownMemberType]

    # Connect handler NOW (before user's signal handlers)
    connect_selection_handler()

    # Track model changes - selection model changes when model is replaced
    if hasattr(model, "modelReset"):
        model.modelReset.connect(connect_selection_handler)  # pyright: ignore[reportUnknownMemberType]

    # Now do initialization and Variable → Widget bindings
    # (only if variables are already resolved)
    if item_var is None and items_var is None and widget_var is None:
        return  # No vars yet, handler is connected and will work when vars are set

    # Initialize from current state or Variable defaults
    if item_var is not None:
        initial_item = get_var_value(item_var)
        sm = container["selection_model"]
        if initial_item is not None and sm is not None:
            # Try to select the item in the tree
            idx = find_index_for_item(initial_item)
            if idx.isValid():
                sm.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
                    idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
                )
        elif initial_item is None:
            # Sync Variable to current selection
            set_var_value(item_var, get_current_item())

    if items_var is not None:
        initial_items = get_var_value(items_var)
        if initial_items is None or not initial_items:
            set_var_value(items_var, get_selected_items())

    # Initialize widget_var to current selection's widget (read-only binding)
    if widget_var is not None:
        sm = container["selection_model"]
        if sm is not None:
            current_idx = sm.currentIndex()  # pyright: ignore[reportUnknownMemberType]
            set_var_value(widget_var, get_widget_at_index(current_idx))

    # Variable → Widget binding (single item)
    if item_var is not None:

        def on_item_var_change(*_args: Any) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                iv = container["item_var"]
                sm = container["selection_model"]
                if iv is not None and sm is not None:
                    new_item = get_var_value(iv)
                    if new_item is not None:
                        idx = find_index_for_item(new_item)
                        if idx.isValid():
                            sm.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
                                idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
                            )
            finally:
                updating["flag"] = False

        item_var.on_change(on_item_var_change)
