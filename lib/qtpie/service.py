# pyright: reportPrivateUsage=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
"""Service - A QtPie primitive for business logic without Qt dependencies.

Services host Variables with declarative callbacks, enabling a clean service
layer that integrates naturally with QtPie's reactive system.

Example:
    @service
    class ConfigService(Service):
        theme: Variable[str] = new("dark", onChange="_save_config")

        def _save_config(self) -> None:
            # persist to disk
            ...
"""

from typing import Any, overload

from .variable import Variable, _RequiredBindingDescriptor, _VariableDescriptor

__all__ = ["Service", "service"]


class ServiceConfig:
    """Class-level configuration for a Service."""

    __slots__ = ("variable_names", "required_bindings", "init_wrapped")

    def __init__(self) -> None:
        self.variable_names: list[str] = []
        self.required_bindings: set[str] = set()
        self.init_wrapped: bool = False


class ServiceState:
    """Per-instance state for a Service."""

    __slots__ = ("variables",)

    def __init__(self) -> None:
        self.variables: dict[str, Variable[Any]] = {}

    def register_variable(self, name: str, var: Variable[Any]) -> None:
        """Register a Variable by name."""
        self.variables[name] = var


class Service:
    """Base class for QtPie services.

    Services host Variables with declarative callbacks.
    They have no Qt dependencies.

    Example:
        @service
        class MyService(Service):
            count: Variable[int] = new(0)
            name: Variable[str] = new("")

        svc = MyService()
        svc.count.value = 42
    """

    # Class-level config (set up in __init_subclass__)
    _service_config: ServiceConfig
    # Instance-level state (set during __init__)
    _service_state: ServiceState

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Create fresh config for this subclass
        cls._service_config = ServiceConfig()

        # Collect variable names from _VariableDescriptor instances
        # (NewField.__set_name__ already converted Variable[T] = new(...) to descriptors)
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, _VariableDescriptor):
                cls._service_config.variable_names.append(name)

        # Detect bare Variable[T] annotations (required bindings)
        _detect_required_bindings_for_service(cls)


def _detect_required_bindings_for_service(cls: type[Service]) -> None:
    """Detect bare Variable[T] annotations as required bindings.

    A bare annotation like `count: Variable[int]` (no `= new()`) indicates
    the Variable must be provided via constructor injection.
    """
    from .utils.common import detect_required_bindings

    detect_required_bindings(cls, "_service_config", Variable, _RequiredBindingDescriptor)


def _wrap_init_for_service(cls: type[Service]) -> None:
    """Wrap __init__ to set up instance state and handle constructor kwargs."""
    if cls._service_config.init_wrapped:
        return

    original_init = cls.__init__

    # Capture config at decoration time
    config = cls._service_config

    def wrapped_init(self: Service, *args: Any, **kwargs: Any) -> None:
        # Extract Variable kwargs (match against variable_names and required_bindings)
        variable_kwargs: dict[str, Any] = {}
        all_variable_names = set(config.variable_names) | config.required_bindings
        for var_name in list(kwargs.keys()):
            if var_name in all_variable_names:
                variable_kwargs[var_name] = kwargs.pop(var_name)

        # Initialize ServiceState early so Variables have somewhere to register
        if not hasattr(self, "_service_state"):
            self._service_state = ServiceState()

        # Apply constructor variable kwargs
        if variable_kwargs:
            _apply_variable_kwargs_for_service(self, variable_kwargs)

        # Call original __init__
        original_init(self, *args, **kwargs)

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._service_config.init_wrapped = True


def _apply_variable_kwargs_for_service(instance: Service, variable_kwargs: dict[str, Any]) -> None:
    """Apply constructor kwargs to Variables on a Service.

    Handles three cases:
    - Static value (int, str, etc.) → set as initial value
    - Observable → bind to it (share the Observable)
    - Variable → bind to its underlying Observable
    """
    from observant import Observable

    for var_name, value in variable_kwargs.items():
        if isinstance(value, Observable):
            # Share the Observable directly
            shared_var: Variable[Any] = Variable(value)
            setattr(instance, var_name, shared_var)
        elif isinstance(value, Variable):
            # Share the underlying Observable from the other Variable
            shared_var = Variable(value.observable)
            setattr(instance, var_name, shared_var)
        else:
            # Static value - need to handle bare Variables differently
            cls_attr = getattr(type(instance), var_name, None)
            if isinstance(cls_attr, _RequiredBindingDescriptor):
                # For bare Variables, create a new Variable with the static value
                wrapper: Observable[Any] = Observable(value)
                new_var: Variable[Any] = Variable(wrapper)
                setattr(instance, var_name, new_var)
            elif isinstance(cls_attr, _VariableDescriptor):
                # For Variables with = new(), access normally and set value
                var = getattr(instance, var_name)
                var.value = value
            else:
                # Fallback - try normal access
                var = getattr(instance, var_name)
                var.value = value


@overload
def service(cls: type[Service]) -> type[Service]: ...


@overload
def service(cls: None = None) -> type[Service]: ...


def service(cls: type[Service] | None = None) -> type[Service]:
    """Decorator to mark a class as a QtPie Service.

    Usage:
        @service
        class MyService(Service):
            count: Variable[int] = new(0)

    Services process new() fields at decoration time, similar to @widget,
    but have no Qt dependencies.
    """

    def decorator(target: type[Service]) -> type[Service]:
        # Wrap __init__ to set up instance state
        _wrap_init_for_service(target)
        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]
