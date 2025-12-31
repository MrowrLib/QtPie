"""Variable - Descriptor for reactive state in QtPie widgets."""

from typing import Self, overload

from observant import Observable


class Variable[T]:
    """Descriptor for reactive state fields.

    Usage:
        @new_fields
        class MyWidget:
            _name: Variable[str] = new("")

        obj = MyWidget()
        obj._name = "hello"  # Reactive! Triggers on_change callbacks
    """

    def __init__(self, default: T) -> None:
        self._default = default
        self._name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def _get_observable(self, obj: object) -> Observable[T]:
        """Get or create the Observable for this instance."""
        key = f"_obs_{self._name}"
        if not hasattr(obj, key):
            object.__setattr__(obj, key, Observable(self._default))
        obs: Observable[T] = getattr(obj, key)
        return obs

    @overload
    def __get__(self, obj: None, objtype: type) -> Self: ...
    @overload
    def __get__(self, obj: object, objtype: type | None) -> T: ...
    def __get__(self, obj: object | None, objtype: type | None = None) -> T | Self:
        if obj is None:
            return self
        return self._get_observable(obj).get()

    def __set__(self, obj: object, value: T) -> None:
        self._get_observable(obj).set(value)

    def observable(self, obj: object) -> Observable[T]:
        """Get the Observable for an instance. Useful for on_change callbacks."""
        return self._get_observable(obj)
