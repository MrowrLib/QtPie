"""Reactive state for widget fields."""

from __future__ import annotations

from typing import Any, cast, overload

from observant import Observable, ObservableProxy

# Metadata key to identify state descriptors
STATE_OBSERVABLE_ATTR = "_qtpie_state_observables"
STATE_PROXY_ATTR = "_qtpie_state_proxies"

# Primitive types that don't need ObservableProxy
_PRIMITIVE_TYPES = (int, float, str, bool, bytes, type(None))


def _is_primitive(value: Any) -> bool:
    """Check if a value is a primitive type."""
    return isinstance(value, _PRIMITIVE_TYPES)


class ReactiveDescriptor[T]:
    """
    Descriptor that makes a field reactive.

    When accessed, returns the actual value (e.g., int, str, Dog).
    When assigned, updates the value and notifies observers.

    For object types (non-primitives), internally uses ObservableProxy
    to support nested path bindings like "dog.name".
    """

    def __init__(self, default: T | None = None) -> None:
        self.default = default
        self.name: str = ""
        self.private_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.private_name = f"_state_{name}"

    def _get_observable(self, obj: object) -> Observable[T]:
        """Get or create the observable for this field on the instance."""
        observables: dict[str, Observable[Any]] = getattr(obj, STATE_OBSERVABLE_ATTR, None) or {}
        if not hasattr(obj, STATE_OBSERVABLE_ATTR):
            setattr(obj, STATE_OBSERVABLE_ATTR, observables)

        if self.name not in observables:
            # Create observable with initial value
            initial = getattr(obj, self.private_name, self.default)
            observables[self.name] = Observable(initial)

        return observables[self.name]

    def get_proxy(self, obj: object) -> ObservableProxy[T] | None:
        """Get or create an ObservableProxy for object types.

        Used by the widget decorator for nested path bindings.
        """
        value = self._get_observable(obj).get()

        # Only create proxy for non-primitive values
        if value is None or _is_primitive(value):
            return None

        proxies: dict[str, ObservableProxy[Any]] = getattr(obj, STATE_PROXY_ATTR, None) or {}
        if not hasattr(obj, STATE_PROXY_ATTR):
            setattr(obj, STATE_PROXY_ATTR, proxies)

        # Create proxy if it doesn't exist
        # Note: The proxy cache is invalidated in __set__ when the value changes
        if self.name not in proxies:
            proxies[self.name] = ObservableProxy(value, sync=True)

        return proxies[self.name]

    @overload
    def __get__(self, obj: None, objtype: type | None = None) -> ReactiveDescriptor[T]: ...

    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> T: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> T | ReactiveDescriptor[T]:
        if obj is None:
            return self
        return self._get_observable(obj).get()

    def __set__(self, obj: object, value: T) -> None:
        self._get_observable(obj).set(value)
        # Invalidate proxy cache when value changes
        proxies = getattr(obj, STATE_PROXY_ATTR, None)
        if proxies and self.name in proxies:
            del proxies[self.name]


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
    observables = getattr(obj, STATE_OBSERVABLE_ATTR, None)
    if observables is None:
        return None
    return observables.get(field_name)


def get_state_proxy(obj: object, field_name: str) -> ObservableProxy[object] | None:
    """
    Get the ObservableProxy for a state field on an object.

    This is used for nested path bindings like "dog.name".

    Args:
        obj: The widget instance
        field_name: The name of the state field

    Returns:
        The ObservableProxy for the field, or None if not a state field or primitive
    """
    # First, get the descriptor from the class
    descriptor = getattr(type(obj), field_name, None)
    if not isinstance(descriptor, ReactiveDescriptor):
        return None

    # Use the descriptor's method to get/create the proxy
    # Cast needed because ReactiveDescriptor is generic and we lose type info via getattr
    return cast(ObservableProxy[object] | None, descriptor.get_proxy(obj))


def is_state_descriptor(value: object) -> bool:
    """Check if a value is a ReactiveDescriptor (state field)."""
    return isinstance(value, ReactiveDescriptor)
