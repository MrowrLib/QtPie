# pyright: reportPrivateUsage=false
"""Widget - QWidget container with automatic layout."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin, overload

from observant import Observable
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from .layout import GridPosition, LayoutType
from .new_field import NewField
from .new_fields import new_fields
from .variable import RecordVariable, Variable, _create_observable_for_type, _VariableDescriptor


class _QtPieConfig:
    """Class-level QtPie configuration."""

    __slots__ = ("layout", "margins", "fields", "variable_names", "init_wrapped", "record_type", "auto_bind", "widget_props")

    def __init__(self) -> None:
        self.layout: LayoutType = "vertical"
        self.margins: int | tuple[int, int, int, int] | None = None
        self.fields: dict[str, NewField] = {}
        self.variable_names: list[str] = []
        self.init_wrapped: bool = False
        self.record_type: type[Any] | None = None  # T from Widget[T]
        self.auto_bind: bool = True  # Auto-bind QWidget fields to matching Variables/record fields
        self.widget_props: dict[str, Any] = {}  # Extra props like windowTitle -> setWindowTitle()


class QtPieState:
    """Instance-level QtPie state."""

    __slots__ = (
        "variables",
        "_view_model",
        "_widget",
        "_was_dirty",
        "_check_dirty",
        "_record",
        "_was_valid",
        "_check_valid",
        "_aggregated_validation_errors",
    )

    def __init__(self, widget: Widget[Any]) -> None:
        self._widget = widget
        self.variables: dict[str, Variable[Any]] = {}
        self._view_model: QtPieViewModel | None = None
        self._was_dirty: bool = False
        self._check_dirty: Callable[[bool], None] | None = None
        self._record: RecordVariable[Any] | None = None
        self._was_valid: bool = True
        self._check_valid: Callable[[bool], None] | None = None
        # Aggregated validation_error_messages (lazy-created)
        self._aggregated_validation_errors: Observable[list[str]] | None = None

    @property
    def view_model(self) -> QtPieViewModel:
        if self._view_model is None:
            self._view_model = QtPieViewModel(self)
        return self._view_model

    @property
    def is_dirty(self) -> bool:
        """Check if any Variable has changed from its clean state."""
        return any(var.is_dirty for var in self.variables.values())

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        return {name for name, var in self.variables.items() if var.is_dirty}

    def reset_dirty(self) -> None:
        """Mark all Variables as clean."""
        for var in self.variables.values():
            var.reset_dirty()

    def enable_dirty_hook(self) -> None:
        """Enable the on_dirty_changed hook (called after __setup__)."""

        def check_dirty_transition(_: bool) -> None:
            is_now_dirty = self.is_dirty
            if self._was_dirty != is_now_dirty:
                self._was_dirty = is_now_dirty
                hook = getattr(self._widget, "on_dirty_changed", None)
                if hook is not None:
                    hook(is_now_dirty)

        self._check_dirty = check_dirty_transition

        # Subscribe to each variable's is_dirty (including those registered before this)
        for var in self.variables.values():
            var.is_dirty.on_change(check_dirty_transition)

    def register_variable(self, name: str, var: Variable[Any] | RecordVariable[Any]) -> None:
        """Register a Variable and wire up dirty/valid hooks if enabled."""
        self.variables[name] = var  # type: ignore[assignment]
        if self._check_dirty is not None:
            var.is_dirty.on_change(self._check_dirty)
        if self._check_valid is not None:
            var.is_valid.on_change(self._check_valid)
        # Subscribe to validation aggregation if active
        self._subscribe_variable_to_aggregation(var)  # type: ignore[arg-type]

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    @property
    def is_valid(self) -> bool:
        """Check if all Variables are valid."""
        return all(var.is_valid.get() for var in self.variables.values())

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Get validation errors: {field: {validator: [errors]}}."""
        return {
            name: var.validation_errors.get()
            for name, var in self.variables.items()
            if var.validation_error_messages.get()  # only include fields with errors
        }

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Aggregated validation errors from all Variables. Reactive/bindable."""
        if self._aggregated_validation_errors is None:
            self._aggregated_validation_errors = Observable[list[str]]([], dirty_tracking=False, validation=False)
            self._setup_validation_aggregation()
        return self._aggregated_validation_errors

    def _setup_validation_aggregation(self) -> None:
        """Subscribe to all Variables' validation_error_messages and aggregate."""

        def update_aggregated(_: Any = None) -> None:
            msgs: list[str] = []
            for var in self.variables.values():
                msgs.extend(var.validation_error_messages.get())
            assert self._aggregated_validation_errors is not None
            self._aggregated_validation_errors.set(msgs)

        # Subscribe to existing variables
        for var in self.variables.values():
            var.validation_error_messages.on_change(update_aggregated)

        # Initial update
        update_aggregated()

    def _subscribe_variable_to_aggregation(self, var: Variable[Any]) -> None:
        """Subscribe a new variable to the aggregation (if active)."""
        if self._aggregated_validation_errors is not None:

            def update_aggregated(_: Any = None) -> None:
                msgs: list[str] = []
                for v in self.variables.values():
                    msgs.extend(v.validation_error_messages.get())
                assert self._aggregated_validation_errors is not None
                self._aggregated_validation_errors.set(msgs)

            var.validation_error_messages.on_change(update_aggregated)
            update_aggregated()

    def enable_valid_hook(self) -> None:
        """Enable the on_valid_changed hook (called after __setup__)."""

        def check_valid_transition(_: bool) -> None:
            is_now_valid = self.is_valid
            if self._was_valid != is_now_valid:
                self._was_valid = is_now_valid
                hook = getattr(self._widget, "on_valid_changed", None)
                if hook is not None:
                    hook(is_now_valid)

        self._check_valid = check_valid_transition

        # Sync _was_valid with current state (after __setup__ ran and added validators)
        self._was_valid = self.is_valid

        # Subscribe to each variable's is_valid
        for var in self.variables.values():
            var.is_valid.on_change(check_valid_transition)

    def add_validator(self, field: str, name: str, validator: Callable[[Any], None | str | list[str]]) -> None:
        """Add named validator to a specific field."""
        # Check if field is already in variables
        if field in self.variables:
            self.variables[field].add_validator(name, validator)
            return

        # Try to trigger variable creation by accessing it on the widget
        # This handles lazy Variable creation via descriptors
        if hasattr(self._widget, field):
            attr = getattr(self._widget, field)
            # After access, check if it's now registered
            if field in self.variables:
                self.variables[field].add_validator(name, validator)
                return
            # If it's a Variable directly (shouldn't happen but handle it)
            if hasattr(attr, "add_validator"):
                attr.add_validator(name, validator)
                return

        # Check if it's a record field
        # First, try to trigger record creation by accessing widget.record
        if self._record is None and hasattr(self._widget, "record"):
            try:
                _ = self._widget.record  # Trigger record creation
            except TypeError:
                pass  # No record type configured

        if self._record is not None:
            try:
                field_obs = getattr(self._record.observable, field)
                field_obs.add_validator(name, validator)
                return
            except AttributeError:
                pass

        raise KeyError(f"No field named '{field}' found in widget")


class QtPieViewModel:
    """Auto-generated view model containing only Variable fields."""

    __slots__ = ("_state",)

    def __init__(self, state: QtPieState) -> None:
        self._state = state

    def __getattr__(self, name: str) -> Variable[Any]:
        # Get variable names from class config
        if name in type(self._state._widget)._qtpie_config.variable_names:
            return getattr(self._state._widget, name)
        raise AttributeError(f"ViewModel has no attribute {name!r}")

    @property
    def is_dirty(self) -> bool:
        """Check if any Variable has changed from its clean state."""
        return self._state.is_dirty

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        return self._state.dirty_fields

    def reset_dirty(self) -> None:
        """Mark all Variables as clean."""
        self._state.reset_dirty()

    @property
    def is_valid(self) -> bool:
        """Check if all Variables are valid."""
        return self._state.is_valid

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Errors: {field: {validator: [errors]}}."""
        return self._state.validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Aggregated validation errors. Reactive/bindable."""
        return self._state.validation_error_messages


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

        return state._record  # type: ignore[return-value]

    def __set__(self, obj: Widget[T], value: T | RecordVariable[T]) -> None:
        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        if isinstance(value, RecordVariable):
            obj._qtpie._record = value
            obj._qtpie.register_variable("record", value)  # type: ignore[arg-type]
        else:
            # Setting a value - create proper ObservableProxy wrapper
            state = obj._qtpie
            from observant import ObservableProxy

            # Check if record doesn't exist yet or has None target
            if state._record is None or state._record.value is None:
                # Create proper ObservableProxy with the value
                wrapper = ObservableProxy(value)
                record_var = RecordVariable(wrapper)
                state._record = record_var
                state.register_variable("record", record_var)
            else:
                # Normal case - record exists, set value directly
                state._record.value = value


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

        # Apply @new_fields to handle non-Variable instantiation
        new_fields(cls)

        # Auto-create record descriptor if Widget[T] but no explicit record
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            # Create a descriptor that will lazily create the record
            cls.record = _RecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    @property
    def view_model(self) -> QtPieViewModel:
        """Access only the Variable fields of this widget."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.view_model

    @property
    def record_state(self: Widget[T]) -> RecordVariable[T] | Variable[T]:
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

        raise TypeError(f"{type(self).__name__} has no record. Use Widget[YourModel] to enable record access.")

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
    def is_valid(self) -> bool:
        """Check if all fields are valid."""
        if not hasattr(self, "_qtpie"):
            return True
        return self._qtpie.is_valid

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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Check that @widget decorator was applied."""
        if not self._qtpie_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @widget. Add @widget above your class definition.")
        # This should never run - @widget replaces __init__
        super().__init__(*args, **kwargs)  # pragma: no cover

    def __getattr__(self, name: str) -> Any:
        """Handle attribute access for special cases."""
        if name == "record":
            raise TypeError(f"{type(self).__name__} has no record type. Use Widget[YourModel] to enable record access.")
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


@overload
def widget[W: Widget[Any]](cls: type[W]) -> type[W]: ...


@overload
def widget(
    cls: None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    title: str | None = None,
    **kwargs: Any,
) -> Callable[[type[Widget[Any]]], type[Widget[Any]]]: ...


def widget[W: Widget[Any]](
    cls: type[W] | None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    title: str | None = None,
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

        @widget(auto_bind=False)
        class MyWidget(Widget[Person]):
            # No auto-binding, must use bind="field" explicitly
            ...

        @widget(title="My App", minimumWidth=400)
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
        title: Shorthand for windowTitle.
        **kwargs: Extra properties applied via setXXX() methods.
                  e.g., windowTitle="Foo" calls self.setWindowTitle("Foo")
    """
    # title is an alias for windowTitle
    if title is not None:
        kwargs["windowTitle"] = title

    def decorator(target: type[W]) -> type[W]:
        # Store layout config
        target._qtpie_config.layout = layout
        target._qtpie_config.margins = margins
        target._qtpie_config.auto_bind = auto_bind
        target._qtpie_config.widget_props = kwargs

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
        # Call original __init__ (which instantiates fields via new_fields)
        original_init(self, *args, **kwargs)

        # Create list widget fields (list[QWidget] = new(bind="..."))
        # This must happen before layout so they're included in the correct order
        _create_list_widget_fields(self, config)

        # Apply widget properties (windowTitle="X" → setWindowTitle("X"))
        _apply_widget_props(self, config)

        # Set up layout if configured
        if config.layout is not None:
            qt_layout = _create_layout(config.layout)
            if qt_layout is not None:
                self.setLayout(qt_layout)

                # Apply margins
                if config.margins is not None:
                    if isinstance(config.margins, int):
                        qt_layout.setContentsMargins(config.margins, config.margins, config.margins, config.margins)
                    else:
                        qt_layout.setContentsMargins(*config.margins)

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
                            _validate_layout_params(name, config.layout, field.label, field.grid)
                            _add_to_layout(qt_layout, widget_instance, config.layout, field.label, field.grid)
                    # Check if it's a Variable with a widget
                    elif name in config.variable_names:
                        var = getattr(self, name, None)
                        if isinstance(var, Variable) and var.widget is not None:
                            # Get label/grid/exclude_from_layout from the descriptor
                            descriptor: Any = getattr(cls, name, None)
                            label: str | None = None
                            grid: GridPosition | None = None
                            if isinstance(descriptor, _VariableDescriptor):
                                if descriptor.exclude_from_layout:
                                    continue
                                label = descriptor.label
                                grid = descriptor.grid  # type: ignore[assignment]
                            _validate_layout_params(name, config.layout, label, grid)
                            _add_to_layout(qt_layout, var.widget, config.layout, label, grid)

        # Connect signals (clicked="on_clicked" or clicked=lambda: ...)
        _connect_signals(self, config)

        # Call __setup__ hook if defined (before bindings, so record can be initialized)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings (after __setup__ so record is available)
        _apply_auto_bindings(self, config)

        # Enable on_dirty_changed and on_valid_changed hooks (subscribes to future Variable changes)
        state = getattr(self, "_qtpie", None)
        if not isinstance(state, QtPieState):
            state = QtPieState(self)
            self._qtpie = state  # type: ignore[assignment]
        state.enable_dirty_hook()
        state.enable_valid_hook()

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
) -> None:
    """Add a widget to the layout.

    Args:
        layout: The Qt layout to add to.
        widget_instance: The widget to add.
        layout_type: The type of layout.
        label: For form layouts, the label text for this row.
        grid: For grid layouts, position as (row, col) or (row, col, rowspan, colspan).
    """
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


def _apply_widget_props(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Apply widget properties from @widget decorator kwargs.

    For each prop like windowTitle="X", calls widget.setWindowTitle("X").
    """
    for prop_name, value in config.widget_props.items():
        # Convert propName to setPropName (capitalize first letter)
        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter = getattr(widget, setter_name, None)
        if setter is not None and callable(setter):
            try:
                setter(value)
            except TypeError as e:
                raise TypeError(f"Failed to call {setter_name}({value!r}) on {type(widget).__name__}: {e}") from e
        else:
            raise AttributeError(f"{type(widget).__name__} has no setter '{setter_name}' for property '{prop_name}'")


def _create_list_widget_fields(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Create WidgetRepeater instances for list[QWidget] fields.

    For each field with annotation like `list[QLabel]` and `bind="some_path"`,
    resolves the bind path to get the source list and creates a WidgetRepeater.

    The source can be:
    - Variable[list[T]] → uses its ObservableList (reactive)
    - ObservableList directly → uses it (reactive)
    - Observable[list] → wraps value in ObservableList (one-time)
    - Plain list → wraps in ObservableList (one-time)
    """
    from observant import Observable, ObservableList

    from .bindings import resolve_binding_source
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

        if source is None:
            raise ValueError(f"Could not resolve bind path '{field.bind}' for field '{name}'")

        if isinstance(source, Variable):
            # Variable[list[T]] - get the underlying observable
            wrapper = source.observable
            if isinstance(wrapper, ObservableList):
                obs_list = wrapper
            elif isinstance(wrapper, Observable):
                # Observable containing a list - create synced ObservableList
                val = wrapper.get()
                if isinstance(val, list):
                    obs_list = ObservableList(cast(list[Any], val))

                    # Sync: when Observable changes, update ObservableList
                    def make_sync_var(obs: Observable[Any], target: ObservableList[Any]) -> None:
                        def on_source_change(new_val: Any) -> None:
                            if isinstance(new_val, list):
                                target.clear()
                                target.extend(cast(list[Any], new_val))

                        obs.on_change(on_source_change)

                    make_sync_var(wrapper, obs_list)
                else:
                    raise TypeError(f"bind='{field.bind}' resolved to Observable[{type(val).__name__}], expected list")
            else:
                raise TypeError(f"bind='{field.bind}' resolved to Variable with {type(wrapper).__name__}, expected list")
        elif isinstance(source, ObservableList):
            obs_list = source
        elif isinstance(source, Observable):
            # Observable containing a list - create synced ObservableList
            val = source.get()
            if isinstance(val, list):
                obs_list = ObservableList(cast(list[Any], val))

                # Sync: when Observable changes, update ObservableList
                def make_sync(obs: Observable[Any], target: ObservableList[Any]) -> None:
                    def on_source_change(new_val: Any) -> None:
                        if isinstance(new_val, list):
                            # Clear and repopulate
                            target.clear()
                            target.extend(cast(list[Any], new_val))

                    obs.on_change(on_source_change)

                make_sync(source, obs_list)
            else:
                raise TypeError(f"bind='{field.bind}' resolved to Observable[{type(val).__name__}], expected list")
        else:
            raise TypeError(f"bind='{field.bind}' resolved to {type(source).__name__}, expected Variable[list[...]] or ObservableList")

        # Create WidgetRepeater
        repeater = WidgetRepeater(
            observable_list=obs_list,
            item_type=item_type,  # Could extract from source type hints if needed
            widget_type=field.list_widget_type,
            widget_args=field.args,
            widget_kwargs=field.kwargs,
            bind_expr="{#self}",  # Each widget binds to its list item
        )

        # Store the repeater on the widget
        setattr(widget, name, repeater)


def _apply_auto_bindings(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Apply auto-bindings for QWidget fields.

    For each QWidget field:
    - If field.bind is set, use that path (always applies)
    - If auto_bind is True, strip leading underscore and use as bind path

    Then resolve the path and create the binding.
    """
    from observant import Observable, ObservableProxy

    from .bindings import bind, create_format_binding, is_format_string, resolve_binding_source
    from .variable import Variable

    for name, field in config.fields.items():
        # Skip list widget fields - they're already bound via WidgetRepeater
        if field.is_list_widget:
            continue

        # Get the widget instance
        widget_instance = getattr(widget, name, None)
        if widget_instance is None:
            continue

        # Skip non-QWidget fields (Variables, etc.)
        if not isinstance(widget_instance, QWidget):
            continue

        # Determine bind path
        if field.bind is not None:
            # Explicit bind - always apply
            bind_path = field.bind
        elif config.auto_bind:
            # Auto-bind: strip underscore prefix
            bind_path = name.lstrip("_")
        else:
            # No explicit bind and auto_bind is disabled
            continue

        # Handle format strings
        if is_format_string(bind_path):
            from .bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                # Create a bound setter function
                setter = adapter.setter

                def make_setter(s: Callable[[Any, Any], None], w: QWidget) -> Callable[[Any], None]:
                    def bound_setter(val: Any) -> None:
                        s(w, val)

                    return bound_setter

                create_format_binding(widget, bind_path, make_setter(setter, widget_instance))
            continue

        # Resolve the binding source
        source = resolve_binding_source(widget, bind_path)
        if source is None:
            continue

        # Create the binding
        if isinstance(source, Variable):
            bind(source).to(widget_instance)
        elif isinstance(source, Observable):
            # Set up binding for Observable (e.g., from record field)
            from .bindings.registry import get_binding_registry

            registry = get_binding_registry()
            default_prop = registry.get_default_prop(widget_instance)
            adapter = registry.get(widget_instance, default_prop)
            if adapter is not None and adapter.setter is not None:
                # Set initial value (Observable → Widget)
                adapter.setter(widget_instance, source.get())

                # Subscribe to Observable changes (Observable → Widget)
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
        elif isinstance(source, ObservableProxy):
            # ObservableProxy - not directly bindable to a widget property
            # This shouldn't normally happen since paths resolve to leaf observables
            pass


def _connect_signals(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Connect signals declared in new() to handlers.

    Supports both callables and string method names:
        clicked=lambda: print("clicked")
        clicked="on_clicked"
    """
    for name, field in config.fields.items():
        if not field.signal_connections:
            continue

        widget_instance = getattr(widget, name, None)
        if widget_instance is None:
            continue

        for signal_name, handler in field.signal_connections.items():
            signal = getattr(widget_instance, signal_name, None)
            if signal is None:
                continue

            if isinstance(handler, str):
                # Method name - resolve on the parent widget
                method = getattr(widget, handler, None)
                if method is not None and callable(method):
                    signal.connect(method)
                else:
                    raise AttributeError(f"{type(widget).__name__} has no method '{handler}' for signal connection {name}.{signal_name}=\"{handler}\"")
            else:
                # Direct callable (lambda, function, etc.)
                signal.connect(handler)
