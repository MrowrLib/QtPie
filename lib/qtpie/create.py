"""build() - Runtime instantiation with new()-like features."""

from collections.abc import Callable
from typing import Any, cast

from qtpie.signals import create_signal_expression_handler
from qtpie.utils import is_signal
from qtpie.utils.common import is_signal_on_type


class _RuntimeData:
    """Data that needs context to be applied."""

    __slots__ = ("signal_connections", "property_bindings", "bind_expr", "ref_bindings")

    def __init__(
        self,
        signal_connections: dict[str, str | Callable[..., Any]],
        property_bindings: dict[str, str],
        bind_expr: str | None,
        ref_bindings: dict[str, Any],
    ) -> None:
        self.signal_connections = signal_connections
        self.property_bindings = property_bindings
        self.bind_expr = bind_expr
        self.ref_bindings = ref_bindings


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

    Supported features (same as new()):
        - Signal connections: clicked="method_name" or clicked=lambda: ...
        - Widget props via setXxx: enabled=False, toolTip="...", etc.
        - name="object-name" -> setObjectName()
        - classes=["css", "classes"] -> CSS class application
        - bind="{_var}" -> Reactive text binding to setText/setTitle/setWindowTitle
        - visible="_var" or visible="{expr}" -> Reactive visibility binding
        - enabled="_var" or enabled="{expr}" -> Reactive enabled binding
        - ref("attr_name") -> Deferred attribute reference from context
        - t("text") -> Translatable strings (resolved immediately, registered for hot-reload)
        - Variable bindings for child widgets with required bindings (bare Variable[T]):
            child = self.build(ChildWidget, count="_my_count")  # passes Variable

    NOT supported (only work with new() at class definition time):
        - list[QWidget] repeaters (e.g., `_items: list[QLabel] = new(bind="_data")`)
        - dict[K, V] repeaters
        - label= for QFormLayout
        - grid=(row, col) for QGridLayout
        - Automatic field-to-record binding in Widget[T]
        - stretch= and other layout hints

    Example:
        # At runtime, recreate a window with signal connections:
        self.main_window = create_instance(self, ForcWindow, on_reload="on_reload")
        self.main_window.show()

        # With reactive bindings:
        self.label = create_instance(self, QLabel, bind="Count: {_count}")
        self.btn = create_instance(self, QPushButton, "Submit", enabled="{_count > 0}")
    """
    instance, runtime_data = _create_instance_internal(cls, *args, **kwargs)
    _apply_context_bindings(context, instance, runtime_data, cls.__name__)
    return instance


def _create_instance_internal[T](cls: type[T], /, *args: Any, **kwargs: Any) -> tuple[T, _RuntimeData]:
    """Internal: Create instance and return runtime data for context bindings.

    Used by create_instance() which handles signal connection and bindings.
    """
    # Separate kwargs into categories
    signal_connections: dict[str, str | Callable[..., Any]] = {}
    widget_props: dict[str, Any] = {}
    property_bindings: dict[str, str] = {}
    constructor_kwargs: dict[str, Any] = {}
    object_name: str | None = None
    css_classes: list[str] = []
    variable_bindings: dict[str, Any] = {}
    bind_expr: str | None = None
    ref_bindings: dict[str, Any] = {}

    # Extract special QtPie kwargs
    if "name" in kwargs:
        object_name = kwargs.pop("name")
    if "classes" in kwargs:
        css_classes = kwargs.pop("classes")
    if "bind" in kwargs:
        bind_expr = kwargs.pop("bind")

    for key, value in kwargs.items():
        # Check if it's a signal on the class
        if is_signal_on_type(key, cls):
            if isinstance(value, str) or callable(value):
                signal_connections[key] = value
        # Check for property bindings (visible=, enabled=)
        elif key in ("visible", "enabled") and isinstance(value, str):
            property_bindings[key] = value
        # Check if it's a ref() binding
        elif _is_ref(value):
            ref_bindings[key] = value
        # Check if it's a widget prop (has setXxx method)
        elif _has_setter(cls, key):
            widget_props[key] = value
        # Check if it's a variable binding (child has required binding for this name)
        elif _is_variable_binding(cls, key):
            variable_bindings[key] = value
        else:
            # Pass to constructor
            constructor_kwargs[key] = value

    # Resolve Translatable in args
    from qtpie.translations.translatable import Translatable

    resolved_args: list[Any] = []
    translatable_args: list[tuple[int, Translatable]] = []
    for i, arg in enumerate(args):
        if isinstance(arg, Translatable):
            translatable_args.append((i, arg))
            resolved_args.append(arg.resolve())
        else:
            resolved_args.append(arg)

    # Instantiate the class
    instance = cls(*resolved_args, **constructor_kwargs)

    # Register translatable args for hot-reload
    if translatable_args:
        from qtpie.translations.store import register_binding

        # Determine the property name based on widget type
        prop_name = _get_text_property_name(instance)
        if prop_name is not None:
            for _idx, t_arg in translatable_args:
                register_binding(
                    instance,
                    prop_name,
                    t_arg.text,
                    t_arg.context,
                )

    # Apply object name
    from qtpy.QtWidgets import QWidget

    if isinstance(instance, QWidget):
        if object_name is not None:
            instance.setObjectName(object_name)
        # Apply CSS classes
        if css_classes:
            from qtpie.styles import set_classes

            set_classes(instance, css_classes)

    # Apply widget props (non-binding values)
    _apply_widget_props(instance, widget_props)

    # Apply variable bindings
    if variable_bindings:
        _apply_variable_bindings_runtime(instance, variable_bindings)

    # Create runtime data for context-dependent bindings
    runtime_data = _RuntimeData(
        signal_connections=signal_connections,
        property_bindings=property_bindings,
        bind_expr=bind_expr,
        ref_bindings=ref_bindings,
    )

    return instance, runtime_data


def _apply_context_bindings(
    context: Any,
    instance: Any,
    runtime_data: _RuntimeData,
    instance_name: str,
) -> None:
    """Apply all bindings that require context."""
    # Connect signals
    _connect_signals(context, instance, runtime_data.signal_connections, instance_name)

    # Apply property bindings (visible=, enabled=)
    if runtime_data.property_bindings:
        _apply_property_bindings(context, instance, runtime_data.property_bindings)

    # Apply bind= format binding
    if runtime_data.bind_expr:
        _apply_bind_expr(context, instance, runtime_data.bind_expr)

    # Apply ref() bindings
    if runtime_data.ref_bindings:
        _apply_ref_bindings(context, instance, runtime_data.ref_bindings)


def _connect_signals(
    context: Any,
    instance: Any,
    signal_connections: dict[str, str | Callable[..., Any]],
    instance_name: str,
) -> None:
    """Connect signals to handlers on context."""
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


def _apply_property_bindings(context: Any, instance: Any, bindings: dict[str, str]) -> None:
    """Apply property bindings (visible=, enabled=) using context to resolve variables."""
    from qtpie.bindings import is_format_string
    from qtpie.bindings.expression import create_expression_binding
    from qtpie.bindings.property_bindings import get_widget_property_setter

    for prop_name, bind_expr in bindings.items():
        prop_setter = get_widget_property_setter(instance, prop_name)
        if prop_setter is None:
            # Fall back to setXxx method
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            setter = getattr(instance, setter_name, None)
            if setter is None or not callable(setter):
                continue
            prop_setter = setter

        setter_fn = cast(Callable[[Any], None], prop_setter)

        if is_format_string(bind_expr):
            # Expression binding like "{_count > 0}"
            create_expression_binding(context, bind_expr, setter_fn)
        else:
            # Simple variable reference like "_is_visible"
            from observant import Observable

            from qtpie.bindings.path import resolve_binding_source
            from qtpie.variable import Variable

            source = resolve_binding_source(context, bind_expr)  # type: ignore[arg-type]
            if source is None:
                continue

            if isinstance(source, Variable):
                setter_fn(source.value)  # pyright: ignore[reportUnknownMemberType]
                source.on_change(setter_fn)
            elif isinstance(source, Observable):
                setter_fn(source.get())
                source.on_change(setter_fn)


def _apply_bind_expr(context: Any, instance: Any, bind_expr: str) -> None:
    """Apply bind= format binding to instance.setText (or appropriate setter)."""
    from qtpie.bindings import create_format_binding

    # Find appropriate setter - try common ones
    setter: Callable[[Any], None] | None = None

    # Try setText (QLabel, QLineEdit, QPushButton, etc.)
    if hasattr(instance, "setText") and callable(instance.setText):
        setter = cast(Callable[[Any], None], instance.setText)
    # Try setTitle (QGroupBox, QDockWidget, etc.)
    elif hasattr(instance, "setTitle") and callable(instance.setTitle):
        setter = cast(Callable[[Any], None], instance.setTitle)
    # Try setWindowTitle (QWidget, QMainWindow, etc.)
    elif hasattr(instance, "setWindowTitle") and callable(instance.setWindowTitle):
        setter = cast(Callable[[Any], None], instance.setWindowTitle)

    if setter is not None:
        create_format_binding(context, bind_expr, setter)


def _apply_ref_bindings(context: Any, instance: Any, ref_bindings: dict[str, Any]) -> None:
    """Apply ref() bindings - resolve deferred attribute references."""
    from qtpie.ref import Ref

    for prop_name, ref_obj in ref_bindings.items():
        if not isinstance(ref_obj, Ref):
            continue

        # Resolve the ref against context
        resolved_value = ref_obj.resolve(context)

        # Apply to instance
        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter = getattr(instance, setter_name, None)
        if setter is not None and callable(setter):
            setter(resolved_value)


def _is_ref(value: Any) -> bool:
    """Check if value is a Ref instance."""
    from qtpie.ref import Ref

    return isinstance(value, Ref)


def _get_text_property_name(instance: Any) -> str | None:
    """Get appropriate text property name for an instance."""
    if hasattr(instance, "setText"):
        return "text"
    if hasattr(instance, "setTitle"):
        return "title"
    if hasattr(instance, "setWindowTitle"):
        return "windowTitle"
    return None


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
        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter = getattr(instance, setter_name, None)
        if setter is None or not callable(setter):
            continue

        # Handle Translatable - resolve and register for hot-reload
        if isinstance(value, Translatable):
            from qtpie.translations.store import register_binding

            resolved = value.resolve()
            setter(resolved)
            # Register for hot-reload
            register_binding(
                instance,
                prop_name,
                value.text,
                value.context,
            )
        else:
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
