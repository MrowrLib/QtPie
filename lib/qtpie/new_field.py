"""NewField - Stores field configuration for deferred instantiation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, cast, get_args, get_origin, get_type_hints

from .event import is_event_hint
from .layout import GridPosition, Stretch
from .setting import Setting
from .utils.common import is_signal_on_type
from .utils.type_checks import (
    is_dock_generic,
    is_model_widget,
    is_qaction,
    is_qcombobox,
    is_qlayout,
    is_qlistview,
    is_qobject,
    is_qspaceritem,
    is_qsplitter,
    is_qtableview,
    is_qtabwidget,
    is_qtext_editor,
    is_qtreeview,
    is_qwidget,
)
from .variable import NO_DEFAULT, Variable, create_variable_descriptor

# Column resize modes for QTableView (maps to QHeaderView.ResizeMode)
# - "interactive": User can resize columns (Qt default)
# - "fixed": Columns cannot be resized
# - "stretch": Columns distribute space equally (QtPie default)
# - "resize_to_contents": Columns fit content, no user resize
ColumnResizeMode = Literal["interactive", "fixed", "stretch", "resize_to_contents"]


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
        # Event handlers (not Qt signals, but handled via event filter)
        # Keys are event names like "onFocus", "onMouseEnter", etc.
        self.event_handlers: dict[str, str | Callable[..., Any]] = {}
        # Event[T] connection - for new(on="handler") on Event annotations
        self.event_on: str | Callable[..., Any] | None = None
        # Variable callbacks (onChange, onInsert, onRemove, etc.)
        self.on_change: str | Callable[..., Any] | None = None
        # List-specific callbacks
        self.on_insert: str | Callable[..., Any] | None = None
        self.on_remove: str | Callable[..., Any] | None = None
        self.on_replace: str | Callable[..., Any] | None = None
        self.on_clear: str | Callable[..., Any] | None = None
        # Set-specific callbacks
        self.on_add: str | Callable[..., Any] | None = None
        # Dict-specific callbacks (onRemove shared with list/set)
        self.on_set: str | Callable[..., Any] | None = None
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
        # list[Dock[W]] support
        self.is_list_dock: bool = False
        self.list_dock_content_type: type | None = None  # The widget type inside list[Dock[W]]
        # Static list/dict support (plain data types for QComboBox binding)
        self.is_static_list: bool = False  # list[str] = new(["a", "b", "c"])
        self.is_static_dict: bool = False  # dict[str, str] = new({"key": "Display"})
        # set[QWidget] support
        self.is_set_widget: bool = False
        self.set_widget_type: type | None = None  # The QWidget type inside set[QWidget]
        self.set_format: str | Callable[[Any], str] | None = None  # Format for set items
        # Sort parameter for list/dict/set repeaters
        self.sort: bool | str | Callable[[Any], Any] | None = None
        # Object name and CSS classes
        self.object_name: str | None = None  # objectName for the widget
        self.css_classes: list[str] = []  # CSS classes for the widget
        # Initial size (width/height) - applied via resize() after widget creation
        # int = absolute pixels, float (0.0-1.0) = percentage of window size
        self.initial_width: int | float | None = None  # width= for initial width
        self.initial_height: int | float | None = None  # height= for initial height
        # Property bindings (visible="_is_visible", enabled="{_count > 0}")
        self.property_bindings: dict[str, str] = {}  # prop_name -> binding expression
        # Model format for QComboBox/QListView/etc. with bind= to list
        # Can be string template "{name}" or callable (lambda, dict.get, etc.)
        self.model_format: str | Callable[[Any], str] | None = None  # Format for model items
        # Table columns for QTableView with bind= to list
        self.table_columns: list[str] | None = None  # Column names: ["name", "age"]
        self.table_prepend_columns: list[str] | None = None  # Columns to prepend to auto-detected
        self.table_append_columns: list[str] | None = None  # Columns to append to auto-detected
        self.table_headers: dict[str | int, str] | None = None  # Custom headers: {"name": "Dog Name"}
        # Custom headers for auto-detected dict binding (simpler than headers= for common case)
        self.key_header: str | None = None  # Custom header for #key or column 0 (default: "Key")
        self.value_header: str | None = None  # Custom header for column 1 (default: "Value")
        # Checkable columns for QTableView (bool fields auto-detected by default)
        self.table_checkable: list[str] | bool | None = None  # Checkable columns or False to disable
        self.table_checkable_text: str | dict[str, str] | None = None  # Text format for checkable columns
        # Editable columns for QTableView (default is editable, like other Qt widgets)
        self.table_editable: list[str | int] | bool | None = None  # Editable columns: True=all, list=specific, False=none
        self.table_readonly: bool | None = None  # readOnly=True sets editable=False (alias for consistency with other widgets)
        # Column resize mode for QTableView (header configuration)
        self.table_column_resize_mode: ColumnResizeMode | None = None  # columnResizeMode= (default: "stretch")
        self.table_stretch_last_column: bool | None = None  # stretchLastColumn= shortcut
        # Selection bindings for model widgets (QComboBox, QListView, etc.)
        self.selected_index: str | None = None  # Variable name for selectedIndex binding
        self.selected_item: str | None = None  # Variable name for selectedItem binding
        self.selected_text: str | None = None  # Variable name for selectedText binding (match by display text)
        self.selected_widget: str | None = None  # Variable name for selectedWidget binding (embedded widget)
        self.selected_dock: str | None = None  # Variable name for selectedDock binding (Dock wrapper)
        # Selection change callbacks (method names)
        self.selected_index_changed: str | None = None  # Callback for selectedIndexChanged
        self.selected_item_changed: str | None = None  # Callback for selectedItemChanged
        self.selected_dock_changed: str | None = None  # Callback for selectedDockChanged
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
        # QTreeView-specific: children attribute name and expand behavior
        self.tree_children: str | None = None  # Attribute name for child items: "children"
        self.tree_expand: bool = False  # If True, expandAll() on init and when root changes
        self.tree_header_hidden: bool = True  # If True, hide the header row (default: True)
        # QTreeView checkable: checkbox support for tree nodes
        # - None/False: no checkboxes (default)
        # - str without braces: two-way binding to bool field name
        # - str with braces "{expr}": one-way expression (read-only checkbox)
        self.tree_checkable: str | bool | None = None
        # QTreeView editable: inline editing support for tree nodes
        # - None/False: no editing (default)
        # - str: field name to edit (supports nested paths like "info.title")
        # - True: edit the item itself (for simple types like str)
        self.tree_editable: str | bool | None = None
        # QListView checkable: checkbox support for list items (same semantics as tree)
        self.list_checkable: str | bool | None = None
        # QListView editable: inline editing support for list items (same semantics as tree)
        self.list_editable: str | bool | None = None
        # Edit triggers for QTreeView/QListView (defaults: doubleClick=True, select=False, editKey=True)
        self.edit_on_double_click: bool | None = None
        self.edit_on_select: bool | None = None
        self.edit_on_edit_key: bool | None = None
        # Validator for tree/list inline editing (same format as QLineEdit validator=)
        self.tree_validator: str | Callable[..., Any] | None = None
        self.list_validator: str | Callable[..., Any] | None = None
        # onEdited callback for tree/list inline editing - called after edit is committed
        # Callback signature: (item, old_value, new_value) -> None
        self.tree_on_edited: str | Callable[..., Any] | None = None
        self.list_on_edited: str | Callable[..., Any] | None = None
        # Filter for model widgets: "{_search} in {name}", "method_name", or callable
        self.model_filter: str | Callable[[Any], bool] | None = None
        # Filter dependencies: Variable names to watch for callable/method filters
        # When these Variables change, the filter is re-evaluated
        self.filter_depends: list[str] | None = None
        # Sort key for model widgets: "{age}", "method_name", or callable
        self.model_sort: str | Callable[[Any], Any] | None = None
        # Embedded widget for model views (QListView, QTreeView, QTableView)
        # widget= specifies a Widget class to embed in each item (QListView/QTreeView)
        # For QTableView, widget classes can appear in columns= list
        self.embed_widget: type | None = None  # Widget class for QListView/QTreeView
        self.embed_config: Any | None = None  # EmbedConfig if embed() was used
        # For QTableView: list of (column_index, widget_class, embed_config) for widget columns
        self.table_widget_columns: list[tuple[int, type, Any | None]] | None = None
        # For prependColumns/appendColumns: widget columns extracted from those lists
        self.table_prepend_widget_columns: list[tuple[int, type, Any | None]] | None = None
        self.table_append_widget_columns: list[tuple[int, type, Any | None]] | None = None
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
        # Layout item support (Stretch, QSpacerItem, QLayout)
        self.is_stretch: bool = False  # True if field type is Stretch
        self.stretch_factor: int = 1  # Factor for addStretch()
        self.is_spacer_item: bool = False  # True if field type is QSpacerItem
        self.is_nested_layout: bool = False  # True if field type is QLayout subclass
        self.target_layout: str | None = None  # Layout to add this item to (field name reference)
        # QSplitter support
        self.is_splitter: bool = False  # True if field type is QSplitter
        self.target_splitter: str | None = None  # Splitter to add this widget to (field name reference)
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
        self.dock_group_selected_dock: str | None = None  # groupSelectedDock="_selected_dock"
        # Static dock group selection change callbacks
        self.dock_group_selected_index_changed: str | None = None  # groupSelectedIndexChanged="on_index_changed"
        self.dock_group_selected_dock_changed: str | None = None  # groupSelectedDockChanged="on_dock_changed"
        self.dock_icon: str | None = None  # icon="terminal.svg" (tab icon)
        self.dock_visible: str | None = None  # visible="_show_dock" or "{expr}"
        self.dock_floating: str | None = None  # floating="_is_floating"
        self.dock_closable: bool | None = None  # closable=False (no X button)
        self.dock_floatable: bool | None = None  # floatable=False (can't pop out)
        self.dock_movable: bool | None = None  # movable=False (can't drag)
        self.dock_allowed_areas: list[str] | None = None  # allowedAreas=["left", "right"]
        self.dock_vertical_title_bar: bool | None = None  # verticalTitleBar=True
        self.dock_hide_title_bar: bool | None = None  # hideTitleBar=True (always hide title bar)
        self.dock_hide_title_bar_when_tabbed: bool | None = None  # hideTitleBarWhenTabbed=True/False
        self.dock_context_menu: type | None = None  # contextMenu=MyMenu (custom context menu class)
        # Variable[T, Dock[W]] support - Variable with a docked widget
        self.is_variable_dock: bool = False
        self.variable_dock_content_type: type | None = None  # The widget type W inside Variable[T, Dock[W]]
        # Variable[list[T], Dock[W]] support - Variable with list of docked widgets
        self.is_variable_list_dock: bool = False
        self.variable_list_dock_item_type: type | None = None  # The item type T inside Variable[list[T], Dock[W]]
        self.variable_list_dock_widget_type: type | None = None  # The widget type W inside Variable[list[T], Dock[W]]
        # QLineEdit input validator support
        # validator= can be:
        # - str (regex): QRegularExpressionValidator with the pattern
        # - Callable[[str], bool]: Simple predicate (True=accept, False=reject)
        # - Callable[[str, int], QValidator.State]: Full control over validation state
        # - str (method name): Look up method on widget instance
        self.validator: str | Callable[..., Any] | None = None
        # QPlainTextEdit/QTextEdit syntax highlighter support
        # highlighter= can be:
        # - type: Static highlighter class to instantiate
        # - str: Variable name binding (e.g., "highlighter" or "_highlighter")
        # - NewField: Direct Variable reference
        self.highlighter: type | str | None = None
        # content_type= binds to a Variable[str | None] for MIME type-based highlighter selection
        # - str: Variable name binding (e.g., "content_type" or "_content_type")
        # - NewField: Direct Variable reference
        self.editor_content_type: str | None = None
        # Chaining support: track all chained () calls for multi-level patterns
        # e.g., new(var_default)(dock_kwargs)(widget_kwargs)
        self._chain_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        # Owner class config (set in __set_name__) for auto-record-bind detection
        self._owner_class_config: Any | None = None

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

        # Store owner's config for auto-record-bind detection
        self._owner_class_config = getattr(owner, "_qtpie_config", None)

        # Normalize aliases (title -> windowTitle, stylesheet -> styleSheet)
        self._normalize_kwargs_aliases()

        # Get the type annotation
        hints = get_type_hints(owner)
        self.field_type = hints.get(name)

        # If it's an Event[T], extract the on= handler and store it
        # Keep the NewField on the class so __init_subclass__ can find it
        # The event annotation processing code will:
        # 1. Check if there's a NewField for this Event
        # 2. Extract the on= handler and store it in config
        # 3. Delete the NewField and create the Event/Signal
        if is_event_hint(self.field_type):
            self.event_on = self.kwargs.pop("on", None)
            # NewField stays on class - will be processed by _process_event_annotations_for_*
            return  # Don't process further - the Event annotation will be handled separately

        # If it's a Variable or Setting, replace self with a Variable descriptor
        origin = get_origin(self.field_type)
        is_variable = origin is Variable or self.field_type is Variable
        is_setting = origin is Setting or self.field_type is Setting
        if is_variable or is_setting:
            default = self._get_variable_default()
            # Extract inner type from Variable[T]/Setting[T] and optional widget type from Variable[T, W]/Setting[T, W]
            inner_type: type | None = None
            widget_type: type | None = None
            if origin is Variable or origin is Setting:
                args = get_args(self.field_type)
                inner_type = args[0] if args else None
                widget_type = args[1] if len(args) > 1 else None

            # For Setting[T], compute the persist_key
            persist_key: str | None = None
            if is_setting:
                # Extract group= kwarg if provided, otherwise use owner class name
                group = self.kwargs.pop("group", None)
                if group is not None:
                    persist_key = f"{group}:{name}"
                else:
                    persist_key = f"{owner.__name__}:{name}"

            # Check if widget_type is Dock[X] - Variable[T, Dock[W]] or Variable[list[T], Dock[W]]
            # If so, extract the inner content type X and mark as variable dock
            dock_info: dict[str, Any] | None = None
            if widget_type is not None and self._is_dock_type_param(widget_type):
                # Extract the content widget type from Dock[W]
                dock_args = get_args(widget_type)
                if dock_args:
                    # Check if inner_type is list[T] - Variable[list[T], Dock[W]]
                    inner_origin = get_origin(inner_type)
                    if inner_origin is list:
                        # This is Variable[list[T], Dock[W]] - a list dock repeater
                        self.is_variable_list_dock = True
                        inner_args = get_args(inner_type)
                        self.variable_list_dock_item_type = inner_args[0] if inner_args else None
                        self.variable_list_dock_widget_type = dock_args[0]

                        # Extract dock kwargs directly from self.kwargs
                        # Pattern: new(group="requests", dock="right", title="{name}", visible="...")
                        # Chained call )(widget_kwargs) provides widget constructor kwargs
                        # Use full=True to also extract visible=, floating=, etc.
                        self._extract_dock_kwargs(self.kwargs, full=True)

                        # Extract widget_args/kwargs from chained call if present
                        widget_args: tuple[Any, ...] = ()
                        widget_kwargs: dict[str, Any] = {}
                        if self._chain_calls:
                            widget_args, widget_kwargs = self._chain_calls[0]

                        # Also check for width=/height= in dock kwargs (self.kwargs)
                        # This allows: new(dock="right", width=400) without chaining
                        dock_width = self.kwargs.pop("width", None)
                        dock_height = self.kwargs.pop("height", None)
                        if dock_width is not None and "width" not in widget_kwargs:
                            widget_kwargs["width"] = dock_width
                        if dock_height is not None and "height" not in widget_kwargs:
                            widget_kwargs["height"] = dock_height

                        # Extract selection bindings
                        self.selected_index = self.kwargs.pop("selectedIndex", None)
                        self.selected_item = self.kwargs.pop("selectedItem", None)
                        self.selected_dock = self.kwargs.pop("selectedDock", None)
                        # Extract selection change callbacks
                        self.selected_index_changed = self.kwargs.pop("selectedIndexChanged", None)
                        self.selected_item_changed = self.kwargs.pop("selectedItemChanged", None)
                        self.selected_dock_changed = self.kwargs.pop("selectedDockChanged", None)

                        # Store dock info for window.py to use
                        dock_info = {
                            "dock_area": self.dock_area,
                            "dock_title": self.dock_title,
                            "dock_group": self.dock_group,
                            "dock_group_selected_index": self.dock_group_selected_index,
                            "dock_closable": self.dock_closable,
                            "dock_floatable": self.dock_floatable,
                            "dock_movable": self.dock_movable,
                            "dock_visible": self.dock_visible,
                            "dock_context_menu": self.dock_context_menu,
                            "is_list_dock": True,
                            "list_dock_item_type": self.variable_list_dock_item_type,
                            "list_dock_widget_type": self.variable_list_dock_widget_type,
                            "selected_index": self.selected_index,
                            "selected_item": self.selected_item,
                            "selected_dock": self.selected_dock,
                            "selected_index_changed": self.selected_index_changed,
                            "selected_item_changed": self.selected_item_changed,
                            "selected_dock_changed": self.selected_dock_changed,
                            "widget_args": widget_args,
                            "widget_kwargs": widget_kwargs,
                        }
                        # Don't create a widget - this is a repeater, widget_type stays None
                        widget_type = None
                    else:
                        # This is Variable[T, Dock[W]] - a single dock
                        self.is_variable_dock = True
                        self.variable_dock_content_type = dock_args[0]

                        # Use triple-chaining pattern: new(var_default)(dock_kwargs)(widget_kwargs)
                        dock_kwargs, widget_args, widget_kwargs = self._interpret_chain_for_variable_dock()

                        # Extract dock-specific kwargs from dock_kwargs
                        self._extract_dock_kwargs(dock_kwargs, full=True)

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
                            "dock_hide_title_bar": self.dock_hide_title_bar,
                            "dock_hide_title_bar_when_tabbed": self.dock_hide_title_bar_when_tabbed,
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
            # layout= can be False (exclude), string (target layout name), or NewField reference
            target_layout: str | None = None
            if layout_kwarg is not False and layout_kwarg is not None:
                if isinstance(layout_kwarg, NewField):
                    target_layout = layout_kwarg.name
                elif isinstance(layout_kwarg, str):
                    target_layout = layout_kwarg

            # Extract name= and classes= for widget configuration (not constructor params)
            object_name: str | None = widget_kwargs_copy.pop("name", None)
            css_classes: list[str] = widget_kwargs_copy.pop("classes", None) or []

            # Extract width= and height= for initial size (handled in variable.py)
            widget_kwargs_copy.pop("width", None)
            widget_kwargs_copy.pop("height", None)

            # Extract validate= for auto-registering validators (only in kwargs, not widget_kwargs)
            validators = self.kwargs.pop("validate", None)

            # Extract Variable callbacks - onChange applies to all types
            on_change = self.kwargs.pop("onChange", None)
            self.on_change = on_change

            # Extract type-specific callbacks based on inner_type
            on_insert: str | Callable[..., Any] | None = None
            on_remove: str | Callable[..., Any] | None = None
            on_replace: str | Callable[..., Any] | None = None
            on_clear: str | Callable[..., Any] | None = None
            on_add: str | Callable[..., Any] | None = None
            on_set: str | Callable[..., Any] | None = None

            inner_origin = get_origin(inner_type)
            if inner_origin is list:
                # List callbacks: onInsert, onRemove, onReplace, onClear
                on_insert = self.kwargs.pop("onInsert", None)
                on_remove = self.kwargs.pop("onRemove", None)
                on_replace = self.kwargs.pop("onReplace", None)
                on_clear = self.kwargs.pop("onClear", None)
            elif inner_origin is set:
                # Set callbacks: onAdd, onRemove
                on_add = self.kwargs.pop("onAdd", None)
                on_remove = self.kwargs.pop("onRemove", None)
            elif inner_origin is dict:
                # Dict callbacks: onSet, onRemove
                on_set = self.kwargs.pop("onSet", None)
                on_remove = self.kwargs.pop("onRemove", None)

            self.on_insert = on_insert
            self.on_remove = on_remove
            self.on_replace = on_replace
            self.on_clear = on_clear
            self.on_add = on_add
            self.on_set = on_set

            # Remaining self.kwargs are constructor kwargs for the inner type T
            # (only used when no widget_type, i.e., Variable[T] not Variable[T, W])
            # Convert any NewField references to string names for deferred resolution
            inner_kwargs: dict[str, Any] = {}
            if widget_type is None and self.kwargs:
                for k, v in self.kwargs.items():
                    if isinstance(v, NewField):
                        inner_kwargs[k] = v.name  # Will be resolved at instantiation time
                    else:
                        inner_kwargs[k] = v

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
                target_layout,
                inner_kwargs if inner_kwargs else None,
                persist_key,
                on_change,
                on_insert,
                on_remove,
                on_replace,
                on_clear,
                on_add,
                on_set,
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

            # Extract dock-specific kwargs from dock_kwargs
            self._extract_dock_kwargs(dock_kwargs, full=True)

            # Extract name= for objectName from dock_kwargs
            self.object_name = dock_kwargs.pop("name", None)

            # Extract classes= for CSS classes from dock_kwargs
            classes = dock_kwargs.pop("classes", None)
            if classes is not None:
                self.css_classes = classes

            # layout=False doesn't apply to docks (they're not in layouts)
            # But pop it anyway to avoid passing to constructor
            dock_kwargs.pop("layout", None)

            # Extract width= and height= for initial size (applied via resize())
            # Can be in dock_kwargs (new(width=...)) or widget_kwargs (new()(width=...))
            self.initial_width = dock_kwargs.pop("width", None) or widget_kwargs.pop("width", None)
            self.initial_height = dock_kwargs.pop("height", None) or widget_kwargs.pop("height", None)

            # Store widget args/kwargs for content widget creation
            self.widget_args = widget_args
            self.widget_kwargs = widget_kwargs

            # Remaining dock_kwargs are ignored (they should all be consumed)
            return

        # Handle Stretch - adds stretch space to layout
        if self.field_type is Stretch:
            self.is_stretch = True
            # Extract stretch factor from first arg (default 1)
            if self.args:
                self.stretch_factor = int(self.args[0])
            # Extract target layout reference (layout=nested_layout or layout="nested_layout")
            self._extract_target_layout()
            return

        # Handle QSpacerItem - adds spacer item to layout
        if self._is_qspaceritem_type():
            self.is_spacer_item = True
            # Extract target layout reference
            self._extract_target_layout()
            # Args/kwargs are passed directly to QSpacerItem constructor
            return

        # Handle QLayout subclasses - nested layouts
        if self._is_qlayout_type():
            self.is_nested_layout = True
            # Extract target layout reference (for nesting layouts in layouts)
            self._extract_target_layout()
            # Args/kwargs are passed directly to layout constructor
            return

        # Handle QSplitter - widget container with resizable dividers
        if self._is_qsplitter_type():
            self.is_splitter = True
            # Extract target layout reference (splitter can be in a layout)
            self._extract_target_layout()
            # Extract bind= for property binding (e.g., bind="orientation")
            self.bind = self.kwargs.pop("bind", None)
            # Remaining kwargs are passed directly to QSplitter constructor
            return

        # Handle list[Dock[W]] - creates a DockWidgetRepeater bound to a list source
        if origin is list:
            type_args = get_args(self.field_type)
            if type_args and self._is_dock_type_param(type_args[0]):
                self.is_list_dock = True
                # Extract the widget type from Dock[W]
                dock_args = get_args(type_args[0])
                if dock_args:
                    self.list_dock_content_type = dock_args[0]

                # Extract bind= (required for list docks)
                self.bind = self.kwargs.pop("bind", None)

                # Extract format= for dock title formatting
                self.list_format = self.kwargs.pop("format", None)

                # Extract dock-specific kwargs
                self._extract_dock_kwargs(self.kwargs)

                # Extract selection bindings for list[Dock[W]]
                self.selected_index = self.kwargs.pop("selectedIndex", None)
                self.selected_item = self.kwargs.pop("selectedItem", None)

                # layout=False → exclude from layout (not really applicable for docks)
                self.kwargs.pop("layout", None)

                # Remaining kwargs go to widget constructor
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

            # Handle plain list[T] where T is not QWidget/QAction/Dock
            # e.g., list[str] = new(["a", "b", "c"]) for QComboBox static options
            # Store the actual list data directly on the class
            if type_args:
                inner_type = type_args[0]
                if not self._is_qwidget_class(inner_type) and not self._is_qaction_class(inner_type) and not self._is_dock_type_param(inner_type):
                    # This is a plain data list - store the data directly
                    self.is_static_list = True
                    setattr(owner, name, self.args[0] if self.args else [])
                    return

        # Handle plain dict[K, V] for static key-value mappings
        # e.g., dict[str, str] = new({"key": "Display"}) for QComboBox options
        if origin is dict:
            # Store the actual dict data directly on the class
            self.is_static_dict = True
            setattr(owner, name, self.args[0] if self.args else {})
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
                # filter_depends= specifies Variables to watch for callable/method filters
                self.filter_depends = self.kwargs.pop("filter_depends", None)
                # sort= specifies how to sort items: "{age}", "method_name", or callable
                self.model_sort = self.kwargs.pop("sort", None)
                # Extract selection bindings for model widgets (QComboBox, QListView, QTableView)
                self.selected_index = self.kwargs.pop("selectedIndex", None)
                self.selected_item = self.kwargs.pop("selectedItem", None)
                self.selected_text = self.kwargs.pop("selectedText", None)
                self.selected_widget = self.kwargs.pop("selectedWidget", None)
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
                    # Can also include Widget classes or embed() configs for widget columns
                    # Can also be a dict for combined columns+headers: {"name": "Dog Name"}
                    # headers= provides custom headers: {"name": "Dog Name"}
                    columns = self.kwargs.pop("columns", None)
                    if columns is not None:
                        if isinstance(columns, dict):
                            # Dict-style: keys are columns, values are headers
                            columns_dict = cast(dict[str | int, str], columns)
                            self._extract_table_columns(list(columns_dict.keys()))
                            self.table_headers = dict(columns_dict)
                        else:
                            self._extract_table_columns(columns)
                    headers = self.kwargs.pop("headers", None)
                    if headers is not None:
                        # headers= can override or supplement columns= dict headers
                        if self.table_headers is None:
                            self.table_headers = {}
                        self.table_headers.update(dict(headers))
                    # prependColumns=/appendColumns= for adding columns to auto-detected ones
                    # These are merged with auto-detected columns in model_binding.py
                    prepend_columns = self.kwargs.pop("prependColumns", None)
                    if prepend_columns is not None:
                        self._extract_prepend_columns(prepend_columns)
                    append_columns = self.kwargs.pop("appendColumns", None)
                    if append_columns is not None:
                        self._extract_append_columns(append_columns)
                    # keyHeader=/valueHeader= for simple dict binding header customization
                    self.key_header = self.kwargs.pop("keyHeader", None)
                    self.value_header = self.kwargs.pop("valueHeader", None)
                    # checkable= specifies which columns have checkboxes
                    # - None (default): auto-detect bool fields
                    # - list[str]: only these columns are checkable
                    # - False: no checkable columns
                    self.table_checkable = self.kwargs.pop("checkable", None)
                    # checkableText= specifies text to show next to checkboxes
                    # - None (default): checkbox only, no text
                    # - str: format expression for all checkable columns
                    # - dict[str, str]: per-column format expressions
                    self.table_checkable_text = self.kwargs.pop("checkableText", None)
                    # editable= specifies which columns can be edited
                    # - None (default): all columns editable (like other Qt widgets)
                    # - True: all columns editable (explicit)
                    # - False: no columns editable (read-only)
                    # - list[str|int]: only these columns are editable
                    self.table_editable = self.kwargs.pop("editable", None)
                    # readOnly= is an alias for editable=False (matches QLineEdit, QTextEdit, etc.)
                    self.table_readonly = self.kwargs.pop("readOnly", None)
                    # columnResizeMode= specifies how columns are resized
                    # - "stretch" (QtPie default): columns distribute space equally
                    # - "interactive" (Qt default): user can resize columns
                    # - "fixed": columns cannot be resized
                    # - "resize_to_contents": columns fit content
                    self.table_column_resize_mode = self.kwargs.pop("columnResizeMode", None)
                    # stretchLastColumn= shortcut for horizontalHeader().setStretchLastSection()
                    self.table_stretch_last_column = self.kwargs.pop("stretchLastColumn", None)
                # Extract QListView-specific kwargs only if this is a QListView
                elif self._is_qlistview_type():
                    # widget= specifies a Widget class to embed in each list item
                    self._extract_embed_widget()
                    # checkable= specifies checkbox for list items
                    # - None/False (default): no checkboxes
                    # - str without braces: two-way binding to bool field name
                    # - str with braces "{expr}": one-way expression (read-only)
                    self.list_checkable = self.kwargs.pop("checkable", None)
                    # editable= specifies inline editing for list items
                    # - None/False: no editing (default)
                    # - str: field name to edit (supports nested paths)
                    # - True: edit the item itself (for simple types)
                    self.list_editable = self.kwargs.pop("editable", None)
                    # Edit triggers (defaults: doubleClick=True, select=False, editKey=True)
                    self.edit_on_double_click = self.kwargs.pop("editOnDoubleClick", None)
                    self.edit_on_select = self.kwargs.pop("editOnSelect", None)
                    self.edit_on_edit_key = self.kwargs.pop("editOnEditKey", None)
                    # validator= for inline editing (same format as QLineEdit validator=)
                    self.list_validator = self.kwargs.pop("validator", None)
                    # onEdited= callback for after inline edit is committed
                    self.list_on_edited = self.kwargs.pop("onEdited", None)
                    # QListView-specific selection bindings (multi)
                    self.selected_indexes = self.kwargs.pop("selectedIndexes", None)
                    self.selected_items_list = self.kwargs.pop("selectedItems", None)
                # Extract QTreeView-specific kwargs only if this is a QTreeView
                elif self._is_qtreeview_type():
                    # widget= specifies a Widget class to embed in each tree node
                    self._extract_embed_widget()
                    # children= specifies attribute for child items
                    self.tree_children = self.kwargs.pop("children", None)
                    # expand= calls expandAll() on init and when root observable changes
                    self.tree_expand = self.kwargs.pop("expand", False)
                    # headerHidden= hides the header row (default: True)
                    self.tree_header_hidden = self.kwargs.pop("headerHidden", True)
                    # checkable= specifies checkbox for tree nodes
                    # - None/False: no checkboxes (default)
                    # - str without braces: two-way binding to bool field name
                    # - str with braces "{expr}": one-way expression (read-only)
                    self.tree_checkable = self.kwargs.pop("checkable", None)
                    # editable= specifies inline editing for tree nodes
                    # - None/False: no editing (default)
                    # - str: field name to edit (supports nested paths)
                    # - True: edit the item itself (for simple types)
                    self.tree_editable = self.kwargs.pop("editable", None)
                    # Edit triggers (defaults: doubleClick=True, select=False, editKey=True)
                    self.edit_on_double_click = self.kwargs.pop("editOnDoubleClick", None)
                    self.edit_on_select = self.kwargs.pop("editOnSelect", None)
                    self.edit_on_edit_key = self.kwargs.pop("editOnEditKey", None)
                    # validator= for inline editing (same format as QLineEdit validator=)
                    self.tree_validator = self.kwargs.pop("validator", None)
                    # onEdited= callback for after inline edit is committed
                    self.tree_on_edited = self.kwargs.pop("onEdited", None)
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

            # Extract QPlainTextEdit/QTextEdit-specific kwargs
            if self._is_qtext_editor_type():
                # highlighter= specifies a SyntaxHighlighter class or Variable binding
                highlighter_val = self.kwargs.pop("highlighter", None)
                if highlighter_val is not None:
                    if isinstance(highlighter_val, NewField):
                        # Direct Variable reference: new(highlighter=_my_highlighter)
                        self.highlighter = highlighter_val.name
                    else:
                        # Either a class or a string variable name
                        self.highlighter = highlighter_val
                # content_type= binds to a Variable[str] for MIME type-based highlighter
                content_type_val = self.kwargs.pop("content_type", None)
                if content_type_val is not None:
                    if isinstance(content_type_val, NewField):
                        self.editor_content_type = content_type_val.name
                    elif isinstance(content_type_val, str):
                        self.editor_content_type = content_type_val

            # Extract validator= for input validation (works on QLineEdit, QComboBox, etc.)
            # - str (regex): QRegularExpressionValidator
            # - Callable[[str], bool]: Simple predicate
            # - Callable[[str, int], State]: Full control
            # - str (method name): Look up on widget
            validator_val = self.kwargs.pop("validator", None)
            if validator_val is not None:
                self.validator = validator_val

            # Handle layout= parameter:
            # - layout=False → exclude from layout
            # - layout=nested_layout (NewField) → add to that nested layout
            # - layout="nested_layout" (str) → add to that nested layout by name
            layout_kwarg = self.kwargs.pop("layout", None)
            if layout_kwarg is False:
                self.exclude_from_layout = True
            elif layout_kwarg is not None:
                # NewField reference or string - store for target layout resolution
                if isinstance(layout_kwarg, NewField):
                    self.target_layout = layout_kwarg.name
                elif isinstance(layout_kwarg, str):
                    self.target_layout = layout_kwarg

            # Handle splitter= parameter:
            # - splitter=_splitter (NewField) → add to that splitter
            # - splitter="_splitter" (str) → add to that splitter by name
            self._extract_target_splitter()

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

            # Extract width= and height= for initial size (applied via resize())
            self.initial_width = self.kwargs.pop("width", None)
            self.initial_height = self.kwargs.pop("height", None)

            # Extract signal connections (e.g., clicked="on_clicked")
            self._extract_signal_connections()

            # Extract event handlers (onFocus, onMousePress, etc.)
            self._extract_event_handlers()

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

            # Extract event handlers (onFocus, onMousePress, etc.) - may not apply to all QObjects
            self._extract_event_handlers()

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
        return is_qwidget(self.field_type)

    def _is_qobject_type(self) -> bool:
        """Check if the field type is a QObject subclass (but not QWidget)."""
        return is_qobject(self.field_type, exclude_qwidget=True)

    def _is_qwidget_class(self, cls: type | None) -> bool:
        """Check if cls is a QWidget subclass."""
        return is_qwidget(cls)

    def _is_qaction_class(self, cls: type | None) -> bool:
        """Check if cls is QAction."""
        return is_qaction(cls)

    def _is_qtableview_type(self) -> bool:
        """Check if the field type is a QTableView subclass."""
        return is_qtableview(self.field_type)

    def _is_qlistview_type(self) -> bool:
        """Check if the field type is a QListView subclass (but not QTableView or QTreeView)."""
        return is_qlistview(self.field_type, exclude_table_tree=True)

    def _is_qtreeview_type(self) -> bool:
        """Check if the field type is a QTreeView subclass."""
        return is_qtreeview(self.field_type)

    def _is_qcombobox_type(self) -> bool:
        """Check if the field type is a QComboBox subclass."""
        return is_qcombobox(self.field_type)

    def _is_model_widget_type(self) -> bool:
        """Check if the field type is a model widget (QComboBox, QListView, QTableView, QTreeView)."""
        return is_model_widget(self.field_type)

    def _is_qtabwidget_type(self) -> bool:
        """Check if the field type is a QTabWidget subclass."""
        return is_qtabwidget(self.field_type)

    def _is_qtext_editor_type(self) -> bool:
        """Check if the field type is a QPlainTextEdit or QTextEdit subclass."""
        return is_qtext_editor(self.field_type)

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
        return is_dock_generic(self.field_type)

    def _is_dock_type_param(self, type_to_check: Any) -> bool:
        """Check if a given type is a Dock[T] generic alias."""
        return is_dock_generic(type_to_check)

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

    # Event handler kwarg names that are extracted and handled via event filter
    _EVENT_HANDLER_NAMES: frozenset[str] = frozenset(
        {
            # Focus events
            "onFocus",
            "onBlur",
            # Mouse events
            "onMouseEnter",
            "onMouseLeave",
            "onMousePress",
            "onMouseRelease",
            "onMouseDoubleClick",
            "onMouseMove",
            "onWheel",
            # Keyboard events
            "onKeyPress",
            "onKeyRelease",
            "onEnterKey",
            "onDeleteKey",
            # Widget events
            "onShow",
            "onHide",
            "onClose",
            "onResize",
            "onMove",
            # Drag & drop events
            "onDragEnter",
            "onDragLeave",
            "onDragMove",
            "onDrop",
        }
    )

    def _extract_event_handlers(self) -> None:
        """Extract event handlers (onFocus, onMouseEnter, etc.) from kwargs.

        These are pseudo-signals implemented via event filter since Qt
        doesn't have actual signals for these events.

        Supports both callables and string method names:
            onFocus=lambda: print("focused")
            onFocus="_on_focus"
            onMousePress="on_mouse_press"
        """
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            if key in self._EVENT_HANDLER_NAMES:
                if isinstance(value, str) or callable(value):
                    self.event_handlers[key] = value
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

        Also handles auto-record-binding: when a parent Widget[T] contains a child Widget[T]
        (same T), automatically bind child's record to parent's record unless opted out.

        Example:
            child: Child = new(count="_my_count")  # count is extracted as a binding
            child: ChildWidget = new()  # Auto: record="record" if T matches parent
            child: ChildWidget = new(bind=False)  # Opt-out: no auto-record-bind
        """
        if self.field_type is None:
            return

        # Check if the field type is a QtPie Widget subclass
        if not self._is_qtpie_widget():
            return

        # Get the child's required bindings and all Variable annotations
        child_config = getattr(self.field_type, "_qtpie_config", None)
        if child_config is None:
            return

        # Collect all Variable names from the child (required and optional)
        variable_names: set[str] = set(child_config.required_bindings)

        # Also check annotations for Variable types (including optional ones with defaults)
        child_annotations = getattr(self.field_type, "__annotations__", {})
        for name, annotation in child_annotations.items():
            origin = get_origin(annotation)
            if origin is Variable or annotation is Variable:
                variable_names.add(name)

        # Add "record" to variable names if child is Widget[T] (has record_type)
        child_record_type = getattr(child_config, "record_type", None)
        if child_record_type is not None:
            variable_names.add("record")

        # Extract kwargs that match Variable names
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            if key in variable_names:
                # If value is a NewField, convert to string reference (its field name)
                # This allows: new(workspace_service=workspace_service) where workspace_service
                # is another field defined on the same widget
                if isinstance(value, NewField):
                    self.variable_bindings[key] = value.name
                else:
                    self.variable_bindings[key] = value
                to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

        # Note: Auto-record-bind (bind="record" -> variable_bindings["record"]="record") is
        # handled at instantiation time in new_fields.py because _auto_record_bind_children()
        # runs in __init_subclass__ AFTER __set_name__, so bind= isn't set yet during this method.

    def _is_qtpie_widget(self) -> bool:
        """Check if the field type is a QtPie Widget subclass (has _qtpie_config)."""
        if self.field_type is None:
            return False
        return hasattr(self.field_type, "_qtpie_config")

    def _get_variable_default(self) -> Any:
        """Extract default value for a Variable field.

        Returns _NO_DEFAULT sentinel if no default was provided (distinct from None).
        """
        # Check for explicit default= kwarg
        if "default" in self.kwargs:
            return self.kwargs["default"]
        # Check for single arg (primitive, list, dict, or object)
        if len(self.args) == 1:
            return self.args[0]
        return NO_DEFAULT

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

    def _is_qspaceritem_type(self) -> bool:
        """Check if the field type is QSpacerItem."""
        return is_qspaceritem(self.field_type)

    def _is_qlayout_type(self) -> bool:
        """Check if the field type is a QLayout subclass."""
        return is_qlayout(self.field_type)

    def _is_qsplitter_type(self) -> bool:
        """Check if the field type is QSplitter."""
        return is_qsplitter(self.field_type)

    def _extract_target_layout(self) -> None:
        """Extract layout= parameter for targeting nested layouts.

        Handles:
        - layout=False → exclude from layout (sets exclude_from_layout)
        - layout=nested_layout (NewField) → add to that nested layout
        - layout="nested_layout" (str) → add to that nested layout by name

        Also extracts grid= and label= for use when adding to the target layout.
        """
        layout_kwarg = self.kwargs.pop("layout", None)
        if layout_kwarg is False:
            self.exclude_from_layout = True
        elif layout_kwarg is not None:
            # NewField reference or string - store for target layout resolution
            if isinstance(layout_kwarg, NewField):
                self.target_layout = layout_kwarg.name
            elif isinstance(layout_kwarg, str):
                self.target_layout = layout_kwarg

        # Extract grid= and label= for nested layout positioning
        # These are used when adding this item to a nested grid/form layout
        self.grid = self.kwargs.pop("grid", None)
        self.label = self.kwargs.pop("label", None)

    def _extract_target_splitter(self) -> None:
        """Extract splitter= parameter for adding widgets to a QSplitter.

        Handles:
        - splitter=_splitter (NewField) → add to that splitter
        - splitter="_splitter" (str) → add to that splitter by name
        """
        splitter_kwarg = self.kwargs.pop("splitter", None)
        if splitter_kwarg is not None:
            # NewField reference or string - store for target splitter resolution
            if isinstance(splitter_kwarg, NewField):
                self.target_splitter = splitter_kwarg.name
            elif isinstance(splitter_kwarg, str):
                self.target_splitter = splitter_kwarg

    def _extract_dock_kwargs(self, source: dict[str, Any], *, full: bool = False) -> None:
        """Extract dock-specific kwargs from source dict into self.dock_* fields.

        Args:
            source: Dict to pop kwargs from (modifies in place).
            full: If True, extract all dock properties including positioning
                  (below, rightOf, etc.). If False, only extract basic properties.
        """
        self.dock_area = source.pop("dock", None)
        self.dock_title = source.pop("windowTitle", None) or source.pop("title", None)
        self.dock_group = source.pop("group", None)
        self.dock_group_selected_index = source.pop("groupSelectedIndex", None)
        self.dock_group_selected_dock = source.pop("groupSelectedDock", None)
        self.dock_group_selected_index_changed = source.pop("groupSelectedIndexChanged", None)
        self.dock_group_selected_dock_changed = source.pop("groupSelectedDockChanged", None)
        self.dock_closable = source.pop("closable", None)
        self.dock_floatable = source.pop("floatable", None)
        self.dock_movable = source.pop("movable", None)

        if full:
            self.dock_below = source.pop("below", None)
            self.dock_right_of = source.pop("rightOf", None)
            self.dock_left_of = source.pop("leftOf", None)
            self.dock_above = source.pop("above", None)
            self.dock_icon = source.pop("icon", None)
            self.dock_visible = source.pop("visible", None)
            self.dock_floating = source.pop("floating", None)
            self.dock_allowed_areas = source.pop("allowedAreas", None)
            self.dock_vertical_title_bar = source.pop("verticalTitleBar", None)
            self.dock_hide_title_bar = source.pop("hideTitleBar", None)
            self.dock_hide_title_bar_when_tabbed = source.pop("hideTitleBarWhenTabbed", None)
            self.dock_context_menu = source.pop("contextMenu", None)

    def _extract_embed_widget(self) -> None:
        """Extract widget= parameter for embedding widgets in QListView/QTreeView.

        Handles:
        - widget=MyWidget (Widget class) → embed widget for each item
        - widget=embed(MyWidget, kwargs) (EmbedConfig) → embed with config
        """
        from qtpie.embed import EmbedConfig

        widget_kwarg = self.kwargs.pop("widget", None)
        if widget_kwarg is None:
            return

        if isinstance(widget_kwarg, EmbedConfig):
            self.embed_widget = widget_kwarg.widget_class
            self.embed_config = widget_kwarg
        elif isinstance(widget_kwarg, type):
            self.embed_widget = widget_kwarg
            self.embed_config = None

    def _extract_table_columns(self, columns: list[Any]) -> None:
        """Extract columns= for QTableView, detecting widget columns.

        Columns can be:
        - str: field name ("name", "age")
        - Widget class: embed widget in that column
        - EmbedConfig: embed widget with config in that column

        Sets:
        - self.table_columns: list of str field names (with placeholder for widgets)
        - self.table_widget_columns: list of (index, widget_class, embed_config|None)
        """
        from qtpie.embed import EmbedConfig

        str_columns: list[str] = []
        widget_columns: list[tuple[int, type, EmbedConfig | None]] = []

        for i, col in enumerate(columns):
            if isinstance(col, str):
                str_columns.append(col)
            elif isinstance(col, EmbedConfig):
                # Get column name from embed config or widget's title
                col_name = self._get_widget_column_name(col.widget_class, col.column_name)
                str_columns.append(col_name)
                widget_columns.append((i, col.widget_class, col))
            elif isinstance(col, type):
                # Widget class directly - get title from widget config
                col_name = self._get_widget_column_name(col, None)
                str_columns.append(col_name)
                widget_columns.append((i, col, None))

        self.table_columns = str_columns if str_columns else None
        self.table_widget_columns = widget_columns if widget_columns else None

    def _extract_prepend_columns(self, columns: list[Any]) -> None:
        """Extract prependColumns= for QTableView, detecting widget columns.

        Same format as columns= but stored separately for merging with auto-detected.
        Sets:
        - self.table_prepend_columns: list of str field names
        - self.table_prepend_widget_columns: list of (index, widget_class, embed_config|None)
        """
        from qtpie.embed import EmbedConfig

        str_columns: list[str] = []
        widget_columns: list[tuple[int, type, EmbedConfig | None]] = []

        for i, col in enumerate(columns):
            if isinstance(col, str):
                str_columns.append(col)
            elif isinstance(col, EmbedConfig):
                col_name = self._get_widget_column_name(col.widget_class, col.column_name)
                str_columns.append(col_name)
                widget_columns.append((i, col.widget_class, col))
            elif isinstance(col, type):
                col_name = self._get_widget_column_name(col, None)
                str_columns.append(col_name)
                widget_columns.append((i, col, None))

        self.table_prepend_columns = str_columns if str_columns else None
        self.table_prepend_widget_columns = widget_columns if widget_columns else None

    def _extract_append_columns(self, columns: list[Any]) -> None:
        """Extract appendColumns= for QTableView, detecting widget columns.

        Same format as columns= but stored separately for merging with auto-detected.
        Sets:
        - self.table_append_columns: list of str field names
        - self.table_append_widget_columns: list of (index, widget_class, embed_config|None)
        """
        from qtpie.embed import EmbedConfig

        str_columns: list[str] = []
        widget_columns: list[tuple[int, type, EmbedConfig | None]] = []

        for i, col in enumerate(columns):
            if isinstance(col, str):
                str_columns.append(col)
            elif isinstance(col, EmbedConfig):
                col_name = self._get_widget_column_name(col.widget_class, col.column_name)
                str_columns.append(col_name)
                widget_columns.append((i, col.widget_class, col))
            elif isinstance(col, type):
                col_name = self._get_widget_column_name(col, None)
                str_columns.append(col_name)
                widget_columns.append((i, col, None))

        self.table_append_columns = str_columns if str_columns else None
        self.table_append_widget_columns = widget_columns if widget_columns else None

    def _get_widget_column_name(self, widget_class: type, override: str | None) -> str:
        """Get column name for a widget column.

        Priority:
        1. override (from embed(column_name=...))
        2. Widget's @widget(title=...) -> _qtpie_config.widget_props["windowTitle"]
        3. Empty string (no header)
        """
        if override is not None:
            return override

        # Try to get title from widget's _qtpie_config
        config = getattr(widget_class, "_qtpie_config", None)
        if config is not None:
            widget_props = getattr(config, "widget_props", None)
            if widget_props is not None:
                title = widget_props.get("windowTitle")
                if title is not None:
                    return str(title)

        # Fallback to empty string
        return ""
