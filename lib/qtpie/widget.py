# pyright: reportPrivateUsage=false
"""Widget - QWidget container with automatic layout."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin, overload

if TYPE_CHECKING:
    from .variable import Variable

from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from .layout import LayoutType
from .new_field import NewField
from .new_fields import new_fields
from .variable import Variable as VariableClass
from .variable import _create_observable_for_type, _VariableDescriptor


class _QtPieConfig:
    """Class-level QtPie configuration."""

    __slots__ = ("layout", "margins", "fields", "variable_names", "init_wrapped", "record_type")

    def __init__(self) -> None:
        self.layout: LayoutType = "vertical"
        self.margins: int | tuple[int, int, int, int] | None = None
        self.fields: dict[str, NewField] = {}
        self.variable_names: list[str] = []
        self.init_wrapped: bool = False
        self.record_type: type[Any] | None = None  # T from Widget[T]


class QtPieState:
    """Instance-level QtPie state."""

    __slots__ = ("variables", "_view_model", "_widget", "_was_dirty", "_check_dirty", "_record")

    def __init__(self, widget: Widget[Any]) -> None:
        self._widget = widget
        self.variables: dict[str, Variable[Any]] = {}
        self._view_model: QtPieViewModel | None = None
        self._was_dirty: bool = False
        self._check_dirty: Callable[[bool], None] | None = None
        self._record: VariableClass[Any] | None = None

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

    def register_variable(self, name: str, var: Variable[Any]) -> None:
        """Register a Variable and wire up dirty hook if enabled."""
        self.variables[name] = var
        if self._check_dirty is not None:
            var.is_dirty.on_change(self._check_dirty)


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


class _RecordDescriptor[T]:
    """Descriptor for auto-created record on Widget[T].

    This is used when the user doesn't explicitly declare `record: Variable[T] = new(...)`.
    It lazily creates the record Variable on first access.
    """

    def __init__(self, record_type: type[T]) -> None:
        self._record_type = record_type

    def __get__(self, obj: Widget[T] | None, objtype: type | None = None) -> VariableClass[T]:
        if obj is None:
            return self  # type: ignore[return-value]

        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        state = obj._qtpie
        if state._record is None:
            wrapper = _create_observable_for_type(self._record_type, None)
            state._record = VariableClass(wrapper)
            state.register_variable("record", state._record)

        return state._record

    def __set__(self, obj: Widget[T], value: T | VariableClass[T]) -> None:
        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        if isinstance(value, VariableClass):
            var = cast(VariableClass[T], value)
            obj._qtpie._record = var
            obj._qtpie.register_variable("record", var)
        else:
            # Get or create record, then set value
            record = self.__get__(obj, type(obj))
            record.value = value  # type: ignore[assignment]


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

    if TYPE_CHECKING:
        # Type stub for autocomplete - actual implementation via descriptor
        record: VariableClass[T]

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
) -> Callable[[type[Widget[Any]]], type[Widget[Any]]]: ...


def widget[W: Widget[Any]](
    cls: type[W] | None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
) -> type[W] | Callable[[type[W]], type[W]]:
    """Decorator to configure Widget layout.

    Usage:
        @widget
        class MyWidget(Widget):
            ...

        @widget(layout="horizontal", margins=10)
        class MyWidget(Widget):
            ...

    Args:
        layout: "vertical" | "horizontal" | "form" | "grid" | None
                Default is "vertical". None disables auto-layout.
        margins: int | tuple[int, int, int, int] | None
                 Layout margins. int applies to all sides.
    """

    def decorator(target: type[W]) -> type[W]:
        # Store layout config
        target._qtpie_config.layout = layout
        target._qtpie_config.margins = margins

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
                for name, field in config.fields.items():
                    if field.exclude_from_layout:
                        continue

                    widget_instance = getattr(self, name, None)
                    if widget_instance is None:
                        continue

                    if not isinstance(widget_instance, QWidget):
                        continue

                    _add_to_layout(qt_layout, widget_instance, config.layout)

        # Call __setup__ hook if defined
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Enable on_dirty_changed hook (subscribes to future Variable changes)
        state = getattr(self, "_qtpie", None)
        if not isinstance(state, QtPieState):
            state = QtPieState(self)
            self._qtpie = state  # type: ignore[assignment]
        state.enable_dirty_hook()

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


def _add_to_layout(layout: QLayout, widget_instance: QWidget, layout_type: LayoutType) -> None:
    """Add a widget to the layout."""
    if layout_type in ("vertical", "horizontal"):
        layout.addWidget(widget_instance)  # type: ignore[union-attr]
    elif layout_type == "form":
        layout.addRow(widget_instance)  # type: ignore[union-attr]
    elif layout_type == "grid":
        layout.addWidget(widget_instance)  # type: ignore[union-attr]
