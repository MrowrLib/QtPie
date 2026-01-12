"""NewField - Stores field configuration for deferred instantiation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, get_args, get_origin, get_type_hints

from .layout import GridPosition
from .utils.common import is_signal_on_type
from .variable import Variable, create_variable_descriptor


class NewField:
    """Stores args/kwargs for deferred field instantiation.

    For Variable[T] annotations: replaces itself with a Variable descriptor.
    For list[QWidget] annotations: stores binding info for list widget creation.
    For QWidget types: tracks layout inclusion/exclusion.
    For other types: @new_fields handles instantiation, passing all args/kwargs.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs
        self.name: str = ""
        self.field_type: type | None = None
        self.exclude_from_layout = False
        self.bind: str | Any | None = None  # Extracted for QWidgets in __set_name__ (can be Translatable)
        self.signal_connections: dict[str, str | Callable[..., Any]] = {}  # signal_name -> method_name or callable
        self.widget_props: dict[str, Any] = {}  # propName -> value (becomes setPropName(value))
        # Layout params for form/grid layouts
        self.label: str | None = None  # For form layouts: new(label="Name")
        self.grid: GridPosition | None = None  # For grid layouts: new(grid=(0, 0)) or (row, col, rowspan, colspan)
        # Widget args for Variable[T, W] - set via __call__
        self.widget_args: tuple[Any, ...] = ()
        self.widget_kwargs: dict[str, Any] = {}
        # list[QWidget] support
        self.is_list_widget: bool = False
        self.list_widget_type: type | None = None  # The QWidget type inside list[QWidget]
        self.list_format: str | Callable[[Any], str] | None = None  # Format for list items
        # set[QWidget] support
        self.is_set_widget: bool = False
        self.set_widget_type: type | None = None  # The QWidget type inside set[QWidget]
        self.set_format: str | Callable[[Any], str] | None = None  # Format for set items
        # Sort parameter for list/dict/set repeaters
        self.sort: bool | str | Callable[[Any], Any] | None = None
        # Object name and CSS classes
        self.object_name: str | None = None  # objectName for the widget
        self.css_classes: list[str] = []  # CSS classes for the widget
        # Property bindings (visible="_is_visible", enabled="{_count > 0}")
        self.property_bindings: dict[str, str] = {}  # prop_name -> binding expression
        # Model format for QComboBox/QListView/etc. with bind= to list
        self.model_format: str | None = None  # Format for model items: "{name} ({age})"
        # Table columns for QTableView with bind= to list
        self.table_columns: list[str] | None = None  # Column names: ["name", "age"]
        self.table_headers: dict[str, str] | None = None  # Custom headers: {"name": "Dog Name"}
        # Selection bindings for model widgets (QComboBox, QListView, etc.)
        self.selected_index: str | None = None  # Variable name for selectedIndex binding
        self.selected_item: str | None = None  # Variable name for selectedItem binding
        # QListView-specific selection bindings (multi)
        self.selected_indexes: str | None = None  # Variable name for selectedIndexes binding (list[int])
        self.selected_items_list: str | None = None  # Variable name for selectedItems binding (list[T]) for QListView
        # QTableView-specific selection bindings (single)
        self.selected_row: str | None = None  # Variable name for selectedRow binding
        self.selected_column: str | None = None  # Variable name for selectedColumn binding
        self.selected_cell: str | None = None  # Variable name for selectedCell binding (tuple[int, int])
        # QTableView-specific selection bindings (multi)
        self.selected_rows: str | None = None  # Variable name for selectedRows binding (list[int])
        self.selected_columns: str | None = None  # Variable name for selectedColumns binding (list[int])
        self.selected_cells: str | None = None  # Variable name for selectedCells binding (list[tuple])
        self.selected_items: str | None = None  # Variable name for selectedItems binding (list[T])
        # QTreeView-specific: children attribute name
        self.tree_children: str | None = None  # Attribute name for child items: "children"
        # Filter expression for model widgets: "{_search} in {name}"
        self.model_filter: str | None = None  # Filter expression evaluated per item
        # Sort key for model widgets: "{age}", "method_name", or callable
        self.model_sort: str | Callable[[Any], Any] | None = None
        # QTabWidget support
        self.is_tab_widget: bool = False
        # tabs= can be:
        # - str: Variable reference like "_tab_defs"
        # - list[dict]: Normalized tabs with type markers:
        #   - {"type": "class", "cls": WidgetClass, "name": "TabName" | None}
        #   - {"type": "ref", "field": "field_name", "name": "TabName" | None}
        self.tabs: list[dict[str, Any]] | str | None = None
        self.tab_selected_index: str | None = None  # Variable name for selectedIndex binding
        self.tab_selected_widget: str | None = None  # Variable name for selectedWidget binding
        # Translation support - track Translatable markers for binding registration
        self.translatable_args: list[tuple[int, Any]] = []  # (index, Translatable)
        self.translatable_kwargs: dict[str, Any] = {}  # kwarg_name -> Translatable
        # Variable bindings - maps child's required Variable names to parent's values/expressions
        self.variable_bindings: dict[str, Any] = {}  # child_var_name -> binding_value
        # Ref bindings - deferred attribute references to resolve after field instantiation
        self.ref_bindings: dict[str, Any] = {}  # kwarg_name -> Ref instance
        # Dock[T] support
        self.is_dock: bool = False
        self.dock_content_type: type | None = None  # The widget type inside Dock[T]
        self.dock_area: str | None = None  # dock="left", "right", "top", "bottom"
        self.dock_title: str | None = None  # title="Explorer"
        self.dock_below: str | None = None  # below="_explorer" (vertical split)
        self.dock_right_of: str | None = None  # rightOf="_console" (horizontal split)
        self.dock_left_of: str | None = None  # leftOf="_console" (horizontal split)
        self.dock_above: str | None = None  # above="_explorer" (vertical split)
        self.dock_group: str | None = None  # group="inspector" (tabify together)
        self.dock_group_selected_index: str | None = None  # groupSelectedIndex="_tab_index"
        self.dock_icon: str | None = None  # icon="terminal.svg" (tab icon)
        self.dock_visible: str | None = None  # visible="_show_dock" or "{expr}"
        self.dock_floating: str | None = None  # floating="_is_floating"
        self.dock_closable: bool | None = None  # closable=False (no X button)
        self.dock_floatable: bool | None = None  # floatable=False (can't pop out)
        self.dock_movable: bool | None = None  # movable=False (can't drag)
        self.dock_allowed_areas: list[str] | None = None  # allowedAreas=["left", "right"]
        self.dock_vertical_title_bar: bool | None = None  # verticalTitleBar=True
        # Variable[T, Dock[W]] support - Variable with a docked widget
        self.is_variable_dock: bool = False
        self.variable_dock_content_type: type | None = None  # The widget type W inside Variable[T, Dock[W]]
        # Chaining support: track all chained () calls for multi-level patterns
        # e.g., new(var_default)(dock_kwargs)(widget_kwargs)
        self._chain_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def __call__(self, *call_args: Any, **call_kwargs: Any) -> NewField:
        """Store chained call args: new(...)(...)(...).

        Supports multiple levels of chaining:
        - Dock[T]: new(dock_kwargs)(widget_kwargs)
        - Variable[T, W]: new(var_default)(widget_kwargs)
        - Variable[T, Dock[W]]: new(var_default)(dock_kwargs)(widget_kwargs)
        """
        self._chain_calls.append((call_args, call_kwargs))
        return self

    def _interpret_chain_for_dock(self) -> tuple[dict[str, Any], tuple[Any, ...], dict[str, Any]]:
        """Interpret chain calls for Dock[T] pattern.

        Pattern: new(dock_kwargs)(widget_args)
        - First call (self.kwargs): dock kwargs
        - Chain[0]: widget args/kwargs

        Returns:
            (dock_kwargs, widget_args, widget_kwargs)
        """
        dock_kwargs = dict(self.kwargs)
        widget_args: tuple[Any, ...] = ()
        widget_kwargs: dict[str, Any] = {}

        if self._chain_calls:
            widget_args, widget_kwargs = self._chain_calls[0]

        return dock_kwargs, widget_args, widget_kwargs

    def _interpret_chain_for_variable_dock(self) -> tuple[dict[str, Any], tuple[Any, ...], dict[str, Any]]:
        """Interpret chain calls for Variable[T, Dock[W]] pattern.

        Pattern: new(var_default)(dock_kwargs)(widget_args)
        - First call (self.args): variable default
        - Chain[0]: dock kwargs
        - Chain[1]: widget args/kwargs

        Returns:
            (dock_kwargs, widget_args, widget_kwargs)
        """
        dock_kwargs: dict[str, Any] = {}
        widget_args: tuple[Any, ...] = ()
        widget_kwargs: dict[str, Any] = {}

        if len(self._chain_calls) >= 1:
            # First chain call is dock kwargs
            _, dock_kwargs = self._chain_calls[0]
        if len(self._chain_calls) >= 2:
            # Second chain call is widget args/kwargs
            widget_args, widget_kwargs = self._chain_calls[1]

        return dock_kwargs, widget_args, widget_kwargs

    def _interpret_chain_for_variable(self) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Interpret chain calls for Variable[T, W] pattern (no Dock).

        Pattern: new(var_default)(widget_args)
        - First call (self.args): variable default
        - Chain[0]: widget args/kwargs

        Returns:
            (widget_args, widget_kwargs)
        """
        widget_args: tuple[Any, ...] = ()
        widget_kwargs: dict[str, Any] = {}

        if self._chain_calls:
            widget_args, widget_kwargs = self._chain_calls[0]

        return widget_args, widget_kwargs

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

        # Normalize aliases (title -> windowTitle, stylesheet -> styleSheet)
        self._normalize_kwargs_aliases()

        # Get the type annotation
        hints = get_type_hints(owner)
        self.field_type = hints.get(name)

        # If it's a Variable, replace self with a Variable descriptor
        origin = get_origin(self.field_type)
        if origin is Variable or self.field_type is Variable:
            default = self._get_variable_default()
            # Extract inner type from Variable[T] and optional widget type from Variable[T, W]
            inner_type: type | None = None
            widget_type: type | None = None
            if origin is Variable:
                args = get_args(self.field_type)
                inner_type = args[0] if args else None
                widget_type = args[1] if len(args) > 1 else None

            # Check if widget_type is Dock[X] - Variable[T, Dock[W]]
            # If so, extract the inner content type X and mark as variable dock
            dock_info: dict[str, Any] | None = None
            if widget_type is not None and self._is_dock_type_param(widget_type):
                # Extract the content widget type from Dock[W]
                dock_args = get_args(widget_type)
                if dock_args:
                    self.is_variable_dock = True
                    self.variable_dock_content_type = dock_args[0]

                    # Use triple-chaining pattern: new(var_default)(dock_kwargs)(widget_kwargs)
                    dock_kwargs, widget_args, widget_kwargs = self._interpret_chain_for_variable_dock()

                    # Normalize title -> windowTitle in dock_kwargs
                    if "title" in dock_kwargs:
                        dock_kwargs["windowTitle"] = dock_kwargs.pop("title")

                    # Extract dock-specific kwargs from dock_kwargs
                    self.dock_area = dock_kwargs.pop("dock", None)
                    self.dock_title = dock_kwargs.pop("windowTitle", None)
                    self.dock_below = dock_kwargs.pop("below", None)
                    self.dock_right_of = dock_kwargs.pop("rightOf", None)
                    self.dock_left_of = dock_kwargs.pop("leftOf", None)
                    self.dock_above = dock_kwargs.pop("above", None)
                    self.dock_group = dock_kwargs.pop("group", None)
                    self.dock_group_selected_index = dock_kwargs.pop("groupSelectedIndex", None)
                    self.dock_icon = dock_kwargs.pop("icon", None)
                    self.dock_visible = dock_kwargs.pop("visible", None)
                    self.dock_floating = dock_kwargs.pop("floating", None)
                    self.dock_closable = dock_kwargs.pop("closable", None)
                    self.dock_floatable = dock_kwargs.pop("floatable", None)
                    self.dock_movable = dock_kwargs.pop("movable", None)
                    self.dock_allowed_areas = dock_kwargs.pop("allowedAreas", None)
                    self.dock_vertical_title_bar = dock_kwargs.pop("verticalTitleBar", None)

                    # Store widget args/kwargs for later widget creation
                    self.widget_args = widget_args
                    self.widget_kwargs = widget_kwargs

                    # Store dock info for window.py to use
                    dock_info = {
                        "dock_area": self.dock_area,
                        "dock_title": self.dock_title,
                        "dock_below": self.dock_below,
                        "dock_right_of": self.dock_right_of,
                        "dock_left_of": self.dock_left_of,
                        "dock_above": self.dock_above,
                        "dock_group": self.dock_group,
                        "dock_group_selected_index": self.dock_group_selected_index,
                        "dock_icon": self.dock_icon,
                        "dock_visible": self.dock_visible,
                        "dock_floating": self.dock_floating,
                        "dock_closable": self.dock_closable,
                        "dock_floatable": self.dock_floatable,
                        "dock_movable": self.dock_movable,
                        "dock_allowed_areas": self.dock_allowed_areas,
                        "dock_vertical_title_bar": self.dock_vertical_title_bar,
                    }
                    # Use the content type as widget_type for the descriptor
                    widget_type = self.variable_dock_content_type
            else:
                # Regular Variable[T, W] - use single-chaining pattern: new(var_default)(widget_kwargs)
                widget_args, widget_kwargs = self._interpret_chain_for_variable()
                self.widget_args = widget_args
                self.widget_kwargs = widget_kwargs

            # Extract layout params from widget_kwargs (they're layout params, not widget constructor params)
            widget_kwargs_copy = dict(self.widget_kwargs)
            label = widget_kwargs_copy.pop("label", None)
            grid = widget_kwargs_copy.pop("grid", None)
            layout_kwarg = widget_kwargs_copy.pop("layout", None)
            exclude_from_layout = layout_kwarg is False

            # Extract name= and classes= for widget configuration (not constructor params)
            object_name: str | None = widget_kwargs_copy.pop("name", None)
            css_classes: list[str] = widget_kwargs_copy.pop("classes", None) or []

            # Extract validate= for auto-registering validators (only in kwargs, not widget_kwargs)
            validators = self.kwargs.pop("validate", None)

            descriptor = create_variable_descriptor(
                default,
                name,
                inner_type,
                widget_type,
                self.widget_args,
                widget_kwargs_copy,
                label,
                grid,
                exclude_from_layout,
                validators,
                object_name,
                css_classes,
                dock_info,
            )
            setattr(owner, name, descriptor)
            return

        # Handle Dock[T] - creates a Dock wrapper around a widget in a QDockWidget
        if self._is_dock_type():
            self.is_dock = True
            # Extract the content widget type from Dock[T]
            type_args = get_args(self.field_type)
            if type_args:
                self.dock_content_type = type_args[0]

            # Use double-chaining pattern: new(dock_kwargs)(widget_kwargs)
            dock_kwargs, widget_args, widget_kwargs = self._interpret_chain_for_dock()

            # Normalize title -> windowTitle in dock_kwargs
            if "title" in dock_kwargs:
                dock_kwargs["windowTitle"] = dock_kwargs.pop("title")

            # Extract dock-specific kwargs from dock_kwargs
            self.dock_area = dock_kwargs.pop("dock", None)
            self.dock_title = dock_kwargs.pop("windowTitle", None)
            self.dock_below = dock_kwargs.pop("below", None)
            self.dock_right_of = dock_kwargs.pop("rightOf", None)
            self.dock_left_of = dock_kwargs.pop("leftOf", None)
            self.dock_above = dock_kwargs.pop("above", None)
            self.dock_group = dock_kwargs.pop("group", None)
            self.dock_group_selected_index = dock_kwargs.pop("groupSelectedIndex", None)
            self.dock_icon = dock_kwargs.pop("icon", None)
            self.dock_visible = dock_kwargs.pop("visible", None)
            self.dock_floating = dock_kwargs.pop("floating", None)
            self.dock_closable = dock_kwargs.pop("closable", None)
            self.dock_floatable = dock_kwargs.pop("floatable", None)
            self.dock_movable = dock_kwargs.pop("movable", None)
            self.dock_allowed_areas = dock_kwargs.pop("allowedAreas", None)
            self.dock_vertical_title_bar = dock_kwargs.pop("verticalTitleBar", None)

            # Extract name= for objectName from dock_kwargs
            self.object_name = dock_kwargs.pop("name", None)

            # Extract classes= for CSS classes from dock_kwargs
            classes = dock_kwargs.pop("classes", None)
            if classes is not None:
                self.css_classes = classes

            # layout=False doesn't apply to docks (they're not in layouts)
            # But pop it anyway to avoid passing to constructor
            dock_kwargs.pop("layout", None)

            # Store widget args/kwargs for content widget creation
            self.widget_args = widget_args
            self.widget_kwargs = widget_kwargs

            # Remaining dock_kwargs are ignored (they should all be consumed)
            return

        # Handle list[QWidget] - creates a WidgetRepeater bound to a list source
        if origin is list:
            type_args = get_args(self.field_type)
            if type_args and self._is_qwidget_class(type_args[0]):
                self.is_list_widget = True
                self.list_widget_type = type_args[0]

                # Extract bind= (required for list widgets)
                self.bind = self.kwargs.pop("bind", None)

                # Extract format= for list item formatting (string template or callable)
                self.list_format = self.kwargs.pop("format", None)

                # Extract sort= for display ordering
                self.sort = self.kwargs.pop("sort", None)

                # layout=False → exclude from layout
                layout_kwarg = self.kwargs.pop("layout", None)
                if layout_kwarg is False:
                    self.exclude_from_layout = True

                # Extract label= for form layouts
                self.label = self.kwargs.pop("label", None)

                # Extract grid= for grid layouts
                self.grid = self.kwargs.pop("grid", None)

                # Extract name= for objectName (applied to each widget in list)
                self.object_name = self.kwargs.pop("name", None)

                # Extract classes= for CSS classes (applied to each widget in list)
                classes = self.kwargs.pop("classes", None)
                if classes is not None:
                    self.css_classes = classes

                # Extract widget props (e.g., styleSheet="..." → setStyleSheet)
                # Use list_widget_type for setter detection
                self._extract_widget_props(self.list_widget_type)

                # Extract Translatable markers for binding registration
                self._extract_translatables()

                # Extract signal connections for the child widget type
                # e.g., on_delete="remove_item" where on_delete is a Signal on list_widget_type
                # list_widget_type is always set at this point (line 121)
                assert self.list_widget_type is not None
                self._extract_signal_connections_for_type(self.list_widget_type)

                # Remaining kwargs go to widget constructor
                return

            # Handle list[QAction] - creates an ActionRepeater in @menu
            if type_args and self._is_qaction_class(type_args[0]):
                # Mark as action list (not widget list, but similar handling)
                self.is_list_widget = False  # Not a widget list

                # Extract bind= (required for action lists)
                self.bind = self.kwargs.pop("bind", None)

                # Extract format= for list item formatting
                self.list_format = self.kwargs.pop("format", None)

                # Extract signal connections (e.g., triggered="on_select")
                self._extract_signal_connections_for_type(type_args[0])

                return

        # Handle set[QWidget] - creates a SetWidgetRepeater bound to a set source
        if origin is set:
            type_args = get_args(self.field_type)
            if type_args and self._is_qwidget_class(type_args[0]):
                self.is_set_widget = True
                self.set_widget_type = type_args[0]

                # Extract bind= (required for set widgets)
                self.bind = self.kwargs.pop("bind", None)

                # Extract format= for set item formatting (string template or callable)
                self.set_format = self.kwargs.pop("format", None)

                # Extract sort= for display ordering
                self.sort = self.kwargs.pop("sort", None)

                # layout=False → exclude from layout
                layout_kwarg = self.kwargs.pop("layout", None)
                if layout_kwarg is False:
                    self.exclude_from_layout = True

                # Extract label= for form layouts
                self.label = self.kwargs.pop("label", None)

                # Extract grid= for grid layouts
                self.grid = self.kwargs.pop("grid", None)

                # Extract name= for objectName (applied to each widget in set)
                self.object_name = self.kwargs.pop("name", None)

                # Extract classes= for CSS classes (applied to each widget in set)
                classes = self.kwargs.pop("classes", None)
                if classes is not None:
                    self.css_classes = classes

                # Extract widget props (e.g., styleSheet="..." → setStyleSheet)
                # Use set_widget_type for setter detection
                self._extract_widget_props(self.set_widget_type)

                # Extract Translatable markers for binding registration
                self._extract_translatables()

                # Extract signal connections for the child widget type
                # e.g., on_delete="remove_item" where on_delete is a Signal on set_widget_type
                assert self.set_widget_type is not None
                self._extract_signal_connections_for_type(self.set_widget_type)

                # Remaining kwargs go to widget constructor
                return

        # Handle QWidget-specific kwargs only
        # For non-QWidgets: leave bind= and layout= in kwargs so they pass to constructor
        if self._is_qwidget_type():
            # Extract refs FIRST (before other extractions might modify kwargs)
            self._extract_refs()

            # Extract bind= for QtPie binding system
            self.bind = self.kwargs.pop("bind", None)

            # Extract format=/filter=/selection bindings for model widgets ONLY (QComboBox, QListView, QTableView)
            # These kwargs should NOT be popped for non-model widgets as they might be constructor params
            if self.bind is not None and self._is_model_widget_type():
                # format= specifies how list items should be displayed: "{name} ({age}}"
                self.model_format = self.kwargs.pop("format", None)
                # filter= specifies expression to filter items: "{_search} in {name}"
                self.model_filter = self.kwargs.pop("filter", None)
                # sort= specifies how to sort items: "{age}", "method_name", or callable
                self.model_sort = self.kwargs.pop("sort", None)
                # Extract selection bindings for model widgets (QComboBox, QListView, QTableView)
                self.selected_index = self.kwargs.pop("selectedIndex", None)
                self.selected_item = self.kwargs.pop("selectedItem", None)
                # Extract QTableView-specific kwargs only if this is a QTableView
                if self._is_qtableview_type():
                    # QTableView-specific selection bindings (single)
                    self.selected_row = self.kwargs.pop("selectedRow", None)
                    self.selected_column = self.kwargs.pop("selectedColumn", None)
                    self.selected_cell = self.kwargs.pop("selectedCell", None)
                    # QTableView-specific selection bindings (multi)
                    self.selected_rows = self.kwargs.pop("selectedRows", None)
                    self.selected_columns = self.kwargs.pop("selectedColumns", None)
                    self.selected_cells = self.kwargs.pop("selectedCells", None)
                    self.selected_items = self.kwargs.pop("selectedItems", None)
                    # Extract columns/headers for QTableView with bind=
                    # columns= specifies which fields to show: ["name", "age"]
                    # headers= provides custom headers: {"name": "Dog Name"}
                    columns = self.kwargs.pop("columns", None)
                    if columns is not None:
                        self.table_columns = list(columns)
                    headers = self.kwargs.pop("headers", None)
                    if headers is not None:
                        self.table_headers = dict(headers)
                # Extract QListView-specific kwargs only if this is a QListView
                elif self._is_qlistview_type():
                    # QListView-specific selection bindings (multi)
                    self.selected_indexes = self.kwargs.pop("selectedIndexes", None)
                    self.selected_items_list = self.kwargs.pop("selectedItems", None)
                # Extract QTreeView-specific kwargs only if this is a QTreeView
                elif self._is_qtreeview_type():
                    # children= specifies attribute for child items
                    self.tree_children = self.kwargs.pop("children", None)
                    # QTreeView selection bindings (multi)
                    # Note: selected_item is already extracted above for all model widgets
                    self.selected_items = self.kwargs.pop("selectedItems", None)

            # Extract QTabWidget-specific kwargs
            if self._is_qtabwidget_type():
                self.is_tab_widget = True
                # tabs= can be dict, list, or Variable reference string
                raw_tabs = self.kwargs.pop("tabs", None)
                self.tabs = self._normalize_tabs(raw_tabs)
                # Selection bindings for QTabWidget
                self.tab_selected_index = self.kwargs.pop("selectedIndex", None)
                self.tab_selected_widget = self.kwargs.pop("selectedWidget", None)

            # layout=False → exclude from layout
            layout_kwarg = self.kwargs.pop("layout", None)
            if layout_kwarg is False:
                self.exclude_from_layout = True

            # Extract label= for form layouts
            self.label = self.kwargs.pop("label", None)

            # Extract grid= for grid layouts
            self.grid = self.kwargs.pop("grid", None)

            # Extract variable bindings for QtPie Widget subclasses BEFORE extracting name=
            # This ensures that if a child widget has a required Variable called "name",
            # it gets treated as a variable binding, not as objectName
            # e.g., child: Child = new(count="_my_count", name="_my_name")
            self._extract_variable_bindings()

            # Extract name= for objectName (only if it wasn't already extracted as a variable binding)
            if "name" not in self.variable_bindings:
                self.object_name = self.kwargs.pop("name", None)

            # Extract classes= for CSS classes
            classes = self.kwargs.pop("classes", None)
            if classes is not None:
                self.css_classes = classes

            # Extract signal connections (e.g., clicked="on_clicked")
            self._extract_signal_connections()

            # Extract widget props (e.g., windowTitle="Foo" → setWindowTitle("Foo"))
            self._extract_widget_props()

            # Extract Translatable markers for binding registration
            self._extract_translatables()

        # Handle QObject subclasses (not QWidget, but have signals and props)
        # This covers QAction, QMenu, etc.
        elif self._is_qobject_type():
            # Extract refs FIRST (before other extractions might modify kwargs)
            self._extract_refs()

            # Extract signal connections (e.g., triggered="on_triggered")
            self._extract_signal_connections()

            # Extract widget props (e.g., shortcut="Ctrl+N" → setShortcut)
            self._extract_widget_props()

            # Extract Translatable markers for binding registration
            self._extract_translatables()

    def _normalize_kwargs_aliases(self) -> None:
        """Normalize convenience aliases in kwargs.

        Converts:
            title -> windowTitle
            stylesheet -> styleSheet
            tooltip -> toolTip
        """
        if "title" in self.kwargs:
            self.kwargs["windowTitle"] = self.kwargs.pop("title")
        if "stylesheet" in self.kwargs:
            self.kwargs["styleSheet"] = self.kwargs.pop("stylesheet")
        if "tooltip" in self.kwargs:
            self.kwargs["toolTip"] = self.kwargs.pop("tooltip")

    def _is_qwidget_type(self) -> bool:
        """Check if the field type is a QWidget subclass."""
        return self._is_qwidget_class(self.field_type)

    def _is_qobject_type(self) -> bool:
        """Check if the field type is a QObject subclass (but not QWidget)."""
        if self.field_type is None:
            return False
        try:
            from qtpy.QtCore import QObject
            from qtpy.QtWidgets import QWidget

            # field_type could be a generic alias, so check it's a proper type
            if not isinstance(self.field_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
                return False
            # Is a QObject but NOT a QWidget (QWidget handled separately above)
            return issubclass(self.field_type, QObject) and not issubclass(self.field_type, QWidget)
        except (ImportError, TypeError):
            return False

    def _is_qwidget_class(self, cls: type | None) -> bool:
        """Check if cls is a QWidget subclass."""
        if cls is None:
            return False
        try:
            from qtpy.QtWidgets import QWidget

            # cls could be a generic alias, so check it's a proper type
            return isinstance(cls, type) and issubclass(cls, QWidget)  # pyright: ignore[reportUnnecessaryIsInstance]
        except (ImportError, TypeError):
            return False

    def _is_qaction_class(self, cls: type | None) -> bool:
        """Check if cls is QAction."""
        if cls is None:
            return False
        try:
            from qtpy.QtGui import QAction

            return cls is QAction or (isinstance(cls, type) and issubclass(cls, QAction))  # pyright: ignore[reportUnnecessaryIsInstance]
        except (ImportError, TypeError):
            return False

    def _is_qtableview_type(self) -> bool:
        """Check if the field type is a QTableView subclass."""
        if self.field_type is None:
            return False
        try:
            from qtpy.QtWidgets import QTableView

            # field_type could be a generic alias, so check it's a proper type
            if not isinstance(self.field_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
                return False
            return issubclass(self.field_type, QTableView)
        except (ImportError, TypeError):
            return False

    def _is_qlistview_type(self) -> bool:
        """Check if the field type is a QListView subclass (but not QTableView or QTreeView)."""
        if self.field_type is None:
            return False
        try:
            from qtpy.QtWidgets import QListView, QTableView, QTreeView

            # field_type could be a generic alias, so check it's a proper type
            if not isinstance(self.field_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
                return False
            # QListView but not QTableView or QTreeView
            return issubclass(self.field_type, QListView) and not issubclass(self.field_type, QTableView) and not issubclass(self.field_type, QTreeView)
        except (ImportError, TypeError):
            return False

    def _is_qtreeview_type(self) -> bool:
        """Check if the field type is a QTreeView subclass."""
        if self.field_type is None:
            return False
        try:
            from qtpy.QtWidgets import QTreeView

            # field_type could be a generic alias, so check it's a proper type
            if not isinstance(self.field_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
                return False
            return issubclass(self.field_type, QTreeView)
        except (ImportError, TypeError):
            return False

    def _is_qcombobox_type(self) -> bool:
        """Check if the field type is a QComboBox subclass."""
        if self.field_type is None:
            return False
        try:
            from qtpy.QtWidgets import QComboBox

            # field_type could be a generic alias, so check it's a proper type
            if not isinstance(self.field_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
                return False
            return issubclass(self.field_type, QComboBox)
        except (ImportError, TypeError):
            return False

    def _is_model_widget_type(self) -> bool:
        """Check if the field type is a model widget (QComboBox, QListView, QTableView, QTreeView)."""
        return self._is_qcombobox_type() or self._is_qlistview_type() or self._is_qtableview_type() or self._is_qtreeview_type()

    def _is_qtabwidget_type(self) -> bool:
        """Check if the field type is a QTabWidget subclass."""
        if self.field_type is None:
            return False
        try:
            from qtpy.QtWidgets import QTabWidget

            # field_type could be a generic alias, so check it's a proper type
            if not isinstance(self.field_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
                return False
            return issubclass(self.field_type, QTabWidget)
        except (ImportError, TypeError):
            return False

    def _normalize_tabs(self, tabs: dict[str, Any] | list[Any] | str | None) -> list[dict[str, Any]] | str | None:
        """Normalize tabs= to a consistent format.

        Supports:
        - tabs=[WidgetClass, ...] - list of widget classes (create new)
        - tabs=[field_ref, ...] - list of NewField references (use existing)
        - tabs=["field_name", ...] - list of string field names (use existing)
        - tabs={"Tab Name": WidgetClass, ...} - dict with classes (create new)
        - tabs={"Tab Name": field_ref, ...} - dict with NewField refs (use existing)
        - tabs={"Tab Name": "field_name", ...} - dict with string refs (use existing)
        - tabs="_var_name" - Variable reference for reactive tabs

        Returns normalized list of dicts:
        - {"type": "class", "cls": WidgetClass, "name": "TabName" | None}
        - {"type": "ref", "field": "field_name", "name": "TabName" | None}
        Or str for Variable references.
        """
        if tabs is None:
            return None

        # String = Variable reference, keep as-is for reactive binding
        if isinstance(tabs, str):
            return tabs

        if isinstance(tabs, dict):
            result: list[dict[str, Any]] = []
            for name, value in tabs.items():
                if isinstance(value, NewField):
                    # NewField reference - use its field name
                    result.append({"type": "ref", "field": value.name, "name": name})
                elif isinstance(value, str):
                    # String reference to a field
                    result.append({"type": "ref", "field": value, "name": name})
                elif isinstance(value, type):
                    # Widget class - create new instance
                    result.append({"type": "class", "cls": value, "name": name})
            return result

        # At this point, tabs must be a list (all other cases returned above)
        result = []
        for item in tabs:
            if isinstance(item, NewField):
                # NewField reference - use its field name
                result.append({"type": "ref", "field": item.name, "name": None})
            elif isinstance(item, str):
                # String reference to a field
                result.append({"type": "ref", "field": item, "name": None})
            elif isinstance(item, type):
                # Widget class - create new instance
                result.append({"type": "class", "cls": item, "name": None})
        return result if result else None

    def _is_dock_type(self) -> bool:
        """Check if the field type is a Dock[T] generic alias."""
        if self.field_type is None:
            return False
        return self._is_dock_type_param(self.field_type)

    def _is_dock_type_param(self, type_to_check: Any) -> bool:
        """Check if a given type is a Dock[T] generic alias."""
        if type_to_check is None:
            return False
        try:
            from .dock import Dock

            # Check if the origin is Dock (e.g., Dock[ExplorerPanel])
            origin = get_origin(type_to_check)
            return origin is Dock
        except (ImportError, TypeError):
            return False

    def _is_signal(self, name: str) -> bool:
        """Check if name is a signal on the field type."""
        if self.field_type is None:
            return False
        return is_signal_on_type(name, self.field_type)

    def _extract_signal_connections(self) -> None:
        """Extract signal=handler kwargs for QWidgets.

        Supports both callables and string method names:
            clicked=lambda: print("clicked")
            clicked="on_clicked"
        """
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            # Check if this kwarg name matches a signal on the widget type
            if self._is_signal(key):
                # Value must be a string (method name) or callable
                if isinstance(value, str) or callable(value):
                    self.signal_connections[key] = value
                    to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _extract_signal_connections_for_type(self, target_type: type) -> None:
        """Extract signal=handler kwargs for a specific type (e.g., QAction for list[QAction]).

        Args:
            target_type: The type to check for signals (e.g., QAction)
        """
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            # Check if this kwarg name matches a signal on the target type
            if self._is_signal_on_type(key, target_type):
                # Value must be a string (method name) or callable
                if isinstance(value, str) or callable(value):
                    self.signal_connections[key] = value
                    to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _is_signal_on_type(self, name: str, target_type: type) -> bool:
        """Check if name is a signal on the given type."""
        return is_signal_on_type(name, target_type)

    def _has_setter(self, prop_name: str, widget_type: type | None = None) -> bool:
        """Check if the widget type has a setXxx method for the given property name."""
        check_type = widget_type or self.field_type
        if check_type is None:
            return False
        try:
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            attr = getattr(check_type, setter_name, None)
            return attr is not None and callable(attr)
        except Exception:
            return False

    def _is_binding_expression(self, value: Any) -> bool:
        """Check if value is a binding expression (string reference or {expr})."""
        if not isinstance(value, str):
            return False
        # If it contains {}, it's definitely a binding expression
        if "{" in value and "}" in value:
            return True
        # If it's a simple identifier (possibly with underscore prefix), treat as variable reference
        # But NOT if it looks like a regular value (e.g., "true", "false", urls, paths, etc.)
        stripped = value.strip()
        if not stripped:
            return False
        # Check if it's a valid Python identifier (variable/method name)
        # This catches things like "_is_visible", "should_show", but not "hello world"
        return stripped.replace("_", "").replace(".", "").isalnum() and stripped[0].isalpha() or stripped[0] == "_"

    def _extract_widget_props(self, widget_type: type | None = None) -> None:
        """Extract property kwargs for QWidgets.

        For kwargs like windowTitle="Foo", if the widget class has a
        setWindowTitle method, extract it to widget_props for later application.

        If the value is a string that looks like a binding expression (e.g., "_is_visible"
        or "{_count > 0}"), it's stored in property_bindings instead.

        Args:
            widget_type: The widget type to check for setters. If None, uses self.field_type.
        """
        # Properties that support binding (common QWidget/QAction properties)
        bindable_props = {"visible", "enabled", "windowModified", "acceptDrops", "updatesEnabled", "checked"}

        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            # Check if this kwarg corresponds to a setter on the widget type
            if self._has_setter(key, widget_type):
                # Check if this is a bindable property with a binding expression
                if key in bindable_props and self._is_binding_expression(value):
                    self.property_bindings[key] = value
                else:
                    self.widget_props[key] = value
                to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _extract_translatables(self) -> None:
        """Extract Translatable markers from args and widget_props for binding registration.

        Translatables are kept in place (not resolved here) - they're resolved
        during widget instantiation in new_fields.py.
        """
        from qtpie.translations.translatable import Translatable

        # Check positional args for Translatable markers
        for i, arg in enumerate(self.args):
            if isinstance(arg, Translatable):
                self.translatable_args.append((i, arg))

        # Check widget_props for Translatable markers
        for key, value in self.widget_props.items():
            if isinstance(value, Translatable):
                self.translatable_kwargs[key] = value

        # Also check remaining kwargs (for widgets that take text in constructor)
        for key, value in self.kwargs.items():
            if isinstance(value, Translatable):
                self.translatable_kwargs[key] = value

    def _extract_variable_bindings(self) -> None:
        """Extract variable bindings for QtPie Widget subclasses.

        When the field type is a QtPie Widget with required/optional Variable bindings,
        extract matching kwargs as variable_bindings instead of passing to constructor.

        Example:
            child: Child = new(count="_my_count")  # count is extracted as a binding
        """
        if self.field_type is None:
            return

        # Check if the field type is a QtPie Widget subclass
        if not self._is_qtpie_widget():
            return

        # Get the child's required bindings and all Variable annotations
        config = getattr(self.field_type, "_qtpie_config", None)
        if config is None:
            return

        # Collect all Variable names from the child (required and optional)
        variable_names: set[str] = set(config.required_bindings)

        # Also check annotations for Variable types (including optional ones with defaults)
        child_annotations = getattr(self.field_type, "__annotations__", {})
        for name, annotation in child_annotations.items():
            origin = get_origin(annotation)
            if origin is Variable or annotation is Variable:
                variable_names.add(name)

        # Extract kwargs that match Variable names
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            if key in variable_names:
                self.variable_bindings[key] = value
                to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _is_qtpie_widget(self) -> bool:
        """Check if the field type is a QtPie Widget subclass (has _qtpie_config)."""
        if self.field_type is None:
            return False
        return hasattr(self.field_type, "_qtpie_config")

    def _get_variable_default(self) -> Any:
        """Extract default value for a Variable field."""
        # Check for explicit default= kwarg
        if "default" in self.kwargs:
            return self.kwargs["default"]
        # Check for single arg (primitive, list, dict, or object)
        if len(self.args) == 1:
            return self.args[0]
        return None

    def _extract_refs(self) -> None:
        """Extract Ref markers from kwargs for deferred resolution.

        Ref instances are removed from kwargs and stored in ref_bindings.
        They will be resolved after field instantiation when sibling fields exist.
        """
        from .ref import Ref

        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            if isinstance(value, Ref):
                self.ref_bindings[key] = value
                to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]
