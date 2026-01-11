"""Shared binding application logic for Widget and Window."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from observant import Observable, ObservableList
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
    from qtpie.variable import _RequiredBindingDescriptor  # pyright: ignore[reportPrivateUsage]

    # First try normal resolution
    source = resolve_binding_source(host, path)  # type: ignore[arg-type]
    if isinstance(source, VarType):
        return source

    # Check for bare Variable[T] annotation (using _RequiredBindingDescriptor)
    # Strip leading underscores for lookup
    lookup_name = path.lstrip("_")
    underscore_name = f"_{lookup_name}"

    # Check both the exact name and underscore-prefixed name
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

    return None


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

    from qtpy.QtCore import QModelIndex, Qt
    from qtpy.QtWidgets import QComboBox

    from qtpie.variable import Variable as VarType

    # Resolve the Variables (creating them if they're bare annotations)
    index_var: VarType[int] | None = None
    item_var: VarType[Any] | None = None

    if selected_index_path is not None:
        source = _resolve_or_create_variable(host, selected_index_path, int)
        if isinstance(source, VarType):
            index_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_item_path is not None:
        source = _resolve_or_create_variable(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]

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
        indexes_var: VarType[list[int]] | None = None
        items_list_var: VarType[list[Any]] | None = None

        if selected_indexes_path is not None:
            source = _resolve_or_create_variable(host, selected_indexes_path, None)
            if isinstance(source, VarType):
                indexes_var = source  # pyright: ignore[reportUnknownVariableType]

        if selected_items_list_path is not None:
            source = _resolve_or_create_variable(host, selected_items_list_path, None)
            if isinstance(source, VarType):
                items_list_var = source  # pyright: ignore[reportUnknownVariableType]

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

    from qtpy.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt

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
        if is_format_string(bind_path):
            from qtpie.bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                setter = adapter.setter

                def make_setter(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                    def setter_fn(val: Any) -> None:
                        s(w, val)

                    return setter_fn

                widget_setter = make_setter(setter, widget_instance)
                create_format_binding(host, bind_path, widget_setter)  # type: ignore[arg-type]

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
            continue

        # Check if this is a model widget (QComboBox, QListView, etc.) with a list source
        if _is_model_widget(widget_instance):
            obs_list: ObservableList[Any] | None = None

            # Extract ObservableList from Variable or use directly
            if isinstance(source, VarType):
                wrapper = source.observable
                if isinstance(wrapper, ObservableList):
                    obs_list = wrapper
            elif isinstance(source, ObservableList):
                obs_list = source

            if obs_list is not None:
                # Decide which model type to use
                # QTableView (or explicit columns=) uses ReactiveTableModel
                # Others (QComboBox, QListView) use ReactiveListModel
                use_table_model = _is_table_view(widget_instance) or field_info.table_columns is not None

                if use_table_model:
                    # Create ReactiveTableModel for QTableView
                    from qtpie.models import ReactiveTableModel

                    model = ReactiveTableModel(
                        obs_list,
                        parent=widget_instance,
                        columns=field_info.table_columns,
                        headers=field_info.table_headers,
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

                widget_instance.setModel(model)  # type: ignore[attr-defined]

                # Set up selection bindings based on widget type
                if use_table_model:
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
