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
from typing import Any, cast, overload, override

from .event import Event, is_event_hint
from .variable import Variable, _RequiredBindingDescriptor, _VariableDescriptor

__all__ = ["Service", "State", "service", "state", "resolve_from_state_hierarchy"]


class StateConfig:
    """Class-level configuration for a State."""

    __slots__ = ("variable_names", "required_bindings", "init_wrapped", "event_names", "event_wiring", "event_new_fields")

    def __init__(self) -> None:
        self.variable_names: list[str] = []
        self.required_bindings: set[str] = set()
        self.init_wrapped: bool = False
        # Event annotation names (e.g., ["on_save", "on_changed"])
        self.event_names: list[str] = []
        # Event-to-handler wiring from decorator kwargs (e.g., {"on_save": "_persist"})
        self.event_wiring: dict[str, str] = {}
        # Event[T] = new(on=...) fields - stores NewField for wiring
        self.event_new_fields: dict[str, Any] = {}  # name -> NewField


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

    def event(self, name: str) -> Event[Any]:
        """Resolve an Event by name from state_parent hierarchy.

        Searches in this order:
        1. This state (with and without underscore prefix)
        2. Parent state hierarchy (walking up state_parent chain)

        Args:
            name: The event name to resolve (e.g., "on_save" or "_on_save").

        Returns:
            The resolved Event.

        Raises:
            AttributeError: If event not found in hierarchy.

        Example:
            event = self.event("on_save")  # Gets Event from hierarchy
        """
        # Try on self (with underscore variants)
        for attr_name in [name, f"_{name}"]:
            if hasattr(self, attr_name):
                attr = getattr(self, attr_name)
                if isinstance(attr, Event):
                    return cast(Event[Any], attr)

        # Walk state_parent chain
        current: State | None = self.state_parent
        while current is not None:
            for attr_name in [name, f"_{name}"]:
                if hasattr(current, attr_name):
                    attr = getattr(current, attr_name)
                    if isinstance(attr, Event):
                        return cast(Event[Any], attr)
            current = current.state_parent

        raise AttributeError(f"Event '{name}' not found on {type(self).__name__} or in state_parent hierarchy")

    def emit_event(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Emit an Event by name, searching up the state_parent hierarchy.

        Convenience method that combines event() lookup with emit().

        Args:
            name: The event name (e.g., "on_save")
            *args: Arguments to pass to event.emit()
            **kwargs: Keyword arguments to pass to event.emit()

        Raises:
            AttributeError: If event not found in hierarchy

        Example:
            self.emit_event("on_save")
            self.emit_event("on_data_changed", new_value)
        """
        evt = self.event(name)
        evt.emit(*args, **kwargs)

    # fmt: off
    # var() overloads for type inference
    @overload
    def var(self, name: str) -> Any: ...
    @overload
    def var[T1](self, name: str, t1: type[T1]) -> T1: ...
    @overload
    def var[T1, T2](self, name: str, t1: type[T1], t2: type[T2]) -> T1 | T2: ...
    @overload
    def var[T1, T2, T3](self, name: str, t1: type[T1], t2: type[T2], t3: type[T3]) -> T1 | T2 | T3: ...
    @overload
    def var[T1, T2, T3, T4](self, name: str, t1: type[T1], t2: type[T2], t3: type[T3], t4: type[T4]) -> T1 | T2 | T3 | T4: ...
    # With None
    @overload
    def var[T1](self, name: str, t1: type[T1], t2: None) -> T1 | None: ...
    @overload
    def var[T1, T2](self, name: str, t1: type[T1], t2: type[T2], t3: None) -> T1 | T2 | None: ...
    @overload
    def var[T1, T2, T3](self, name: str, t1: type[T1], t2: type[T2], t3: type[T3], t4: None) -> T1 | T2 | T3 | None: ...
    # fmt: on
    def var(self, name: str, *types: type[Any] | None) -> Any:  # pyright: ignore[reportInconsistentOverload]
        """Resolve a variable by name from state_parent hierarchy.

        Searches in this order:
        1. This state (with and without underscore prefix)
        2. Parent state hierarchy (walking up state_parent chain)

        Args:
            name: The variable name to resolve (e.g., "count" or "_count").
            *types: Optional type(s) for type inference. Pass None as last arg for optional.

        Returns:
            The resolved value (unwrapped from Variable if applicable).

        Raises:
            AttributeError: If variable not found in hierarchy.

        Example:
            x = self.var("count")  # Returns Any
            x = self.var("count", int)  # Returns int
            x = self.var("pet", Dog, Cat)  # Returns Dog | Cat
            x = self.var("pet", Dog, None)  # Returns Dog | None
        """
        # Try on self (with underscore variants)
        for attr_name in [name, f"_{name}"]:
            if hasattr(self, attr_name):
                attr = getattr(self, attr_name)
                if isinstance(attr, Variable):
                    return attr.value
                return attr

        # Walk state_parent chain
        current: State | None = self.state_parent
        while current is not None:
            for attr_name in [name, f"_{name}"]:
                if hasattr(current, attr_name):
                    attr = getattr(current, attr_name)
                    if isinstance(attr, Variable):
                        return attr.value
                    return attr
            current = current.state_parent

        raise AttributeError(f"Variable '{name}' not found on {type(self).__name__} or in state_parent hierarchy")

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

    For Event = new(on=...) syntax, the NewField is removed and the
    on= handler is stored in config for later wiring.
    """
    import typing

    from .new_field import NewField

    # Get annotations including from parent classes
    hints = typing.get_type_hints(cls) if hasattr(cls, "__annotations__") else {}

    for name, hint in hints.items():
        # Check if it's an Event annotation
        if not is_event_hint(hint):
            continue

        # Check if there's a NewField on this name (Event = new(on=...))
        existing = cls.__dict__.get(name)
        if isinstance(existing, NewField):
            # Extract the on= handler and store in config
            if existing.event_on is not None:
                cls._state_config.event_new_fields[name] = existing
            # Remove the NewField so we can create the Event
            delattr(cls, name)

        # Skip if already has a non-NewField value (e.g., on_save: Event = Event())
        if name in cls.__dict__:
            continue

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
        # Extract _qtpie_parent if passed (for auto-parenting child States)
        qtpie_parent = kwargs.pop("_qtpie_parent", None)
        if qtpie_parent is not None:
            self.state_parent = qtpie_parent

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

        # Wire Events from new(on=...) fields
        _wire_event_new_fields_for_state(self, config.event_new_fields)

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


def _wire_event_new_fields_for_state(instance: State, event_new_fields: dict[str, Any]) -> None:
    """Wire Events from new(on=...) fields to handlers.

    For on_save: Event = new(on="_persist"), connects instance.on_save to instance._persist.
    Supports:
    - String method names: on="_persist"
    - Callables: on=lambda: print("saved")
    - Expression strings: on="{print('saved')}"
    """
    from .bindings import is_format_string
    from .signals.expression_handler import create_signal_expression_handler

    for event_name, field in event_new_fields.items():
        if field.event_on is None:
            continue

        event = getattr(instance, event_name, None)
        if event is None or not isinstance(event, Event):
            continue

        handler = field.event_on
        if isinstance(handler, str):
            # Check if it's an expression (format string with {})
            if is_format_string(handler):
                # Create expression handler for State context
                expr_handler = create_signal_expression_handler(instance, handler, ["#state", "#self"])
                event.connect(expr_handler)
            else:
                # Simple string handler - method name
                target = getattr(instance, handler, None)
                if target is None:
                    raise AttributeError(f"{type(instance).__name__} has no method '{handler}' for Event connection {event_name} = new(on=\"{handler}\")")
                if callable(target):
                    event.connect(target)
                else:
                    raise AttributeError(f'{type(instance).__name__}.{handler} is not callable for Event connection {event_name} = new(on="{handler}")')
        elif callable(handler):
            event.connect(handler)


def _setup_auto_parenting(instance: State) -> None:
    """Set up auto-parenting for Variables that hold State children.

    - Direct State children: state_parent is set immediately
    - List[State] children: state_parent is set on insert
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

    for _var_name, var in qtpie_state.variables.items():
        if not isinstance(var, Variable):
            continue

        # Check if current value is a State - set state_parent immediately
        current_value = var.value
        if isinstance(current_value, State):
            current_value.state_parent = instance

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


# Aliases for semantic distinction (Services are States with a different intent)
Service = State
"""Alias for State. Services are States intended for application-level logic."""


@overload
def service[S: State](cls: type[S]) -> type[S]: ...


@overload
def service[S: State](
    cls: None = None,
    **event_wiring: str,
) -> Callable[[type[S]], type[S]]: ...


def service[S: State](
    cls: type[S] | None = None,
    **event_wiring: str,
) -> type[S] | Callable[[type[S]], type[S]]:
    """Alias for @state decorator. Use for application-level services.

    Usage:
        @service
        class ApiService(Service):
            base_url: Variable[str] = new("https://api.example.com")

    Semantically equivalent to @state, but conveys intent for service-layer logic.
    """
    return state(cls, **event_wiring)
