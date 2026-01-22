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
    selected_widget_path: str | None = None,
    resolve_or_create_variable_fn: Any = None,  # Callable to resolve/create variables
    root_variable: Any = None,  # Root Variable for nested paths (passed from model_binding)
) -> None:
    """Set up selection bindings specific to QTableView.

    Supports both single and multi-selection bindings:
    - Single: selectedRow, selectedColumn, selectedCell, selectedItem, selectedWidget
    - Multi: selectedRows, selectedColumns, selectedCells, selectedItems

    Args:
        root_variable: Root Variable for nested binding paths (e.g., workspace for "workspace?.selected_row")
    """
    # Check if any binding is specified
    has_single = any([selected_row_path, selected_column_path, selected_cell_path, selected_item_path, selected_widget_path])
    has_multi = any([selected_rows_path, selected_columns_path, selected_cells_path, selected_items_path])
    if not has_single and not has_multi:
        return

    from observant import Observable, ObservableProxy

    from qtpie.variable import Variable as VarType

    # Helper to check if source is Variable, Observable, or ObservableProxy
    def is_var_or_obs(source: Any) -> bool:
        return isinstance(source, (VarType, Observable, ObservableProxy))

    # Resolve all Variables (or Observables for record field bindings)
    row_var: Any | None = None
    column_var: Any | None = None
    cell_var: Any | None = None
    item_var: Any | None = None
    widget_var: Any | None = None
    rows_var: Any | None = None
    columns_var: Any | None = None
    cells_var: Any | None = None
    items_var: Any | None = None

    # Single selection variables
    if selected_row_path:
        source = resolve_or_create_variable_fn(host, selected_row_path, int)
        if is_var_or_obs(source):
            row_var = source

    if selected_column_path:
        source = resolve_or_create_variable_fn(host, selected_column_path, int)
        if is_var_or_obs(source):
            column_var = source

    if selected_cell_path:
        source = resolve_or_create_variable_fn(host, selected_cell_path, None)
        if is_var_or_obs(source):
            cell_var = source

    if selected_item_path:
        source = resolve_or_create_variable_fn(host, selected_item_path, None)
        if is_var_or_obs(source):
            item_var = source

    if selected_widget_path:
        source = resolve_or_create_variable_fn(host, selected_widget_path, None)
        if is_var_or_obs(source):
            widget_var = source

    # Multi selection variables
    if selected_rows_path:
        source = resolve_or_create_variable_fn(host, selected_rows_path, None)
        if is_var_or_obs(source):
            rows_var = source

    if selected_columns_path:
        source = resolve_or_create_variable_fn(host, selected_columns_path, None)
        if is_var_or_obs(source):
            columns_var = source

    if selected_cells_path:
        source = resolve_or_create_variable_fn(host, selected_cells_path, None)
        if is_var_or_obs(source):
            cells_var = source

    if selected_items_path:
        source = resolve_or_create_variable_fn(host, selected_items_path, None)
        if is_var_or_obs(source):
            items_var = source

    # ALWAYS call _setup_table_selection_bindings_impl to connect the signal handler early.
    # This ensures the selection binding handler is connected BEFORE user's signal handlers.
    # The handler uses a mutable container so it can access Variables resolved later.
    _setup_table_selection_bindings_impl(
        host,
        widget,
        model,
        row_var,
        column_var,
        cell_var,
        item_var,
        widget_var,
        rows_var,
        columns_var,
        cells_var,
        items_var,
        root_variable=root_variable,
        selected_row_path=selected_row_path,
        selected_item_path=selected_item_path,
        resolve_or_create_variable_fn=resolve_or_create_variable_fn,
    )


def _setup_table_selection_bindings_impl(
    host: QWidget,
    widget: QWidget,
    model: Any,  # ReactiveTableModel
    row_var: Any | None,  # Variable[int] | None
    column_var: Any | None,  # Variable[int] | None
    cell_var: Any | None,  # Variable[tuple[int, int]] | None
    item_var: Any | None,  # Variable[Any] | None
    widget_var: Any | None,  # Variable[QWidget | None] | None
    rows_var: Any | None,  # Variable[list[int]] | None
    columns_var: Any | None,  # Variable[list[int]] | None
    cells_var: Any | None,  # Variable[list[tuple[int, int]]] | None
    items_var: Any | None,  # Variable[list[Any]] | None
    root_variable: Any = None,  # Root Variable for nested paths
    selected_row_path: str | None = None,  # For re-resolution
    selected_item_path: str | None = None,  # For re-resolution
    resolve_or_create_variable_fn: Any = None,  # For re-resolving nested paths
) -> None:
    """Implementation of table selection bindings (called after Variables are resolved)."""
    from observant import Observable, ObservableProxy
    from qtpy.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt

    # Flag to prevent circular updates
    updating = {"flag": False}

    # Use mutable container so handler closures can access updated values
    # (Variables may be resolved AFTER handler is connected)
    container: dict[str, Any] = {
        "model": model,
        "row_var": row_var,
        "column_var": column_var,
        "cell_var": cell_var,
        "item_var": item_var,
        "widget_var": widget_var,
        "rows_var": rows_var,
        "columns_var": columns_var,
        "cells_var": cells_var,
        "items_var": items_var,
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
    def set_var_value(var: Any, value: Any, row: int = -1) -> None:
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

        from qtpie.models.reactive_table_model import TABLE_PROXY_ROLE

        if var is None:
            return
        if is_observable(var):
            var.set(value)  # pyright: ignore[reportUnknownMemberType]
        else:
            # For item_var, try to get the proxy from the model
            proxy: ObservableProxy[Any] | None = None
            if row >= 0 and var is container["item_var"]:
                m = container["model"]
                if m is not None:
                    try:
                        model_index = m.index(row, 0)
                        proxy = m.data(model_index, TABLE_PROXY_ROLE)
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

    # Helper functions - use container for model/selection_model
    def get_item_at_row(row: int) -> Any:
        m = container["model"]
        if m is None:
            return None
        if row < 0 or row >= m.rowCount():
            return None
        model_index = m.index(row, 0)
        return m.data(model_index, Qt.ItemDataRole.UserRole)

    def get_current_row() -> int:
        sm = container["selection_model"]
        if sm is None:
            return -1
        idx = sm.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if idx.isValid():  # pyright: ignore[reportUnknownMemberType]
            return int(idx.row())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return -1

    def get_current_column() -> int:
        sm = container["selection_model"]
        if sm is None:
            return -1
        idx = sm.currentIndex()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if idx.isValid():  # pyright: ignore[reportUnknownMemberType]
            return int(idx.column())  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return -1

    def get_selected_rows() -> list[int]:
        sm = container["selection_model"]
        if sm is None:
            return []
        indexes = sm.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        rows: set[int] = set()
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            rows.add(int(idx.row()))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return sorted(rows)

    def get_selected_columns() -> list[int]:
        sm = container["selection_model"]
        if sm is None:
            return []
        indexes = sm.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        cols: set[int] = set()
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            cols.add(int(idx.column()))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return sorted(cols)

    def get_selected_cells() -> list[tuple[int, int]]:
        sm = container["selection_model"]
        if sm is None:
            return []
        indexes = sm.selectedIndexes()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        cells: list[tuple[int, int]] = []
        for idx in indexes:  # pyright: ignore[reportUnknownVariableType]
            cells.append((int(idx.row()), int(idx.column())))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return sorted(cells)

    def get_selected_items() -> list[Any]:
        rows = get_selected_rows()
        return [get_item_at_row(r) for r in rows if get_item_at_row(r) is not None]

    def set_current_cell(row: int, col: int) -> None:
        m = container["model"]
        sm = container["selection_model"]
        if m is None or sm is None:
            return
        if row < 0 or row >= m.rowCount():
            return
        if col < 0 or col >= m.columnCount():
            return
        idx = m.index(row, col)
        sm.setCurrentIndex(  # pyright: ignore[reportUnknownMemberType]
            idx, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )

    # Helper to get the embedded widget at a cell (for selectedWidget binding)
    def get_widget_at_cell(index: QModelIndex) -> Any:
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
            row = current.row() if current.isValid() else -1
            col = current.column() if current.isValid() else -1
            rv = container["row_var"]
            cv = container["column_var"]
            cellv = container["cell_var"]
            iv = container["item_var"]
            wv = container["widget_var"]
            if rv is not None:
                set_var_value(rv, row)
            if cv is not None:
                set_var_value(cv, col)
            if cellv is not None:
                set_var_value(cellv, (row, col))
            if iv is not None:
                set_var_value(iv, get_item_at_row(row) if row >= 0 else None, row)
            if wv is not None:
                set_var_value(wv, get_widget_at_cell(current))
        finally:
            updating["flag"] = False

    def on_selection_changed(_selected: QItemSelection, _deselected: QItemSelection) -> None:
        if updating["flag"]:
            return
        updating["flag"] = True
        try:
            rowsv = container["rows_var"]
            colsv = container["columns_var"]
            cellsv = container["cells_var"]
            itemsv = container["items_var"]
            if rowsv is not None:
                set_var_value(rowsv, get_selected_rows())
            if colsv is not None:
                set_var_value(colsv, get_selected_columns())
            if cellsv is not None:
                set_var_value(cellsv, get_selected_cells())
            if itemsv is not None:
                set_var_value(itemsv, get_selected_items())
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
        # Always connect to currentChanged for single selection vars
        # Handler will check if vars are None
        sm.currentChanged.connect(on_current_changed)  # pyright: ignore[reportUnknownMemberType]
        # Always connect to selectionChanged for multi selection vars
        sm.selectionChanged.connect(on_selection_changed)  # pyright: ignore[reportUnknownMemberType]

    # Connect handler NOW (before user's signal handlers)
    connect_selection_handler()

    # Track model changes - selection model changes when model is replaced
    if hasattr(model, "modelReset"):
        model.modelReset.connect(connect_selection_handler)  # pyright: ignore[reportUnknownMemberType]

    # Now do initialization and Variable → Widget bindings
    # (only if variables are already resolved)

    # Check if we have any vars to work with
    has_single = row_var is not None or column_var is not None or cell_var is not None or item_var is not None or widget_var is not None
    has_multi = rows_var is not None or columns_var is not None or cells_var is not None or items_var is not None

    if not has_single and not has_multi:
        return  # No vars yet, handler is connected and will work when vars are set

    # Initialize single selection variables from current state
    current_row = get_current_row()
    current_col = get_current_column()

    if row_var is not None:
        if get_var_value(row_var) is None:
            set_var_value(row_var, current_row if current_row >= 0 else 0)
        else:
            set_current_cell(get_var_value(row_var), current_col if current_col >= 0 else 0)
            current_row = get_var_value(row_var)

    if column_var is not None:
        if get_var_value(column_var) is None:
            set_var_value(column_var, current_col if current_col >= 0 else 0)
        else:
            set_current_cell(current_row if current_row >= 0 else 0, get_var_value(column_var))
            current_col = get_var_value(column_var)

    if cell_var is not None:
        if get_var_value(cell_var) is None:
            effective_row = current_row if current_row >= 0 else 0
            effective_col = current_col if current_col >= 0 else 0
            set_var_value(cell_var, (effective_row, effective_col))
        else:
            r, c = get_var_value(cell_var)
            set_current_cell(r, c)

    if item_var is not None:
        effective_row = current_row if current_row >= 0 else 0
        initial_item = get_var_value(item_var)
        if initial_item is None:
            set_var_value(item_var, get_item_at_row(effective_row))
        else:
            # Sync selection Widget to match the Variable value
            m = container["model"]
            if m is not None:
                for row in range(m.rowCount()):
                    if get_item_at_row(row) == initial_item:
                        col = get_current_column()
                        set_current_cell(row, col if col >= 0 else 0)
                        break

    # Initialize widget_var to current selection's widget (read-only binding)
    if widget_var is not None:
        sm = container["selection_model"]
        if sm is not None:
            current_idx = sm.currentIndex()  # pyright: ignore[reportUnknownMemberType]
            set_var_value(widget_var, get_widget_at_cell(current_idx))

    # Initialize multi selection variables
    if rows_var is not None:
        if get_var_value(rows_var) is None:
            m = container["model"]
            set_var_value(rows_var, get_selected_rows() or ([0] if m and m.rowCount() > 0 else []))

    if columns_var is not None:
        if get_var_value(columns_var) is None:
            m = container["model"]
            set_var_value(columns_var, get_selected_columns() or ([0] if m and m.columnCount() > 0 else []))

    if cells_var is not None:
        if get_var_value(cells_var) is None:
            m = container["model"]
            set_var_value(cells_var, get_selected_cells() or ([(0, 0)] if m and m.rowCount() > 0 else []))

    if items_var is not None:
        if get_var_value(items_var) is None:
            set_var_value(items_var, get_selected_items())

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
                cellv = container["cell_var"]
                iv = container["item_var"]
                if cellv is not None:
                    set_var_value(cellv, (new_row, col if col >= 0 else 0))
                if iv is not None:
                    set_var_value(iv, get_item_at_row(new_row), new_row)
            finally:
                updating["flag"] = False

        row_var.on_change(on_row_var_change)

        # For nested paths like "workspace?.selected_row", subscribe to ROOT
        # Variable changes. When root changes from None to a real object,
        # we need to re-resolve the row_var path and sync the selection.
        if root_variable is not None and selected_row_path is not None and resolve_or_create_variable_fn is not None:
            from qtpie.variable import Variable as VarType

            root_subscribed_key = f"row_root_subscribed_{id(widget)}"
            if not container.get(root_subscribed_key, False):
                container[root_subscribed_key] = True

                def on_root_variable_change_row(*_args: Any) -> None:
                    """Re-resolve row_var when root Variable changes."""
                    if updating["flag"]:
                        return

                    assert selected_row_path is not None
                    assert resolve_or_create_variable_fn is not None
                    new_source = resolve_or_create_variable_fn(host, selected_row_path, int)
                    if new_source is None:
                        return

                    new_row: int | None = None
                    if isinstance(new_source, VarType):
                        new_row = new_source.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    elif isinstance(new_source, (Observable, ObservableProxy)):
                        val = new_source.get() if isinstance(new_source, Observable) else new_source.unwrap()  # pyright: ignore[reportUnknownVariableType]
                        new_row = val if isinstance(val, int) else None

                    if new_row is not None and new_row >= 0:
                        updating["flag"] = True
                        try:
                            col = get_current_column()
                            set_current_cell(new_row, col if col >= 0 else 0)  # pyright: ignore[reportUnknownArgumentType]
                        finally:
                            updating["flag"] = False

                root_variable.on_change(on_root_variable_change_row)

    if column_var is not None:

        def on_column_var_change(new_col: int) -> None:
            if updating["flag"]:
                return
            updating["flag"] = True
            try:
                row = get_current_row()
                set_current_cell(row if row >= 0 else 0, new_col)
                # Update related variables
                cellv = container["cell_var"]
                if cellv is not None:
                    set_var_value(cellv, (row if row >= 0 else 0, new_col))
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
                rv = container["row_var"]
                cv = container["column_var"]
                iv = container["item_var"]
                if rv is not None:
                    set_var_value(rv, r)
                if cv is not None:
                    set_var_value(cv, c)
                if iv is not None:
                    set_var_value(iv, get_item_at_row(r), r)
            finally:
                updating["flag"] = False

        cell_var.on_change(on_cell_var_change)

    # For nested paths like "workspace?.selected_item", subscribe to ROOT Variable changes.
    # When root changes from None to a real object, we need to re-resolve the item_var path
    # and sync the selection to match the item value.
    if item_var is not None and root_variable is not None and selected_item_path is not None and resolve_or_create_variable_fn is not None:
        from qtpie.variable import Variable as VarType

        root_subscribed_key = f"item_root_subscribed_{id(widget)}"
        if not container.get(root_subscribed_key, False):
            container[root_subscribed_key] = True

            def on_root_variable_change_item(*_args: Any) -> None:
                """Re-resolve item_var when root Variable changes."""
                if updating["flag"]:
                    return

                assert selected_item_path is not None
                assert resolve_or_create_variable_fn is not None
                new_source = resolve_or_create_variable_fn(host, selected_item_path, None)
                if new_source is None:
                    return

                new_item: Any = None
                if isinstance(new_source, VarType):
                    new_item = new_source.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                elif isinstance(new_source, (Observable, ObservableProxy)):
                    new_item = new_source.get() if isinstance(new_source, Observable) else new_source.unwrap()  # pyright: ignore[reportUnknownVariableType]

                if new_item is not None:
                    # Find the row for this item and select it
                    updating["flag"] = True
                    try:
                        m = container["model"]
                        if m is not None:
                            for row in range(m.rowCount()):
                                if get_item_at_row(row) == new_item:
                                    col = get_current_column()
                                    set_current_cell(row, col if col >= 0 else 0)
                                    break
                    finally:
                        updating["flag"] = False

            root_variable.on_change(on_root_variable_change_item)
