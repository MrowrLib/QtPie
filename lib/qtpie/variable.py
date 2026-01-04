"""Variable - Per-instance reactive state in QtPie widgets."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, cast, get_origin, overload, override

from observant import Observable, ObservableDict, ObservableList, ObservableProxy

# Union of all observable types
type AnyObservable[T] = Observable[T] | ObservableList[T] | ObservableDict[Any, T] | ObservableProxy[T]


def _is_primitive_type(t: type | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))


def _create_observable_for_type(inner_type: type | None, default: Any) -> AnyObservable[Any]:
    """Create the appropriate observable wrapper based on type.

    Note: Mutable defaults (list, dict, complex objects) are deep-copied
    to ensure each instance gets its own copy.
    """
    if inner_type is None:
        # No type info, use Observable with the default
        return Observable(default)

    inner_origin = get_origin(inner_type)

    # list[T] → ObservableList
    if inner_origin is list:
        if default is None:
            default = []
        else:
            default = deepcopy(default)
        return ObservableList(default)

    # dict[K, V] → ObservableDict
    if inner_origin is dict:
        if default is None:
            default = {}
        else:
            default = deepcopy(default)
        return ObservableDict(default)

    # Primitives → Observable
    if _is_primitive_type(inner_type):
        return Observable(default)

    # Complex types → ObservableProxy
    # Need to create an instance if default is None
    if default is None:
        # Try to instantiate with no args
        try:
            default = inner_type()
        except TypeError as e:
            raise ValueError(f"Cannot create Variable[{inner_type.__name__}] without a default value. Use new(default=YourClass(...)) or provide constructor args.") from e
    else:
        # Copy the default so each instance gets its own object
        default = deepcopy(default)
    return ObservableProxy(default)


class Variable[T]:
    """Per-instance variable with value and observable access.

    Works with all observable types:
    - Variable[str] → wraps Observable[str]
    - Variable[list[T]] → wraps ObservableList[T]
    - Variable[dict[K,V]] → wraps ObservableDict[K,V]
    - Variable[MyClass] → wraps ObservableProxy[MyClass]

    Usage:
        self._name.value = "hello"      # set value
        print(self._name.value)         # get value
        self._name.observable.on_change(callback)  # subscribe
        if self._name.is_dirty:         # check dirty state
        self._name.reset_dirty()        # mark as clean
    """

    _wrapper: AnyObservable[T]

    def __init__(self, wrapper: AnyObservable[T]) -> None:
        self._wrapper = wrapper

    @property
    def value(self) -> T:
        """Get the current value."""
        if isinstance(self._wrapper, Observable):
            return self._wrapper.get()
        if isinstance(self._wrapper, ObservableList):
            return cast(T, self._wrapper.to_list())
        if isinstance(self._wrapper, ObservableDict):
            return cast(T, self._wrapper.to_dict())
        # Must be ObservableProxy (pyright narrows type)
        return self._wrapper.unwrap()

    @value.setter
    def value(self, val: T) -> None:
        """Set the value (triggers change notifications)."""
        if isinstance(self._wrapper, Observable):
            self._wrapper.set(val)
        elif isinstance(self._wrapper, ObservableList):
            # Replace entire list
            self._wrapper.clear()
            if isinstance(val, list):
                self._wrapper.extend(cast(list[Any], val))
        elif isinstance(self._wrapper, ObservableDict):
            # Replace entire dict
            self._wrapper.clear()
            if isinstance(val, dict):
                self._wrapper.update(cast(dict[Any, Any], val))
        else:
            # Must be ObservableProxy - can't replace target
            raise TypeError("Cannot replace ObservableProxy value. Modify fields directly.")

    @property
    def observable(self) -> AnyObservable[T]:
        """Get the underlying observable (Observable, ObservableList, etc.)."""
        return self._wrapper

    @property
    def is_dirty(self) -> Observable[bool]:
        """Dirty state - usable as bool or Observable."""
        return self._wrapper.is_dirty

    def reset_dirty(self) -> None:
        """Mark current value as clean."""
        self._wrapper.reset_dirty()

    def on_change(self, callback: Any) -> None:
        """Register a change callback on the underlying wrapper."""
        self._wrapper.on_change(callback)

    # Descriptor protocol for pyright - tells it that assignment accepts T or Variable[T]
    if TYPE_CHECKING:

        @overload
        def __get__(self, obj: None, owner: type) -> Variable[T]: ...
        @overload
        def __get__(self, obj: object, owner: type) -> Variable[T]: ...
        def __get__(self, obj: object | None, owner: type) -> Variable[T]: ...

        @overload
        def __set__(self, obj: object, value: T) -> None: ...
        @overload
        def __set__(self, obj: object, value: Variable[T]) -> None: ...
        def __set__(self, obj: object, value: T | Variable[T]) -> None: ...

    # Augmented assignment operators - allow self._count += 1
    def __iadd__(self, other: Any) -> Variable[T]:
        self.value = self.value + other  # type: ignore[operator]
        return self

    def __isub__(self, other: Any) -> Variable[T]:
        self.value = self.value - other  # type: ignore[operator]
        return self

    def __imul__(self, other: Any) -> Variable[T]:
        self.value = self.value * other  # type: ignore[operator]
        return self

    def __itruediv__(self, other: Any) -> Variable[T]:
        self.value = self.value / other  # type: ignore[operator]
        return self

    def __ifloordiv__(self, other: Any) -> Variable[T]:
        self.value = self.value // other  # type: ignore[operator]
        return self

    def __imod__(self, other: Any) -> Variable[T]:
        self.value = self.value % other  # type: ignore[operator]
        return self


class RecordVariable[T]:
    """Variable specifically for Widget[T] records.

    Has properly typed `observable` that returns `ObservableProxy[T]`
    instead of the union type, so pyright understands field access.

    Supports direct field access: self.record.name = "x" forwards to the proxy.

    Same interface as Variable[T] but specialized for records.
    """

    __slots__ = ("_wrapper",)

    def __init__(self, wrapper: ObservableProxy[T]) -> None:
        object.__setattr__(self, "_wrapper", wrapper)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the underlying proxy.

        Returns the actual value (not Observable) for field access.
        Use .observable.field for the Observable itself.
        """
        result = getattr(self._wrapper, name)
        # Unwrap Observable to return actual value
        if isinstance(result, Observable):
            return cast(Any, result.get())
        return result

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        """Forward attribute setting to the underlying proxy."""
        if name == "_wrapper":
            object.__setattr__(self, name, value)
        else:
            setattr(self._wrapper, name, value)

    @property
    def value(self) -> T:
        """Get the current value."""
        return cast(T, self._wrapper.unwrap())

    @value.setter
    def value(self, val: T) -> None:
        """Set the value by replacing proxy target."""
        self._wrapper._target = val  # type: ignore[attr-defined]
        self._wrapper._notify_change()  # type: ignore[attr-defined]

    @property
    def observable(self) -> ObservableProxy[T]:
        """Get the underlying ObservableProxy."""
        return self._wrapper

    @property
    def is_dirty(self) -> Observable[bool]:
        """Dirty state - usable as bool or Observable."""
        return cast(Observable[bool], self._wrapper.is_dirty)

    def reset_dirty(self) -> None:
        """Mark current value as clean."""
        self._wrapper.reset_dirty()

    def on_change(self, callback: Any) -> None:
        """Register a change callback on the underlying wrapper."""
        self._wrapper.on_change(callback)

    def __call__(self) -> RecordVariable[T]:
        """Call syntax: self.record().is_dirty returns RecordVariable for state access."""
        return self

    # Descriptor protocol for pyright - assignment accepts T or RecordVariable[T]
    if TYPE_CHECKING:

        @overload
        def __get__(self, obj: None, owner: type) -> RecordVariable[T]: ...
        @overload
        def __get__(self, obj: object, owner: type) -> RecordVariable[T]: ...
        def __get__(self, obj: object | None, owner: type) -> RecordVariable[T]: ...

        @overload
        def __set__(self, obj: object, value: T) -> None: ...
        @overload
        def __set__(self, obj: object, value: RecordVariable[T]) -> None: ...
        def __set__(self, obj: object, value: T | RecordVariable[T]) -> None: ...


class _VariableDescriptor[T]:
    """Descriptor that returns per-instance Variable objects.

    This is an internal class. Users see Variable[T] in type hints.
    """

    def __init__(self, default: T, name: str, inner_type: type | None = None) -> None:
        self._default = default
        self._name = name
        self._inner_type = inner_type

    @overload
    def __get__(self, obj: None, objtype: type) -> Variable[T]: ...
    @overload
    def __get__(self, obj: object, objtype: type | None) -> Variable[T]: ...
    def __get__(self, obj: object | None, objtype: type | None = None) -> Variable[T]:
        if obj is None:
            # Class access - return self but typed as Variable for Pyright
            return self  # type: ignore[return-value]

        # Get or create per-instance Variable in _qtpie.variables
        from .widget import QtPieState

        if not hasattr(obj, "_qtpie"):
            # Lazily create state if accessed before __init__
            obj._qtpie = QtPieState(obj)  # type: ignore[arg-type, attr-defined]
        qtpie_state = cast(QtPieState, obj._qtpie)  # type: ignore[attr-defined]

        if self._name not in qtpie_state.variables:
            wrapper = _create_observable_for_type(self._inner_type, self._default)
            var: Variable[T] = Variable(wrapper)
            qtpie_state.register_variable(self._name, var)

        return qtpie_state.variables[self._name]

    @overload
    def __set__(self, obj: object, value: T) -> None: ...
    @overload
    def __set__(self, obj: object, value: Variable[T]) -> None: ...
    def __set__(self, obj: object, value: T | Variable[T]) -> None:
        """Allow direct assignment: self._name = value sets .value."""
        if isinstance(value, Variable):
            # Edge case: assigning a Variable directly (shouldn't normally happen)
            from .widget import QtPieState

            if not hasattr(obj, "_qtpie"):
                obj._qtpie = QtPieState(obj)  # type: ignore[arg-type, attr-defined]
            qtpie_state = cast(QtPieState, obj._qtpie)  # type: ignore[attr-defined]
            qtpie_state.variables[self._name] = value
        else:
            # Normal case: self._name = "hello" → sets the value
            var = self.__get__(obj, type(obj))
            var.value = value


def create_variable_descriptor(default: Any, name: str, inner_type: type | None = None) -> Any:
    """Create a variable descriptor. Used by NewField."""
    return _VariableDescriptor(default, name, inner_type)
