# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Window - QMainWindow with QtPie features."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NoReturn, cast, get_args, get_origin, overload

from observant import Observable
from qtpy.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QMainWindow,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from .layout import GridPosition, LayoutType
from .new_field import NewField
from .new_fields import new_fields
from .state import QtPieState, QtPieViewModel
from .variable import RecordVariable, Variable


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

    @property
    def view_model(self) -> QtPieViewModel:
        """Access only the Variable fields of this window."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.view_model

    @property
    def record_state(self: Window[T]) -> RecordVariable[T] | Variable[T]:
        """Access the RecordVariable/Variable wrapper for .is_dirty, .value, .observable."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        state = self._qtpie

        # If we have a RecordVariable already, return it
        if state._record is not None:
            return cast(RecordVariable[T], state._record)

        # Trigger access to create/register the record
        _ = self.record

        # Check if it's now a RecordVariable (auto-created)
        if state._record is not None:
            return cast(RecordVariable[T], state._record)

        # Otherwise it's an explicit Variable declaration
        if "record" in state.variables:
            return cast(Variable[T], state.variables["record"])

        raise TypeError(f"{type(self).__name__} has no record. Use Window[YourModel] to enable record access.")

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
    def validation_error_messages(self) -> list[str]:
        """Flat list of all error messages."""
        if not hasattr(self, "_qtpie"):
            return []
        return self._qtpie.validation_error_messages.get()


def _collect_fields(cls: type[Window[Any]]) -> None:
    """Collect NewField instances from class before they're processed."""
    config = cls._qtpie_config
    for name in getattr(cls, "__annotations__", {}):
        value = getattr(cls, name, None)
        if isinstance(value, NewField):
            config.fields[name] = value


@overload
def window[W: Window[Any]](cls: type[W]) -> type[W]: ...


@overload
def window(
    cls: None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    record: Any | None = None,
    **kwargs: Any,
) -> Callable[[type[Window[Any]]], type[Window[Any]]]: ...


def window[W: Window[Any]](
    cls: type[W] | None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    record: Any | None = None,
    stylesheet: str | None = None,
    **kwargs: Any,
) -> type[W] | Callable[[type[W]], type[W]]:
    """Decorator for Window classes.

    Usage:
        @window
        class MainWindow(Window):
            file_menu: FileMenu = new()

        @window(title="My App")
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
        stylesheet: Shorthand for styleSheet.
        **kwargs: Extra properties applied via setXXX() methods.
    """
    if title is not None:
        kwargs["windowTitle"] = title
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

        # Create list widget fields (list[QWidget] = new(bind="..."))
        from .widget import _create_list_widget_fields

        _create_list_widget_fields(self, config)  # type: ignore[arg-type]

        # Apply widget properties (windowTitle="X" → setWindowTitle("X"))
        for prop_name, value in config.widget_props.items():
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            setter = getattr(self, setter_name, None)
            if setter is not None and callable(setter):
                setter(value)

        # Set objectName
        if config.object_name is not None:
            self.setObjectName(config.object_name)
        else:
            self.setObjectName(type(self).__name__)

        # Apply CSS classes
        if config.css_classes:
            from .styles import set_classes

            set_classes(self, config.css_classes)

        # Connect signals for fields
        for fname, fld in config.fields.items():
            instance = getattr(self, fname, None)
            if instance is not None:
                for signal_name, handler in fld.signal_connections.items():
                    signal = getattr(instance, signal_name, None)
                    if signal is not None:
                        if isinstance(handler, str):
                            method = getattr(self, handler, None)
                            if method is not None:
                                signal.connect(method)
                        elif callable(handler):
                            signal.connect(handler)

        # Auto-add QMenu fields to menu bar (in declaration order)
        # And collect non-menu QWidget fields for central widget
        non_menu_widgets: list[tuple[str, QWidget]] = []
        for name in getattr(cls, "__annotations__", {}):
            if name.startswith("_"):
                continue
            instance = getattr(self, name, None)
            if isinstance(instance, QMenu):
                self.menuBar().addMenu(instance)
            elif isinstance(instance, QWidget) and name != "central_widget":
                non_menu_widgets.append((name, instance))
            elif isinstance(instance, Variable) and instance.widget is not None and name != "central_widget":
                # Variable[T, W] - add the widget to layout
                non_menu_widgets.append((name, instance.widget))

        # Set up central widget
        # Option 1: If there's an explicit central_widget field, use it
        explicit_central = getattr(self, "central_widget", None)
        # Handle Variable[T, W] as central_widget
        if isinstance(explicit_central, Variable) and explicit_central.widget is not None:
            explicit_central = explicit_central.widget
        if explicit_central is not None and isinstance(explicit_central, QWidget):
            self.setCentralWidget(explicit_central)
        # Option 2: Create a container with layout for non-menu widgets
        elif non_menu_widgets and config.layout is not None:
            central = QWidget()
            qt_layout = _create_layout(config.layout)
            if qt_layout is not None:
                central.setLayout(qt_layout)

                # Apply margins
                if config.margins is not None:
                    if isinstance(config.margins, int):
                        qt_layout.setContentsMargins(config.margins, config.margins, config.margins, config.margins)
                    else:
                        qt_layout.setContentsMargins(*config.margins)

                # Add non-menu widgets to layout (in field definition order)
                for name, widget_instance in non_menu_widgets:
                    fld = config.fields.get(name)
                    if fld is not None and fld.exclude_from_layout:
                        continue
                    label = fld.label if fld else None
                    grid = fld.grid if fld else None
                    _add_to_layout(qt_layout, widget_instance, config.layout, label, grid)

            self.setCentralWidget(central)

        # Ensure QtPieState exists BEFORE bindings run (binding code checks hasattr)
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)

        # Set initial record value if provided via @window(record=...)
        if config.record_default is not None and hasattr(self, "record"):
            self.record = config.record_default

        # Call __setup__ hook (before bindings, so record can be initialized)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings using shared logic (after __setup__ so record is available)
        from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props
        from .widget import _create_expression_binding

        apply_auto_bindings(self, config)
        apply_property_bindings(self, config, create_expression_binding_fn=_create_expression_binding)
        apply_reactive_widget_props(self, config)

        # Enable on_dirty_changed and on_valid_changed hooks
        self._qtpie.enable_dirty_hook()
        self._qtpie.enable_valid_hook()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_config.init_wrapped = True


def _create_layout(layout_type: LayoutType) -> QLayout | None:
    """Create a Qt layout based on type."""
    if layout_type == "vertical":
        return QVBoxLayout()
    elif layout_type == "horizontal":
        return QHBoxLayout()
    elif layout_type == "form":
        return QFormLayout()
    elif layout_type == "grid":
        return QGridLayout()
    return None


def _add_to_layout(
    layout: QLayout,
    widget_instance: QWidget,
    layout_type: LayoutType,
    label: str | None = None,
    grid: GridPosition | None = None,
) -> None:
    """Add a widget to the layout."""
    if layout_type in ("vertical", "horizontal"):
        layout.addWidget(widget_instance)  # type: ignore[union-attr]
    elif layout_type == "form":
        form_layout = cast(QFormLayout, layout)
        if label is not None:
            form_layout.addRow(label, widget_instance)
        else:
            form_layout.addRow(widget_instance)
    elif layout_type == "grid":
        grid_layout = cast(QGridLayout, layout)
        if grid is not None:
            row, col = grid[0], grid[1]
            rowspan = grid[2] if len(grid) > 2 else 1
            colspan = grid[3] if len(grid) > 3 else 1
            grid_layout.addWidget(widget_instance, row, col, rowspan, colspan)
        else:
            grid_layout.addWidget(widget_instance)
