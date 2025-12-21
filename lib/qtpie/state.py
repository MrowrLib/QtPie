"""Reactive state for widget fields - powered by ObservableProxy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast, overload

from observant import Observable, ObservableProxy

# Metadata key to identify state proxies on instances
STATE_PROXY_ATTR = "_qtpie_state_proxies"
# Metadata key for object observables (persists across proxy replacements)
STATE_OBJECT_OBS_ATTR = "_qtpie_state_object_observables"

# Primitive types that need wrapping in a container
_PRIMITIVE_TYPES = (int, float, str, bool, bytes, type(None))


def _is_primitive(value: Any) -> bool:
    """Check if a value is a primitive type."""
    return isinstance(value, _PRIMITIVE_TYPES)


@dataclass
class _PrimitiveContainer[T]:
    """Container for primitive values so they can be wrapped with ObservableProxy."""

    value: T


class ReactiveDescriptor[T]:
    """
    Descriptor that makes a field reactive using ObservableProxy.

    When accessed, returns the actual value (e.g., int, str, Dog).
    When assigned, updates the value and notifies observers.

    All values are backed by ObservableProxy:
    - Primitives (int, str, etc.) are wrapped in _PrimitiveContainer
    - Objects (dataclasses, etc.) are wrapped directly
    """

    def __init__(self, default: T | None = None) -> None:
        self.default = default
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def get_proxy(self, obj: object) -> ObservableProxy[Any]:
        """Get or create the ObservableProxy for this field on the instance."""
        proxies: dict[str, ObservableProxy[Any]] = getattr(obj, STATE_PROXY_ATTR, None) or {}
        if not hasattr(obj, STATE_PROXY_ATTR):
            setattr(obj, STATE_PROXY_ATTR, proxies)

        if self.name not in proxies:
            if _is_primitive(self.default):
                # Wrap primitive in container
                container = _PrimitiveContainer(self.default)
                proxies[self.name] = ObservableProxy(container, sync=True)
            else:
                # Wrap object directly
                proxies[self.name] = ObservableProxy(self.default, sync=True)

        return proxies[self.name]

    def get_observable(self, obj: object) -> Observable[T]:
        """Get the observable for this field's value."""
        proxy = self.get_proxy(obj)
        if _is_primitive(self.default):
            # For primitives, the value is in container.value
            return cast(Observable[T], proxy.observable(object, "value"))
        else:
            # For objects, get or create a persistent _ObjectObservable
            # This survives proxy replacement and holds callbacks
            obj_observables: dict[str, _ObjectObservable[Any]] = getattr(obj, STATE_OBJECT_OBS_ATTR, None) or {}
            if not hasattr(obj, STATE_OBJECT_OBS_ATTR):
                setattr(obj, STATE_OBJECT_OBS_ATTR, obj_observables)

            if self.name not in obj_observables:
                obj_observables[self.name] = _ObjectObservable(self.name, obj)

            return cast(Observable[T], obj_observables[self.name])

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> ReactiveDescriptor[T]: ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> T: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> T | ReactiveDescriptor[T]:
        if obj is None:
            return self
        proxy = self.get_proxy(obj)
        if _is_primitive(self.default):
            return cast(T, proxy.observable(object, "value").get())
        else:
            # For objects, return the proxied object itself
            return cast(T, proxy.get())

    def __set__(self, obj: object, value: T) -> None:
        proxies: dict[str, ObservableProxy[Any]] = getattr(obj, STATE_PROXY_ATTR, None) or {}

        if _is_primitive(self.default):
            proxy = self.get_proxy(obj)
            proxy.observable(object, "value").set(value)
        else:
            # For objects, replace the entire proxy with a new one
            proxies[self.name] = ObservableProxy(value, sync=True)
            if not hasattr(obj, STATE_PROXY_ATTR):
                setattr(obj, STATE_PROXY_ATTR, proxies)

            # Notify any object observable callbacks
            obj_observables: dict[str, _ObjectObservable[Any]] = getattr(obj, STATE_OBJECT_OBS_ATTR, None) or {}
            if self.name in obj_observables:
                obj_observables[self.name].notify(value)


class _ObjectObservable[T]:
    """
    Observable wrapper for object-type state fields.

    This provides an Observable-like interface for the whole object,
    allowing subscriptions to be notified when the object is replaced.
    Stored persistently so callbacks survive proxy replacement.
    """

    def __init__(self, field_name: str, widget: object) -> None:
        self._field_name = field_name
        self._widget = widget
        self._callbacks: list[Any] = []

    def get(self) -> T:
        # Get current value from widget
        return cast(T, getattr(self._widget, self._field_name))

    def set(self, value: T) -> None:
        # Set via widget (triggers __set__)
        setattr(self._widget, self._field_name, value)

    def on_change(self, callback: Any) -> None:
        self._callbacks.append(callback)

    def notify(self, value: T) -> None:
        """Called by ReactiveDescriptor.__set__ when object is replaced."""
        for cb in self._callbacks:
            cb(value)


class _SubscriptedState[T]:
    """Helper class for state[Type]() syntax - returned by state.__class_getitem__."""

    def __call__(self, default: T | None = None) -> T:
        """Create a ReactiveDescriptor with the given default."""
        return cast(T, ReactiveDescriptor(default))


class state[T]:
    """
    Mark a field as reactive state.

    Usage:
        # Type inferred from default
        count: int = state(0)
        name: str = state("")

        # Explicit type (for optionals or when default is None)
        dog: Dog | None = state[Dog | None]()
        user: User | None = state[User | None](None)

        # Pre-initialized with specific value
        config: Config = state(Config(debug=True))

    When you assign to a state field, all bound widgets update automatically:

        def increment(self):
            self.count += 1  # Just works - bound widgets update

    Bindings:

        count: int = state(0)
        label: QLabel = make(QLabel, bind="count")  # Auto-updates when count changes

    """

    @overload
    def __new__(cls, default: T) -> T: ...

    @overload
    def __new__(cls) -> None: ...

    def __new__(cls, default: T | None = None) -> T:  # type: ignore[misc]
        return cast(T, ReactiveDescriptor(default))

    def __class_getitem__(cls, item: type) -> _SubscriptedState[Any]:
        """Support state[Type]() syntax for explicit type parameters."""
        return _SubscriptedState()


def get_state_observable(obj: object, field_name: str) -> Observable[Any] | None:
    """
    Get the Observable for a state field on an object.

    This is used by the widget decorator to bind state fields to widgets.

    Args:
        obj: The widget instance
        field_name: The name of the state field

    Returns:
        The Observable for the field, or None if not a state field
    """
    # Get the descriptor from the class
    descriptor = getattr(type(obj), field_name, None)
    if not isinstance(descriptor, ReactiveDescriptor):
        return None

    return cast(Observable[Any], descriptor.get_observable(obj))


def get_state_proxy(obj: object, field_name: str) -> ObservableProxy[object] | None:
    """
    Get the ObservableProxy for a state field on an object.

    This is used for nested path bindings like "dog.name".

    Args:
        obj: The widget instance
        field_name: The name of the state field

    Returns:
        The ObservableProxy for the field, or None if not a state field
    """
    # Get the descriptor from the class
    descriptor = getattr(type(obj), field_name, None)
    if not isinstance(descriptor, ReactiveDescriptor):
        return None

    # For primitives wrapped in container, the proxy is on the container
    # For nested paths, caller will use observable_for_path which needs the raw object proxy
    proxy = descriptor.get_proxy(obj)

    # If it's a primitive (wrapped in container), nested paths don't make sense
    # But we still return the proxy - caller can decide what to do
    # Cast descriptor to get proper typing (getattr returns Unknown for generic descriptors)
    typed_descriptor = cast(ReactiveDescriptor[object], descriptor)
    if _is_primitive(typed_descriptor.default):
        return None  # Nested paths don't work on primitives

    return cast(ObservableProxy[object], proxy)


def is_state_descriptor(value: object) -> bool:
    """Check if a value is a ReactiveDescriptor (state field)."""
    return isinstance(value, ReactiveDescriptor)
