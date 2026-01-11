# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Widget - QWidget container with automatic layout."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NoReturn, cast, get_args, get_origin, overload

from observant import Observable, ObservableDict, ObservableList, ObservableSet
from qtpy.QtWidgets import (
    QLayout,
    QWidget,
)

from .layout import GridPosition, LayoutType
from .new_field import NewField
from .new_fields import new_fields
from .signals import create_signal_expression_handler
from .state import QtPieState
from .utils.common import detect_required_bindings
from .utils.layouts import IconType, add_to_layout, create_layout, resolve_icon
from .variable import RecordVariable, Variable, _create_observable_for_type, _RequiredBindingDescriptor, _VariableDescriptor

# Re-export for backwards compatibility (window.py imports from here)
_resolve_icon = resolve_icon


class _QtPieConfig:
    """Class-level QtPie configuration."""

    __slots__ = ("layout", "margins", "fields", "variable_names", "init_wrapped", "record_type", "record_default", "auto_bind", "widget_props", "object_name", "css_classes", "required_bindings")

    def __init__(self) -> None:
        self.layout: LayoutType = "vertical"
        self.margins: int | tuple[int, int, int, int] | None = None
        self.fields: dict[str, NewField] = {}
        self.variable_names: list[str] = []
        self.init_wrapped: bool = False
        self.record_type: type[Any] | None = None  # T from Widget[T]
        self.record_default: Any | None = None  # Initial record value from @widget(record=...)
        self.auto_bind: bool = True  # Auto-bind QWidget fields to matching Variables/record fields
        self.widget_props: dict[str, Any] = {}  # Extra props like windowTitle -> setWindowTitle()
        self.object_name: str | None = None  # objectName for the widget
        self.css_classes: list[str] = []  # CSS classes for the widget
        self.required_bindings: set[str] = set()  # Bare Variable[T] fields that must be provided


class _RecordDescriptor[T]:
    """Descriptor for auto-created record on Widget[T].

    This is used when the user doesn't explicitly declare `record: Variable[T] = new(...)`.
    It lazily creates the record Variable on first access.
    """

    def __init__(self, record_type: type[T]) -> None:
        self._record_type = record_type

    def __get__(self, obj: Widget[T] | None, objtype: type | None = None) -> RecordVariable[T]:
        if obj is None:
            return self  # type: ignore[return-value]

        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        state = obj._qtpie
        if state._record is None:
            from observant import ObservableProxy

            try:
                wrapper = _create_observable_for_type(self._record_type, None)
            except ValueError:
                # Type requires constructor args - create proxy with None target
                # User must set it in __setup__ or later
                wrapper = ObservableProxy[T](None)  # type: ignore[arg-type]
            record_var = RecordVariable(cast(ObservableProxy[T], wrapper))
            state._record = record_var
            state.register_variable("record", record_var)
            # Subscribe record to widget-level aggregation if active
            state._subscribe_record_to_widget_dirty()
            state._subscribe_record_to_widget_valid()

        return state._record  # type: ignore[return-value]

    def __set__(self, obj: Widget[T], value: T | RecordVariable[T]) -> None:
        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        if isinstance(value, RecordVariable):
            obj._qtpie._record = value
            obj._qtpie.register_variable("record", value)  # type: ignore[arg-type]
        else:
            # Setting a value - always create a new ObservableProxy with the value
            # We can't just set state._record.value because that doesn't update
            # the field-level observables that ObservableProxy caches
            from observant import ObservableProxy

            wrapper = ObservableProxy(value)
            record_var = RecordVariable(wrapper)
            obj._qtpie._record = record_var
            obj._qtpie.register_variable("record", record_var)

        # Subscribe record to widget-level aggregation if active
        obj._qtpie._subscribe_record_to_widget_dirty()
        obj._qtpie._subscribe_record_to_widget_valid()


class Widget[T = None](QWidget):
    """QWidget container with automatic layout and QtPie features.

    Usage:
        @widget(layout="horizontal", margins=10)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click")

            def __setup__(self):
                self._button.clicked.connect(self._on_click)

    Or with defaults (vertical layout, no margins):
        @widget
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

    With a record type (model binding):
        @widget
        class PersonEditor(Widget[Person]):
            _name: QLineEdit = new()

            def __setup__(self):
                # self.record is Variable[Person]
                self.record.observable.name.set("Alice")
    """

    # Class-level config
    _qtpie_config: _QtPieConfig
    # Instance-level state (set during __init__)
    _qtpie: QtPieState

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Create fresh config for this subclass
        cls._qtpie_config = _QtPieConfig()

        # Extract T from Widget[T] if present
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is Widget:
                args = get_args(base)
                if args:
                    cls._qtpie_config.record_type = args[0]
                break

        # Check if user declared 'record' explicitly
        has_explicit_record = "record" in cls.__dict__

        # Collect fields and variable names
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, NewField):
                cls._qtpie_config.fields[name] = value
            elif isinstance(value, _VariableDescriptor):
                cls._qtpie_config.variable_names.append(name)

        # Detect bare Variable[T] annotations (no = new())
        # These are required bindings - must be provided by parent
        _detect_required_bindings(cls)

        # Apply @new_fields to handle non-Variable instantiation
        new_fields(cls)

        # Auto-create record descriptor if Widget[T] but no explicit record
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            # Create a descriptor that will lazily create the record
            cls.record = _RecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    if TYPE_CHECKING:
        # Lie to pyright: say record returns T for field autocomplete
        # Runtime: _RecordDescriptor returns RecordVariable which forwards via __getattr__
        @property
        def record(self) -> T: ...
        @record.setter
        def record(self, value: T) -> None: ...

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

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    def on_dirty_changed(self, is_dirty: bool) -> None:
        """Called when dirty state transitions (clean→dirty or dirty→clean).

        Override this to react to dirty state changes, e.g., enable/disable save button.

        Example:
            @widget
            class MyWidget(Widget):
                @override
                def on_dirty_changed(self, is_dirty: bool) -> None:
                    self._save_btn.setEnabled(is_dirty)
        """
        pass

    def on_valid_changed(self, is_valid: bool) -> None:
        """Called when validity state transitions (valid→invalid or invalid→valid).

        Override this to react to validation changes, e.g., show/hide error messages.

        Example:
            @widget
            class MyWidget(Widget):
                @override
                def on_valid_changed(self, is_valid: bool) -> None:
                    self._submit_btn.setEnabled(is_valid)
        """
        pass

    async def on_close(self) -> None:
        """Async hook called when the widget is closing.

        Override this to perform async cleanup before the widget closes.
        The close event is automatically accepted after this completes.

        Example:
            @widget
            class MyWidget(Widget):
                @override
                async def on_close(self) -> None:
                    await self.save_data()
        """
        pass

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Check that @widget decorator was applied."""
        if not self._qtpie_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @widget. Add @widget above your class definition.")
        # This should never run - @widget replaces __init__
        super().__init__(*args, **kwargs)  # pragma: no cover

    if not TYPE_CHECKING:
        # Runtime-only: provide better error messages for .record access
        # Hidden from pyright so it doesn't disable attribute checking
        def __getattr__(self, name: str) -> NoReturn:
            """Handle attribute access for special cases."""
            if name == "record":
                raise TypeError(f"{type(self).__name__} has no record type. Use Widget[YourModel] to enable record access.")
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


@overload
def widget[W: Widget[Any]](cls: type[W]) -> type[W]: ...


@overload
def widget[W: Widget[Any]](
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
    **kwargs: Any,
) -> Callable[[type[W]], type[W]]: ...


def widget[W: Widget[Any]](
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
    **kwargs: Any,
) -> type[W] | Callable[[type[W]], type[W]]:
    """Decorator to configure Widget layout.

    Usage:
        @widget
        class MyWidget(Widget):
            ...

        @widget(layout="horizontal", margins=10)
        class MyWidget(Widget):
            ...

        @widget(name="my-widget", classes=["card", "primary"])
        class MyWidget(Widget):
            # Sets objectName and CSS classes
            ...

        @widget(auto_bind=False)
        class MyWidget(Widget[Person]):
            # No auto-binding, must use bind="field" explicitly
            ...

        @widget(title="My App", icon=":/icons/app.png")
        class MyWidget(Widget):
            # Extra kwargs become setXXX() calls on the widget
            ...

    Args:
        layout: "vertical" | "horizontal" | "form" | "grid" | None
                Default is "vertical". None disables auto-layout.
        margins: int | tuple[int, int, int, int] | None
                 Layout margins. int applies to all sides.
        auto_bind: If True (default), QWidget fields are automatically bound
                   to matching Variables or record fields.
        name: Set the widget's objectName.
        classes: List of CSS classes to apply to the widget.
        title: Shorthand for windowTitle.
        icon: Window icon. Accepts str path (file or Qt resource ":/..."),
              QIcon, QPixmap, or QStyle.StandardPixmap.
        stylesheet: Shorthand for styleSheet.
        **kwargs: Extra properties applied via setXXX() methods.
                  e.g., windowTitle="Foo" calls self.setWindowTitle("Foo")
    """
    # title is an alias for windowTitle
    if title is not None:
        kwargs["windowTitle"] = title
    # icon is resolved and stored for later application
    resolved_icon = _resolve_icon(icon)
    if resolved_icon is not None:
        kwargs["windowIcon"] = resolved_icon
    # stylesheet is an alias for styleSheet
    if stylesheet is not None:
        kwargs["styleSheet"] = stylesheet

    def decorator(target: type[W]) -> type[W]:
        # Store layout config
        target._qtpie_config.layout = layout
        target._qtpie_config.margins = margins
        target._qtpie_config.auto_bind = auto_bind
        target._qtpie_config.record_default = record
        target._qtpie_config.widget_props = kwargs
        target._qtpie_config.object_name = name
        target._qtpie_config.css_classes = classes or []

        # Auto-wrap async methods (e.g., async def closeEvent)
        from qtpie.async_wrap import wrap_async_methods

        wrap_async_methods(target)

        # Wrap __init__ to set up layout
        _wrap_init_for_layout(target)

        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]


def _wrap_init_for_layout(cls: type[Widget[Any]]) -> None:
    """Wrap __init__ to create layout, add child widgets, and call __setup__."""
    if cls._qtpie_config.init_wrapped:
        return

    original_init = cls.__init__

    # Capture config at decoration time
    config = cls._qtpie_config

    def wrapped_init(self: Widget[Any], *args: Any, **kwargs: Any) -> None:
        # Set translation context to class name (used by t() markers)
        from qtpie.translations import set_translation_context

        set_translation_context(type(self).__name__)

        # Call original __init__ (which instantiates fields via new_fields)
        original_init(self, *args, **kwargs)

        # Create list widget fields (list[QWidget] = new(bind="..."))
        # This must happen before layout so they're included in the correct order
        _create_list_widget_fields(self, config)

        # Apply widget properties (windowTitle="X" → setWindowTitle("X"))
        _apply_widget_props(self, config)

        # Set up layout if configured
        if config.layout is not None:
            qt_layout = create_layout(config.layout)
            if qt_layout is not None:
                self.setLayout(qt_layout)

                # Apply margins
                from .utils.layouts import apply_layout_margins

                apply_layout_margins(qt_layout, config.margins)

                # Add child widgets to layout (in field definition order)
                # Use __annotations__ to preserve order across QWidget and Variable[T, W] fields
                for name in getattr(cls, "__annotations__", {}):
                    # Check if it's a QWidget field
                    if name in config.fields:
                        field = config.fields[name]
                        if field.exclude_from_layout:
                            continue
                        widget_instance = getattr(self, name, None)
                        if widget_instance is not None and isinstance(widget_instance, QWidget):
                            # Resolve Translatable labels (keep original for retranslation)
                            from qtpie.translations.translatable import Translatable

                            label_translatable = field.label if isinstance(field.label, Translatable) else None
                            label = field.label.resolve() if isinstance(field.label, Translatable) else field.label
                            _validate_layout_params(name, config.layout, label, field.grid)
                            _add_to_layout(qt_layout, widget_instance, config.layout, label, field.grid, label_translatable)
                    # Check if it's a Variable with a widget
                    elif name in config.variable_names:
                        var = getattr(self, name, None)
                        if isinstance(var, Variable) and var.widget is not None:
                            # Get label/grid/exclude_from_layout from the descriptor
                            descriptor: Any = getattr(cls, name, None)
                            var_label: str | None = None
                            var_label_translatable: Any = None
                            grid: GridPosition | None = None
                            if isinstance(descriptor, _VariableDescriptor):
                                if descriptor.exclude_from_layout:
                                    continue
                                # Resolve Translatable labels (keep original for retranslation)
                                from qtpie.translations.translatable import Translatable

                                raw_label = descriptor.label
                                if isinstance(raw_label, Translatable):
                                    var_label = raw_label.resolve()
                                    var_label_translatable = raw_label
                                else:
                                    var_label = raw_label
                                grid = descriptor.grid  # type: ignore[assignment]
                            _validate_layout_params(name, config.layout, var_label, grid)
                            _add_to_layout(qt_layout, var.widget, config.layout, var_label, grid, var_label_translatable)

        # Connect signals (clicked="on_clicked" or clicked=lambda: ...)
        _connect_signals(self, config)

        # Register validators from validate= parameter (before __setup__ so they're active)
        _register_validators(self, config)

        # Set initial record value if provided via @widget(record=...)
        if config.record_default is not None and hasattr(self, "record"):
            self.record = config.record_default

        # Call __setup__ hook if defined (before bindings, so record can be initialized)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings (after __setup__ so record is available)
        # BUT: if we have required bindings that haven't been set up yet (provided by parent),
        # defer binding application until after the parent applies Variable bindings
        from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props
        from .bindings.expression import create_expression_binding

        if _has_unset_required_bindings(self, config):
            self._qtpie_pending_auto_bindings = True  # type: ignore[attr-defined]
        else:
            apply_auto_bindings(self, config)

            # Apply property bindings (visible="_is_visible", enabled="{_count > 0}", etc.)
            apply_property_bindings(self, config, create_expression_binding_fn=create_expression_binding)

            # Apply reactive widget props from @widget decorator (windowTitle="{title}", etc.)
            apply_reactive_widget_props(self, config)

        # Enable on_dirty_changed and on_valid_changed hooks (subscribes to future Variable changes)
        state = getattr(self, "_qtpie", None)
        if not isinstance(state, QtPieState):
            state = QtPieState(self)
            self._qtpie = state  # type: ignore[assignment]
        state.enable_dirty_hook()
        state.enable_valid_hook()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_config.init_wrapped = True


def _has_unset_required_bindings(widget: Widget[Any], config: _QtPieConfig) -> bool:
    """Check if the widget has required bindings that haven't been set up yet.

    Returns True if any required Variable binding is missing (not yet provided by parent).
    """
    if not config.required_bindings:
        return False

    # Check if _qtpie state exists and has the required Variables
    state = getattr(widget, "_qtpie", None)
    if state is None:
        # No state yet - all required bindings are unset
        return True

    # Check each required binding
    for name in config.required_bindings:
        if name not in state.variables:
            return True

    return False


def _validate_layout_params(
    field_name: str,
    layout_type: LayoutType,
    label: str | None,
    grid: GridPosition | None,
) -> None:
    """Validate that required layout params are provided.

    Raises:
        TypeError: If form layout is used without label=, or grid layout without grid=.
    """
    if layout_type == "form" and label is None:
        raise TypeError(f"Field '{field_name}' requires label= for form layout. Use: new(..., label=\"Field Label\")")
    if layout_type == "grid" and grid is None:
        raise TypeError(f"Field '{field_name}' requires grid= for grid layout. Use: new(..., grid=(row, col)) or new(..., grid=(row, col, rowspan, colspan))")


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


def _apply_widget_props(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Apply widget properties from @widget decorator kwargs.

    For each prop like windowTitle="X", calls widget.setWindowTitle("X").
    Also applies name and classes from the decorator.

    Reactive props (with {}) are skipped here and applied later by _apply_reactive_widget_props.
    """
    from .bindings import is_format_string
    from .utils.layouts import apply_object_name_and_classes, apply_widget_props

    # Apply objectName and CSS classes
    apply_object_name_and_classes(
        widget,
        config.object_name,
        config.css_classes,
        default_name=type(widget).__name__,
    )

    # Apply widget properties, skipping reactive ones
    def skip_reactive(prop_name: str, value: Any) -> bool:
        return isinstance(value, str) and is_format_string(value)

    apply_widget_props(widget, config.widget_props, skip_filter=skip_reactive, strict=True)


def _register_validators(widget: Widget[Any], config: _QtPieConfig) -> None:  # pyright: ignore[reportUnknownArgumentType]
    """Register validators defined via validate= parameter on Variables.

    Supports multiple formats:
    - validate="method_name" → single string method
    - validate=callable → single callable
    - validate=["method1", "method2"] → list of method names
    - validate=[callable1, callable2] → list of callables
    - validate=[("custom_name", "method")] → tuple with explicit validator name
    - validate=[("custom_name", callable)] → tuple with explicit name and callable
    """
    from .variable import Variable, _VariableDescriptor

    cls = type(widget)

    for name in config.variable_names:
        # Get the descriptor to access validators list
        descriptor = getattr(cls, name, None)
        if not isinstance(descriptor, _VariableDescriptor):
            continue

        if not descriptor.validators:
            continue

        # Access the Variable instance to register validators
        var = getattr(widget, name, None)
        if not isinstance(var, Variable):
            continue

        # Normalize validators to a list
        raw_validators: Any = descriptor.validators
        validators_list: list[Any] = cast(list[Any], raw_validators) if isinstance(raw_validators, list) else [raw_validators]

        for spec in validators_list:
            validator_name: str
            validator_fn: Callable[..., Any]

            if isinstance(spec, tuple) and len(spec) == 2:  # pyright: ignore[reportUnknownArgumentType]
                # ("name", "method") or ("name", callable)
                name_part = str(spec[0])  # pyright: ignore[reportUnknownArgumentType]
                fn_part = cast(Any, spec[1])
                if isinstance(fn_part, str):
                    fn = getattr(widget, fn_part, None)
                    if fn is None or not callable(fn):
                        raise AttributeError(f"Validator method '{fn_part}' not found on {cls.__name__}")
                    validator_name = name_part
                    validator_fn = fn
                elif callable(fn_part):  # pyright: ignore[reportUnknownArgumentType]
                    validator_name = name_part
                    validator_fn = fn_part
                else:
                    raise TypeError(f"Invalid validator spec: {spec}")
            elif isinstance(spec, str):
                # "method_name" → name defaults to method name
                validator_name = spec
                fn = getattr(widget, spec, None)
                if fn is None or not callable(fn):
                    raise AttributeError(f"Validator method '{spec}' not found on {cls.__name__}")
                validator_fn = fn
            elif callable(spec):  # pyright: ignore[reportUnknownArgumentType]
                # callable → name from __name__ attribute
                validator_name = getattr(spec, "__name__", str(spec))
                validator_fn = spec
            else:
                raise TypeError(f"Invalid validator spec: {spec}")

            var.add_validator(validator_name, validator_fn)  # pyright: ignore[reportUnknownMemberType]


def _create_list_widget_fields(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Create WidgetRepeater/SetWidgetRepeater instances for list[QWidget]/set[QWidget] fields.

    For each field with annotation like `list[QLabel]` or `set[QLabel]` and `bind="some_path"`,
    resolves the bind path to get the source collection and creates an appropriate repeater.

    The source can be:
    - Variable[list[T]/set[T]] → uses its ObservableList/ObservableSet (reactive)
    - ObservableList/ObservableSet directly → uses it (reactive)
    - Observable[list/set] → wraps value in ObservableList/ObservableSet (one-time)
    - Plain list/set → wraps in ObservableList/ObservableSet (one-time)
    """
    from observant import Observable, ObservableDict, ObservableList, ObservableSet

    from .bindings import resolve_binding_source
    from .set_widget_repeater import SetWidgetRepeater
    from .variable import Variable
    from .widget_repeater import WidgetRepeater

    for name, field in config.fields.items():
        if not field.is_list_widget:
            continue

        # list_widget_type is always set when is_list_widget is True
        assert field.list_widget_type is not None

        if field.bind is None:
            raise ValueError(f"list[{field.list_widget_type.__name__}] field '{name}' requires bind='...'")

        # Resolve the bind path to get the source
        source = resolve_binding_source(widget, field.bind)

        # Convert source to ObservableList
        obs_list: ObservableList[Any]
        item_type: type | None = None

        # If source is None, check if it's a plain list/dict attribute
        if source is None:
            # Try to get raw attribute (handles plain list/dict fields)
            bind_path = field.bind.lstrip("_")
            raw_attr = None
            if hasattr(widget, bind_path):
                raw_attr = getattr(widget, bind_path)
            elif hasattr(widget, f"_{bind_path}"):
                raw_attr = getattr(widget, f"_{bind_path}")

            if isinstance(raw_attr, list):
                # Wrap plain list in ObservableList
                obs_list = ObservableList(cast(list[Any], raw_attr))
                setattr(widget, field.bind, obs_list)  # Replace with observable version
                # Skip to repeater creation
                plain_bind_expr: Any = field.list_format if field.list_format is not None else "{#self}"
                repeater = WidgetRepeater(
                    observable_list=obs_list,
                    item_type=item_type,
                    widget_type=field.list_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=plain_bind_expr,
                    sort=field.sort,
                    object_name=field.object_name or name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, repeater)
                continue
            elif isinstance(raw_attr, dict):
                from .dict_widget_repeater import DictWidgetRepeater

                obs_dict: ObservableDict[Any, Any] = ObservableDict(cast(dict[Any, Any], raw_attr))
                setattr(widget, field.bind, obs_dict)
                bind_expr_dict: Any = field.list_format if field.list_format is not None else "{#key} = {#value}"
                dict_repeater: DictWidgetRepeater[Any, Any] = DictWidgetRepeater(
                    observable_dict=obs_dict,
                    key_type=None,
                    value_type=None,
                    widget_type=field.list_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=bind_expr_dict,
                    sort=field.sort,
                    object_name=field.object_name or name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, dict_repeater)
                continue
            else:
                raise ValueError(f"Could not resolve bind path '{field.bind}' for field '{name}'")

        # Get the underlying observable from Variable or use source directly
        wrapper: Any = None
        if isinstance(source, Variable):
            wrapper = source.observable
        else:
            wrapper = source

        # Handle ObservableDict -> DictWidgetRepeater
        if isinstance(wrapper, ObservableDict):
            from .dict_widget_repeater import DictWidgetRepeater

            # Determine bind expression: use format= if provided, else "{#key} = {#value}"
            bind_expr_dict: Any = field.list_format if field.list_format is not None else "{#key} = {#value}"

            dict_repeater: DictWidgetRepeater[Any, Any] = DictWidgetRepeater(
                observable_dict=wrapper,  # pyright: ignore[reportUnknownArgumentType]
                key_type=None,  # Could extract from type hints if needed
                value_type=None,
                widget_type=field.list_widget_type,  # pyright: ignore[reportArgumentType]
                widget_args=field.args,
                widget_kwargs=field.kwargs,
                widget_props=field.widget_props,
                bind_expr=bind_expr_dict,
                sort=field.sort,
                object_name=field.object_name or name,
                css_classes=field.css_classes,
                signal_connections=field.signal_connections,
                parent_widget=widget,
            )
            setattr(widget, name, dict_repeater)
            continue

        # Handle ObservableList -> WidgetRepeater
        obs_list: ObservableList[Any]
        if isinstance(wrapper, ObservableList):
            obs_list = wrapper  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(wrapper, Observable):
            # Observable containing a list - create synced ObservableList
            val: Any = wrapper.get()  # pyright: ignore[reportUnknownVariableType]
            if isinstance(val, list):
                obs_list = ObservableList(cast(list[Any], val))

                # Sync: when Observable changes, update ObservableList
                def make_sync(obs: Observable[Any], target: ObservableList[Any]) -> None:
                    def on_source_change(new_val: Any) -> None:
                        if isinstance(new_val, list):
                            target.clear()
                            target.extend(cast(list[Any], new_val))

                    obs.on_change(on_source_change)

                make_sync(wrapper, obs_list)  # pyright: ignore[reportUnknownArgumentType]
            else:
                raise TypeError(f"bind='{field.bind}' resolved to Observable[{type(val).__name__}], expected list or dict")  # pyright: ignore[reportUnknownArgumentType]
        else:
            raise TypeError(f"bind='{field.bind}' resolved to {type(wrapper).__name__}, expected Variable[list[...]], Variable[dict[...]], ObservableList, or ObservableDict")

        # Determine bind expression: use format= if provided, else "{#self}"
        bind_expr: str | Callable[[Any], str] = field.list_format if field.list_format is not None else "{#self}"

        # Create WidgetRepeater
        repeater = WidgetRepeater(
            observable_list=obs_list,
            item_type=item_type,  # Could extract from source type hints if needed
            widget_type=field.list_widget_type,
            widget_args=field.args,
            widget_kwargs=field.kwargs,
            widget_props=field.widget_props,
            bind_expr=bind_expr,
            sort=field.sort,
            object_name=field.object_name or name,
            css_classes=field.css_classes,
            signal_connections=field.signal_connections,
            parent_widget=widget,
        )

        # Store the repeater on the widget
        setattr(widget, name, repeater)

    # Handle set[QWidget] fields
    for name, field in config.fields.items():
        if not field.is_set_widget:
            continue

        # set_widget_type is always set when is_set_widget is True
        assert field.set_widget_type is not None

        if field.bind is None:
            raise ValueError(f"set[{field.set_widget_type.__name__}] field '{name}' requires bind='...'")

        # Resolve the bind path to get the source
        source = resolve_binding_source(widget, field.bind)

        # Convert source to ObservableSet
        obs_set: ObservableSet[Any]
        item_type: type | None = None

        # If source is None, check if it's a plain set attribute
        if source is None:
            # Try to get raw attribute (handles plain set fields)
            bind_path = field.bind.lstrip("_")
            raw_attr = None
            if hasattr(widget, bind_path):
                raw_attr = getattr(widget, bind_path)
            elif hasattr(widget, f"_{bind_path}"):
                raw_attr = getattr(widget, f"_{bind_path}")

            if isinstance(raw_attr, set):
                # Wrap plain set in ObservableSet
                obs_set = ObservableSet(cast(set[Any], raw_attr))
                setattr(widget, field.bind, obs_set)  # Replace with observable version
                # Skip to repeater creation
                plain_bind_expr: Any = field.set_format if field.set_format is not None else "{#self}"
                set_repeater = SetWidgetRepeater(
                    observable_set=obs_set,
                    item_type=item_type,
                    widget_type=field.set_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=plain_bind_expr,
                    sort=field.sort,
                    object_name=field.object_name or name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, set_repeater)
                continue
            else:
                raise ValueError(f"Could not resolve bind path '{field.bind}' for field '{name}'")

        # Get the underlying observable from Variable or use source directly
        wrapper: Any = None
        if isinstance(source, Variable):
            wrapper = source.observable
        else:
            wrapper = source

        # Handle ObservableSet -> SetWidgetRepeater
        if isinstance(wrapper, ObservableSet):
            # Determine bind expression: use format= if provided, else "{#self}"
            set_bind_expr: Any = field.set_format if field.set_format is not None else "{#self}"

            set_repeater: SetWidgetRepeater[Any] = SetWidgetRepeater(
                observable_set=wrapper,  # pyright: ignore[reportUnknownArgumentType]
                item_type=None,  # Could extract from type hints if needed
                widget_type=field.set_widget_type,
                widget_args=field.args,
                widget_kwargs=field.kwargs,
                widget_props=field.widget_props,
                bind_expr=set_bind_expr,
                sort=field.sort,
                object_name=field.object_name or name,
                css_classes=field.css_classes,
                signal_connections=field.signal_connections,
                parent_widget=widget,
            )
            setattr(widget, name, set_repeater)
            continue

        # Handle Observable containing a set - create synced ObservableSet
        if isinstance(wrapper, Observable):
            val: Any = wrapper.get()  # pyright: ignore[reportUnknownVariableType]
            if isinstance(val, set):
                obs_set = ObservableSet(cast(set[Any], val))

                # Sync: when Observable changes, update ObservableSet
                def make_set_sync(obs: Observable[Any], target: ObservableSet[Any]) -> None:
                    def on_source_change(new_val: Any) -> None:
                        if isinstance(new_val, set):
                            target.clear()
                            target.update(cast(set[Any], new_val))

                    obs.on_change(on_source_change)

                make_set_sync(wrapper, obs_set)  # pyright: ignore[reportUnknownArgumentType]

                # Determine bind expression
                set_bind_expr = field.set_format if field.set_format is not None else "{#self}"

                set_repeater = SetWidgetRepeater(
                    observable_set=obs_set,
                    item_type=item_type,
                    widget_type=field.set_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=set_bind_expr,
                    sort=field.sort,
                    object_name=field.object_name or name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, set_repeater)
                continue
            else:
                raise TypeError(f"bind='{field.bind}' resolved to Observable[{type(val).__name__}], expected set")  # pyright: ignore[reportUnknownArgumentType]
        else:
            raise TypeError(f"bind='{field.bind}' resolved to {type(wrapper).__name__}, expected Variable[set[...]] or ObservableSet")


def _connect_signals(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Connect signals declared in new() to handlers."""
    from qtpie.signals import connect_field_signals

    connect_field_signals(widget, config.fields, _create_signal_expression_handler)


def _create_signal_expression_handler(widget: Widget[Any], expression: str) -> Callable[..., Any]:
    """Create a signal handler from an expression string like "{my_signal(123)}"."""
    return create_signal_expression_handler(widget, expression, ["#widget", "#self"])


def _detect_required_bindings(cls: type[Widget[Any]]) -> None:
    """Detect bare Variable[T] annotations as required bindings."""
    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)
