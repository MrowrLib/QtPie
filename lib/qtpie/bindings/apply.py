"""Shared binding application logic for Widget and Window."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy
from qtpy.QtWidgets import QWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from qtpie.new_field import NewField


class BindingConfig(Protocol):
    """Protocol for config objects that support bindings."""

    fields: dict[str, NewField]
    auto_bind: bool
    widget_props: dict[str, Any]


def _is_model_widget(widget: QWidget) -> bool:
    """Check if widget supports setModel() - e.g., QComboBox, QListView, QTableView."""
    set_model = getattr(widget, "setModel", None)
    return set_model is not None and callable(set_model)


def _is_table_view(widget: QWidget) -> bool:
    """Check if widget is a QTableView (needs ReactiveTableModel)."""
    from qtpy.QtWidgets import QTableView

    return isinstance(widget, QTableView)


def _is_tree_view(widget: QWidget) -> bool:
    """Check if widget is a QTreeView (needs ReactiveTreeModel)."""
    from qtpy.QtWidgets import QTreeView

    return isinstance(widget, QTreeView)


def pre_create_selection_variables(host: QWidget, config: BindingConfig) -> None:
    """Pre-create Variables for selection bindings that reference bare Variable[T] annotations.

    This allows `_index: Variable[int]` (no new()) to work with selectedIndex="_index".
    Must be called BEFORE binding application.

    Works with both Widget and App configs.
    """
    from observant import Observable

    from qtpie.state import QtPieState
    from qtpie.variable import Variable as VarType
    from qtpie.variable import _RequiredBindingDescriptor  # pyright: ignore[reportPrivateUsage]

    # Get required bindings from config
    required_bindings: set[str] = getattr(config, "required_bindings", set())
    if not required_bindings:
        return

    # Find which required bindings are used as selection bindings
    all_selection_paths: set[str] = set()
    for field_info in config.fields.values():
        # QComboBox/QListView bindings
        if field_info.selected_index is not None:
            all_selection_paths.add(field_info.selected_index.lstrip("_"))
        if field_info.selected_item is not None:
            all_selection_paths.add(field_info.selected_item.lstrip("_"))
        # QListView multi selection bindings
        if field_info.selected_indexes is not None:
            all_selection_paths.add(field_info.selected_indexes.lstrip("_"))
        if field_info.selected_items_list is not None:
            all_selection_paths.add(field_info.selected_items_list.lstrip("_"))
        # QTableView single selection bindings
        if field_info.selected_row is not None:
            all_selection_paths.add(field_info.selected_row.lstrip("_"))
        if field_info.selected_column is not None:
            all_selection_paths.add(field_info.selected_column.lstrip("_"))
        if field_info.selected_cell is not None:
            all_selection_paths.add(field_info.selected_cell.lstrip("_"))
        # QTableView multi selection bindings
        if field_info.selected_rows is not None:
            all_selection_paths.add(field_info.selected_rows.lstrip("_"))
        if field_info.selected_columns is not None:
            all_selection_paths.add(field_info.selected_columns.lstrip("_"))
        if field_info.selected_cells is not None:
            all_selection_paths.add(field_info.selected_cells.lstrip("_"))
        if field_info.selected_items is not None:
            all_selection_paths.add(field_info.selected_items.lstrip("_"))
        # Note: QTreeView uses selected_item and selected_items which are already
        # handled above (shared with QComboBox/QListView/QTableView)

    if not all_selection_paths:
        return

    # Ensure _qtpie state exists
    state = getattr(host, "_qtpie", None)
    if state is None:
        state = QtPieState(host)
        host._qtpie = state  # type: ignore[attr-defined]

    # Create Variables for required bindings that are used as selection bindings
    for name in list(required_bindings):
        lookup_name = name.lstrip("_")
        if lookup_name not in all_selection_paths:
            continue

        # Check if already created
        if name in state.variables:
            continue

        # Get the descriptor to find the inner type
        cls_attr = getattr(type(host), name, None)
        if isinstance(cls_attr, _RequiredBindingDescriptor):
            # For selection bindings, always use Observable(None)
            # The value will be synced from the widget's current selection
            wrapper = Observable(None)
            var: VarType[Any] = VarType(wrapper)
            state.register_variable(name, var)


def _resolve_or_create_variable(
    host: QWidget,
    path: str,
    inner_type: type | None = None,
) -> Any:
    """Resolve a binding path to a Variable, creating one if it's a bare annotation.

    For bare `Variable[T]` annotations (no `= new()`), this will create the Variable
    on-the-fly with a None default, allowing it to sync from the widget.

    Also searches the parent widget hierarchy for matching Variables.

    Args:
        host: The Widget/Window instance
        path: The binding path (e.g., "_index")
        inner_type: The inner type for the Variable if we need to create it (unused for selection bindings)

    Returns:
        The Variable instance, or None if not found/creatable.
    """
    from observant import Observable

    from qtpie.bindings import resolve_binding_source
    from qtpie.state import QtPieState
    from qtpie.variable import Variable as VarType
    from qtpie.variable import (
        _RequiredBindingDescriptor,  # pyright: ignore[reportPrivateUsage]
        _try_get_variable,  # pyright: ignore[reportPrivateUsage]
    )

    # First try normal resolution on host
    source = resolve_binding_source(host, path)  # type: ignore[arg-type]
    if isinstance(source, VarType):
        return source

    # Check for bare Variable[T] annotation (using _RequiredBindingDescriptor)
    # Strip leading underscores for lookup
    lookup_name = path.lstrip("_")
    underscore_name = f"_{lookup_name}"

    # Check both the exact name and underscore-prefixed name on host
    for attr_name in [lookup_name, underscore_name]:
        cls_attr = getattr(type(host), attr_name, None)
        if isinstance(cls_attr, _RequiredBindingDescriptor):
            # Found a required binding - create the Variable now
            if not hasattr(host, "_qtpie"):
                host._qtpie = QtPieState(host)  # type: ignore[attr-defined]

            qtpie_state = host._qtpie  # type: ignore[attr-defined]

            # For selection bindings, always use Observable(None)
            # The value will be synced from the widget's current selection
            # We can't use _create_observable_for_type because it tries to instantiate complex types
            wrapper = Observable(None)
            var: VarType[Any] = VarType(wrapper)
            qtpie_state.register_variable(attr_name, var)  # pyright: ignore[reportUnknownMemberType]

            return var

    # Try to find Variable in parent hierarchy (for selection bindings to parent Variables)
    from qtpy.QtWidgets import QApplication

    current: Any = host
    while True:
        if not hasattr(current, "parent") or not callable(current.parent):
            break
        parent: Any = current.parent()
        if parent is None:
            break

        # Try both the original path and underscore variants
        for attr_name in [path, lookup_name, underscore_name]:
            found = _try_get_variable(parent, attr_name)
            if found is not None:
                return found

        current = parent

    # Fallback: check QApplication.instance()
    app = QApplication.instance()
    if app is not None:
        for attr_name in [path, lookup_name, underscore_name]:
            found = _try_get_variable(app, attr_name)
            if found is not None:
                return found

    return None


def _apply_model_binding(
    host: QWidget,
    widget_instance: QWidget,
    source: Any,  # BindingSource
    bind_path: str,
    field_info: Any,  # NewField
) -> bool:
    """Apply model binding for QComboBox, QListView, QTreeView, QTableView.

    Returns True if model binding was applied, False otherwise.
    """

    from observant import Observable, ObservableList

    from qtpie.variable import Variable as VarType

    obs_list: ObservableList[Any] | None = None
    root_variable: VarType[Any] | None = None

    # For nested paths like "workspace.collections", find the ROOT Variable
    # so we can re-sync when it changes from None to a real object
    bind_path_normalized = bind_path.replace("?.", ".")
    if "." in bind_path_normalized:
        root_name = bind_path_normalized.split(".")[0]
        # Try to find root variable on host or in parent hierarchy
        root_attr: Any = getattr(host, root_name, None)
        if root_attr is None:
            # Walk up parent hierarchy
            from qtpy.QtWidgets import QApplication

            current: Any = host
            while root_attr is None:
                if not hasattr(current, "parent") or not callable(current.parent):
                    break
                parent: Any = current.parent()
                if parent is None:
                    break
                root_attr = getattr(parent, root_name, None)
                current = parent
            # Fallback to QApplication
            if root_attr is None:
                app = QApplication.instance()
                if app is not None:
                    root_attr = getattr(app, root_name, None)
        if root_attr is not None and isinstance(root_attr, VarType):
            root_variable = cast(VarType[Any], root_attr)

    # Extract ObservableList from Variable or use directly
    if isinstance(source, VarType):
        wrapper = source.observable  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if isinstance(wrapper, ObservableList):
            obs_list = wrapper  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(wrapper, (Observable, ObservableProxy)):
            # Source might be Observable[list] or ObservableProxy with nested list
            # Create a synced ObservableList that updates when source changes
            val = wrapper.get() if isinstance(wrapper, Observable) else wrapper.unwrap()  # pyright: ignore[reportUnknownVariableType]
            if isinstance(val, list):
                obs_list = ObservableList(cast(list[Any], val))
            elif val is None:
                # Initially None - create empty list, will populate later
                obs_list = ObservableList[Any]()
    elif isinstance(source, ObservableList):
        obs_list = source  # pyright: ignore[reportUnknownVariableType]
    elif isinstance(source, Observable):
        val = source.get()  # pyright: ignore[reportUnknownVariableType]
        if isinstance(val, list):
            obs_list = ObservableList(cast(list[Any], val))
        elif val is None:
            obs_list = ObservableList[Any]()

    if obs_list is None:
        return False

    # Decide which model type to use
    # QTableView (or explicit columns=) uses ReactiveTableModel
    # QTreeView (or explicit children=) uses ReactiveTreeModel
    # Others (QComboBox, QListView) use ReactiveListModel
    use_table_model = _is_table_view(widget_instance) or field_info.table_columns is not None
    use_tree_model = _is_tree_view(widget_instance) or field_info.tree_children is not None

    if use_tree_model:
        # Create ReactiveTreeModel for QTreeView
        from qtpie.bindings.format_binding import create_item_formatter
        from qtpie.models import ReactiveTreeModel

        # Check for format= to customize item display
        format_fn = None
        if field_info.model_format is not None:
            format_fn = create_item_formatter(field_info.model_format)

        # Default children attribute to "children" if not specified
        children_attr = field_info.tree_children or "children"

        model = ReactiveTreeModel(
            obs_list,
            parent=widget_instance,
            children_attr=children_attr,
            format_fn=format_fn,
        )
    elif use_table_model:
        # Create ReactiveTableModel for QTableView
        from qtpie.models import ReactiveTableModel

        model = ReactiveTableModel(
            obs_list,
            parent=widget_instance,
            columns=field_info.table_columns,
            headers=field_info.table_headers,
            checkable=field_info.table_checkable,
            checkable_text=field_info.table_checkable_text,
        )
    else:
        # Create ReactiveListModel for QComboBox, QListView, etc.
        from qtpie.bindings.format_binding import create_item_formatter
        from qtpie.models import ReactiveListModel

        # Check for format= to customize item display
        format_fn = None
        if field_info.model_format is not None:
            format_fn = create_item_formatter(field_info.model_format)

        model = ReactiveListModel(obs_list, parent=widget_instance, format_fn=format_fn)

    # Wrap in filter/sort proxy if filter= or sort= is specified
    if field_info.model_filter is not None or field_info.model_sort is not None:
        from qtpie.models import ReactiveFilterProxyModel

        proxy = ReactiveFilterProxyModel(
            parent=widget_instance,
            filter_expr=field_info.model_filter,
            sort_key=field_info.model_sort,
            widget=host,  # type: ignore[arg-type]
        )
        proxy.setSourceModel(model)
        widget_instance.setModel(proxy)  # type: ignore[attr-defined]
    else:
        widget_instance.setModel(model)  # type: ignore[attr-defined]

    # For nested paths, subscribe to ROOT Variable to re-sync when it changes
    # Also handle expand=True for QTreeView
    should_expand = use_tree_model and getattr(field_info, "tree_expand", False)

    if root_variable is not None:
        nested_path = ".".join(bind_path_normalized.split(".")[1:])

        def make_root_sync_for_model(
            root_var: VarType[Any],
            target: ObservableList[Any],
            path: str,
            tree_widget: QWidget | None,
            expand_on_change: bool,
        ) -> None:
            def on_root_change(*_: Any) -> None:
                root_val: Any = root_var.value
                if root_val is None:
                    target.clear()
                    return
                # Traverse nested path
                nested_val: Any = root_val
                for part in path.split("."):
                    if nested_val is None:
                        break
                    nested_val = getattr(nested_val, part, None)
                if isinstance(nested_val, list):
                    target.clear()
                    target.extend(cast(list[Any], nested_val))
                    # Expand all if requested (QTreeView with expand=True)
                    if expand_on_change and tree_widget is not None:
                        from qtpy.QtCore import QTimer

                        # Defer expandAll to after model updates
                        QTimer.singleShot(0, tree_widget.expandAll)  # type: ignore[attr-defined]
                elif nested_val is None:
                    target.clear()

            root_var.observable.on_change(on_root_change)  # pyright: ignore[reportUnknownMemberType]

        make_root_sync_for_model(
            root_variable,
            obs_list,
            nested_path,
            widget_instance if should_expand else None,
            should_expand,
        )

    # Set up selection bindings based on widget type
    if use_tree_model:
        # QTreeView selection bindings
        _setup_tree_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_item,
            field_info.selected_items,
        )

        # Handle expand=True: expandAll immediately and on data changes
        if should_expand:
            from qtpy.QtCore import QTimer

            # Expand all immediately after model is set (defer to let model populate)
            QTimer.singleShot(0, widget_instance.expandAll)  # type: ignore[attr-defined]

    elif use_table_model:
        # QTableView-specific selection bindings
        _setup_table_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_row,
            field_info.selected_column,
            field_info.selected_cell,
            field_info.selected_item,
            field_info.selected_rows,
            field_info.selected_columns,
            field_info.selected_cells,
            field_info.selected_items,
        )
    else:
        # QComboBox/QListView selection bindings
        _setup_selection_bindings(
            host,
            widget_instance,
            model,
            field_info.selected_index,
            field_info.selected_item,
            field_info.selected_indexes,
            field_info.selected_items_list,
        )

    return True


def _setup_selection_bindings(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveListModel
    selected_index_path: str | None,
    selected_item_path: str | None,
    selected_indexes_path: str | None = None,
    selected_items_list_path: str | None = None,
) -> None:
    """Set up two-way selection bindings for model widgets.

    Args:
        host: The Widget/Window instance containing the Variables
        widget: The model widget (QComboBox, QListView, etc.)
        model: The ReactiveListModel backing the widget
        selected_index_path: Variable path for index binding (e.g., "_selected_idx")
        selected_item_path: Variable path for item binding (e.g., "_selected_item")
        selected_indexes_path: Variable path for multi-index binding (QListView only)
        selected_items_list_path: Variable path for multi-item binding (QListView only)
    """
    has_single = selected_index_path is not None or selected_item_path is not None
    has_multi = selected_indexes_path is not None or selected_items_list_path is not None
    if not has_single and not has_multi:
        return

    from qtpy.QtCore import QTimer

    from qtpie.variable import Variable as VarType

    # Resolve the Variables (creating them if they're bare annotations)
    index_var: VarType[int] | None = None
    item_var: VarType[Any] | None = None
    indexes_var: VarType[list[int]] | None = None
    items_list_var: VarType[list[Any]] | None = None

    if selected_index_path is not None:
        source = _resolve_or_create_variable(host, selected_index_path, int)
        if isinstance(source, VarType):
            index_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_item_path is not None:
        source = _resolve_or_create_variable(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_indexes_path is not None:
        source = _resolve_or_create_variable(host, selected_indexes_path, None)
        if isinstance(source, VarType):
            indexes_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_items_list_path is not None:
        source = _resolve_or_create_variable(host, selected_items_list_path, None)
        if isinstance(source, VarType):
            items_list_var = source  # pyright: ignore[reportUnknownVariableType]

    # Check if we couldn't resolve any Variables that were requested
    # If so, the widget might not be parented yet - schedule deferred retry
    missing_single = (selected_index_path is not None and index_var is None) or (selected_item_path is not None and item_var is None)
    missing_multi = (selected_indexes_path is not None and indexes_var is None) or (selected_items_list_path is not None and items_list_var is None)

    if missing_single or missing_multi:

        def retry_binding() -> None:
            # Re-resolve Variables after parenting
            nonlocal index_var, item_var, indexes_var, items_list_var
            if selected_index_path is not None and index_var is None:
                source = _resolve_or_create_variable(host, selected_index_path, int)
                if isinstance(source, VarType):
                    index_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_item_path is not None and item_var is None:
                source = _resolve_or_create_variable(host, selected_item_path, None)
                if isinstance(source, VarType):
                    item_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_indexes_path is not None and indexes_var is None:
                source = _resolve_or_create_variable(host, selected_indexes_path, None)
                if isinstance(source, VarType):
                    indexes_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_items_list_path is not None and items_list_var is None:
                source = _resolve_or_create_variable(host, selected_items_list_path, None)
                if isinstance(source, VarType):
                    items_list_var = source  # pyright: ignore[reportUnknownVariableType]

            # If we found them now, set up the actual bindings
            has_vars = index_var is not None or item_var is not None or indexes_var is not None or items_list_var is not None
            if has_vars:
                _setup_selection_bindings_impl(host, widget, model, index_var, item_var, indexes_var, items_list_var)

        QTimer.singleShot(0, retry_binding)
        return

    # Set up bindings immediately if Variables were found
    _setup_selection_bindings_impl(host, widget, model, index_var, item_var, indexes_var, items_list_var)


def _setup_selection_bindings_impl(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveListModel
    index_var: Any | None,  # Variable[int] | None
    item_var: Any | None,  # Variable[Any] | None
    indexes_var: Any | None,  # Variable[list[int]] | None
    items_list_var: Any | None,  # Variable[list[Any]] | None
) -> None:
    """Implementation of selection bindings (called after Variables are resolved)."""
    from qtpy.QtCore import QModelIndex, Qt
    from qtpy.QtWidgets import QComboBox

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Helper to get item at index via model's UserRole
    def get_item_at_index(idx: int) -> Any:
        if idx < 0 or idx >= model.rowCount():
            return None
        model_index = model.index(idx, 0)
        return model.data(model_index, Qt.ItemDataRole.UserRole)

    # Helper to find index of item
    def find_index_of_item(item: Any) -> int:
        for i in range(model.rowCount()):
            if get_item_at_index(i) == item:
                return i
        return -1

    # Detect widget type and set up appropriate bindings
    # QComboBox: currentIndex() returns int, setCurrentIndex(int), currentIndexChanged signal
    # QListView/QTableView: use selectionModel, currentIndex() returns QModelIndex
    is_combobox = isinstance(widget, QComboBox)

    if is_combobox:
        # QComboBox-specific setup
        set_current_index_fn = getattr(widget, "setCurrentIndex", None)
        current_index_changed = getattr(widget, "currentIndexChanged", None)
        current_widget_index_fn = getattr(widget, "currentIndex", None)

        # Get the current widget index (will sync Variables from this if they're None)
        current_widget_idx: int = current_widget_index_fn() if current_widget_index_fn else 0

        if index_var is not None and set_current_index_fn is not None:
            initial_idx = index_var.value
            # Variable[int] can have None value if no default provided
            if initial_idx is not None:  # pyright: ignore[reportUnnecessaryComparison]
                set_current_index_fn(initial_idx)
                current_widget_idx = initial_idx  # Update for item_var sync below
            else:
                # Sync Variable to widget's current state
                index_var.value = current_widget_idx

        if item_var is not None:
            initial_item = item_var.value
            if initial_item is not None:
                # Set widget to match item if index didn't already set it
                if index_var is None and set_current_index_fn is not None:
                    idx = find_index_of_item(initial_item)
                    if idx >= 0:
                        set_current_index_fn(idx)
            else:
                # Sync item Variable to widget's current selection
                item_var.value = get_item_at_index(current_widget_idx)

        # Variable → Widget binding (and cross-update between index/item vars)
        if index_var is not None and set_current_index_fn is not None:

            def on_index_var_change_combo(new_idx: int) -> None:
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    set_current_index_fn(new_idx)
                    # Also update item_var if both bindings are present
                    if item_var is not None:
                        item_var.value = get_item_at_index(new_idx)
                finally:
                    updating["flag"] = False

            index_var.on_change(on_index_var_change_combo)

        if item_var is not None and set_current_index_fn is not None:

            def on_item_var_change_combo(*_args: Any) -> None:
                # Note: Observable passes value, ObservableProxy passes nothing
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    new_item = item_var.value  # type: ignore[union-attr]
                    idx = find_index_of_item(new_item)
                    if idx >= 0:
                        set_current_index_fn(idx)
                        # Also update index_var if both bindings are present
                        if index_var is not None:
                            index_var.value = idx
                finally:
                    updating["flag"] = False

            item_var.on_change(on_item_var_change_combo)

        # Widget → Variable binding
        if current_index_changed is not None and (index_var is not None or item_var is not None):

            def on_widget_selection_changed_combo(new_idx: int) -> None:
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    if index_var is not None:
                        index_var.value = new_idx
                    if item_var is not None:
                        item_var.value = get_item_at_index(new_idx)
                finally:
                    updating["flag"] = False

            current_index_changed.connect(on_widget_selection_changed_combo)

    else:
        # QListView/QTableView - use selectionModel
        from qtpy.QtCore import QItemSelectionModel

        selection_model = widget.selectionModel()  # type: ignore[attr-defined]
        if selection_model is None:
            return

        # Helper to set index via selection model
        def set_row_index(row: int) -> None:
            if row < 0 or row >= model.rowCount():
                return
            model_idx = model.index(row, 0)
            selection_model.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
                model_idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )

        # Get current row from selection model
        def get_current_row() -> int:
            current_idx = selection_model.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            if current_idx.isValid():  # pyright: ignore[reportUnknownMemberType]
                return int(current_idx.row())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
            return -1

        # Initialize from current state
        current_row = get_current_row()

        if index_var is not None:
            initial_idx = index_var.value
            # Variable[int] can have None value if no default provided
            if initial_idx is not None:  # pyright: ignore[reportUnnecessaryComparison]
                set_row_index(initial_idx)
                current_row = initial_idx
            else:
                # Sync Variable to widget's current state
                index_var.value = current_row if current_row >= 0 else 0

        if item_var is not None:
            initial_item = item_var.value
            if initial_item is not None:
                # Set widget to match item if index didn't already set it
                if index_var is None:
                    idx = find_index_of_item(initial_item)
                    if idx >= 0:
                        set_row_index(idx)
                        current_row = idx
            else:
                # Sync item Variable to widget's current selection
                effective_row = current_row if current_row >= 0 else 0
                item_var.value = get_item_at_index(effective_row)

        # Variable → Widget binding
        if index_var is not None:

            def on_index_var_change_view(new_idx: int) -> None:
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    set_row_index(new_idx)
                    # Also update item_var if both bindings are present
                    if item_var is not None:
                        item_var.value = get_item_at_index(new_idx)
                finally:
                    updating["flag"] = False

            index_var.on_change(on_index_var_change_view)

        if item_var is not None:

            def on_item_var_change_view(*_args: Any) -> None:
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    new_item = item_var.value  # type: ignore[union-attr]
                    idx = find_index_of_item(new_item)
                    if idx >= 0:
                        set_row_index(idx)
                        if index_var is not None:
                            index_var.value = idx
                finally:
                    updating["flag"] = False

            item_var.on_change(on_item_var_change_view)

        # Widget → Variable binding via selection model's currentChanged signal
        if index_var is not None or item_var is not None:

            def on_view_selection_changed(current: QModelIndex, _previous: QModelIndex) -> None:
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    row = current.row() if current.isValid() else -1
                    if index_var is not None:
                        index_var.value = row
                    if item_var is not None:
                        item_var.value = get_item_at_index(row) if row >= 0 else None
                finally:
                    updating["flag"] = False

            selection_model.currentChanged.connect(on_view_selection_changed)  # pyright: ignore[reportUnknownMemberType]

        # QListView multi-selection bindings (selectedIndexes, selectedItems)
        # indexes_var and items_list_var are already resolved and passed in
        if indexes_var is not None or items_list_var is not None:
            from qtpy.QtCore import QItemSelection

            # Helper to get selected rows from selection model
            def get_selected_rows() -> list[int]:
                selected_indexes = selection_model.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                rows: set[int] = set()
                for idx in selected_indexes:  # pyright: ignore[reportUnknownVariableType]
                    rows.add(idx.row())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
                return sorted(rows)

            # Helper to get items at selected rows
            def get_selected_items() -> list[Any]:
                rows = get_selected_rows()
                return [get_item_at_index(row) for row in rows if get_item_at_index(row) is not None]

            # Initialize multi-selection Variables
            if indexes_var is not None:
                initial_indexes = indexes_var.value
                if initial_indexes is None or not initial_indexes:  # pyright: ignore[reportUnnecessaryComparison]
                    indexes_var.value = get_selected_rows()

            if items_list_var is not None:
                initial_items = items_list_var.value
                if initial_items is None or not initial_items:  # pyright: ignore[reportUnnecessaryComparison]
                    items_list_var.value = get_selected_items()

            # Widget → Variable binding via selectionChanged signal (for multi-selection)
            def on_view_multi_selection_changed(_selected: QItemSelection, _deselected: QItemSelection) -> None:
                if updating["flag"]:
                    return
                updating["flag"] = True
                try:
                    if indexes_var is not None:
                        indexes_var.value = get_selected_rows()
                    if items_list_var is not None:
                        items_list_var.value = get_selected_items()
                finally:
                    updating["flag"] = False

            selection_model.selectionChanged.connect(on_view_multi_selection_changed)  # pyright: ignore[reportUnknownMemberType]


def _setup_table_selection_bindings(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTableModel
    selected_row_path: str | None,
    selected_column_path: str | None,
    selected_cell_path: str | None,
    selected_item_path: str | None,
    selected_rows_path: str | None,
    selected_columns_path: str | None,
    selected_cells_path: str | None,
    selected_items_path: str | None,
) -> None:
    """Set up selection bindings specific to QTableView.

    Supports both single and multi-selection bindings:
    - Single: selectedRow, selectedColumn, selectedCell, selectedItem
    - Multi: selectedRows, selectedColumns, selectedCells, selectedItems
    """
    # Check if any binding is specified
    has_single = any([selected_row_path, selected_column_path, selected_cell_path, selected_item_path])
    has_multi = any([selected_rows_path, selected_columns_path, selected_cells_path, selected_items_path])
    if not has_single and not has_multi:
        return

    from qtpy.QtCore import QTimer

    from qtpie.variable import Variable as VarType

    # Resolve all Variables
    row_var: VarType[int] | None = None
    column_var: VarType[int] | None = None
    cell_var: VarType[tuple[int, int]] | None = None
    item_var: VarType[Any] | None = None
    rows_var: VarType[list[int]] | None = None
    columns_var: VarType[list[int]] | None = None
    cells_var: VarType[list[tuple[int, int]]] | None = None
    items_var: VarType[list[Any]] | None = None

    # Single selection variables
    if selected_row_path:
        source = _resolve_or_create_variable(host, selected_row_path, int)
        if isinstance(source, VarType):
            row_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_column_path:
        source = _resolve_or_create_variable(host, selected_column_path, int)
        if isinstance(source, VarType):
            column_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_cell_path:
        source = _resolve_or_create_variable(host, selected_cell_path, None)
        if isinstance(source, VarType):
            cell_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_item_path:
        source = _resolve_or_create_variable(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]

    # Multi selection variables
    if selected_rows_path:
        source = _resolve_or_create_variable(host, selected_rows_path, None)
        if isinstance(source, VarType):
            rows_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_columns_path:
        source = _resolve_or_create_variable(host, selected_columns_path, None)
        if isinstance(source, VarType):
            columns_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_cells_path:
        source = _resolve_or_create_variable(host, selected_cells_path, None)
        if isinstance(source, VarType):
            cells_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_items_path:
        source = _resolve_or_create_variable(host, selected_items_path, None)
        if isinstance(source, VarType):
            items_var = source  # pyright: ignore[reportUnknownVariableType]

    # Check if we couldn't resolve any Variables that were requested
    # If so, the widget might not be parented yet - schedule deferred retry
    missing_single = (
        (selected_row_path is not None and row_var is None)
        or (selected_column_path is not None and column_var is None)
        or (selected_cell_path is not None and cell_var is None)
        or (selected_item_path is not None and item_var is None)
    )
    missing_multi = (
        (selected_rows_path is not None and rows_var is None)
        or (selected_columns_path is not None and columns_var is None)
        or (selected_cells_path is not None and cells_var is None)
        or (selected_items_path is not None and items_var is None)
    )

    if missing_single or missing_multi:

        def retry_binding() -> None:
            # Re-resolve Variables after parenting
            nonlocal row_var, column_var, cell_var, item_var, rows_var, columns_var, cells_var, items_var
            if selected_row_path is not None and row_var is None:
                source = _resolve_or_create_variable(host, selected_row_path, int)
                if isinstance(source, VarType):
                    row_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_column_path is not None and column_var is None:
                source = _resolve_or_create_variable(host, selected_column_path, int)
                if isinstance(source, VarType):
                    column_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_cell_path is not None and cell_var is None:
                source = _resolve_or_create_variable(host, selected_cell_path, None)
                if isinstance(source, VarType):
                    cell_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_item_path is not None and item_var is None:
                source = _resolve_or_create_variable(host, selected_item_path, None)
                if isinstance(source, VarType):
                    item_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_rows_path is not None and rows_var is None:
                source = _resolve_or_create_variable(host, selected_rows_path, None)
                if isinstance(source, VarType):
                    rows_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_columns_path is not None and columns_var is None:
                source = _resolve_or_create_variable(host, selected_columns_path, None)
                if isinstance(source, VarType):
                    columns_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_cells_path is not None and cells_var is None:
                source = _resolve_or_create_variable(host, selected_cells_path, None)
                if isinstance(source, VarType):
                    cells_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_items_path is not None and items_var is None:
                source = _resolve_or_create_variable(host, selected_items_path, None)
                if isinstance(source, VarType):
                    items_var = source  # pyright: ignore[reportUnknownVariableType]

            # If we found any Variables now, set up the actual bindings
            has_vars = (
                row_var is not None
                or column_var is not None
                or cell_var is not None
                or item_var is not None
                or rows_var is not None
                or columns_var is not None
                or cells_var is not None
                or items_var is not None
            )
            if has_vars:
                _setup_table_selection_bindings_impl(host, widget, model, row_var, column_var, cell_var, item_var, rows_var, columns_var, cells_var, items_var)

        QTimer.singleShot(0, retry_binding)
        return

    # Set up bindings immediately if Variables were found
    _setup_table_selection_bindings_impl(host, widget, model, row_var, column_var, cell_var, item_var, rows_var, columns_var, cells_var, items_var)


def _setup_table_selection_bindings_impl(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTableModel
    row_var: Any | None,  # Variable[int] | None
    column_var: Any | None,  # Variable[int] | None
    cell_var: Any | None,  # Variable[tuple[int, int]] | None
    item_var: Any | None,  # Variable[Any] | None
    rows_var: Any | None,  # Variable[list[int]] | None
    columns_var: Any | None,  # Variable[list[int]] | None
    cells_var: Any | None,  # Variable[list[tuple[int, int]]] | None
    items_var: Any | None,  # Variable[list[Any]] | None
) -> None:
    """Implementation of table selection bindings (called after Variables are resolved)."""
    from qtpy.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt

    has_single = row_var is not None or column_var is not None or cell_var is not None or item_var is not None
    has_multi = rows_var is not None or columns_var is not None or cells_var is not None or items_var is not None

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Get selection model
    selection_model = widget.selectionModel()  # type: ignore[attr-defined]
    if selection_model is None:
        return

    # Helper functions
    def get_item_at_row(row: int) -> Any:
        if row < 0 or row >= model.rowCount():
            return None
        model_index = model.index(row, 0)
        return model.data(model_index, Qt.ItemDataRole.UserRole)

    def get_current_row() -> int:
        idx = selection_model.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if idx.isValid():  # pyright: ignore[reportUnknownMemberType]
            return int(idx.row())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return -1

    def get_current_column() -> int:
        idx = selection_model.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if idx.isValid():  # pyright: ignore[reportUnknownMemberType]
            return int(idx.column())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return -1

    def get_selected_rows() -> list[int]:
        indexes = selection_model.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        rows: set[int] = set()
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            rows.add(int(idx.row()))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return sorted(rows)

    def get_selected_columns() -> list[int]:
        indexes = selection_model.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        cols: set[int] = set()
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            cols.add(int(idx.column()))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return sorted(cols)

    def get_selected_cells() -> list[tuple[int, int]]:
        indexes = selection_model.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        cells: list[tuple[int, int]] = []
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            cells.append((int(idx.row()), int(idx.column())))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return sorted(cells)

    def get_selected_items() -> list[Any]:
        rows = get_selected_rows()
        return [get_item_at_row(r) for r in rows if get_item_at_row(r) is not None]

    def set_current_cell(row: int, col: int) -> None:
        if row < 0 or row >= model.rowCount():
            return
        if col < 0 or col >= model.columnCount():
            return
        idx = model.index(row, col)
        selection_model.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
            idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )

    # Initialize single selection variables from current state
    current_row = get_current_row()
    current_col = get_current_column()

    if row_var is not None:
        if row_var.value is None:  # pyright: ignore[reportUnnecessaryComparison]
            row_var.value = current_row if current_row >= 0 else 0
        else:
            set_current_cell(row_var.value, current_col if current_col >= 0 else 0)
            current_row = row_var.value

    if column_var is not None:
        if column_var.value is None:  # pyright: ignore[reportUnnecessaryComparison]
            column_var.value = current_col if current_col >= 0 else 0
        else:
            set_current_cell(current_row if current_row >= 0 else 0, column_var.value)
            current_col = column_var.value

    if cell_var is not None:
        if cell_var.value is None:  # pyright: ignore[reportUnnecessaryComparison]
            effective_row = current_row if current_row >= 0 else 0
            effective_col = current_col if current_col >= 0 else 0
            cell_var.value = (effective_row, effective_col)
        else:
            r, c = cell_var.value
            set_current_cell(r, c)

    if item_var is not None:
        effective_row = current_row if current_row >= 0 else 0
        if item_var.value is None:
            item_var.value = get_item_at_row(effective_row)

    # Initialize multi selection variables
    if rows_var is not None:
        if rows_var.value is None:  # pyright: ignore[reportUnnecessaryComparison]
            rows_var.value = get_selected_rows() or [0] if model.rowCount() > 0 else []

    if columns_var is not None:
        if columns_var.value is None:  # pyright: ignore[reportUnnecessaryComparison]
            columns_var.value = get_selected_columns() or [0] if model.columnCount() > 0 else []

    if cells_var is not None:
        if cells_var.value is None:  # pyright: ignore[reportUnnecessaryComparison]
            cells_var.value = get_selected_cells() or [(0, 0)] if model.rowCount() > 0 else []

    if items_var is not None:
        if items_var.value is None:  # pyright: ignore[reportUnnecessaryComparison]
            items_var.value = get_selected_items()

    # Variable → Widget bindings (single)
    if row_var is not None:

        def on_row_var_change(new_row: int) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                col = get_current_column()
                set_current_cell(new_row, col if col >= 0 else 0)
                # Update related variables
                if cell_var is not None:
                    cell_var.value = (new_row, col if col >= 0 else 0)
                if item_var is not None:
                    item_var.value = get_item_at_row(new_row)
            finally:
                updating["flag"] = False

        row_var.on_change(on_row_var_change)

    if column_var is not None:

        def on_column_var_change(new_col: int) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                row = get_current_row()
                set_current_cell(row if row >= 0 else 0, new_col)
                # Update related variables
                if cell_var is not None:
                    cell_var.value = (row if row >= 0 else 0, new_col)
            finally:
                updating["flag"] = False

        column_var.on_change(on_column_var_change)

    if cell_var is not None:

        def on_cell_var_change(new_cell: tuple[int, int]) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                r, c = new_cell
                set_current_cell(r, c)
                # Update related variables
                if row_var is not None:
                    row_var.value = r
                if column_var is not None:
                    column_var.value = c
                if item_var is not None:
                    item_var.value = get_item_at_row(r)
            finally:
                updating["flag"] = False

        cell_var.on_change(on_cell_var_change)

    # Widget → Variable bindings
    def on_current_changed(current: QModelIndex, _previous: QModelIndex) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            row = current.row() if current.isValid() else -1
            col = current.column() if current.isValid() else -1
            if row_var is not None:
                row_var.value = row
            if column_var is not None:
                column_var.value = col
            if cell_var is not None:
                cell_var.value = (row, col)
            if item_var is not None:
                item_var.value = get_item_at_row(row) if row >= 0 else None
        finally:
            updating["flag"] = False

    def on_selection_changed(_selected: QItemSelection, _deselected: QItemSelection) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            if rows_var is not None:
                rows_var.value = get_selected_rows()
            if columns_var is not None:
                columns_var.value = get_selected_columns()
            if cells_var is not None:
                cells_var.value = get_selected_cells()
            if items_var is not None:
                items_var.value = get_selected_items()
        finally:
            updating["flag"] = False

    # Connect signals
    if has_single:
        selection_model.currentChanged.connect(on_current_changed)  # pyright: ignore[reportUnknownMemberType]

    if has_multi:
        selection_model.selectionChanged.connect(on_selection_changed)  # pyright: ignore[reportUnknownMemberType]


def _setup_tree_selection_bindings(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTreeModel
    selected_item_path: str | None,
    selected_items_path: str | None,
) -> None:
    """Set up selection bindings for QTreeView.

    Args:
        host: The Widget/Window instance containing the Variables
        widget: The QTreeView widget
        model: The ReactiveTreeModel backing the widget
        selected_item_path: Variable path for single item binding (e.g., "_selected_node")
        selected_items_path: Variable path for multi-item binding (e.g., "_selected_nodes")
    """
    if selected_item_path is None and selected_items_path is None:
        return

    from qtpy.QtCore import QTimer

    from qtpie.variable import Variable as VarType

    # Resolve Variables - may be None initially if widget isn't parented yet
    item_var: VarType[Any] | None = None
    items_var: VarType[list[Any]] | None = None

    if selected_item_path is not None:
        source = _resolve_or_create_variable(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_items_path is not None:
        source = _resolve_or_create_variable(host, selected_items_path, None)
        if isinstance(source, VarType):
            items_var = source  # pyright: ignore[reportUnknownVariableType]

    # If we didn't find the Variables yet, the widget might not be parented.
    # Schedule a deferred retry after the event loop processes parenting.
    if (selected_item_path is not None and item_var is None) or (selected_items_path is not None and items_var is None):

        def retry_binding() -> None:
            # Re-attempt resolution after parenting
            nonlocal item_var, items_var
            if selected_item_path is not None and item_var is None:
                source = _resolve_or_create_variable(host, selected_item_path, None)
                if isinstance(source, VarType):
                    item_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_items_path is not None and items_var is None:
                source = _resolve_or_create_variable(host, selected_items_path, None)
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


def _set_tabs_from_dict(
    tab_widget: Any,  # QTabWidget
    tabs: dict[str, type[QWidget]],
) -> dict[str, QWidget]:
    """Populate QTabWidget from dict. Returns name -> widget mapping."""
    tab_widget.clear()
    tab_widgets: dict[str, QWidget] = {}
    for name, widget_type in tabs.items():
        widget = widget_type(parent=tab_widget)
        tab_widgets[name] = widget
        tab_widget.addTab(widget, name)
    return tab_widgets


def _set_tabs_from_list(
    tab_widget: Any,  # QTabWidget
    tabs: list[type[QWidget]],
) -> dict[str, QWidget]:
    """Populate QTabWidget from list. Names from windowTitle() or class name."""
    tab_widget.clear()
    tab_widgets: dict[str, QWidget] = {}
    for widget_type in tabs:
        widget = widget_type(parent=tab_widget)
        name = widget.windowTitle() or widget_type.__name__  # Fallback to class name
        tab_widgets[name] = widget
        tab_widget.addTab(widget, name)
    return tab_widgets


def _resolve_widget_from_field(host: QWidget, field_name: str) -> QWidget | None:
    """Resolve a widget from a field name on the host.

    Handles:
    - Regular widget fields: returns the widget
    - Variable[T, W]: returns .widget
    - Variable[T, Dock[W]]: returns .widget.widget (the inner content widget)
    """
    if not hasattr(host, field_name):
        return None

    field_value = getattr(host, field_name)

    # Check if it's a Variable with a widget
    if hasattr(field_value, "widget"):
        widget = field_value.widget
        # Check if it's a Dock (Variable[T, Dock[W]])
        if hasattr(widget, "widget"):
            # It's a Dock, get the inner widget
            return widget.widget  # type: ignore[no-any-return]
        return widget  # type: ignore[no-any-return]

    # Regular widget field
    if isinstance(field_value, QWidget):
        return field_value

    return None


def _set_tabs_from_normalized(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    tabs: list[dict[str, Any]],
) -> dict[str, QWidget]:
    """Populate QTabWidget from normalized tab definitions.

    Tab definitions are dicts with:
    - {"type": "class", "cls": WidgetClass, "name": "TabName" | None}
    - {"type": "ref", "field": "field_name", "name": "TabName" | None}
    """
    tab_widget.clear()
    tab_widgets: dict[str, QWidget] = {}

    for tab_def in tabs:
        tab_type = tab_def.get("type")
        explicit_name = tab_def.get("name")

        if tab_type == "class":
            # Create new widget instance
            widget_cls = tab_def["cls"]
            widget = widget_cls(parent=tab_widget)
            # Name: explicit > windowTitle > class name
            name = explicit_name or widget.windowTitle() or widget_cls.__name__

        elif tab_type == "ref":
            # Reference existing widget by field name
            field_name = tab_def["field"]
            widget = _resolve_widget_from_field(host, field_name)
            if widget is None:
                continue  # Skip if field not found
            # Name: explicit > windowTitle > field name
            name = explicit_name or widget.windowTitle() or field_name

        else:
            continue  # Unknown type

        tab_widgets[name] = widget
        tab_widget.addTab(widget, name)

    return tab_widgets


def _bind_tab_widget_to_dict(
    tab_widget: Any,  # QTabWidget
    obs: ObservableDict[str, type[QWidget]],
    tab_widgets: dict[str, QWidget],
) -> None:
    """Bind QTabWidget to ObservableDict for granular reactive updates."""

    def on_insert(key: str, value: type[QWidget]) -> None:
        widget = value(parent=tab_widget)
        tab_widgets[key] = widget
        tab_widget.addTab(widget, key)

    def on_remove(key: str, _value: type[QWidget]) -> None:
        if key in tab_widgets:
            widget = tab_widgets.pop(key)
            idx = tab_widget.indexOf(widget)
            if idx >= 0:
                tab_widget.removeTab(idx)

    def on_replace(key: str, old: type[QWidget], new: type[QWidget]) -> None:
        on_remove(key, old)
        on_insert(key, new)

    def on_clear(_items: dict[str, type[QWidget]]) -> None:
        tab_widget.clear()
        tab_widgets.clear()

    obs.on_insert(on_insert)
    obs.on_remove(on_remove)
    obs.on_replace(on_replace)
    obs.on_clear(on_clear)


def _bind_tab_widget_to_list(
    tab_widget: Any,  # QTabWidget
    obs: ObservableList[type[QWidget]],
    tab_widgets: dict[str, QWidget],
) -> None:
    """Bind QTabWidget to ObservableList for granular reactive updates."""
    # Track widgets by index for proper removal
    widgets_by_index: list[QWidget] = list(tab_widgets.values())

    def on_insert(index: int, value: type[QWidget]) -> None:
        widget = value(parent=tab_widget)
        name = widget.windowTitle() or value.__name__
        widgets_by_index.insert(index, widget)
        tab_widgets[name] = widget
        tab_widget.insertTab(index, widget, name)

    def on_remove(index: int, _value: type[QWidget]) -> None:
        if 0 <= index < len(widgets_by_index):
            widget = widgets_by_index.pop(index)
            # Remove from name mapping
            for name, w in list(tab_widgets.items()):
                if w is widget:
                    del tab_widgets[name]
                    break
            tab_widget.removeTab(index)

    def on_replace(index: int, old: type[QWidget], new: type[QWidget]) -> None:
        on_remove(index, old)
        on_insert(index, new)

    def on_clear(_items: list[type[QWidget]]) -> None:
        tab_widget.clear()
        tab_widgets.clear()
        widgets_by_index.clear()

    obs.on_insert(on_insert)
    obs.on_remove(on_remove)
    obs.on_replace(on_replace)
    obs.on_clear(on_clear)


def _setup_tab_index_binding(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    var_name: str,
) -> None:
    """Set up two-way binding for selectedIndex."""
    from qtpie.bindings import resolve_binding_source
    from qtpie.variable import Variable as VarType

    source = resolve_binding_source(host, var_name)  # type: ignore[arg-type]
    if not isinstance(source, VarType):
        return

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Variable -> Tab
    def update_tab(value: int) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            if tab_widget.currentIndex() != value:
                tab_widget.setCurrentIndex(value)
        finally:
            updating["flag"] = False

    source.on_change(update_tab)

    # Initial sync
    initial_value = source.value
    if initial_value is not None:  # pyright: ignore[reportUnnecessaryComparison]
        tab_widget.setCurrentIndex(initial_value)
    else:
        # Sync Variable from widget's current state
        source.value = tab_widget.currentIndex()

    # Tab -> Variable
    def on_tab_changed(index: int) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            if source.value != index:
                source.value = index
        finally:
            updating["flag"] = False

    tab_widget.currentChanged.connect(on_tab_changed)


def _setup_tab_widget_binding(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    var_name: str,
) -> None:
    """Set up binding for selectedWidget (widget reference tracking)."""
    from qtpie.bindings import resolve_binding_source
    from qtpie.variable import Variable as VarType

    source = resolve_binding_source(host, var_name)  # type: ignore[arg-type]
    if not isinstance(source, VarType):
        return

    # Tab -> Variable (widget reference)
    def on_tab_changed(index: int) -> None:
        widget = tab_widget.widget(index)
        if source.value is not widget:
            source.value = widget

    tab_widget.currentChanged.connect(on_tab_changed)

    # Initial sync
    current_idx = tab_widget.currentIndex()
    if current_idx >= 0:
        source.value = tab_widget.widget(current_idx)


def _apply_tab_widget_bindings(
    host: QWidget,
    tab_widget: Any,  # QTabWidget
    field_info: Any,  # NewField
) -> None:
    """Apply tabs= and selection bindings to QTabWidget."""
    from qtpie.bindings import resolve_binding_source
    from qtpie.variable import Variable as VarType

    tabs_source = field_info.tabs
    tab_widgets: dict[str, QWidget] = {}

    if isinstance(tabs_source, str):
        # Variable reference - resolve and bind reactively
        source = resolve_binding_source(host, tabs_source)  # type: ignore[arg-type]
        if isinstance(source, VarType):
            obs = source.observable
            if isinstance(obs, ObservableDict):
                # Initial population from dict
                initial_value = obs.to_dict()
                tab_widgets = _set_tabs_from_dict(tab_widget, initial_value)  # pyright: ignore[reportArgumentType]
                # Subscribe for reactive updates
                _bind_tab_widget_to_dict(tab_widget, obs, tab_widgets)  # pyright: ignore[reportArgumentType]
            elif isinstance(obs, ObservableList):
                # Initial population from list
                initial_value = obs.to_list()
                tab_widgets = _set_tabs_from_list(tab_widget, initial_value)  # pyright: ignore[reportArgumentType]
                # Subscribe for reactive updates
                _bind_tab_widget_to_list(tab_widget, obs, tab_widgets)  # pyright: ignore[reportArgumentType]

    elif isinstance(tabs_source, list):
        # Normalized tab definitions (list of dicts with type markers)
        tab_widgets = _set_tabs_from_normalized(host, tab_widget, tabs_source)  # pyright: ignore[reportUnknownArgumentType]

    # Set up selection bindings
    if field_info.tab_selected_index:
        _setup_tab_index_binding(host, tab_widget, field_info.tab_selected_index)
    if field_info.tab_selected_widget:
        _setup_tab_widget_binding(host, tab_widget, field_info.tab_selected_widget)


def apply_auto_bindings(
    host: QWidget,
    config: BindingConfig,
    *,
    create_expression_binding_fn: Callable[[Any, str, Callable[[Any], None]], None] | None = None,
) -> None:
    """Apply auto-bindings for QWidget fields.

    Works with both Widget and Window instances.

    Args:
        host: The Widget or Window instance
        config: Configuration with fields, auto_bind, etc.
        create_expression_binding_fn: Optional function to create expression bindings
    """
    from qtpie.bindings import bind, create_format_binding, is_format_string, resolve_binding_source
    from qtpie.translations.translatable import Translatable
    from qtpie.variable import Variable as VarType

    for name, field_info in config.fields.items():
        # Skip list widget fields
        if field_info.is_list_widget:
            continue

        # Get the widget instance
        widget_instance = getattr(host, name, None)
        if widget_instance is None or not isinstance(widget_instance, QWidget):
            continue

        # Handle QTabWidget with tabs= binding
        if field_info.is_tab_widget and field_info.tabs is not None:
            _apply_tab_widget_bindings(host, widget_instance, field_info)
            continue

        # Determine bind path - may be string or Translatable
        bind_value = field_info.bind
        translatable: Translatable | None = None

        if isinstance(bind_value, Translatable):
            # Resolve translatable to get format string
            translatable = bind_value
            bind_path = translatable.resolve()
        elif bind_value is not None:
            bind_path = bind_value
        elif config.auto_bind:
            bind_path = name.lstrip("_")
        else:
            continue

        # Handle format strings
        # Also handle nested paths for NON-record widgets (paths like "parent_var.field")
        # because ObservableProxy creates new Observables for each path lookup.
        # But DON'T convert nested paths for Widget[T] record bindings - those should use
        # the existing record binding code path which handles optional chaining properly.
        is_nested_path = "." in bind_path.replace("?.", ".")

        # Check if this is a record binding (Widget[T] with a record type)
        has_record = hasattr(config, "record_type") and config.record_type is not None  # type: ignore[union-attr]

        # For record bindings, only use format binding if it's explicitly a format string
        # For non-record widgets, convert nested paths to format bindings for parent hierarchy lookup
        use_format_binding = is_format_string(bind_path) or (is_nested_path and not has_record and not _is_model_widget(widget_instance))
        format_template = bind_path if is_format_string(bind_path) else f"{{{bind_path}}}" if use_format_binding and is_nested_path else None

        if use_format_binding and (is_format_string(bind_path) or format_template is not None):
            from qtpie.bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                setter = adapter.setter

                def make_setter(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                    def setter_fn(val: Any) -> None:
                        s(w, val)  # noqa: B023 - val is parameter, not loop var

                    return setter_fn

                widget_setter = make_setter(setter, widget_instance)
                create_format_binding(host, bind_path if is_format_string(bind_path) else format_template, widget_setter)  # type: ignore[arg-type]

                # Register for hot-reload if this was a Translatable
                if translatable is not None:
                    from qtpie.translations.store import register_format_binding

                    register_format_binding(
                        widget_instance,
                        default_prop,
                        translatable.text,
                        translatable.context,
                        host,  # type: ignore[arg-type]
                        widget_setter,
                    )
            continue

        # Resolve the binding source
        source = resolve_binding_source(host, bind_path)  # type: ignore[arg-type]
        if source is None:
            # Source not found - might not be parented yet
            # Schedule deferred retry for model widgets
            if _is_model_widget(widget_instance):
                from qtpy.QtCore import QTimer

                def make_deferred_model_bind(w: QWidget, h: QWidget, bp: str, fi: Any) -> Callable[[], None]:
                    def retry_bind() -> None:
                        # Re-attempt resolution after parenting
                        deferred_source = resolve_binding_source(h, bp)  # type: ignore[arg-type]
                        if deferred_source is not None:
                            _apply_model_binding(h, w, deferred_source, bp, fi)

                    return retry_bind

                QTimer.singleShot(0, make_deferred_model_bind(widget_instance, host, bind_path, field_info))
            continue

        # Check if this is a model widget (QComboBox, QListView, etc.) with a list source
        if _is_model_widget(widget_instance):
            if _apply_model_binding(host, widget_instance, source, bind_path, field_info):
                continue

        # Create the binding
        if isinstance(source, VarType):
            bind(source).to(widget_instance)
        elif isinstance(source, Observable):
            # Set up binding for Observable (e.g., from record field)
            from qtpie.bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                # Set initial value
                adapter.setter(widget_instance, source.get())

                # Subscribe to Observable changes
                setter = adapter.setter

                def make_obs_to_widget(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                    def on_observable_change(v: Any) -> None:
                        s(w, v)

                    return on_observable_change

                source.on_change(make_obs_to_widget(setter, widget_instance))

                # Two-way binding: Widget → Observable
                if adapter.signal_name is not None and adapter.getter is not None:
                    signal = getattr(widget_instance, adapter.signal_name, None)
                    getter = adapter.getter

                    def make_widget_to_obs(obs: Observable[Any], g: Callable[[Any], Any], w: QWidget) -> Callable[[], None]:
                        def on_widget_change() -> None:
                            obs.set(g(w))

                        return on_widget_change

                    if signal is not None:
                        signal.connect(make_widget_to_obs(source, getter, widget_instance))


def apply_property_bindings(
    host: QWidget,
    config: BindingConfig,
    *,
    create_expression_binding_fn: Callable[[Any, str, Callable[[Any], None]], None] | None = None,
) -> None:
    """Apply property bindings like visible="_is_visible" or enabled="{_count > 0}".

    Works with both Widget and Window instances.
    """
    from qtpie.bindings import is_format_string, resolve_binding_source
    from qtpie.bindings.registry import get_binding_registry
    from qtpie.variable import Variable as VarType

    registry = get_binding_registry()

    for name, field_info in config.fields.items():
        if not field_info.property_bindings:
            continue

        widget_instance = getattr(host, name, None)
        if widget_instance is None or not isinstance(widget_instance, QWidget):
            continue

        for prop_name, bind_expr in field_info.property_bindings.items():
            adapter = registry.get(widget_instance, prop_name)
            if adapter is None or adapter.setter is None:
                continue

            setter = adapter.setter

            def make_setter(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                def setter_fn(val: Any) -> None:
                    s(w, val)

                return setter_fn

            prop_setter = make_setter(setter, widget_instance)

            if is_format_string(bind_expr):
                if create_expression_binding_fn is not None:
                    create_expression_binding_fn(host, bind_expr, prop_setter)
            else:
                source = resolve_binding_source(host, bind_expr)  # type: ignore[arg-type]
                if source is None:
                    continue

                if isinstance(source, VarType):
                    prop_setter(source.value)
                    source.on_change(prop_setter)
                elif isinstance(source, Observable):
                    prop_setter(source.get())
                    source.on_change(prop_setter)


def apply_reactive_widget_props(
    host: QWidget,
    config: BindingConfig,
) -> None:
    """Apply reactive widget properties from @widget/@window decorator.

    For props like windowTitle="{title}" or windowTitle=t("My App"), creates bindings.
    """
    from qtpie.bindings import create_format_binding, is_format_string
    from qtpie.translations.translatable import Translatable

    for prop_name, value in config.widget_props.items():
        translatable: Translatable | None = None
        template: str | None = None

        # Handle Translatable objects
        if isinstance(value, Translatable):
            translatable = value
            template = translatable.resolve()
        elif isinstance(value, str) and is_format_string(value):
            template = value
        else:
            continue

        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter_method = getattr(host, setter_name, None)
        if setter_method is None or not callable(setter_method):
            raise AttributeError(f"{type(host).__name__} has no setter '{setter_name}' for property '{prop_name}'")

        # If it's a format string, create format binding
        if is_format_string(template):
            create_format_binding(host, template, setter_method)  # type: ignore[arg-type]
        else:
            # Static translated text - just set it
            setter_method(template)

        # Register for hot-reload if this was a Translatable
        if translatable is not None:
            from qtpie.translations.store import register_format_binding

            register_format_binding(
                host,
                prop_name,
                translatable.text,
                translatable.context,
                host,  # type: ignore[arg-type]
                setter_method,  # type: ignore[arg-type]
            )
