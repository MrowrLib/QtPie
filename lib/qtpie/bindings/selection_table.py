"""Selection bindings for QTableView."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


def setup_table_selection_bindings(
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
    resolve_or_create_variable_fn: Any = None,  # Callable to resolve/create variables
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
        source = resolve_or_create_variable_fn(host, selected_row_path, int)
        if isinstance(source, VarType):
            row_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_column_path:
        source = resolve_or_create_variable_fn(host, selected_column_path, int)
        if isinstance(source, VarType):
            column_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_cell_path:
        source = resolve_or_create_variable_fn(host, selected_cell_path, None)
        if isinstance(source, VarType):
            cell_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_item_path:
        source = resolve_or_create_variable_fn(host, selected_item_path, None)
        if isinstance(source, VarType):
            item_var = source  # pyright: ignore[reportUnknownVariableType]

    # Multi selection variables
    if selected_rows_path:
        source = resolve_or_create_variable_fn(host, selected_rows_path, None)
        if isinstance(source, VarType):
            rows_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_columns_path:
        source = resolve_or_create_variable_fn(host, selected_columns_path, None)
        if isinstance(source, VarType):
            columns_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_cells_path:
        source = resolve_or_create_variable_fn(host, selected_cells_path, None)
        if isinstance(source, VarType):
            cells_var = source  # pyright: ignore[reportUnknownVariableType]

    if selected_items_path:
        source = resolve_or_create_variable_fn(host, selected_items_path, None)
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
                source = resolve_or_create_variable_fn(host, selected_row_path, int)
                if isinstance(source, VarType):
                    row_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_column_path is not None and column_var is None:
                source = resolve_or_create_variable_fn(host, selected_column_path, int)
                if isinstance(source, VarType):
                    column_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_cell_path is not None and cell_var is None:
                source = resolve_or_create_variable_fn(host, selected_cell_path, None)
                if isinstance(source, VarType):
                    cell_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_item_path is not None and item_var is None:
                source = resolve_or_create_variable_fn(host, selected_item_path, None)
                if isinstance(source, VarType):
                    item_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_rows_path is not None and rows_var is None:
                source = resolve_or_create_variable_fn(host, selected_rows_path, None)
                if isinstance(source, VarType):
                    rows_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_columns_path is not None and columns_var is None:
                source = resolve_or_create_variable_fn(host, selected_columns_path, None)
                if isinstance(source, VarType):
                    columns_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_cells_path is not None and cells_var is None:
                source = resolve_or_create_variable_fn(host, selected_cells_path, None)
                if isinstance(source, VarType):
                    cells_var = source  # pyright: ignore[reportUnknownVariableType]
            if selected_items_path is not None and items_var is None:
                source = resolve_or_create_variable_fn(host, selected_items_path, None)
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
