"""Selection bindings for QTreeView."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

logger = logging.getLogger("qtpie.bindings.selection_tree")


def setup_tree_selection_bindings(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTreeModel
    selected_item_path: str | None,
    selected_items_path: str | None,
    selected_widget_path: str | None = None,
    resolve_or_create_variable_fn: Any = None,  # Callable to resolve/create variables
    root_variable: Any = None,  # Root Variable for nested paths (passed from model_binding)
    *,
    _items_var_path: str | None = None,  # Internal: for re-resolution of items_var
    deselect_on_escape: bool = False,  # Install Escape key handler to clear selection
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
        root_variable: Root Variable for nested binding paths (e.g., workspace for "workspace?.selected_item")
        deselect_on_escape: If True, pressing Escape clears selection and sets Variables to None/[]
    """
    has_bindings = selected_item_path is not None or selected_items_path is not None or selected_widget_path is not None
    if not has_bindings and not deselect_on_escape:
        return

    from observant import Observable, ObservableList, ObservableProxy

    from qtpie.variable import Variable as VarType

    # Helper to check if source is Variable, Observable, or ObservableProxy
    def is_var_or_obs(source: Any) -> bool:
        return isinstance(source, (VarType, Observable, ObservableProxy))

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
        elif isinstance(source, ObservableList):
            items_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_widget_path is not None:
        source = resolve_or_create_variable_fn(host, selected_widget_path, None)
        if is_var_or_obs(source):
            widget_var = source

    # ALWAYS call _setup_tree_selection_bindings_impl to connect the signal handler early.
    # This ensures the selection binding handler is connected BEFORE user's signal handlers.
    # The handler uses a mutable container so it can access Variables resolved later.
    _setup_tree_selection_bindings_impl(
        host,
        widget,
        model,
        item_var,
        items_var,
        widget_var,
        root_variable=root_variable,
        selected_item_path=selected_item_path,
        selected_items_path=selected_items_path,
        resolve_or_create_variable_fn=resolve_or_create_variable_fn,
        deselect_on_escape=deselect_on_escape,
    )


def _setup_tree_selection_bindings_impl(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTreeModel
    item_var: Any | None,  # Variable[Any] | None
    items_var: Any | None,  # Variable[list[Any]] | ObservableList | None
    widget_var: Any | None = None,  # Variable[QWidget | None] | None
    root_variable: Any = None,  # Root Variable for nested paths (from model_binding)
    selected_item_path: str | None = None,  # Original path for re-resolution
    selected_items_path: str | None = None,  # Original path for re-resolution of multi-selection
    deselect_on_escape: bool = False,  # Install Escape key handler to clear selection
    resolve_or_create_variable_fn: Any = None,  # For re-resolving nested paths
) -> None:
    """Implementation of tree selection bindings (called after Variables are resolved)."""
    from observant import Observable, ObservableList, ObservableProxy
    from qtpy.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt

    from qtpie.bindings.selection_helpers import subscribe_to_root_variable_change

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Track if items_var is an ObservableList (vs Variable[list])
    is_items_var_observable_list = isinstance(items_var, ObservableList) if items_var is not None else False

    # Use mutable container so handler closures can access updated values
    # (Variables may be resolved AFTER handler is connected)
    container: dict[str, Any] = {
        "model": model,
        "item_var": item_var,
        "items_var": items_var,
        "widget_var": widget_var,
        "selection_model": None,
    }

    # Helper to check if something is an Observable or ObservableProxy
    def is_observable(obj: Any) -> bool:
        return isinstance(obj, Observable)

    def is_observable_proxy(obj: Any) -> bool:
        return isinstance(obj, ObservableProxy)

    # Helper to get value from Variable, Observable, or ObservableProxy
    def get_var_value(var: Any) -> Any:
        if var is None:
            return None
        if is_observable(var):
            return var.get()  # pyright: ignore[reportUnknownMemberType]
        if is_observable_proxy(var):
            return var.unwrap()  # pyright: ignore[reportUnknownMemberType]
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
            # Try to get the proxy from the model (use view model for proxy indices)
            proxy: ObservableProxy[Any] | None = None
            if index is not None and index.isValid():
                view_model = widget.model()  # type: ignore[attr-defined]
                if view_model is not None:
                    try:
                        proxy = view_model.data(index, TREE_PROXY_ROLE)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
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
        if not index.isValid():
            return None
        # Use the view's model (may be a proxy) to get data - it handles mapping internally
        view_model = widget.model()  # type: ignore[attr-defined]
        if view_model is None:
            return None
        return view_model.data(index, Qt.ItemDataRole.UserRole)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]

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

    # Helpers for items_var (Variable[list], Observable[list], or ObservableList)
    def get_items_var_value() -> list[Any]:  # pyright: ignore[reportUnknownVariableType]
        """Get the current value from items_var (Variable, Observable, or ObservableList)."""
        itemsv = container["items_var"]
        if itemsv is None:
            return []
        if is_items_var_observable_list:
            return list(itemsv)  # pyright: ignore[reportUnknownArgumentType]
        if is_observable(itemsv):
            val = itemsv.get()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            return val if isinstance(val, list) else []  # pyright: ignore[reportUnknownArgumentType,reportUnknownVariableType]
        return itemsv.value or []  # pyright: ignore[reportUnknownMemberType]

    def set_items_var_value(items: list[Any]) -> None:
        """Set the value on items_var (Variable, Observable, or ObservableList)."""
        itemsv = container["items_var"]
        if itemsv is None:
            return
        if is_items_var_observable_list:
            itemsv.clear()  # pyright: ignore[reportUnknownMemberType]
            itemsv.extend(items)  # pyright: ignore[reportUnknownMemberType]
        elif is_observable(itemsv):
            itemsv.set(items)  # pyright: ignore[reportUnknownMemberType]
        else:
            itemsv.value = items  # pyright: ignore[reportUnknownMemberType]

    # Helper to find model index for an item (searches entire tree)
    # Uses view model (may be proxy) so returned indices work with selection model
    def find_index_for_item(item: Any, parent: QModelIndex | None = None) -> QModelIndex:
        view_model = widget.model()  # type: ignore[attr-defined]
        if view_model is None:
            return QModelIndex()
        if parent is None:
            parent = QModelIndex()
        for row in range(view_model.rowCount(parent)):  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
            idx = view_model.index(row, 0, parent)  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            if get_item_at_index(idx) == item:  # pyright: ignore[reportUnknownArgumentType]
                return idx  # pyright: ignore[reportUnknownVariableType]
            # Search children recursively
            child_result = find_index_for_item(item, idx)  # pyright: ignore[reportUnknownArgumentType]
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
            item = get_item_at_index(current)
            if iv is not None:
                set_var_value(iv, item, current)
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
                set_items_var_value(get_selected_items())
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

    # Install Escape key handler to clear selection and directly set Variables to None/[]
    # This must be installed BEFORE the early return below, so it works even without selection bindings
    if deselect_on_escape:
        from qtpie.signals.connect import connect_event_handlers

        def on_escape_clear_selection() -> bool:
            # Use updating flag to prevent recursion from Variable change callbacks
            if updating["flag"]:
                return True
            updating["flag"] = True
            try:
                # Clear Qt selection model
                sm = container["selection_model"]
                if sm is not None:
                    sm.clear()  # pyright: ignore[reportUnknownMemberType]

                # Directly set Variables - don't rely on Qt signals
                # IMPORTANT: Check if value is already None/[] before setting to avoid
                # triggering notification chains when sibling proxies share the same value
                iv = container["item_var"]
                if iv is not None and get_var_value(iv) is not None:
                    set_var_value(iv, None)

                isv = container["items_var"]
                if isv is not None:
                    current_items = get_items_var_value()
                    if current_items:  # Only set if not already empty
                        set_items_var_value([])

                wv = container["widget_var"]
                if wv is not None and get_var_value(wv) is not None:
                    set_var_value(wv, None)
            finally:
                updating["flag"] = False

            return True  # Consume the event

        connect_event_handlers(host, widget, "", {"onEscapeKey": on_escape_clear_selection})

    # Now do initialization and Variable → Widget bindings
    # (only if variables are already resolved)
    if item_var is None and items_var is None and widget_var is None:
        return  # No vars yet, escape handler is connected and will work

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
        initial_items = get_items_var_value()
        if not initial_items:
            set_items_var_value(get_selected_items())

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

        # For nested paths like "workspace?.selected_item", subscribe to ROOT Variable
        def on_item_resolved(item: Any) -> None:
            sm = container["selection_model"]
            if sm is not None:
                idx = find_index_for_item(item)
                if idx.isValid():
                    sm.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
                        idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
                    )

        subscribe_to_root_variable_change(
            root_variable,
            selected_item_path,
            resolve_or_create_variable_fn,
            host,
            container,
            updating,
            "item",
            id(widget),
            None,
            on_item_resolved,
        )

    # For nested paths like "workspace?.selected_items", subscribe to ROOT Variable
    # This must be OUTSIDE the items_var check because when root is None,
    # items_var will also be None (path can't be resolved yet)
    def on_items_resolved(items: Any) -> None:
        if not isinstance(items, list) or not items:
            return
        sm = container["selection_model"]
        if sm is not None:
            sm.clearSelection()  # pyright: ignore[reportUnknownMemberType]
            for item in items:  # pyright: ignore[reportUnknownVariableType]
                idx = find_index_for_item(item)
                if idx.isValid():
                    sm.select(idx, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)  # pyright: ignore[reportUnknownMemberType]

    subscribe_to_root_variable_change(
        root_variable,
        selected_items_path,
        resolve_or_create_variable_fn,
        host,
        container,
        updating,
        "items",
        id(widget),
        None,
        on_items_resolved,
    )
