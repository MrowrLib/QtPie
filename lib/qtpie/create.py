"""create() - Runtime instantiation with new()-like features."""

from collections.abc import Callable
from typing import Any

from qtpie.signals import create_signal_expression_handler
from qtpie.utils import is_signal
from qtpie.utils.common import is_signal_on_type


def create_instance[T](context: Any, cls: type[T], /, *args: Any, **kwargs: Any) -> T:
    """Create an instance at runtime with new()-like signal and property wiring.

    This is the runtime equivalent of new(). Use it when you need to create
    widget instances dynamically (not at class definition time).

    Args:
        context: The object containing handler methods (e.g., self in an App/Widget).
        cls: The class to instantiate.
        *args: Positional arguments passed to the constructor.
        **kwargs: Keyword arguments. Signal names (e.g., clicked="handler")
                  are extracted and connected. Property names with setXxx
                  methods are applied. The rest go to the constructor.

    Returns:
        The created instance with signals connected and properties applied.

    Example:
        # At runtime, recreate a window with signal connections:
        self.main_window = create_instance(self, ForcWindow, on_reload="on_reload")
        self.main_window.show()
    """
    instance = _create_instance_internal(cls, *args, **kwargs)
    _connect_signals(context, instance, cls.__name__)
    return instance


def _create_instance_internal[T](cls: type[T], /, *args: Any, **kwargs: Any) -> T:
    """Internal: Create instance without connecting signals.

    Used by create_instance() which handles signal connection.

    Args:
        cls: The class to instantiate.
        *args: Positional arguments passed to the constructor.
        **kwargs: Keyword arguments. Signal names (e.g., clicked="handler")
                  are extracted and connected. Property names with setXxx
                  methods are applied. The rest go to the constructor.

    Returns:
        The created instance with signals connected and properties applied.

    Example:
        # At runtime, recreate a window with signal connections:
        self.main_window = create(ForcWindow, on_reload="on_reload")
        self.main_window.show()

        # With constructor args and properties:
        btn = create(QPushButton, "Click Me", clicked="on_click", enabled=False)
    """
    # Separate kwargs into: signals, widget props, and constructor kwargs
    signal_connections: dict[str, str | Callable[..., Any]] = {}
    widget_props: dict[str, Any] = {}
    property_bindings: dict[str, str] = {}
    constructor_kwargs: dict[str, Any] = {}
    object_name: str | None = None
    css_classes: list[str] = []
    variable_bindings: dict[str, Any] = {}

    # Extract special QtPie kwargs
    if "name" in kwargs:
        object_name = kwargs.pop("name")
    if "classes" in kwargs:
        css_classes = kwargs.pop("classes")

    for key, value in kwargs.items():
        # Check if it's a signal on the class
        if is_signal_on_type(key, cls):
            if isinstance(value, str) or callable(value):
                signal_connections[key] = value
        # Check for property bindings (visible=, enabled=)
        elif key in ("visible", "enabled") and isinstance(value, str):
            property_bindings[key] = value
        # Check if it's a widget prop (has setXxx method)
        elif _has_setter(cls, key):
            widget_props[key] = value
        # Check if it's a variable binding (child has required binding for this name)
        elif _is_variable_binding(cls, key):
            variable_bindings[key] = value
        else:
            # Pass to constructor
            constructor_kwargs[key] = value

    # Instantiate the class
    instance = cls(*args, **constructor_kwargs)

    # Apply object name
    from qtpy.QtWidgets import QWidget

    if isinstance(instance, QWidget):
        if object_name is not None:
            instance.setObjectName(object_name)
        # Apply CSS classes
        if css_classes:
            from qtpie.styles import set_classes

            set_classes(instance, css_classes)

    # Apply widget props
    _apply_widget_props(instance, widget_props)

    # Apply variable bindings
    if variable_bindings:
        _apply_variable_bindings_runtime(instance, variable_bindings)

    # Apply property bindings (visible=, enabled=)
    if property_bindings:
        _apply_property_bindings_runtime(instance, property_bindings)

    # Store signal connections for connect_signals to use
    instance._qtpie_runtime_signals = signal_connections  # type: ignore[attr-defined]

    return instance


def _connect_signals(context: Any, instance: Any, instance_name: str = "instance") -> None:
    """Internal: Connect signals stored by _create_instance_internal.

    Args:
        context: The object containing the handler methods (e.g., self in an App).
        instance: The instance created by _create_instance_internal().
        instance_name: Name for error messages.
    """
    signal_connections: dict[str, str | Callable[..., Any]] = getattr(instance, "_qtpie_runtime_signals", {})
    if not signal_connections:
        return

    from qtpie.bindings import is_format_string

    def expression_handler_factory(ctx: Any, expr: str) -> Callable[..., Any]:
        return create_signal_expression_handler(ctx, expr, ["#self", "#widget", "#app"])

    for signal_name, handler in signal_connections.items():
        signal = getattr(instance, signal_name, None)
        if signal is None:
            continue

        if isinstance(handler, str):
            if is_format_string(handler):
                # Expression handler
                expr_handler = expression_handler_factory(context, handler)
                signal.connect(expr_handler)
            else:
                # Method name or signal name on context
                target = getattr(context, handler, None)
                if target is None:
                    raise AttributeError(f"{type(context).__name__} has no method or signal '{handler}' for signal connection {instance_name}.{signal_name}=\"{handler}\"")

                if is_signal(target):
                    signal.connect(target)
                elif callable(target):
                    signal.connect(target)
                else:
                    raise AttributeError(f'{type(context).__name__}.{handler} is not callable or a Signal for signal connection {instance_name}.{signal_name}="{handler}"')
        elif callable(handler):
            signal.connect(handler)

    # Clean up
    del instance._qtpie_runtime_signals


def _has_setter(cls: type, prop_name: str) -> bool:
    """Check if cls has a setXxx method for prop_name."""
    setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
    attr = getattr(cls, setter_name, None)
    return attr is not None and callable(attr)


def _is_variable_binding(cls: type, name: str) -> bool:
    """Check if cls has a required binding for this name."""
    config = getattr(cls, "_qtpie_config", None)
    if config is None:
        return False
    required: set[str] = getattr(config, "required_bindings", set())
    return name in required


def _apply_widget_props(instance: Any, props: dict[str, Any]) -> None:
    """Apply widget properties via setXxx methods."""
    from qtpie.translations.translatable import Translatable

    for prop_name, value in props.items():
        # Resolve Translatable
        if isinstance(value, Translatable):
            value = value.resolve()

        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter = getattr(instance, setter_name, None)
        if setter is not None and callable(setter):
            setter(value)


def _apply_variable_bindings_runtime(instance: Any, bindings: dict[str, Any]) -> None:
    """Apply variable bindings to the instance at runtime.

    This wires up parent Variables to child required bindings.
    """
    from observant import Observable

    from qtpie.variable import Variable

    for child_var_name, binding_value in bindings.items():
        if isinstance(binding_value, Variable):
            # Direct Variable - share the observable
            child_var: Variable[Any] = Variable(binding_value.observable)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            setattr(instance, child_var_name, child_var)
        elif isinstance(binding_value, Observable):
            # Direct Observable
            child_var = Variable(binding_value)  # pyright: ignore[reportUnknownArgumentType]
            setattr(instance, child_var_name, child_var)
        else:
            # Literal value
            child_var = Variable(Observable(binding_value))
            setattr(instance, child_var_name, child_var)


def _apply_property_bindings_runtime(instance: Any, bindings: dict[str, str]) -> None:
    """Apply property bindings (visible=, enabled=) at runtime.

    Note: These bindings require a context to resolve variable references.
    For now, we store them for later application when connect_signals is called.
    """
    # Store for later - we need context to resolve these
    instance._qtpie_runtime_property_bindings = bindings  # type: ignore[attr-defined]
