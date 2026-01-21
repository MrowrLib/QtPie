# pyright: reportPrivateUsage=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false
"""State - A QtPie primitive for reactive state without Qt dependencies.

State hosts Variables with declarative callbacks, enabling a clean state
layer that integrates naturally with QtPie's reactive system.

Example:
    @state
    class ConfigState(State):
        theme: Variable[str] = new("dark", onChange="_save_config")

        def _save_config(self) -> None:
            # persist to disk
            ...

Event annotations are automatically instantiated:
    @state
    class MyState(State):
        on_save: Event           # Auto-creates Event() instance
        on_changed: Event[int]   # Auto-creates Event() instance

Wire Events to handlers via decorator kwargs:
    @state(on_save="_persist")
    class MyState(State):
        on_save: Event

        def _persist(self) -> None:
            ...
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, overload, override

from .event import Event, is_event_hint
from .variable import Variable, _RequiredBindingDescriptor, _VariableDescriptor

__all__ = ["State", "state", "resolve_from_state_hierarchy"]


class StateConfig:
    """Class-level configuration for a State."""

    __slots__ = ("variable_names", "required_bindings", "init_wrapped", "event_names", "event_wiring")

    def __init__(self) -> None:
        self.variable_names: list[str] = []
        self.required_bindings: set[str] = set()
        self.init_wrapped: bool = False
        # Event annotation names (e.g., ["on_save", "on_changed"])
        self.event_names: list[str] = []
        # Event-to-handler wiring from decorator kwargs (e.g., {"on_save": "_persist"})
        self.event_wiring: dict[str, str] = {}


class StateInstance:
    """Per-instance state for a State."""

    __slots__ = ("variables", "state_parent")

    def __init__(self) -> None:
        self.variables: dict[str, Variable[Any]] = {}
        self.state_parent: State | None = None

    def register_variable(self, name: str, var: Variable[Any]) -> None:
        """Register a Variable by name."""
        self.variables[name] = var


class State:
    """Base class for QtPie state objects.

    State hosts Variables with declarative callbacks.
    They have no Qt dependencies.

    Example:
        @state
        class MyState(State):
            count: Variable[int] = new(0)
            name: Variable[str] = new("")

        s = MyState()
        s.count.value = 42

    Parent hierarchy:
        States can have a parent State, enabling callback bubbling.
        When a child's callback target is not found on itself, it searches
        up the state_parent chain.
    """

    # Class-level config (set up in __init_subclass__)
    _state_config: StateConfig
    # Instance-level state (set during __init__)
    _state_instance: StateInstance

    @property
    def state_parent(self) -> State | None:
        """Get the parent State in the hierarchy."""
        if hasattr(self, "_state_instance"):
            return self._state_instance.state_parent
        return None

    @state_parent.setter
    def state_parent(self, parent: State | None) -> None:
        """Set the parent State in the hierarchy."""
        if not hasattr(self, "_state_instance"):
            self._state_instance = StateInstance()
        self._state_instance.state_parent = parent

    def to_dict(self) -> dict[str, Any]:
        """Return a dict of all Variable fields with their unwrapped values.

        Only includes Variable fields (not Events, state_parent, or other attributes).
        """
        if not hasattr(self, "_state_config"):
            return {}

        result: dict[str, Any] = {}
        for name in self._state_config.variable_names:
            var = getattr(self, name, None)
            if var is not None and hasattr(var, "value"):
                result[name] = var.value
        return result

    @override
    def __repr__(self) -> str:
        """Return a repr showing all Variable fields with their unwrapped values."""
        class_name = type(self).__name__
        data = self.to_dict()
        if not data:
            return f"{class_name}()"
        items = [f"{k}={v!r}" for k, v in data.items()]
        return f"{class_name}({', '.join(items)})"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Create fresh config for this subclass
        cls._state_config = StateConfig()

        # Collect variable names from _VariableDescriptor instances
        # (NewField.__set_name__ already converted Variable[T] = new(...) to descriptors)
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, _VariableDescriptor):
                cls._state_config.variable_names.append(name)

        # Detect Event[T] annotations and create Event instances
        _process_event_annotations_for_state(cls)

        # Detect bare Variable[T] annotations (required bindings)
        _detect_required_bindings_for_state(cls)


def resolve_from_state_hierarchy(state: State, name: str) -> Event[Any] | Callable[..., Any] | None:
    """Walk state_parent chain looking for method, Event, or callable.

    Resolution order:
    1. state itself
    2. state.state_parent
    3. state.state_parent.state_parent, etc.

    Args:
        state: The starting State instance
        name: The attribute name to find (method, Event, etc.)

    Returns:
        The callable/Event if found, None otherwise.
    """
    current: State | None = state
    while current is not None:
        target = getattr(current, name, None)
        if target is not None:
            if isinstance(target, Event) or callable(target):
                return target  # type: ignore[return-value]
        current = current.state_parent
    return None


def _process_event_annotations_for_state(cls: type[State]) -> None:
    """Process Event[T] annotations and create Event instances.

    A bare annotation like `on_save: Event` or `on_changed: Event[int]`
    gets an Event() instance created on the class.
    """
    import typing

    # Get annotations including from parent classes
    hints = typing.get_type_hints(cls) if hasattr(cls, "__annotations__") else {}

    for name, hint in hints.items():
        # Skip if already has a value (e.g., on_save: Event = Event())
        if name in cls.__dict__:
            continue

        # Check if it's an Event annotation
        if is_event_hint(hint):
            # Create Event instance on the class
            setattr(cls, name, Event())
            cls._state_config.event_names.append(name)


def _detect_required_bindings_for_state(cls: type[State]) -> None:
    """Detect bare Variable[T] annotations as required bindings.

    A bare annotation like `count: Variable[int]` (no `= new()`) indicates
    the Variable must be provided via constructor injection.
    """
    from .utils.common import detect_required_bindings

    detect_required_bindings(cls, "_state_config", Variable, _RequiredBindingDescriptor)


def _wrap_init_for_state(cls: type[State], event_wiring: dict[str, str] | None = None) -> None:
    """Wrap __init__ to set up instance state and handle constructor kwargs."""
    if cls._state_config.init_wrapped:
        return

    # Store event wiring in config if provided
    if event_wiring:
        cls._state_config.event_wiring = event_wiring

    original_init = cls.__init__

    # Capture config at decoration time
    config = cls._state_config

    def wrapped_init(self: State, *args: Any, **kwargs: Any) -> None:
        # Extract Variable kwargs (match against variable_names and required_bindings)
        variable_kwargs: dict[str, Any] = {}
        all_variable_names = set(config.variable_names) | config.required_bindings
        for var_name in list(kwargs.keys()):
            if var_name in all_variable_names:
                variable_kwargs[var_name] = kwargs.pop(var_name)

        # Initialize StateInstance early so Variables have somewhere to register
        if not hasattr(self, "_state_instance"):
            self._state_instance = StateInstance()

        # Create per-instance Event objects (class-level ones are just placeholders)
        for event_name in config.event_names:
            setattr(self, event_name, Event())

        # Apply constructor variable kwargs
        if variable_kwargs:
            _apply_variable_kwargs_for_state(self, variable_kwargs)

        # Call original __init__
        original_init(self, *args, **kwargs)

        # Set up auto-parenting for Variables that hold State children
        _setup_auto_parenting(self)

        # Wire Events to handlers based on decorator kwargs
        _wire_events_for_state(self, config.event_wiring)

        # Call __setup__ hook if defined
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._state_config.init_wrapped = True


def _wire_events_for_state(instance: State, event_wiring: dict[str, str]) -> None:
    """Wire Events to handler methods based on decorator kwargs.

    For @state(on_save="_persist"), connects instance.on_save to instance._persist.
    """
    for event_name, handler_name in event_wiring.items():
        event = getattr(instance, event_name, None)
        if event is None:
            continue

        if not isinstance(event, Event):
            continue

        handler = getattr(instance, handler_name, None)
        if handler is None or not callable(handler):
            continue

        event.connect(handler)


def _setup_auto_parenting(instance: State) -> None:
    """Set up auto-parenting for Variables that hold State children.

    When a Variable[list[ChildState]] has items appended, the child's
    state_parent is automatically set to this instance.
    """
    from observant import ObservableList

    from .variable import Variable

    # Force lazy Variable creation by accessing them
    config = instance._state_config
    for var_name in config.variable_names:
        # Access the Variable to trigger its creation (via descriptor __get__)
        _ = getattr(instance, var_name, None)

    # Get the QtPieState where Variables are actually stored
    # (State uses _qtpie like Widget, not _state_instance)
    qtpie_state = getattr(instance, "_qtpie", None)
    if qtpie_state is None:
        return

    # Now hook into any ObservableLists
    for _var_name, var in qtpie_state.variables.items():
        if not isinstance(var, Variable):
            continue
        observable: Any = var.observable
        if isinstance(observable, ObservableList):
            # Hook into on_insert to auto-parent new State children
            def make_parent_hook(parent: State) -> Callable[[int, Any], None]:
                def on_insert(index: int, item: Any) -> None:
                    if isinstance(item, State):
                        item.state_parent = parent

                return on_insert

            observable.on_insert(make_parent_hook(instance))


def _apply_variable_kwargs_for_state(instance: State, variable_kwargs: dict[str, Any]) -> None:
    """Apply constructor kwargs to Variables on a State.

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
def state[S: State](cls: type[S]) -> type[S]: ...


@overload
def state[S: State](
    cls: None = None,
    **event_wiring: str,
) -> Callable[[type[S]], type[S]]: ...


def state[S: State](
    cls: type[S] | None = None,
    **event_wiring: str,
) -> type[S] | Callable[[type[S]], type[S]]:
    """Decorator to mark a class as a QtPie State.

    Usage:
        @state
        class MyState(State):
            count: Variable[int] = new(0)

    Wire Events to handlers via kwargs:
        @state(on_save="_persist")
        class MyState(State):
            on_save: Event

            def _persist(self) -> None:
                ...

    State objects process new() fields at decoration time, similar to @widget,
    but have no Qt dependencies.
    """

    def decorator(target: type[S]) -> type[S]:
        # Wrap __init__ to set up instance state
        _wrap_init_for_state(target, event_wiring if event_wiring else None)  # type: ignore[arg-type]
        return target

    if cls is not None:
        return decorator(cls)

    return decorator
