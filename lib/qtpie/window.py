# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Window - QMainWindow with QtPie features."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NoReturn, get_args, get_origin, overload

from observant import Observable
from qtpy.QtWidgets import (
    QDockWidget,
    QLayout,
    QMainWindow,
    QMenu,
    QWidget,
)

from .layout import GridPosition, LayoutType
from .new_field import NewField
from .new_fields import new_fields
from .signals import create_signal_expression_handler
from .state import QtPieState
from .utils.common import detect_required_bindings
from .utils.layouts import add_to_layout, create_layout
from .variable import Variable, _RequiredBindingDescriptor, _VariableDescriptor
from .widget import IconType, _resolve_icon, _validate_layout_params


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
    # Window-level dock configuration
    corners: dict[str, str] | None = None  # {"top_left": "left", "bottom_right": "bottom", ...}
    dock_state_key: str | None = None  # Key for QSettings persistence
    docks_locked: str | None = None  # Variable binding for lock/unlock all docks


class Window[T = None](QMainWindow):
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

    if not TYPE_CHECKING:
        # Runtime-only: provide better error messages for .record access
        # Hidden from pyright so it doesn't disable attribute checking
        def __getattr__(self, name: str) -> NoReturn:
            """Handle attribute access for special cases."""
            if name == "record":
                raise TypeError(f"{type(self).__name__} has no record type. Use Window[YourModel] to enable record access.")
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    def on_dirty_changed(self, is_dirty: bool) -> None:
        """Called when dirty state transitions (clean→dirty or dirty→clean).

        Override this to react to dirty state changes, e.g., enable/disable save button.
        """
        pass

    def on_valid_changed(self, is_valid: bool) -> None:
        """Called when validity state transitions (valid→invalid or invalid→valid).

        Override this to react to validation changes, e.g., show/hide error messages.
        """
        pass

    async def on_close(self) -> None:
        """Async hook called when the window is closing.

        Override this to perform async cleanup before the window closes.
        """
        pass

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, field: str, name: str, validator: Callable[[Any], None | str | list[str]]) -> None:
        """Add a named validator to a field.

        Usage:
            def __setup__(self) -> None:
                self.add_validator("name", "required", lambda v: None if v else "Required")
        """
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        self._qtpie.add_validator(field, name, validator)

    def remove_validator(self, field: str, name: str) -> None:
        """Remove a named validator from a field."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        self._qtpie.remove_validator(field, name)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Check if any field has changed. Returns Observable[bool] for reactive bindings.

        Aggregates dirty state from Variables AND record (if present).
        """
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.widget_is_dirty

    def reset_dirty(self) -> None:
        """Mark all fields as clean (Variables and record)."""
        if not hasattr(self, "_qtpie"):
            return  # Nothing to reset
        # Reset Variables
        self._qtpie.reset_dirty()
        # Reset record if present
        if self._qtpie._record is not None:
            self._qtpie._record.reset_dirty()

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        if not hasattr(self, "_qtpie"):
            return set()
        return self._qtpie.dirty_fields

    @property
    def is_valid(self) -> Observable[bool]:
        """Check if all fields are valid. Returns Observable[bool] for reactive bindings.

        Aggregates validity from Variables AND record (if present).
        """
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.widget_is_valid

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Errors: {field: {validator: [errors]}}."""
        if not hasattr(self, "_qtpie"):
            return {}
        return self._qtpie.validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Returns Observable[list[str]] for reactive bindings."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.validation_error_messages


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
        # Check for Variable[T, Dock[W]] descriptors
        elif isinstance(value, _VariableDescriptor) and value.dock_info is not None:
            config.variable_dock_fields.append(name)


def _detect_required_bindings_for_window(cls: type[Window[Any]]) -> None:
    """Detect bare Variable[T] annotations as required bindings."""
    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)


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
    record: Any | None = None,
    corners: dict[str, str] | None = None,
    dockStateKey: str | None = None,
    docksLocked: str | None = None,
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
    record: Any | None = None,
    stylesheet: str | None = None,
    corners: dict[str, str] | None = None,
    dockStateKey: str | None = None,
    docksLocked: str | None = None,
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
    # icon is resolved and stored for later application
    resolved_icon = _resolve_icon(icon)
    if resolved_icon is not None:
        kwargs["windowIcon"] = resolved_icon
    if stylesheet is not None:
        kwargs["styleSheet"] = stylesheet

    def decorator(target: type[W]) -> type[W]:
        config = target._qtpie_config
        config.layout = layout
        config.margins = margins
        config.auto_bind = auto_bind
        config.record_default = record
        config.widget_props = kwargs
        config.object_name = name
        config.css_classes = classes or []
        config.corners = corners
        config.dock_state_key = dockStateKey
        config.docks_locked = docksLocked

        # Auto-wrap async methods (e.g., async def on_close)
        from qtpie.async_wrap import wrap_async_methods

        wrap_async_methods(target)

        # Wrap __init__
        _wrap_init_for_window(target)

        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]


def _wrap_init_for_window(cls: type[Window[Any]]) -> None:
    """Wrap __init__ to add menus, create central widget, apply props, and call __setup__."""
    if cls._qtpie_config.init_wrapped:
        return

    original_init = cls.__init__
    config = cls._qtpie_config

    def wrapped_init(self: Window[Any], *args: Any, **kwargs: Any) -> None:
        # Set translation context to class name (used by t() markers)
        from qtpie.translations import set_translation_context

        set_translation_context(type(self).__name__)

        # Call original __init__
        original_init(self, *args, **kwargs)

        # Apply corner assignments before creating docks
        if config.corners:
            _apply_corner_assignments(self, config.corners)

        # Create list widget fields (list[QWidget] = new(bind="..."))
        from .widget import _create_list_widget_fields

        _create_list_widget_fields(self, config)  # type: ignore[arg-type]

        # Create dock widget fields (Dock[T] = new(dock="left", ...))
        _create_dock_fields(self, config)

        # Create Variable dock fields (Variable[T, Dock[W]] = new(..., dock="right", ...))
        _create_variable_dock_fields(self, config)

        # Apply widget properties (windowTitle="X" → setWindowTitle("X"))
        # Skip reactive props (with {}) and Translatable - they'll be handled by apply_reactive_widget_props
        from .bindings import is_format_string
        from .translations.translatable import Translatable
        from .utils.layouts import apply_object_name_and_classes, apply_widget_props

        def skip_reactive_or_translatable(prop_name: str, value: Any) -> bool:
            if isinstance(value, str) and is_format_string(value):
                return True
            if isinstance(value, Translatable):
                return True
            return False

        apply_widget_props(self, config.widget_props, skip_filter=skip_reactive_or_translatable)

        # Apply objectName and CSS classes
        apply_object_name_and_classes(
            self,
            config.object_name,
            config.css_classes,
            default_name=type(self).__name__,
        )

        # Connect signals for fields
        from qtpie.signals import connect_field_signals

        connect_field_signals(self, config.fields, _create_window_signal_expression_handler)

        # Auto-add QMenu fields to menu bar (in declaration order)
        # And collect non-menu QWidget fields for central widget
        non_menu_widgets: list[tuple[str, QWidget]] = []
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
            elif isinstance(instance, QWidget) and name not in ("central_widget", "_central_widget"):
                non_menu_widgets.append((name, instance))
            elif isinstance(instance, Variable) and instance.widget is not None and name not in ("central_widget", "_central_widget"):
                # Variable[T, W] - add the widget to layout
                non_menu_widgets.append((name, instance.widget))

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
        # Option 2: Create a container with layout for non-menu widgets
        elif non_menu_widgets and config.layout is not None:
            central = QWidget()
            qt_layout = create_layout(config.layout)
            if qt_layout is not None:
                central.setLayout(qt_layout)

                # Apply margins
                from .utils.layouts import apply_layout_margins

                apply_layout_margins(qt_layout, config.margins)

                # Add non-menu widgets to layout (in field definition order)
                from .variable import _VariableDescriptor

                for name, widget_instance in non_menu_widgets:
                    fld = config.fields.get(name)
                    label: str | None = None
                    label_translatable: Any = None
                    grid: GridPosition | None = None

                    # Check if this is a Variable[T, W] field - get label/grid from descriptor
                    descriptor = getattr(cls, name, None)
                    if isinstance(descriptor, _VariableDescriptor):
                        if descriptor.exclude_from_layout:
                            continue
                        raw_label = descriptor.label
                        if isinstance(raw_label, Translatable):
                            label = raw_label.resolve()
                            label_translatable = raw_label
                        else:
                            label = raw_label
                        grid = descriptor.grid  # type: ignore[assignment]
                    elif fld is not None:
                        # Regular QWidget field
                        if fld.exclude_from_layout:
                            continue
                        if isinstance(fld.label, Translatable):
                            label = fld.label.resolve()
                            label_translatable = fld.label
                        else:
                            label = fld.label
                        grid = fld.grid

                    _validate_layout_params(name, config.layout, label, grid)
                    _add_to_layout(qt_layout, widget_instance, config.layout, label, grid, label_translatable)

            self.setCentralWidget(central)

        # Ensure QtPieState exists BEFORE bindings run (binding code checks hasattr)
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)

        # Register validators from validate= parameter (before __setup__ so they're active)
        from .widget import _register_validators

        _register_validators(self, config)  # type: ignore[arg-type]

        # Set initial record value if provided via @window(record=...)
        if config.record_default is not None and hasattr(self, "record"):
            self.record = config.record_default

        # Call __setup__ hook (before bindings, so record can be initialized)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings using shared logic (after __setup__ so record is available)
        from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props
        from .bindings.expression import create_expression_binding

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
        content_widget = content_type(*fld.args, **fld.kwargs)

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
    """Set up bindings for dock fields (title=, icon=, visible=, floating=, groupSelectedIndex=)."""
    from .dock import Dock

    # Track which groups have had groupSelectedIndex binding set up
    groups_with_binding: set[str] = set()

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

        # groupSelectedIndex= binding: two-way sync between Variable and tab bar index
        if fld.dock_group_selected_index and fld.dock_group:
            group_name = fld.dock_group
            if group_name not in groups_with_binding:
                groups_with_binding.add(group_name)
                # Set up binding for this group's tab bar
                group_dock_names = groups.get(group_name, [])
                if group_dock_names:
                    _setup_group_selected_index_binding(window, fld.dock_group_selected_index, group_dock_names, created_docks)


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
) -> None:
    """Apply dock widget features (closable, floatable, movable, etc.)."""
    from qtpy.QtCore import Qt as QtCore

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
    binding: str,
    group_dock_names: list[str],
    created_docks: dict[str, Any],
) -> None:
    """Set up two-way binding between Variable and tab bar current index for a dock group."""
    from qtpy.QtWidgets import QTabBar

    from .variable import _get_variable_observable

    observable = _get_variable_observable(window, binding)
    if observable is None:
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

        # Variable -> Tab bar index
        def on_variable_change(index: int) -> None:
            if 0 <= index < tab_bar.count() and tab_bar.currentIndex() != index:
                tab_bar.setCurrentIndex(index)

        observable.on_change(on_variable_change)
        # Set initial state
        on_variable_change(observable.get())

        # Tab bar index -> Variable
        def on_tab_change(index: int) -> None:
            if observable.get() != index:
                observable.set(index)

        tab_bar.currentChanged.connect(on_tab_change)

    # Defer binding setup to ensure tab bar exists
    QTimer.singleShot(0, setup_binding)


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
    """Wrap Variable[T, Dock[W]] widgets in dock containers.

    For Variable[T, Dock[W]], the _VariableDescriptor creates the inner widget W
    and stores it on var.widget. This function wraps that widget in a QDockWidget
    and Dock wrapper, replacing var.widget with the Dock so users can access:
    - self._name.value -> T (the variable value)
    - self._name.widget -> Dock[W] (the dock wrapper)
    - self._name.widget.widget -> W (the inner widget)
    - self._name.widget.dock_widget -> QDockWidget
    """
    from .dock import Dock, parse_dock_area

    if not config.variable_dock_fields:
        return

    for name in config.variable_dock_fields:
        # Get the Variable from the instance
        var: Variable[Any, Any] = getattr(window, name)
        if var.widget is None:
            continue

        # Get the descriptor to access dock_info
        descriptor = getattr(type(window), name, None)
        if not isinstance(descriptor, _VariableDescriptor) or descriptor.dock_info is None:
            continue

        dock_info = descriptor.dock_info

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
