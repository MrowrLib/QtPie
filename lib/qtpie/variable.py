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

    def __init__(self, default: T, name: str) -> None:
        self._default = default
        self._name = name

    @overload
    def __get__(self, obj: None, objtype: type) -> Variable[T]: ...
    @overload
    def __get__(self, obj: object, objtype: type | None) -> Variable[T]: ...
    def __get__(self, obj: object | None, objtype: type | None = None) -> Variable[T]:
        if obj is None:
            # Class access - return self but typed as Variable for Pyright
            return self  # type: ignore[return-value]

        # Get or create per-instance Variable in _qtpie.variables
        qtpie_state = obj.__dict__.get("_qtpie")
        if qtpie_state is None:
            # Lazily create state if accessed before __init__
            from .widget import QtPieState

            qtpie_state = QtPieState(obj)  # type: ignore[arg-type]
            obj.__dict__["_qtpie"] = qtpie_state

        if self._name not in qtpie_state.variables:
            observable: Observable[T] = Observable(self._default)
            var: Variable[T] = Variable(observable)
            qtpie_state.variables[self._name] = var

        return qtpie_state.variables[self._name]

    @overload
    def __set__(self, obj: object, value: T) -> None: ...
    @overload
    def __set__(self, obj: object, value: Variable[T]) -> None: ...
    def __set__(self, obj: object, value: T | Variable[T]) -> None:
        """Allow direct assignment: self._name = value sets .value."""
        if isinstance(value, Variable):
            # Edge case: assigning a Variable directly (shouldn't normally happen)
            qtpie_state = obj.__dict__.get("_qtpie")
            if qtpie_state is None:
                from .widget import QtPieState

                qtpie_state = QtPieState(obj)  # type: ignore[arg-type]
                obj.__dict__["_qtpie"] = qtpie_state
            qtpie_state.variables[self._name] = value
        else:
            # Normal case: self._name = "hello" → sets the value
            var = self.__get__(obj, type(obj))
            var.value = value


def create_variable_descriptor(default: Any, name: str) -> Any:
    """Create a variable descriptor. Used by NewField."""
    return _VariableDescriptor(default, name)
