# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Window - QMainWindow with QtPie features."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin, overload

from observant import Observable
from qtpy.QtWidgets import (
    QDockWidget,
    QLayout,
    QMainWindow,
    QMenu,
    QWidget,
)

from .event import extract_event_args, is_event_hint
from .layout import GridPosition, LayoutType
from .mixins import QtPieComponentBase
from .new_field import NewField
from .new_fields import new_fields
from .qt_pie_state import QtPieState
from .signals import create_signal_expression_handler
from .utils.common import detect_required_bindings
from .utils.layouts import add_to_layout, create_layout
from .variable import Variable, _RequiredBindingDescriptor, _VariableDescriptor
from .widget import IconType, _validate_layout_params


@dataclass
class WindowConfig:
    """Configuration for @window decorator."""

    init_wrapped: bool = False
    auto_bind: bool = True
    widget_props: dict[str, Any] = field(default_factory=lambda: {})
    object_name: str | None = None
    css_classes: list[str] = field(default_factory=lambda: [])
    # Track fields for signal connections and menu handling
    fields: dict[str, NewField] = field(default_factory=lambda: {})
    variable_names: list[str] = field(default_factory=lambda: [])
    # Layout configuration for central widget
    layout: LayoutType = "vertical"
    margins: int | tuple[int, int, int, int] | None = None
    # Record type from Window[T]
    record_type: type[Any] | None = None
    # Initial record value from @window(record=...)
    record_default: Any | None = None
    # Required bindings - bare Variable[T] fields that must be provided
    required_bindings: set[str] = field(default_factory=lambda: set[str]())
    # Dock fields - field names that are Dock[T] types
    dock_fields: list[str] = field(default_factory=lambda: [])
    variable_dock_fields: list[str] = field(default_factory=lambda: [])  # Variable[T, Dock[W]] fields
    list_dock_fields: list[str] = field(default_factory=lambda: [])  # list[Dock[W]] fields
    # Window-level dock configuration
    corners: dict[str, str] | None = None  # {"top_left": "left", "bottom_right": "bottom", ...}
    dock_state_key: str | None = None  # Key for QSettings persistence
    docks_locked: str | None = None  # Variable binding for lock/unlock all docks
    # Dock tab configuration
    dock_nesting: bool = True  # Enable nested dock splitting
    dock_tabs_position: str = "top"  # Tab bar position: "top", "bottom", "left", "right"
    dock_tabs_closable: bool = False  # Show close buttons on dock tabs
    dock_tabs_movable: bool = False  # Allow reordering tabs by dragging
    dock_tabs_hide_title_bar: bool = False  # Auto-hide title bar when dock is tabified
    dock_tabs_drag_to_undock: bool = False  # Drag tab outside tab bar to float dock
    dock_tabs_drag_margin: int = 50  # Pixel margin for drag-to-undock detection
    dock_tabs_middle_click_close: bool = True  # Middle-click on tab closes dock
    # Window icon (resolved at runtime)
    icon: IconType = None
    # Window size
    size: tuple[int, int] | None = None  # Initial size (width, height)
    # Signal connections from decorator: {signal_name: handler_name}
    signal_connections: dict[str, str] = field(default_factory=lambda: {})


class Window[T = None](QMainWindow, QtPieComponentBase):
    """QMainWindow with QtPie declarative features.

    Similar to Widget but for main windows. Automatically:
    - Adds QMenu fields to the menu bar
    - Processes new() fields
    - Creates central widget with layout for QWidget fields
    - Calls __setup__ after initialization

    Example:
        @window(title="My App")
        class MainWindow(Window):
            file_menu: FileMenu = new()
            edit_menu: EditMenu = new()
            label: QLabel = new("Hello!")  # Added to central widget

            # Menus auto-added to menuBar() - no __setup__ needed!

        # With record type (like Widget[T]):
        @window(title="Dog Editor")
        class DogWindow(Window[Dog]):
            name: QLineEdit = new()  # Auto-binds to record.name
    """

    _qtpie_config: WindowConfig
    _qtpie: QtPieState

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Each subclass gets its own config
        cls._qtpie_config = WindowConfig()

        # Extract T from Window[T] if present
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is Window:
                args = get_args(base)
                if args:
                    cls._qtpie_config.record_type = args[0]
                break

        # Check if user declared 'record' explicitly
        has_explicit_record = "record" in cls.__dict__

        # Collect NewField instances (must happen before new_fields processes them)
        _collect_fields(cls)

        # Detect bare Variable[T] annotations (no = new())
        # These are required bindings - must be provided by parent
        _detect_required_bindings_for_window(cls)

        # Process Event[T] annotations and create real Qt Signals
        _process_event_annotations_for_window(cls)

        # Auto-new bare annotations (non-Variable types)
        from .widget_base import _auto_new_bare_annotations

        _auto_new_bare_annotations(cls)

        # Apply new_fields to handle Variable and QWidget instantiation
        new_fields(cls)

        # Collect variable names (after new_fields converts NewField → _VariableDescriptor)
        from .variable import _VariableDescriptor

        for name, value in list(cls.__dict__.items()):
            if isinstance(value, _VariableDescriptor):
                cls._qtpie_config.variable_names.append(name)

        # Auto-create record descriptor if Window[T] but no explicit record
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            from .widget import _RecordDescriptor

            cls.record = _RecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Check that @window decorator was applied."""
        if not self._qtpie_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @window")
        super().__init__(*args, **kwargs)

    if TYPE_CHECKING:
        # Lie to pyright: say record returns T for field autocomplete
        @property
        def record(self) -> T: ...
        @record.setter
        def record(self, value: T) -> None: ...

        @property
        def record_value(self) -> T:
            """Get the raw record value, unwrapped from the ObservableProxy.

            Use this when you need the actual object (e.g., for isinstance checks):
                if isinstance(self.record_value.auth, ApiKeyAuth):
                    ...
            """
            ...

    if not TYPE_CHECKING:
        # Runtime-only: provide better error messages for .record access
        # Hidden from pyright so it doesn't disable attribute checking
        def __getattr__(self, name: str) -> Any:
            """Handle attribute access for special cases."""
            if name == "record":
                raise TypeError(f"{type(self).__name__} has no record type. Use Window[YourModel] to enable record access.")
            if name == "record_value":
                # Return unwrapped record value if available
                if hasattr(self, "_qtpie") and self._qtpie._record is not None:
                    return self._qtpie._record.value
                raise AttributeError(f"{type(self).__name__} has no record type. Use Window[YourModel] to enable record_value access.")
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    async def on_close(self) -> None:
        """Async hook called when the window is closing.

        Override this to perform async cleanup before the window closes.
        """
        pass


def _collect_fields(cls: type[Window[Any]]) -> None:
    """Collect NewField instances from class before they're processed."""
    config = cls._qtpie_config
    for name in getattr(cls, "__annotations__", {}):
        value = getattr(cls, name, None)
        if isinstance(value, NewField):
            config.fields[name] = value
            # Track dock fields separately (after __set_name__ has run, is_dock is set)
            if value.is_dock:
                config.dock_fields.append(name)
            # Track list[Dock[W]] fields
            elif value.is_list_dock:
                config.list_dock_fields.append(name)
        # Check for Variable[T, Dock[W]] descriptors
        elif isinstance(value, _VariableDescriptor) and value.dock_info is not None:
            config.variable_dock_fields.append(name)


def _detect_required_bindings_for_window(cls: type[Window[Any]]) -> None:
    """Detect bare Variable[T] and Setting[T] annotations as required bindings."""
    from .setting import Setting

    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)
    detect_required_bindings(cls, "_qtpie_config", Setting, _RequiredBindingDescriptor)


def _process_event_annotations_for_window(cls: type[Window[Any]]) -> None:
    """Process Event[T] annotations and create real Qt Signals.

    A bare annotation like `on_click: Event` or `on_changed: Event[int]`
    gets a real Qt Signal created on the class.
    """
    import typing

    from qtpy.QtCore import Signal

    # Get annotations including from parent classes
    hints = typing.get_type_hints(cls) if hasattr(cls, "__annotations__") else {}

    for name, hint in hints.items():
        # Skip if already has a value
        if name in cls.__dict__:
            continue

        # Check if it's an Event annotation
        if is_event_hint(hint):
            # Extract signal argument types from Event[T]
            args = extract_event_args(hint)
            # Create real Qt Signal on the class
            setattr(cls, name, Signal(*args))


@overload
def window[W: Window[Any]](cls: type[W]) -> type[W]: ...


@overload
def window[W: Window[Any]](
    cls: None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    icon: IconType = None,
    size: tuple[int, int] | None = None,
    record: Any | None = None,
    corners: dict[str, str] | None = None,
    dockStateKey: str | None = None,
    docksLocked: str | None = None,
    # Dock tab options
    dockNesting: bool = True,
    dockTabsPosition: str = "top",
    dockTabsClosable: bool = False,
    dockTabsMovable: bool = False,
    dockTabsHideTitleBar: bool = False,
    dockTabsDragToUndock: bool = False,
    dockTabsDragMargin: int = 50,
    dockTabsMiddleClickClose: bool = True,
    **kwargs: Any,
) -> Callable[[type[W]], type[W]]: ...


def window[W: Window[Any]](
    cls: type[W] | None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    icon: IconType = None,
    size: tuple[int, int] | None = None,
    record: Any | None = None,
    stylesheet: str | None = None,
    corners: dict[str, str] | None = None,
    dockStateKey: str | None = None,
    docksLocked: str | None = None,
    # Dock tab options
    dockNesting: bool = True,
    dockTabsPosition: str = "top",
    dockTabsClosable: bool = False,
    dockTabsMovable: bool = False,
    dockTabsHideTitleBar: bool = False,
    dockTabsDragToUndock: bool = False,
    dockTabsDragMargin: int = 50,
    dockTabsMiddleClickClose: bool = True,
    **kwargs: Any,
) -> type[W] | Callable[[type[W]], type[W]]:
    """Decorator for Window classes.

    Usage:
        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()

        @window(title="My App", icon=":/icons/app.png")
        class MainWindow(Window):
            file_menu: FileMenu = new()
            edit_menu: EditMenu = new()
            # Menus automatically added to menu bar!

            label: QLabel = new("Hello!")  # Added to central widget layout
            button: QPushButton = new("Click")  # Added to central widget layout

        # Custom central widget:
        @window(title="My App")
        class MainWindow(Window):
            central_widget: QLabel = new("I AM THE CENTRAL WIDGET")
            # Uses central_widget as the central widget directly

    Args:
        layout: "vertical" | "horizontal" | "form" | "grid" | None
                Layout for the auto-created central widget. Default is "vertical".
                Ignored if central_widget field is defined.
        margins: int | tuple[int, int, int, int] | None
                 Layout margins. int applies to all sides.
        auto_bind: If True (default), enable auto-binding for Variables.
        name: Set the window's objectName.
        classes: List of CSS classes to apply.
        title: Shorthand for windowTitle.
        icon: Window icon. Accepts str path (file or Qt resource ":/..."),
              QIcon, QPixmap, or QStyle.StandardPixmap.
        stylesheet: Shorthand for styleSheet.
        **kwargs: Extra properties applied via setXXX() methods.
    """
    if title is not None:
        kwargs["windowTitle"] = title
    # icon is stored raw and resolved at runtime (when Qt resources are available)
    if stylesheet is not None:
        kwargs["styleSheet"] = stylesheet

    def decorator(target: type[W]) -> type[W]:
        from qtpie.utils.common import is_signal_on_type

        config = target._qtpie_config

        # Extract signal connections from kwargs
        # Signal connections are kwargs where the key is a Signal name on the class
        signal_connections: dict[str, str] = {}
        widget_props: dict[str, Any] = {}
        for key, value in kwargs.items():
            if is_signal_on_type(key, target) and isinstance(value, str):
                signal_connections[key] = value
            else:
                widget_props[key] = value

        config.layout = layout
        config.margins = margins
        config.auto_bind = auto_bind
        config.record_default = record
        config.widget_props = widget_props
        config.object_name = name
        config.css_classes = classes or []
        config.corners = corners
        config.dock_state_key = dockStateKey
        config.docks_locked = docksLocked
        config.dock_nesting = dockNesting
        config.dock_tabs_position = dockTabsPosition
        config.dock_tabs_closable = dockTabsClosable
        config.dock_tabs_movable = dockTabsMovable
        config.dock_tabs_hide_title_bar = dockTabsHideTitleBar
        config.dock_tabs_drag_to_undock = dockTabsDragToUndock
        config.dock_tabs_drag_margin = dockTabsDragMargin
        config.dock_tabs_middle_click_close = dockTabsMiddleClickClose
        config.icon = icon
        config.size = size
        config.signal_connections = signal_connections

        # Auto-wrap async methods (e.g., async def on_close)
        from qtpie.async_wrap import wrap_async_methods

        wrap_async_methods(target)

        # Wrap __init__
        _wrap_init_for_window(target)

        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]


def _has_layout_items(
    cls: type[Window[Any]],
    config: WindowConfig,
    dock_field_names: set[str],
    variable_dock_field_names: set[str],
) -> bool:
    """Check if there are any fields that should go in a central widget layout.

    Returns True if there are QWidgets, Variables with widgets, Stretch,
    QSpacerItem, or QLayout fields that aren't docks or menus.
    """

    for name in getattr(cls, "__annotations__", {}):
        # Skip dock fields
        if name in dock_field_names or name in variable_dock_field_names:
            continue
        # Skip central_widget and status_bar (handled separately)
        if name in ("central_widget", "_central_widget", "status_bar", "_status_bar"):
            continue

        # Check if it's a field we handle
        if name in config.fields:
            field = config.fields[name]
            # These types go in the layout
            if field.is_stretch or field.is_spacer_item or field.is_nested_layout:
                return True
            # Check if field type is a QWidget (not QMenu)
            if field.field_type is not None:
                if _is_qwidget_not_qmenu(field.field_type):
                    return True

        # Check if it's a Variable with widget (Variable[T, W] has widget_type set)
        if name in config.variable_names:
            # Get the descriptor to check if it actually has a widget type
            descriptor = getattr(cls, name, None)
            from .variable import _VariableDescriptor

            if isinstance(descriptor, _VariableDescriptor) and descriptor._widget_type is not None:
                return True

    return False


def _is_qwidget_not_qmenu(field_type: type) -> bool:
    """Check if field_type is a QWidget but not a QMenu."""
    try:
        from qtpy.QtWidgets import QMenu, QWidget

        return issubclass(field_type, QWidget) and not issubclass(field_type, QMenu)
    except (ImportError, TypeError):
        return False


def _wrap_init_for_window(cls: type[Window[Any]]) -> None:
    """Wrap __init__ to add menus, create central widget, apply props, and call __setup__."""
    if cls._qtpie_config.init_wrapped:
        return

    original_init = cls.__init__
    config = cls._qtpie_config

    def wrapped_init(self: Window[Any], *args: Any, **kwargs: Any) -> None:
        # Extract _qtpie_bindings before passing kwargs to original init
        _qtpie_bindings = kwargs.pop("_qtpie_bindings", None)

        # Extract Variable kwargs (match against variable_names and required_bindings)
        variable_kwargs: dict[str, Any] = {}
        all_variable_names = set(config.variable_names) | config.required_bindings
        for var_name in all_variable_names:
            if var_name in kwargs:
                variable_kwargs[var_name] = kwargs.pop(var_name)

        # Set translation context to class name (used by t() markers)
        from qtpie.translations import set_translation_context

        set_translation_context(type(self).__name__)

        # Initialize QtPieState early so Variables have somewhere to register
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)

        # Apply parent variable bindings BEFORE original_init runs
        # This ensures required Variables exist before child widgets are created
        if _qtpie_bindings is not None:
            parent, bindings = _qtpie_bindings
            from .new_fields import _apply_variable_bindings_direct

            _apply_variable_bindings_direct(parent, self, bindings)

        # Apply constructor variable kwargs
        if variable_kwargs:
            from .new_fields import apply_variable_kwargs

            apply_variable_kwargs(self, variable_kwargs)

        # Call original __init__
        original_init(self, *args, **kwargs)

        # Apply corner assignments before creating docks
        if config.corners:
            _apply_corner_assignments(self, config.corners)

        # Apply dock tab options (nesting, tab position) before creating docks
        from .dock_tabs import setup_dock_tab_options

        setup_dock_tab_options(self, config)

        # Create list widget fields (list[QWidget] = new(bind="..."))
        from .widget import _create_list_widget_fields

        _create_list_widget_fields(self, config)  # type: ignore[arg-type]

        # Pre-create bare Variables for selection bindings BEFORE creating dock fields
        # This allows groupSelectedDock="_var" to work with bare Variable[Dock[Any] | None] annotations
        from .bindings.apply import pre_create_selection_variables

        pre_create_selection_variables(self, config)

        # Create dock widget fields (Dock[T] = new(dock="left", ...))
        _create_dock_fields(self, config)

        # Create Variable dock fields (Variable[T, Dock[W]] = new(..., dock="right", ...))
        _create_variable_dock_fields(self, config)

        # Create list dock fields (list[Dock[W]] = new(bind="...", dock="right", ...))
        _create_list_dock_fields(self, config)

        # Install dock tab features (closable, movable, hide title bar, drag-to-undock)
        from .dock_tabs import install_dock_tab_features

        dock_overrides = _collect_dock_overrides(self, config)
        install_dock_tab_features(self, config, dock_overrides)

        # Apply widget properties (windowTitle="X" → setWindowTitle("X"))
        # Skip reactive props (with {}) and Translatable - they'll be handled by apply_reactive_widget_props
        from .bindings import is_format_string
        from .translations.translatable import Translatable
        from .utils.layouts import apply_object_name_and_classes, apply_widget_props, resolve_icon

        def skip_reactive_or_translatable(prop_name: str, value: Any) -> bool:
            if isinstance(value, str) and is_format_string(value):
                return True
            if isinstance(value, Translatable):
                return True
            return False

        apply_widget_props(self, config.widget_props, skip_filter=skip_reactive_or_translatable)

        # Apply icon at runtime (when Qt resources are available)
        if config.icon is not None:
            resolved_icon = resolve_icon(config.icon)
            if resolved_icon is not None:
                self.setWindowIcon(resolved_icon)

        # Apply initial size
        if config.size is not None:
            self.resize(*config.size)

        # Apply objectName and CSS classes
        apply_object_name_and_classes(
            self,
            config.object_name,
            config.css_classes,
            default_name=type(self).__name__,
        )

        # Connect signals for fields
        from qtpie.signals import connect_field_event_handlers, connect_field_signals

        connect_field_signals(self, config.fields, _create_window_signal_expression_handler)
        connect_field_event_handlers(self, config.fields)

        # Connect signals from decorator (e.g., @window(on_reload="_on_reload"))
        _connect_decorator_signals(self, config)

        # Auto-add QMenu fields to menu bar (in declaration order)
        # And track non-menu QWidget fields for central widget, plus layout items
        dock_field_names = set(config.dock_fields)
        variable_dock_field_names = set(config.variable_dock_fields)
        for name in getattr(cls, "__annotations__", {}):
            # Skip dock fields - they're handled separately
            if name in dock_field_names:
                continue
            # Skip Variable[T, Dock[W]] fields - they're handled separately
            if name in variable_dock_field_names:
                continue
            instance = getattr(self, name, None)
            if isinstance(instance, QMenu):
                self.menuBar().addMenu(instance)
                # Store reference to parent window for #parent bindings
                instance._parent_window = self  # type: ignore[attr-defined]
                # Refresh parent-dependent bindings now that menu has a parent
                if hasattr(instance, "_refresh_parent_bindings"):
                    instance._refresh_parent_bindings()  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]

        # Set up central widget
        # Option 1: If there's an explicit central_widget or _central_widget field, use it
        # Note: Use `is None` check, not `or`, because Variable can be falsy (empty value)
        explicit_central = getattr(self, "central_widget", None)
        if explicit_central is None:
            explicit_central = getattr(self, "_central_widget", None)
        # Handle Variable[T, W] as central_widget
        if isinstance(explicit_central, Variable) and explicit_central.widget is not None:
            explicit_central = explicit_central.widget
        if explicit_central is not None and isinstance(explicit_central, QWidget):
            self.setCentralWidget(explicit_central)
        # Option 2: Create a container with layout for non-menu/non-layout fields
        elif config.layout is not None and _has_layout_items(cls, config, dock_field_names, variable_dock_field_names):
            from .variable import _VariableDescriptor
            from .widget import _add_layout_to_nested_layout, _add_spacer_to_layout, _add_stretch_to_layout, _add_widget_to_nested_layout, _create_spacer_item, _get_target_layout

            central = QWidget()
            qt_layout = create_layout(config.layout)
            if qt_layout is not None:
                central.setLayout(qt_layout)

                # Apply margins
                from .utils.layouts import apply_layout_margins

                apply_layout_margins(qt_layout, config.margins)

                # Track nested layouts by field name for later reference
                nested_layouts: dict[str, QLayout] = {}

                # Track splitters by field name for later reference
                from qtpy.QtWidgets import QSplitter

                splitters: dict[str, QSplitter] = {}

                # First pass: Create nested layouts and splitters (so they exist before items reference them)
                # Don't ADD them yet - that happens in second pass to preserve field order
                for name in getattr(cls, "__annotations__", {}):
                    if name in dock_field_names or name in variable_dock_field_names:
                        continue
                    if name in config.fields:
                        field = config.fields[name]
                        if field.is_nested_layout:
                            # Create the nested layout instance (but don't add to layout yet - preserve order)
                            layout_instance = field.field_type(*field.args, **field.kwargs)  # type: ignore[misc]
                            setattr(self, name, layout_instance)
                            nested_layouts[name] = layout_instance

                        elif field.is_splitter:
                            # Create the splitter instance (but don't add to layout yet - preserve order)
                            splitter_instance = field.field_type(*field.args, **field.kwargs)  # type: ignore[misc]
                            setattr(self, name, splitter_instance)
                            splitters[name] = splitter_instance

                # Second pass: Add child widgets, Variables, Stretch, and QSpacerItem to layouts
                from qtpie.layout import Stretch

                for name in getattr(cls, "__annotations__", {}):
                    if name in dock_field_names or name in variable_dock_field_names:
                        continue
                    if name in ("central_widget", "_central_widget", "status_bar", "_status_bar"):
                        continue

                    annotation = getattr(cls, "__annotations__", {}).get(name)

                    # Handle bare Stretch annotation (without = new())
                    if annotation is Stretch and name not in config.fields:
                        _add_stretch_to_layout(qt_layout, 1)  # Default factor
                        continue

                    if name in config.fields:
                        field = config.fields[name]
                        if field.exclude_from_layout:
                            continue

                        # Handle nested layouts - add to layout in order
                        if field.is_nested_layout:
                            layout_instance = nested_layouts.get(name)
                            if layout_instance is not None:
                                target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                                if target is not None:
                                    _add_layout_to_nested_layout(target, layout_instance, field.grid, name)
                            continue

                        # Handle QSplitter - add to layout in order
                        if field.is_splitter:
                            splitter_instance = splitters.get(name)
                            if splitter_instance is not None:
                                target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                                if target is not None:
                                    _add_to_layout(target, splitter_instance, config.layout, None, field.grid, None)
                            continue

                        # Check if widget should go to a splitter instead of layout
                        from .widget import _get_target_splitter

                        target_splitter = _get_target_splitter(splitters, field.target_splitter)
                        if target_splitter is not None:
                            # Add to splitter, not layout
                            widget_instance = getattr(self, name, None)
                            if widget_instance is not None and isinstance(widget_instance, QWidget):
                                target_splitter.addWidget(widget_instance)
                            continue

                        # Determine target layout
                        target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                        if target is None:
                            continue

                        # Handle Stretch
                        if field.is_stretch:
                            _add_stretch_to_layout(target, field.stretch_factor)
                            continue

                        # Handle QSpacerItem
                        if field.is_spacer_item:
                            spacer = _create_spacer_item(field)
                            setattr(self, name, spacer)
                            _add_spacer_to_layout(target, spacer, field.grid)
                            continue

                        # Handle regular QWidget
                        widget_instance = getattr(self, name, None)
                        if widget_instance is not None and isinstance(widget_instance, QWidget) and not isinstance(widget_instance, QMenu):
                            label: str | None = None
                            label_translatable: Any = None
                            grid: GridPosition | None = None

                            if isinstance(field.label, Translatable):
                                label = field.label.resolve()
                                label_translatable = field.label
                            else:
                                label = field.label
                            grid = field.grid

                            # For default layout: validate and use decorator's layout type
                            # For nested layout: detect actual layout type and use appropriate add method
                            if field.target_layout is None:
                                _validate_layout_params(name, config.layout, label, grid)
                                _add_to_layout(target, widget_instance, config.layout, label, grid, label_translatable)
                            else:
                                _add_widget_to_nested_layout(target, widget_instance, label, grid, name)

                    # Check if it's a Variable with a widget
                    elif name in config.variable_names:
                        var = getattr(self, name, None)
                        if isinstance(var, Variable) and var.widget is not None:
                            # Get label/grid/exclude_from_layout/target_layout from the descriptor
                            descriptor = getattr(cls, name, None)
                            var_label: str | None = None
                            var_label_translatable: Any = None
                            grid: GridPosition | None = None
                            target_layout_name: str | None = None
                            is_format_label = False
                            raw_label: Any = None
                            if isinstance(descriptor, _VariableDescriptor):
                                if descriptor.exclude_from_layout:
                                    continue
                                raw_label = descriptor.label
                                if isinstance(raw_label, Translatable):
                                    var_label = raw_label.resolve()
                                    var_label_translatable = raw_label
                                elif isinstance(raw_label, str) and "{" in raw_label and "}" in raw_label:
                                    # Format string label like "{kind}" - use placeholder, will be set by binding
                                    # Use space (not empty string) so Qt creates the QLabel widget
                                    var_label = " "  # Placeholder - binding sets initial value immediately
                                    is_format_label = True
                                else:
                                    var_label = raw_label
                                grid = descriptor.grid  # type: ignore[assignment]
                                target_layout_name = descriptor.target_layout

                            # Determine target layout
                            target = _get_target_layout(qt_layout, nested_layouts, target_layout_name)
                            if target is None:
                                continue

                            # For default layout: validate and use decorator's layout type
                            # For nested layout: detect actual layout type and use appropriate add method
                            if target_layout_name is None:
                                _validate_layout_params(name, config.layout, var_label, grid)
                                _add_to_layout(target, var.widget, config.layout, var_label, grid, var_label_translatable)

                                # Apply format binding to form label if it was a format string
                                if is_format_label and config.layout == "form" and isinstance(raw_label, str):
                                    from qtpy.QtWidgets import QFormLayout

                                    from .bindings import create_format_binding

                                    form_layout = cast(QFormLayout, target)
                                    label_widget = form_layout.labelForField(var.widget)
                                    if label_widget is not None:  # pyright: ignore[reportUnnecessaryComparison] - Qt returns None for spanningWidget
                                        create_format_binding(self, raw_label, label_widget.setText)  # type: ignore[union-attr]
                            else:
                                _add_widget_to_nested_layout(target, var.widget, var_label, grid, name)

            self.setCentralWidget(central)

        # Set up status bar widget if defined (status_bar or _status_bar field)
        # Note: Use `is None` check because Variable can be falsy (empty value)
        status_bar_widget = getattr(self, "status_bar", None)
        if status_bar_widget is None:
            status_bar_widget = getattr(self, "_status_bar", None)
        # Handle Variable[T, W] as status_bar
        if isinstance(status_bar_widget, Variable) and status_bar_widget.widget is not None:
            status_bar_widget = status_bar_widget.widget
        if status_bar_widget is not None and isinstance(status_bar_widget, QWidget):
            self.statusBar().addPermanentWidget(status_bar_widget, 1)  # stretch=1 to fill

        # Ensure QtPieState exists BEFORE bindings run (binding code checks hasattr)
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)

        # Register validators from validate= parameter (before __setup__ so they're active)
        from .widget import _register_validators

        _register_validators(self, config)  # type: ignore[arg-type]

        # Set initial record value if provided via @window(record=...)
        if config.record_default is not None and hasattr(self, "record"):
            self.record = config.record_default

        # Call __setup__ hook (required bindings are now available)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings using shared logic (after __setup__ so record is available)
        from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props, pre_create_selection_variables
        from .bindings.expression import create_expression_binding

        # Pre-create Variables for selection bindings (bare Variable[T] without new())
        pre_create_selection_variables(self, config)

        apply_auto_bindings(self, config)
        apply_property_bindings(self, config, create_expression_binding_fn=create_expression_binding)
        apply_reactive_widget_props(self, config)

        # Set up docksLocked binding (reactive dock locking)
        if config.docks_locked:
            _setup_docks_locked_binding(self, config.docks_locked)

        # Restore dock state from QSettings (after all docks created)
        if config.dock_state_key:
            _restore_dock_state(self, config.dock_state_key)
            # Install close event handler to save state
            _install_dock_state_save_handler(self, config.dock_state_key)

        # Enable on_dirty_changed and on_valid_changed hooks
        self._qtpie.enable_dirty_hook()
        self._qtpie.enable_valid_hook()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_config.init_wrapped = True


def _create_window_signal_expression_handler(window: Window[Any], expression: str) -> Callable[..., Any]:
    """Create a signal handler from an expression string like "{my_signal(123)}"."""
    return create_signal_expression_handler(window, expression, ["#window", "#widget", "#self"])


def _connect_decorator_signals(window: Window[Any], config: WindowConfig) -> None:
    """Connect signals defined in @window decorator kwargs.

    Example:
        @window(title="My App", on_reload="_on_reload")
        class MainWindow(Window):
            on_reload = Signal()
            def _on_reload(self): ...

    Args:
        window: The Window instance
        config: The WindowConfig containing signal_connections
    """
    from .utils.common import is_signal

    for signal_name, handler_name in config.signal_connections.items():
        signal = getattr(window, signal_name, None)
        if signal is None:
            continue

        if not is_signal(signal):
            continue

        handler = getattr(window, handler_name, None)
        if handler is None:
            raise AttributeError(f"Handler '{handler_name}' not found on {type(window).__name__} for signal '{signal_name}'")

        if callable(handler):
            signal.connect(handler)


def _create_dock_fields(window: Window[Any], config: WindowConfig) -> None:
    """Create Dock[T] fields for the window.

    Handles:
    - Basic dock placement with dock="left|right|top|bottom"
    - Splits with below=/above=/rightOf=/leftOf= referencing other docks
    - Group-based tabification with group="name"
    """
    from .dock import Dock, parse_dock_area

    if not config.dock_fields:
        return

    # Build dependency graph for topological sort
    # dock_info[name] = {field, dependencies}
    dock_info: dict[str, dict[str, Any]] = {}
    for name in config.dock_fields:
        field = config.fields.get(name)
        if field is None or not field.is_dock:
            continue
        fld = field

        deps: list[str] = []
        # Dependencies are the docks referenced by below/above/rightOf/leftOf
        if fld.dock_below:
            deps.append(fld.dock_below)
        if fld.dock_above:
            deps.append(fld.dock_above)
        if fld.dock_right_of:
            deps.append(fld.dock_right_of)
        if fld.dock_left_of:
            deps.append(fld.dock_left_of)

        dock_info[name] = {"field": fld, "deps": deps}

    # Topological sort - process docks with no deps first, then docks that depend on them
    processed: set[str] = set()
    ordered_names: list[str] = []

    def process(name: str) -> None:
        if name in processed:
            return
        info = dock_info.get(name)
        if info is None:
            return
        # Process dependencies first
        for dep in info["deps"]:
            process(dep)
        processed.add(name)
        ordered_names.append(name)

    for name in dock_info:
        process(name)

    # Track created docks for reference-based positioning
    created_docks: dict[str, Dock[Any]] = {}

    # Track groups for tabification
    groups: dict[str, list[str]] = {}  # group_name -> [dock_names in order]

    # First pass: create all dock widgets
    for name in ordered_names:
        info = dock_info[name]
        fld: NewField = info["field"]

        # Get the content widget type
        content_type = fld.dock_content_type
        if content_type is None:
            continue

        # Instantiate the content widget
        # For Dock[T], widget args come from chained call: new(dock_kwargs)(widget_args)
        # Pass parent reference for logical parent hierarchy (if content is a QtPie widget)
        dock_widget_kwargs = dict(fld.widget_kwargs)
        if hasattr(content_type, "_qtpie_config"):
            dock_widget_kwargs["_qtpie_bindings"] = (window, {})
        content_widget = content_type(*fld.widget_args, **dock_widget_kwargs)

        # Create the QDockWidget
        title = fld.dock_title or name
        dock_widget = QDockWidget(title, window)
        dock_widget.setWidget(content_widget)

        # Apply objectName
        if fld.object_name:
            dock_widget.setObjectName(fld.object_name)
        else:
            dock_widget.setObjectName(name)

        # Apply dock features (closable, floatable, movable)
        _apply_dock_features(
            dock_widget,
            fld.dock_closable,
            fld.dock_floatable,
            fld.dock_movable,
            fld.dock_allowed_areas,
            fld.dock_vertical_title_bar,
            fld.dock_hide_title_bar,
        )

        # Create Dock wrapper
        dock = Dock(content_widget, dock_widget)
        created_docks[name] = dock

        # Store on window instance
        setattr(window, name, dock)

        # Track group membership
        if fld.dock_group:
            if fld.dock_group not in groups:
                groups[fld.dock_group] = []
            groups[fld.dock_group].append(name)

        # Determine placement
        from qtpy.QtCore import Qt as QtCore

        if fld.dock_area:
            # Direct area placement
            area = parse_dock_area(fld.dock_area)
            window.addDockWidget(area, dock_widget)
        elif fld.dock_below:
            # Vertical split below referenced dock
            ref_dock = created_docks.get(fld.dock_below)
            if ref_dock:
                window.splitDockWidget(ref_dock.dock_widget, dock_widget, QtCore.Orientation.Vertical)
        elif fld.dock_above:
            # Vertical split above referenced dock (insert this one first)
            ref_dock = created_docks.get(fld.dock_above)
            if ref_dock:
                # Split and then swap order by tabifying then untabifying
                # Actually, Qt doesn't have a direct "above" - we split and the new one goes below
                # To put it above, we need to split the reference first
                area = window.dockWidgetArea(ref_dock.dock_widget)
                window.addDockWidget(area, dock_widget)
                window.splitDockWidget(dock_widget, ref_dock.dock_widget, QtCore.Orientation.Vertical)
        elif fld.dock_right_of:
            # Horizontal split to the right
            ref_dock = created_docks.get(fld.dock_right_of)
            if ref_dock:
                window.splitDockWidget(ref_dock.dock_widget, dock_widget, QtCore.Orientation.Horizontal)
        elif fld.dock_left_of:
            # Horizontal split to the left
            ref_dock = created_docks.get(fld.dock_left_of)
            if ref_dock:
                area = window.dockWidgetArea(ref_dock.dock_widget)
                window.addDockWidget(area, dock_widget)
                window.splitDockWidget(dock_widget, ref_dock.dock_widget, QtCore.Orientation.Horizontal)
        elif fld.dock_group:
            # Group without explicit positioning - will be tabified with group anchor
            # Find the anchor dock (first in group with dock= or reference positioning)
            pass  # Handled in tabification pass below

    # Second pass: handle group tabification
    for _group_name, dock_names in groups.items():
        if len(dock_names) < 2:
            continue

        # Find the anchor dock (first one that has placement)
        anchor_name: str | None = None
        for name in dock_names:
            fld = dock_info[name]["field"]
            if fld.dock_area or fld.dock_below or fld.dock_above or fld.dock_right_of or fld.dock_left_of:
                anchor_name = name
                break

        if anchor_name is None:
            # No anchor found - use first dock and default to left
            anchor_name = dock_names[0]
            anchor_dock = created_docks[anchor_name]
            window.addDockWidget(parse_dock_area("left"), anchor_dock.dock_widget)

        # Tabify all other docks in the group with the anchor
        anchor_dock = created_docks[anchor_name]
        for name in dock_names:
            if name == anchor_name:
                continue
            dock = created_docks[name]
            # Check if this dock was already placed via reference positioning
            fld = dock_info[name]["field"]
            if not (fld.dock_area or fld.dock_below or fld.dock_above or fld.dock_right_of or fld.dock_left_of):
                # Not placed yet - add to same area as anchor
                from qtpy.QtCore import Qt as QtCore

                area = window.dockWidgetArea(anchor_dock.dock_widget)
                if area == QtCore.DockWidgetArea.NoDockWidgetArea:
                    area = parse_dock_area("left")
                window.addDockWidget(area, dock.dock_widget)
            # Tabify with anchor
            window.tabifyDockWidget(anchor_dock.dock_widget, dock.dock_widget)

        # Raise the anchor tab to front
        anchor_dock.dock_widget.raise_()

    # Third pass: set up bindings (visible=, floating=, groupSelectedIndex=)
    _setup_dock_bindings(window, config, dock_info, created_docks, groups)


def _setup_dock_bindings(
    window: Window[Any],
    config: WindowConfig,
    dock_info: dict[str, dict[str, Any]],
    created_docks: dict[str, Any],
    groups: dict[str, list[str]],
) -> None:
    """Set up bindings for dock fields (title=, icon=, visible=, floating=, groupSelectedIndex=, groupSelectedDock=)."""
    from .dock import Dock

    # Track which groups have had groupSelectedIndex/groupSelectedDock binding set up
    groups_with_index_binding: set[str] = set()
    groups_with_dock_binding: set[str] = set()

    for name in config.dock_fields:
        info = dock_info.get(name)
        if info is None:
            continue
        fld: NewField = info["field"]
        dock: Dock[Any] = created_docks[name]

        # title= binding: reactive title (expression or variable reference)
        if fld.dock_title:
            _setup_dock_title_binding(window, dock, fld.dock_title, name)

        # icon= binding: reactive icon (expression, variable, or static path)
        if fld.dock_icon:
            _setup_dock_icon_binding(window, dock, fld.dock_icon)

        # visible= binding: two-way sync between Variable and dock visibility
        if fld.dock_visible:
            _setup_dock_visible_binding(window, dock, fld.dock_visible)

        # floating= binding: two-way sync between Variable and dock floating state
        if fld.dock_floating:
            _setup_dock_floating_binding(window, dock, fld.dock_floating)

        # groupSelectedIndex= binding and/or groupSelectedIndexChanged= callback
        # Either binding or callback (or both) can be specified
        if (fld.dock_group_selected_index or fld.dock_group_selected_index_changed) and fld.dock_group:
            group_name = fld.dock_group
            if group_name not in groups_with_index_binding:
                groups_with_index_binding.add(group_name)
                # Set up binding for this group's tab bar
                group_dock_names = groups.get(group_name, [])
                if group_dock_names:
                    # Resolve callback if specified
                    index_changed_cb = None
                    if fld.dock_group_selected_index_changed:
                        index_changed_cb = getattr(window, fld.dock_group_selected_index_changed, None)
                    _setup_group_selected_index_binding(window, fld.dock_group_selected_index, group_dock_names, created_docks, index_changed_cb)

        # groupSelectedDock= binding and/or groupSelectedDockChanged= callback
        # Either binding or callback (or both) can be specified
        if (fld.dock_group_selected_dock or fld.dock_group_selected_dock_changed) and fld.dock_group:
            group_name = fld.dock_group
            if group_name not in groups_with_dock_binding:
                groups_with_dock_binding.add(group_name)
                # Set up binding for this group's tab bar
                group_dock_names = groups.get(group_name, [])
                if group_dock_names:
                    # Resolve callback if specified
                    dock_changed_cb = None
                    if fld.dock_group_selected_dock_changed:
                        dock_changed_cb = getattr(window, fld.dock_group_selected_dock_changed, None)
                    _setup_group_selected_dock_binding(window, fld.dock_group_selected_dock, group_dock_names, created_docks, dock_changed_cb)


def _setup_dock_visible_binding(window: Window[Any], dock: Any, binding: str) -> None:
    """Set up two-way binding between Variable and dock visibility."""
    from .variable import _get_variable_observable

    observable = _get_variable_observable(window, binding)
    # Note: Use `is None` check, not truthiness - Observable(False) is falsy!
    if observable is None:
        return

    dock_widget = dock.dock_widget

    # Variable -> Dock visibility
    # Use isHidden() instead of isVisible() because isVisible() returns False
    # when the parent window isn't shown yet, which would skip initial setup
    def on_variable_change(visible: bool) -> None:
        # isHidden() = True means widget was explicitly hidden
        # We want: visible=False -> isHidden()=True, visible=True -> isHidden()=False
        if visible and dock_widget.isHidden():
            dock_widget.setVisible(True)
        elif not visible and not dock_widget.isHidden():
            dock_widget.setVisible(False)

    observable.on_change(on_variable_change)
    # Set initial state
    on_variable_change(observable.get())

    # Dock visibility -> Variable
    def on_visibility_change(visible: bool) -> None:
        if observable.get() != visible:
            observable.set(visible)

    dock_widget.visibilityChanged.connect(on_visibility_change)


def _setup_dock_floating_binding(window: Window[Any], dock: Any, binding: str) -> None:
    """Set up two-way binding between Variable and dock floating state."""
    from .variable import _get_variable_observable

    observable = _get_variable_observable(window, binding)
    if observable is None:
        return

    dock_widget = dock.dock_widget

    # Variable -> Dock floating
    def on_variable_change(floating: bool) -> None:
        if dock_widget.isFloating() != floating:
            dock_widget.setFloating(floating)

    observable.on_change(on_variable_change)
    # Set initial state
    on_variable_change(observable.get())

    # Dock floating -> Variable
    def on_floating_change(floating: bool) -> None:
        if observable.get() != floating:
            observable.set(floating)

    dock_widget.topLevelChanged.connect(on_floating_change)


def _setup_dock_title_binding(window: Window[Any], dock: Any, title: str, field_name: str) -> None:
    """Set up reactive binding for dock title.

    Supports:
    - Expression: title="{_filename}{'*' if _dirty else ''}"
    - Variable reference: title="_title_var"
    - Static value: title="My Dock" (no binding, just set once)
    """
    dock_widget = dock.dock_widget

    # Check if it's an expression (contains {})
    if "{" in title:
        from .bindings import create_format_binding

        def set_title(value: Any) -> None:
            dock_widget.setWindowTitle(str(value))

        create_format_binding(window, title, set_title)
        return

    # Check if it's a variable reference (starts with _)
    if title.startswith("_"):
        from .variable import _get_variable_observable

        observable = _get_variable_observable(window, title)
        if observable is not None:

            def on_title_change(value: Any) -> None:
                dock_widget.setWindowTitle(str(value))

            observable.on_change(on_title_change)
            # Set initial value
            on_title_change(observable.get())
            return

    # Static value - already set during dock creation
    # (title is passed to QDockWidget constructor)


def _apply_dock_features(
    dock_widget: QDockWidget,
    closable: bool | None,
    floatable: bool | None,
    movable: bool | None,
    allowed_areas: list[str] | None,
    vertical_title_bar: bool | None,
    hide_title_bar: bool | None = None,
) -> None:
    """Apply dock widget features (closable, floatable, movable, etc.)."""
    from qtpy.QtCore import Qt as QtCore
    from qtpy.QtWidgets import QWidget

    # Build features flag - start with all features enabled
    features = QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable

    # Remove features based on parameters
    if closable is False:
        features &= ~QDockWidget.DockWidgetFeature.DockWidgetClosable
    if floatable is False:
        features &= ~QDockWidget.DockWidgetFeature.DockWidgetFloatable
    if movable is False:
        features &= ~QDockWidget.DockWidgetFeature.DockWidgetMovable

    dock_widget.setFeatures(features)

    # Set allowed areas
    if allowed_areas is not None:
        areas = QtCore.DockWidgetArea(0)  # Start with no areas
        area_map = {
            "left": QtCore.DockWidgetArea.LeftDockWidgetArea,
            "right": QtCore.DockWidgetArea.RightDockWidgetArea,
            "top": QtCore.DockWidgetArea.TopDockWidgetArea,
            "bottom": QtCore.DockWidgetArea.BottomDockWidgetArea,
        }
        for area_name in allowed_areas:
            area_name_lower = area_name.lower()
            if area_name_lower in area_map:
                areas |= area_map[area_name_lower]
        dock_widget.setAllowedAreas(areas)

    # Set vertical title bar
    if vertical_title_bar is True:
        dock_widget.setFeatures(dock_widget.features() | QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar)

    # Hide title bar completely (use setFixedHeight like _hide_titlebar does)
    if hide_title_bar is True:
        empty_widget = QWidget()
        empty_widget.setFixedHeight(0)
        dock_widget.setTitleBarWidget(empty_widget)
        dock_widget.setProperty("_qtpie_titlebar_hidden", True)


def _collect_dock_overrides(window: Window[Any], config: WindowConfig) -> dict[QDockWidget, dict[str, Any]]:
    """Collect per-dock overrides from NewField configurations.

    Returns a dict mapping QDockWidget instances to their override settings.
    Currently supports:
    - hide_title_bar: Always hide title bar for this dock
    - hide_title_bar_when_tabbed: Override window's dockTabsHideTitleBar for this dock
    """
    from .dock import Dock

    overrides: dict[QDockWidget, dict[str, Any]] = {}

    # Collect from Dock[T] fields
    for field_name in config.dock_fields:
        dock_obj = getattr(window, field_name, None)
        if isinstance(dock_obj, Dock):
            field = config.fields.get(field_name)
            if field is not None:
                dock_overrides: dict[str, Any] = {}
                if field.dock_hide_title_bar is not None:
                    dock_overrides["hide_title_bar"] = field.dock_hide_title_bar
                if field.dock_hide_title_bar_when_tabbed is not None:
                    dock_overrides["hide_title_bar_when_tabbed"] = field.dock_hide_title_bar_when_tabbed
                if dock_overrides:
                    overrides[dock_obj.dock_widget] = dock_overrides

    # Collect from Variable[T, Dock[W]] fields
    for field_name in config.variable_dock_fields:
        var = getattr(window, field_name, None)
        if var is not None and hasattr(var, "dock"):
            dock_attr = getattr(var, "dock", None)
            if isinstance(dock_attr, Dock):
                field = config.fields.get(field_name)
                if field is not None:
                    dock_overrides_var: dict[str, Any] = {}
                    if field.dock_hide_title_bar is not None:
                        dock_overrides_var["hide_title_bar"] = field.dock_hide_title_bar
                    if field.dock_hide_title_bar_when_tabbed is not None:
                        dock_overrides_var["hide_title_bar_when_tabbed"] = field.dock_hide_title_bar_when_tabbed
                    if dock_overrides_var:
                        overrides[dock_attr.dock_widget] = dock_overrides_var

    return overrides


def _apply_corner_assignments(window: Window[Any], corners: dict[str, str]) -> None:
    """Apply corner assignments for dock areas.

    Args:
        window: The Window instance
        corners: Dict mapping corner names to area names, e.g.:
            {"top_left": "left", "bottom_right": "bottom"}

    Valid corner names: "top_left", "top_right", "bottom_left", "bottom_right"
    Valid area names: "left", "right", "top", "bottom"
    """
    from qtpy.QtCore import Qt as QtCore

    corner_map = {
        "top_left": QtCore.Corner.TopLeftCorner,
        "top_right": QtCore.Corner.TopRightCorner,
        "bottom_left": QtCore.Corner.BottomLeftCorner,
        "bottom_right": QtCore.Corner.BottomRightCorner,
    }

    area_map = {
        "left": QtCore.DockWidgetArea.LeftDockWidgetArea,
        "right": QtCore.DockWidgetArea.RightDockWidgetArea,
        "top": QtCore.DockWidgetArea.TopDockWidgetArea,
        "bottom": QtCore.DockWidgetArea.BottomDockWidgetArea,
    }

    for corner_name, area_name in corners.items():
        corner_name_lower = corner_name.lower().replace("-", "_")
        area_name_lower = area_name.lower()

        if corner_name_lower in corner_map and area_name_lower in area_map:
            window.setCorner(corner_map[corner_name_lower], area_map[area_name_lower])


def _setup_docks_locked_binding(window: Window[Any], binding: str) -> None:
    """Set up reactive binding for locking/unlocking all docks.

    When the bound Variable is True, all docks become immovable and unfloatable.
    When False, docks return to their original features.
    """
    from .variable import _get_variable_observable

    observable = _get_variable_observable(window, binding)
    if observable is None:
        return

    # Store original features for each dock widget
    original_features: dict[QDockWidget, QDockWidget.DockWidgetFeature] = {}

    def on_locked_change(locked: bool) -> None:
        # Find all dock widgets in the window
        for dock_widget in window.findChildren(QDockWidget):
            if locked:
                # Store original features if not already stored
                if dock_widget not in original_features:
                    original_features[dock_widget] = dock_widget.features()
                # Remove movable and floatable
                features = dock_widget.features()
                features &= ~QDockWidget.DockWidgetFeature.DockWidgetMovable
                features &= ~QDockWidget.DockWidgetFeature.DockWidgetFloatable
                dock_widget.setFeatures(features)
            else:
                # Restore original features
                if dock_widget in original_features:
                    dock_widget.setFeatures(original_features[dock_widget])

    observable.on_change(on_locked_change)
    # Apply initial state
    on_locked_change(observable.get())


def _restore_dock_state(window: Window[Any], state_key: str) -> None:
    """Restore dock layout from QSettings."""
    from qtpy.QtCore import QSettings

    settings = QSettings()
    state = settings.value(f"{state_key}/state")
    geometry = settings.value(f"{state_key}/geometry")

    if state is not None:
        window.restoreState(state)
    if geometry is not None:
        window.restoreGeometry(geometry)


def _install_dock_state_save_handler(window: Window[Any], state_key: str) -> None:
    """Install a close event handler to save dock state."""
    # Store original closeEvent
    original_close_event = window.closeEvent

    def save_and_close(event: Any) -> None:
        from qtpy.QtCore import QSettings

        settings = QSettings()
        settings.setValue(f"{state_key}/state", window.saveState())
        settings.setValue(f"{state_key}/geometry", window.saveGeometry())

        # Call original close event
        original_close_event(event)

    window.closeEvent = save_and_close  # type: ignore[method-assign]


def _setup_dock_icon_binding(window: Window[Any], dock: Any, icon: str) -> None:
    """Set up reactive binding for dock icon.

    Supports:
    - Expression: icon="{_mode}_icon.svg"
    - Variable reference: icon="_icon_path"
    - Static path: icon="terminal.svg" (no binding, just set once)

    Icon value can be:
    - str: Path to icon file or Qt resource path
    - QIcon: Used directly
    - QPixmap: Converted to QIcon
    - None or "": Clears the icon

    The icon is shown in the tab bar when the dock is tabified with other docks.
    """
    from qtpy.QtGui import QIcon, QPixmap

    dock_widget = dock.dock_widget

    def apply_icon(value: Any) -> None:
        if value is None or value == "":
            dock_widget.setWindowIcon(QIcon())
        elif isinstance(value, QIcon):
            dock_widget.setWindowIcon(value)
        elif isinstance(value, QPixmap):
            dock_widget.setWindowIcon(QIcon(value))
        else:
            # Assume string path
            dock_widget.setWindowIcon(QIcon(str(value)))

    # Check if it's an expression (contains {})
    if "{" in icon:
        from .bindings import create_format_binding

        create_format_binding(window, icon, apply_icon)
        return

    # Check if it's a variable reference (starts with _)
    if icon.startswith("_"):
        from .variable import _get_variable_observable

        observable = _get_variable_observable(window, icon)
        if observable is not None:
            observable.on_change(apply_icon)
            # Set initial value
            apply_icon(observable.get())
            return

    # Static value - set once
    apply_icon(icon)


def _setup_group_selected_index_binding(
    window: Window[Any],
    binding: str | None,
    group_dock_names: list[str],
    created_docks: dict[str, Any],
    callback: Callable[[int], None] | None = None,
) -> None:
    """Set up two-way binding between Variable and tab bar current index for a dock group.

    Either binding or callback (or both) can be specified.
    """
    from qtpy.QtWidgets import QTabBar

    from .variable import _get_variable_observable

    observable = _get_variable_observable(window, binding) if binding else None

    # Need either observable or callback to do anything
    if observable is None and callback is None:
        return

    if not group_dock_names:
        return

    # Get the first dock in the group to find the tab bar
    first_dock = created_docks.get(group_dock_names[0])
    if first_dock is None:
        return

    dock_widget = first_dock.dock_widget

    # Find the tab bar that contains this dock
    # Tab bars are children of the main window
    def find_tab_bar_for_dock() -> QTabBar | None:
        for tab_bar in window.findChildren(QTabBar):
            for i in range(tab_bar.count()):
                if tab_bar.tabText(i) == dock_widget.windowTitle():
                    return tab_bar
        return None

    # Need to defer this slightly because tab bar might not exist yet
    # Use a single-shot approach with processEvents
    from qtpy.QtCore import QTimer

    def setup_binding() -> None:
        tab_bar = find_tab_bar_for_dock()
        if tab_bar is None:
            return

        # Variable -> Tab bar index (only if observable exists)
        if observable is not None:

            def on_variable_change(index: int) -> None:
                if 0 <= index < tab_bar.count() and tab_bar.currentIndex() != index:
                    tab_bar.setCurrentIndex(index)

            observable.on_change(on_variable_change)
            # Set initial state
            on_variable_change(observable.get())

        # Tab bar index -> Variable and/or callback
        def on_tab_change(index: int) -> None:
            if observable is not None and observable.get() != index:
                observable.set(index)
            if callback is not None:
                callback(index)

        tab_bar.currentChanged.connect(on_tab_change)

    # Defer binding setup to ensure tab bar exists
    QTimer.singleShot(0, setup_binding)


def _setup_group_selected_dock_binding(
    window: Window[Any],
    binding: str | None,
    group_dock_names: list[str],
    created_docks: dict[str, Any],
    callback: Callable[[Any], None] | None = None,
) -> None:
    """Set up two-way binding between Variable and selected dock for a dock group.

    Unlike groupSelectedIndex which binds to the tab bar index, this binds to
    the actual Dock wrapper object. This allows users to:
    - Check which dock is currently selected by identity
    - Programmatically select a dock by setting the Variable

    The Variable type should be Dock[Any] | None since static dock groups
    can have heterogeneous dock types.

    Either binding or callback (or both) can be specified.
    """
    from qtpy.QtWidgets import QTabBar

    from .dock import Dock
    from .variable import _get_variable_observable

    observable = _get_variable_observable(window, binding) if binding else None

    # Need either observable or callback to do anything
    if observable is None and callback is None:
        return

    if not group_dock_names:
        return

    # Build ordered list of docks (same order as they appear in the tab bar)
    docks: list[Dock[Any]] = []
    for dock_name in group_dock_names:
        dock = created_docks.get(dock_name)
        if dock is not None:
            docks.append(dock)

    if not docks:
        return

    first_dock = docks[0]
    dock_widget = first_dock.dock_widget

    # Find the tab bar that contains this dock
    def find_tab_bar_for_dock() -> QTabBar | None:
        for tab_bar in window.findChildren(QTabBar):
            for i in range(tab_bar.count()):
                if tab_bar.tabText(i) == dock_widget.windowTitle():
                    return tab_bar
        return None

    # Defer to allow tab bar to be created
    from qtpy.QtCore import QTimer

    def setup_binding() -> None:
        tab_bar = find_tab_bar_for_dock()
        if tab_bar is None:
            return

        # Build a mapping from tab title to dock for efficient lookup
        # Note: This assumes dock titles are unique within a group
        title_to_dock: dict[str, Dock[Any]] = {d.dock_widget.windowTitle(): d for d in docks}

        # Set initial value silently if observable exists (don't fire callbacks)
        if observable is not None:
            initial_index = tab_bar.currentIndex()
            if 0 <= initial_index < tab_bar.count():
                initial_title = tab_bar.tabText(initial_index)
                initial_dock = title_to_dock.get(initial_title)
                if initial_dock is not None:
                    observable._value = initial_dock  # pyright: ignore[reportPrivateUsage]

            # Variable -> Tab bar (raise the dock when Variable changes)
            def on_variable_change(dock: Dock[Any] | None) -> None:
                if dock is None:
                    return
                # Find the tab index for this dock
                dock_title = dock.dock_widget.windowTitle()
                for i in range(tab_bar.count()):
                    if tab_bar.tabText(i) == dock_title:
                        if tab_bar.currentIndex() != i:
                            tab_bar.setCurrentIndex(i)
                        break

            observable.on_change(on_variable_change)

        # Tab bar -> Variable and/or callback (update when tab changes)
        def on_tab_change(index: int) -> None:
            if 0 <= index < tab_bar.count():
                tab_title = tab_bar.tabText(index)
                dock = title_to_dock.get(tab_title)
                if dock is not None:
                    if observable is not None and observable.get() is not dock:
                        observable.set(dock)
                    if callback is not None:
                        callback(dock)

        tab_bar.currentChanged.connect(on_tab_change)

        # Also track floating dock focus
        _setup_floating_dock_focus_for_group(docks, observable, callback)

    QTimer.singleShot(0, setup_binding)


def _setup_floating_dock_focus_for_group(
    docks: list[Any],
    observable: Any,
    callback: Callable[[Any], None] | None = None,
) -> None:
    """Set up focus tracking for floating docks in a static group.

    When a floating dock gains focus, update the selection Variable.
    """
    from qtpy.QtWidgets import QApplication

    updating = [False]  # Mutable flag to prevent recursive updates

    for dock in docks:
        dock_widget = dock.dock_widget
        focus_handler: list[Any] = [None]  # Store handler reference for cleanup

        def make_on_focus_changed(d: Any) -> Any:
            def on_focus_changed(old: QWidget | None, new: QWidget | None) -> None:
                if updating[0]:
                    return
                if new is None or not d.dock_widget.isFloating():
                    return
                if not d.dock_widget.isAncestorOf(new) and new is not d.dock_widget:
                    return

                # This floating dock gained focus - update selection
                updating[0] = True
                try:
                    if observable.get() is not d:
                        observable.set(d)
                        if callback is not None:
                            callback(d)
                finally:
                    updating[0] = False

            return on_focus_changed

        def make_on_top_level_changed(d: Any, fh: list[Any]) -> Any:
            def on_top_level_changed(floating: bool) -> None:
                app = QApplication.instance()
                if app is None or not isinstance(app, QApplication):
                    return

                if floating:
                    # Dock became floating - start tracking focus
                    fh[0] = make_on_focus_changed(d)
                    app.focusChanged.connect(fh[0])
                else:
                    # Dock was re-docked - stop tracking focus
                    if fh[0] is not None:
                        try:
                            app.focusChanged.disconnect(fh[0])
                        except (TypeError, RuntimeError):
                            pass
                        fh[0] = None

            return on_top_level_changed

        dock_widget.topLevelChanged.connect(make_on_top_level_changed(dock, focus_handler))

        # If already floating, start tracking immediately
        if dock_widget.isFloating():
            make_on_top_level_changed(dock, focus_handler)(True)


def _add_to_layout(
    layout: QLayout,
    widget_instance: QWidget,
    layout_type: LayoutType,
    label: str | None = None,
    grid: GridPosition | None = None,
    label_translatable: Any | None = None,
) -> None:
    """Add a widget to the layout."""
    add_to_layout(layout, widget_instance, layout_type, label, grid, label_translatable)


def _create_variable_dock_fields(window: Window[Any], config: WindowConfig) -> None:
    """Wrap Variable[T, Dock[W]] or Variable[list[T], Dock[W]] in dock containers.

    For Variable[T, Dock[W]], the _VariableDescriptor creates the inner widget W
    and stores it on var.widget. This function wraps that widget in a QDockWidget
    and Dock wrapper, replacing var.widget with the Dock so users can access:
    - self._name.value -> T (the variable value)
    - self._name.widget -> Dock[W] (the dock wrapper)
    - self._name.widget.widget -> W (the inner widget)
    - self._name.widget.dock_widget -> QDockWidget

    For Variable[list[T], Dock[W]], creates a DockWidgetRepeater that:
    - Dynamically creates/removes docks as items are added/removed from the list
    - self._name.value -> list[T] (the list value, also accessible as self._name.append(), etc.)
    - self._name.widget -> DockWidgetRepeater (the repeater)
    """
    from .dock import Dock, parse_dock_area

    if not config.variable_dock_fields:
        return

    for name in config.variable_dock_fields:
        # Get the Variable from the instance
        var: Variable[Any, Any] = getattr(window, name)

        # Get the descriptor to access dock_info
        descriptor = getattr(type(window), name, None)
        if not isinstance(descriptor, _VariableDescriptor) or descriptor.dock_info is None:
            continue

        dock_info = descriptor.dock_info

        # Check if this is a Variable[list[T], Dock[W]] - a list dock repeater
        if dock_info.get("is_list_dock"):
            _create_variable_list_dock_field(window, name, var, dock_info)
            continue

        # Otherwise it's Variable[T, Dock[W]] - a single dock
        if var.widget is None:
            continue

        # The inner widget was already created by the descriptor
        inner_widget = var.widget

        # Create the QDockWidget
        title = dock_info.get("dock_title") or name
        dock_widget = QDockWidget(title, window)
        dock_widget.setWidget(inner_widget)

        # Apply objectName
        object_name = dock_info.get("object_name")
        if object_name:
            dock_widget.setObjectName(object_name)
        else:
            dock_widget.setObjectName(name)

        # Apply dock features (closable, floatable, movable)
        _apply_dock_features(
            dock_widget,
            dock_info.get("dock_closable"),
            dock_info.get("dock_floatable"),
            dock_info.get("dock_movable"),
            dock_info.get("dock_allowed_areas"),
            dock_info.get("dock_vertical_title_bar"),
            dock_info.get("dock_hide_title_bar"),
        )

        # Create Dock wrapper
        dock = Dock(inner_widget, dock_widget)

        # Replace var.widget with the Dock wrapper
        var.widget = dock

        # Determine placement
        dock_area = dock_info.get("dock_area")
        dock_below = dock_info.get("dock_below")
        dock_above = dock_info.get("dock_above")
        dock_right_of = dock_info.get("dock_right_of")
        dock_left_of = dock_info.get("dock_left_of")

        if dock_area:
            # Direct area placement
            area = parse_dock_area(dock_area)
            window.addDockWidget(area, dock_widget)
        elif dock_below or dock_above or dock_right_of or dock_left_of:
            # Reference-based placement - find the referenced dock
            from qtpy.QtCore import Qt as QtCore

            ref_name = dock_below or dock_above or dock_right_of or dock_left_of
            ref_dock = getattr(window, ref_name, None) if ref_name else None

            if ref_dock is not None and hasattr(ref_dock, "dock_widget"):
                ref_dock_widget = ref_dock.dock_widget
                if dock_below:
                    window.splitDockWidget(ref_dock_widget, dock_widget, QtCore.Orientation.Vertical)
                elif dock_above:
                    window.splitDockWidget(dock_widget, ref_dock_widget, QtCore.Orientation.Vertical)
                    # Swap order so new dock is above
                    window.splitDockWidget(ref_dock_widget, dock_widget, QtCore.Orientation.Vertical)
                elif dock_right_of:
                    window.splitDockWidget(ref_dock_widget, dock_widget, QtCore.Orientation.Horizontal)
                elif dock_left_of:
                    window.splitDockWidget(dock_widget, ref_dock_widget, QtCore.Orientation.Horizontal)
                    # Swap order so new dock is to the left
                    window.splitDockWidget(ref_dock_widget, dock_widget, QtCore.Orientation.Horizontal)
            else:
                # Reference not found, default to left
                window.addDockWidget(parse_dock_area("left"), dock_widget)
        else:
            # No placement specified, default to right
            window.addDockWidget(parse_dock_area("right"), dock_widget)

        # Set up bindings if specified
        # Reactive title binding
        dock_title = dock_info.get("dock_title")
        if dock_title:
            _setup_dock_title_binding(window, dock, dock_title, name)

        # Reactive icon binding
        dock_icon = dock_info.get("dock_icon")
        if dock_icon:
            _setup_dock_icon_binding(window, dock, dock_icon)

        visible_binding = dock_info.get("dock_visible")
        if visible_binding:
            _setup_dock_visible_binding(window, dock, visible_binding)

        floating_binding = dock_info.get("dock_floating")
        if floating_binding:
            _setup_dock_floating_binding(window, dock, floating_binding)


def _create_list_dock_fields(window: Window[Any], config: WindowConfig) -> None:
    """Create list[Dock[W]] fields for the window.

    For list[Dock[W]] = new(bind="...", dock="right", group="..."), creates a
    DockWidgetRepeater that dynamically creates/removes docks as items are
    added/removed from the bound list.
    """
    from observant import ObservableList

    from .bindings import resolve_binding_source
    from .dock_widget_repeater import DockWidgetRepeater

    if not config.list_dock_fields:
        return

    for name in config.list_dock_fields:
        field = config.fields.get(name)
        if field is None or not field.is_list_dock:
            continue

        content_type = field.list_dock_content_type
        if content_type is None:
            continue

        if field.bind is None:
            raise ValueError(f"list[Dock[{content_type.__name__}]] field '{name}' requires bind='...'")

        # Resolve the binding source
        source = resolve_binding_source(window, field.bind)
        if source is None:
            raise ValueError(f"Could not resolve bind='{field.bind}' for list dock field '{name}'")

        # Get the ObservableList
        obs_list: ObservableList[Any]
        if isinstance(source, Variable):
            wrapper = source.observable
            if isinstance(wrapper, ObservableList):
                obs_list = wrapper
            elif isinstance(wrapper, Observable):
                # Observable containing a list - get the list value
                raw_list: Any = wrapper.get()
                if isinstance(raw_list, list):
                    obs_list = ObservableList[Any](cast(list[Any], raw_list))
                else:
                    raise TypeError(f"bind='{field.bind}' is Observable but doesn't contain a list")
            else:
                raise TypeError(f"bind='{field.bind}' resolved to unsupported type {type(wrapper).__name__}")
        elif isinstance(source, ObservableList):
            obs_list = source
        else:
            raise TypeError(f"bind='{field.bind}' must resolve to Variable[list[...]] or ObservableList, got {type(source).__name__}")

        # Determine title expression (only strings allowed for dock titles)
        title_expr = field.dock_title
        if title_expr is None and isinstance(field.list_format, str):
            title_expr = field.list_format
        if title_expr is None:
            title_expr = "{#self}"

        # Resolve selection bindings
        from .variable import _get_variable, _get_variable_observable

        selected_index_obs = None
        selected_item_obs = None
        selected_item_var = None
        selected_dock_obs = None
        if field.selected_index:
            selected_index_obs = _get_variable_observable(window, field.selected_index)
        if field.selected_item:
            selected_item_obs = _get_variable_observable(window, field.selected_item)
            selected_item_var = _get_variable(window, field.selected_item)
        if field.selected_dock:
            selected_dock_obs = _get_variable_observable(window, field.selected_dock)

        # Resolve selection change callbacks
        selected_index_changed_cb = None
        selected_item_changed_cb = None
        selected_dock_changed_cb = None
        if field.selected_index_changed:
            selected_index_changed_cb = getattr(window, field.selected_index_changed, None)
        if field.selected_item_changed:
            selected_item_changed_cb = getattr(window, field.selected_item_changed, None)
        if field.selected_dock_changed:
            selected_dock_changed_cb = getattr(window, field.selected_dock_changed, None)

        # Create the DockWidgetRepeater
        repeater: DockWidgetRepeater[Any, QWidget] = DockWidgetRepeater(
            observable_list=obs_list,
            item_type=None,  # Could extract from type hints if needed
            widget_type=content_type,
            window=window,
            dock_area=field.dock_area or "right",
            group=field.dock_group,
            title=title_expr,
            closable=field.dock_closable if field.dock_closable is not None else True,
            floatable=field.dock_floatable if field.dock_floatable is not None else True,
            movable=field.dock_movable if field.dock_movable is not None else True,
            widget_args=field.args,
            widget_kwargs=field.kwargs,
            selected_index_observable=selected_index_obs,
            selected_item_observable=selected_item_obs,
            selected_item_variable=selected_item_var,
            selected_dock_observable=selected_dock_obs,
            selected_index_changed_callback=selected_index_changed_cb,
            selected_item_changed_callback=selected_item_changed_cb,
            selected_dock_changed_callback=selected_dock_changed_cb,
        )

        # Store on window instance
        setattr(window, name, repeater)


def _create_variable_list_dock_field(
    window: Window[Any],
    name: str,
    var: Variable[Any, Any],
    dock_info: dict[str, Any],
) -> None:
    """Create a DockWidgetRepeater for Variable[list[T], Dock[W]].

    This function handles the Variable[list[T], Dock[W]] pattern where:
    - T is the item type (e.g., Request)
    - W is a Widget[T] type (e.g., RequestEditorWidget extends Widget[Request])

    Each item in the list gets its own dock tab, with the widget's record bound
    to that list item.
    """
    from observant import ObservableList

    from .dock_widget_repeater import DockWidgetRepeater
    from .variable import _get_variable_observable

    widget_type = dock_info.get("list_dock_widget_type")
    if widget_type is None:
        return

    # Get the ObservableList from the Variable
    wrapper = var.observable
    obs_list: ObservableList[Any]
    if isinstance(wrapper, ObservableList):
        obs_list = wrapper
    elif isinstance(wrapper, Observable):
        # Observable containing a list - need to wrap it
        raw_list: Any = wrapper.get()
        if isinstance(raw_list, list):
            obs_list = ObservableList[Any](cast(list[Any], raw_list))
            # Update the Variable's observable to use the ObservableList
            # so mutations via self._name.append() work
            var._observable = obs_list  # type: ignore[attr-defined]
        else:
            raise TypeError(f"Variable '{name}' inner type is not a list")
    else:
        raise TypeError(f"Variable '{name}' must have list inner type")

    # Determine title expression
    title_expr = dock_info.get("dock_title") or "{#self}"

    # Resolve selection bindings
    # For list dock repeaters, groupSelectedIndex and selectedIndex work the same way
    # (both bind to the tab bar index, which corresponds to list index)
    from .variable import _get_variable

    selected_index_obs = None
    selected_item_obs = None
    selected_item_var = None
    selected_dock_obs = None
    index_binding = dock_info.get("selected_index") or dock_info.get("dock_group_selected_index")
    if index_binding:
        selected_index_obs = _get_variable_observable(window, index_binding)
    if dock_info.get("selected_item"):
        selected_item_obs = _get_variable_observable(window, dock_info["selected_item"])
        selected_item_var = _get_variable(window, dock_info["selected_item"])
    if dock_info.get("selected_dock"):
        selected_dock_obs = _get_variable_observable(window, dock_info["selected_dock"])

    # Resolve selection change callbacks
    selected_index_changed_cb = None
    selected_item_changed_cb = None
    selected_dock_changed_cb = None
    if dock_info.get("selected_index_changed"):
        selected_index_changed_cb = getattr(window, dock_info["selected_index_changed"], None)
    if dock_info.get("selected_item_changed"):
        selected_item_changed_cb = getattr(window, dock_info["selected_item_changed"], None)
    if dock_info.get("selected_dock_changed"):
        selected_dock_changed_cb = getattr(window, dock_info["selected_dock_changed"], None)

    # Extract dock feature flags with defaults
    closable_val = dock_info.get("dock_closable")
    floatable_val = dock_info.get("dock_floatable")
    movable_val = dock_info.get("dock_movable")

    # Create the DockWidgetRepeater
    repeater: DockWidgetRepeater[Any, QWidget] = DockWidgetRepeater(
        observable_list=obs_list,
        item_type=dock_info.get("list_dock_item_type"),
        widget_type=widget_type,
        window=window,
        dock_area=dock_info.get("dock_area") or "right",
        group=dock_info.get("dock_group"),
        title=title_expr,
        closable=closable_val if isinstance(closable_val, bool) else True,
        floatable=floatable_val if isinstance(floatable_val, bool) else True,
        movable=movable_val if isinstance(movable_val, bool) else True,
        widget_args=(),
        widget_kwargs={},
        selected_index_observable=selected_index_obs,
        selected_item_observable=selected_item_obs,
        selected_item_variable=selected_item_var,
        selected_dock_observable=selected_dock_obs,
        selected_index_changed_callback=selected_index_changed_cb,
        selected_item_changed_callback=selected_item_changed_cb,
        selected_dock_changed_callback=selected_dock_changed_cb,
    )

    # Store the repeater on the Variable's widget property
    var.widget = repeater  # type: ignore[assignment]
