"""Variable - Per-instance reactive state in QtPie widgets."""

from typing import Any, overload

from observant import Observable


class Variable[T]:
    """Per-instance variable with value and observable access.

    Usage:
        self._name.value = "hello"      # set value
        print(self._name.value)         # get value
        self._name.observable.on_change(callback)  # subscribe
        bind(self._name).to(widget)     # bind to widget
    """

    def __init__(self, observable: Observable[T]) -> None:
        self._observable = observable

    @property
    def value(self) -> T:
        """Get the current value."""
        return self._observable.get()

    @value.setter
    def value(self, val: T) -> None:
        """Set the value (triggers change notifications)."""
        self._observable.set(val)

    @property
    def observable(self) -> Observable[T]:
        """Get the underlying Observable for subscriptions."""
        return self._observable


class _VariableDescriptor[T]:
    """Descriptor that returns per-instance Variable objects.

    This is an internal class. Users see Variable[T] in type hints.
    """

    def __init__(self, default: T) -> None:
        self._default = default
        self._name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    @overload
    def __get__(self, obj: None, objtype: type) -> Variable[T]: ...
    @overload
    def __get__(self, obj: object, objtype: type | None) -> Variable[T]: ...
    def __get__(self, obj: object | None, objtype: type | None = None) -> Variable[T]:
        if obj is None:
            # Class access - return self but typed as Variable for Pyright
            return self  # type: ignore[return-value]

        # Get or create per-instance Variable
        key = f"_var_{self._name}"
        if not hasattr(obj, key):
            observable: Observable[T] = Observable(self._default)
            var: Variable[T] = Variable(observable)
            object.__setattr__(obj, key, var)
        return getattr(obj, key)

    @overload
    def __set__(self, obj: object, value: T) -> None: ...
    @overload
    def __set__(self, obj: object, value: Variable[T]) -> None: ...
    def __set__(self, obj: object, value: T | Variable[T]) -> None:
        """Allow direct assignment: self._name = value sets .value."""
        if isinstance(value, Variable):
            # Edge case: assigning a Variable directly (shouldn't normally happen)
            key = f"_var_{self._name}"
            object.__setattr__(obj, key, value)
        else:
            # Normal case: self._name = "hello" → sets the value
            var = self.__get__(obj, type(obj))
            var.value = value


def create_variable_descriptor(default: Any) -> Any:
    """Create a variable descriptor. Used by NewField."""
    return _VariableDescriptor(default)
