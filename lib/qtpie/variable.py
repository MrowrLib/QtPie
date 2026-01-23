"""Variable - Per-instance reactive state in QtPie widgets."""

from __future__ import annotations

import types
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast, get_args, get_origin, overload, override

from observant import (
    AnyObservable,
    Observable,
    ObservableDict,
    ObservableList,
    ObservableProxy,
    ObservableSet,
    ValidatorFn,
)

from .utils.common import is_primitive_type, is_signal_on_type


class NoDefault:
    """Sentinel for 'no default provided' (distinct from None which is a valid default)."""

    __slots__ = ()


NO_DEFAULT = NoDefault()

# TypeVars for list/dict/set item types (used in overloads)
_ItemT = TypeVar("_ItemT")
_KeyT = TypeVar("_KeyT")
_ValT = TypeVar("_ValT")
_SetItemT = TypeVar("_SetItemT")


def _create_observable_for_type(
    inner_type: type | types.UnionType | None,
    default: Any,
    inner_kwargs: dict[str, Any] | None = None,
) -> AnyObservable[Any]:
    """Create the appropriate observable wrapper based on type.

    Args:
        inner_type: The type inside Variable[T], e.g., str, list[int], MyClass, etc.
        default: The default value, or NO_DEFAULT if no default was provided.
        inner_kwargs: Constructor kwargs for inner_type (for complex types).
    """
    # Check if no default was provided (distinct from None which is a valid default)
    no_default_provided = isinstance(default, NoDefault)

    if inner_type is None:
        # No type info, use Observable with the default
        return Observable(None if no_default_provided else default)

    inner_origin = get_origin(inner_type)

    # list[T] → ObservableList
    if inner_origin is list:
        if no_default_provided or default is None:
            default = []
        return ObservableList(default)

    # dict[K, V] → ObservableDict
    if inner_origin is dict:
        if no_default_provided or default is None:
            default = {}
        return ObservableDict(default)

    # set[T] → ObservableSet
    if inner_origin is set:
        if no_default_provided or default is None:
            default = set()  # pyright: ignore[reportUnknownVariableType]
        return ObservableSet(default)

    # Primitives → Observable
    if is_primitive_type(inner_type):
        return Observable(None if no_default_provided else default)

    # Qt value types (QIcon, QPixmap, etc.) → Observable
    # These are value types, not objects with fields, so treat like primitives
    if not no_default_provided:
        try:
            from qtpy.QtGui import QIcon, QPixmap

            if isinstance(default, (QIcon, QPixmap)):
                return Observable(default)
        except ImportError:
            pass

    # Union types (e.g., str | None, int | None, MyClass | None)
    if isinstance(inner_type, types.UnionType):
        type_args = get_args(inner_type)
        # Check if all args are primitive types (including None)
        if all(is_primitive_type(t) for t in type_args):
            return Observable(None if no_default_provided else default)

        # For T | None unions with complex type T, extract T and construct it
        if no_default_provided:
            non_none_types = [t for t in type_args if t is not type(None)]
            if len(non_none_types) == 1:
                # It's T | None - try to construct T()
                concrete_type = non_none_types[0]
                if isinstance(concrete_type, type):
                    try:
                        if inner_kwargs:
                            default = concrete_type(**inner_kwargs)
                        else:
                            default = concrete_type()
                    except TypeError as e:
                        raise ValueError(f"Cannot create Variable[{inner_type!r}] without a default value. Use new(default={concrete_type.__name__}(...)) or provide constructor args.") from e
                    return ObservableProxy(default)
            # Multi-type union like T1 | T2 | None - can't know which to construct
            raise ValueError(f"Cannot create Variable[{inner_type!r}] without a default value. Use new(default=...) or provide constructor args.")
        # Has a default value - wrap it in ObservableProxy
        return ObservableProxy(default)

    # Complex types → ObservableProxy
    # Need to create an instance if no default was provided
    if no_default_provided:
        # inner_type is a regular type here (not UnionType)
        assert isinstance(inner_type, type)
        # Try to instantiate with inner_kwargs (or no args if none provided)
        try:
            if inner_kwargs:
                default = inner_type(**inner_kwargs)
            else:
                default = inner_type()
        except TypeError as e:
            raise ValueError(f"Cannot create Variable[{inner_type.__name__}] without a default value. Use new(default=YourClass(...)) or provide constructor args.") from e
    return ObservableProxy(default)


class Variable[T, W = None]:
    """Per-instance variable with value and observable access.

    Works with all observable types:
    - Variable[str] → wraps Observable[str]
    - Variable[list[T]] → wraps ObservableList[T]
    - Variable[dict[K,V]] → wraps ObservableDict[K,V]
    - Variable[MyClass] → wraps ObservableProxy[MyClass]

    Optionally includes a widget type:
    - Variable[str, QLineEdit] → wraps Observable[str] with auto-bound QLineEdit

    Usage:
        self._name.value = "hello"      # set value
        print(self._name.value)         # get value
        self._name.observable.on_change(callback)  # subscribe
        if self._name.is_dirty:         # check dirty state
        self._name.reset_dirty()        # mark as clean
        self._name.widget               # access the bound widget (if any)

    For Variable[MyClass] (ObservableProxy), direct field access is supported:
        self._dog.name = "Max"          # reactive! same as self._dog.observable.name = "Max"
        print(self._dog.name)           # gets the value
    """

    # Known attributes that belong to Variable itself (not forwarded to proxy)
    _SELF_ATTRS = frozenset(
        {
            "_wrapper",
            "_widget_type",
            "_widget",
            "_callbacks",
            "widget",
            "value",
            "observable",
            "is_dirty",
            "is_valid",
            "validation_errors",
            "validation_error_messages",
        }
    )

    _wrapper: AnyObservable[T]
    _widget_type: type | None
    _widget: Any  # Will be W | None where W is the widget type
    _callbacks: list[Any]  # Callbacks registered via on_change, tracked for replace_wrapper

    def __init__(self, wrapper: AnyObservable[T], widget_type: type | None = None) -> None:
        object.__setattr__(self, "_wrapper", wrapper)
        object.__setattr__(self, "_widget_type", widget_type)
        object.__setattr__(self, "_widget", None)  # Populated later when widget is created
        object.__setattr__(self, "_callbacks", [])  # Track callbacks for re-registration on replace_wrapper

    def __getattr__(  # pyright: ignore[reportUnknownParameterType]
        self, name: str
    ):  # noqa: ANN204 - intentionally untyped for pyright Unknown
        """Forward attribute access to ObservableProxy for field access.

        For Variable[Dog], self._dog.name returns dog.name (unwrapped value).
        Use .observable.name for the Observable itself.

        NOTE: Return type intentionally omitted so pyright treats it as Unknown.
        This allows reportUnknownMemberType to catch accidental direct access
        in strict mode, encouraging use of .value or () instead.
        """
        # Only forward to proxy if we're wrapping an ObservableProxy
        wrapper = object.__getattribute__(self, "_wrapper")
        if isinstance(wrapper, ObservableProxy):
            result = getattr(wrapper, name)  # pyright: ignore[reportUnknownArgumentType]
            # Unwrap Observable to return actual value
            if isinstance(result, Observable):
                return result.get()  # pyright: ignore[reportUnknownVariableType]
            return result
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        """Forward attribute setting to ObservableProxy for field mutation.

        For Variable[Dog], self._dog.name = "Max" sets dog.name reactively.
        """
        # Handle Variable's own attributes normally
        if name in Variable._SELF_ATTRS:
            object.__setattr__(self, name, value)
            return

        # Forward to proxy if we're wrapping an ObservableProxy
        wrapper: Any = object.__getattribute__(self, "_wrapper")
        if isinstance(wrapper, ObservableProxy):
            setattr(cast(Any, wrapper), name, value)
            return

        # Fall back to normal attribute setting
        object.__setattr__(self, name, value)

    @property
    def widget(self) -> Any:
        """Get the bound widget (if Variable was declared with a widget type)."""
        return self._widget

    @widget.setter
    def widget(self, value: Any) -> None:
        """Set the bound widget (used internally by the descriptor)."""
        self._widget = value

    @property
    def value(self) -> T:
        """Get the current value."""
        if isinstance(self._wrapper, Observable):
            return self._wrapper.get()
        if isinstance(self._wrapper, ObservableList):
            return cast(T, self._wrapper.to_list())
        if isinstance(self._wrapper, ObservableDict):
            return cast(T, self._wrapper.to_dict())
        if isinstance(self._wrapper, ObservableSet):
            return cast(T, self._wrapper.to_set())
        # Must be ObservableProxy (pyright narrows type)
        return self._wrapper.unwrap()

    @value.setter
    def value(self, val: T) -> None:
        """Set the value (triggers change notifications)."""
        if isinstance(self._wrapper, Observable):
            self._wrapper.set(val)
        elif isinstance(self._wrapper, ObservableList):
            # Replace entire list atomically
            self._wrapper.replace(cast(list[Any], val) if isinstance(val, list) else [])
        elif isinstance(self._wrapper, ObservableDict):
            # Replace entire dict atomically
            self._wrapper.replace(cast(dict[Any, Any], val) if isinstance(val, dict) else {})
        elif isinstance(self._wrapper, ObservableSet):
            # Replace entire set atomically
            self._wrapper.replace(cast(set[Any], val) if isinstance(val, set) else set())
        else:
            # Must be ObservableProxy - replace target object
            self._wrapper.replace_target(val)

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
        """Register a change callback on the underlying wrapper.

        Callbacks are tracked at the Variable level so they can be re-registered
        when replace_wrapper() is called.
        """
        self._callbacks.append(callback)
        self._wrapper.on_change(callback)

    def replace_wrapper(self, new_wrapper: AnyObservable[T]) -> None:
        """Replace the underlying wrapper with a different one.

        This is used to share an ObservableProxy between multiple Variables,
        ensuring they share dirty state, validation state, etc.

        All callbacks registered via on_change() are automatically re-registered
        on the new wrapper, and then fired to notify of the value change.

        Args:
            new_wrapper: The new wrapper to use (must be same type as current).
        """
        object.__setattr__(self, "_wrapper", new_wrapper)
        # Re-register all callbacks on the new wrapper
        for callback in self._callbacks:
            new_wrapper.on_change(callback)
        # Fire callbacks to notify that the value has changed
        # (the wrapper itself won't fire because it didn't "change" from its perspective)
        for callback in self._callbacks:
            try:
                callback()
            except TypeError:
                # Some callbacks may expect a value argument (from Observable.on_change)
                # Try passing the current value
                try:
                    callback(self.value)
                except TypeError:
                    pass  # Callback signature doesn't match - skip

    def __call__(self) -> T:
        """Shorthand for .value - allows my_var() instead of my_var.value."""
        return self.value

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[T]) -> None:
        """Add a named validator. Validator returns None (valid) or str/list[str] (errors)."""
        # type: ignore needed because AnyObservable union has different validator signatures
        self._wrapper.add_validator(name, validator)  # type: ignore[arg-type]

    def remove_validator(self, name: str) -> None:
        """Remove a named validator."""
        self._wrapper.remove_validator(name)

    @property
    def is_valid(self) -> Observable[bool]:
        """Validity state. Bindable."""
        return self._wrapper.is_valid

    @property
    def validation_errors(self) -> Observable[dict[str, list[str]]]:
        """Errors by validator name. Bindable."""
        return self._wrapper.validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Bindable."""
        return self._wrapper.validation_error_messages

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

    # Primitive coercion - allow Variable[int] to be used as int, etc.
    def __int__(self) -> int:
        return int(self.value)  # type: ignore[arg-type]

    def __float__(self) -> float:
        return float(self.value)  # type: ignore[arg-type]

    @override
    def __str__(self) -> str:
        return str(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    # Augmented assignment operators - allow self._count += 1
    def __iadd__(self, other: Any) -> Self:
        self.value = self.value + other  # type: ignore[operator]
        return self

    def __isub__(self, other: Any) -> Self:
        self.value = self.value - other  # type: ignore[operator]
        return self

    def __imul__(self, other: Any) -> Self:
        self.value = self.value * other  # type: ignore[operator]
        return self

    def __itruediv__(self, other: Any) -> Self:
        self.value = self.value / other  # type: ignore[operator]
        return self

    def __ifloordiv__(self, other: Any) -> Self:
        self.value = self.value // other  # type: ignore[operator]
        return self

    def __imod__(self, other: Any) -> Self:
        self.value = self.value % other  # type: ignore[operator]
        return self

    # -------------------------------------------------------------------------
    # List/Dict/Set delegation
    # Typed overloads provide intellisense for list/dict/set item types
    # -------------------------------------------------------------------------

    if TYPE_CHECKING:
        # List-specific methods
        def append(self: Variable[list[_ItemT], Any], item: _ItemT) -> None: ...
        def extend(self: Variable[list[_ItemT], Any], items: list[_ItemT]) -> None: ...
        def insert(self: Variable[list[_ItemT], Any], index: int, item: _ItemT) -> None: ...
        def remove(self: Variable[list[_ItemT], Any], item: _ItemT) -> None: ...

        # Set-specific methods
        def add(self: Variable[set[_SetItemT], Any], item: _SetItemT) -> None: ...
        def discard(self: Variable[set[_SetItemT], Any], item: _SetItemT) -> None: ...

        # Pop overloads (list takes index, set takes nothing)
        @overload
        def pop(self: Variable[list[_ItemT], Any], index: int = -1) -> _ItemT: ...
        @overload
        def pop(self: Variable[dict[_KeyT, _ValT], Any], index: _KeyT) -> _ValT: ...  # pyright: ignore[reportInconsistentOverload]
        @overload
        def pop(self: Variable[set[_SetItemT], Any]) -> _SetItemT: ...  # pyright: ignore[reportInconsistentOverload]
        def pop(self, index: Any = -1) -> Any: ...

        # Shared list/dict/set methods with overloads
        @overload
        def clear(self: Variable[list[_ItemT], Any]) -> None: ...
        @overload
        def clear(self: Variable[dict[_KeyT, _ValT], Any]) -> None: ...
        @overload
        def clear(self: Variable[set[_SetItemT], Any]) -> None: ...
        def clear(self) -> None: ...

        @overload
        def __len__(self: Variable[list[_ItemT], Any]) -> int: ...
        @overload
        def __len__(self: Variable[dict[_KeyT, _ValT], Any]) -> int: ...
        @overload
        def __len__(self: Variable[set[_SetItemT], Any]) -> int: ...
        def __len__(self) -> int: ...

        @overload
        def __iter__(self: Variable[list[_ItemT], Any]) -> Iterator[_ItemT]: ...
        @overload
        def __iter__(self: Variable[dict[_KeyT, _ValT], Any]) -> Iterator[_KeyT]: ...
        @overload
        def __iter__(self: Variable[set[_SetItemT], Any]) -> Iterator[_SetItemT]: ...
        def __iter__(self) -> Iterator[Any]: ...

        @overload
        def __contains__(self: Variable[list[_ItemT], Any], item: _ItemT) -> bool: ...
        @overload
        def __contains__(self: Variable[dict[_KeyT, _ValT], Any], item: _KeyT) -> bool: ...  # pyright: ignore[reportInconsistentOverload]
        @overload
        def __contains__(self: Variable[set[_SetItemT], Any], item: _SetItemT) -> bool: ...  # pyright: ignore[reportInconsistentOverload]
        def __contains__(self, item: Any) -> bool: ...

        @overload
        def __getitem__(self: Variable[list[_ItemT], Any], key: int) -> _ItemT: ...  # pyright: ignore[reportInconsistentOverload]
        @overload
        def __getitem__(self: Variable[dict[_KeyT, _ValT], Any], key: _KeyT) -> _ValT: ...
        def __getitem__(self, key: Any) -> Any: ...

        @overload
        def __setitem__(self: Variable[list[_ItemT], Any], key: int, value: _ItemT) -> None: ...  # pyright: ignore[reportInconsistentOverload]
        @overload
        def __setitem__(self: Variable[dict[_KeyT, _ValT], Any], key: _KeyT, value: _ValT) -> None: ...
        def __setitem__(self, key: Any, value: Any) -> None: ...

        @overload
        def __delitem__(self: Variable[list[_ItemT], Any], key: int) -> None: ...  # pyright: ignore[reportInconsistentOverload]
        @overload
        def __delitem__(self: Variable[dict[_KeyT, _ValT], Any], key: _KeyT) -> None: ...
        def __delitem__(self, key: Any) -> None: ...

        # Dict-specific methods
        def keys(self: Variable[dict[_KeyT, _ValT], Any]) -> list[_KeyT]: ...
        def values(self: Variable[dict[_KeyT, _ValT], Any]) -> list[_ValT]: ...
        def items(self: Variable[dict[_KeyT, _ValT], Any]) -> list[tuple[_KeyT, _ValT]]: ...
        def get(self: Variable[dict[_KeyT, _ValT], Any], key: _KeyT, default: _ValT | None = None) -> _ValT | None: ...
        def update(self: Variable[dict[_KeyT, _ValT], Any], other: dict[_KeyT, _ValT]) -> None: ...
    else:

        def append(self, item: Any) -> None:
            """Append item (delegates to ObservableList)."""
            if not isinstance(self._wrapper, ObservableList):
                raise TypeError(f"append() requires ObservableList, got {type(self._wrapper).__name__}")
            self._wrapper.append(item)

        def extend(self, items: list[Any]) -> None:
            """Extend with items (delegates to ObservableList)."""
            if not isinstance(self._wrapper, ObservableList):
                raise TypeError(f"extend() requires ObservableList, got {type(self._wrapper).__name__}")
            self._wrapper.extend(items)

        def insert(self, index: int, item: Any) -> None:
            """Insert item at index (delegates to ObservableList)."""
            if not isinstance(self._wrapper, ObservableList):
                raise TypeError(f"insert() requires ObservableList, got {type(self._wrapper).__name__}")
            self._wrapper.insert(index, item)

        def remove(self, item: Any) -> None:
            """Remove first occurrence of item (delegates to ObservableList)."""
            if not isinstance(self._wrapper, ObservableList):
                raise TypeError(f"remove() requires ObservableList, got {type(self._wrapper).__name__}")
            self._wrapper.remove(item)

        # Set-specific methods
        def add(self, item: Any) -> None:
            """Add item to set (delegates to ObservableSet)."""
            if not isinstance(self._wrapper, ObservableSet):
                raise TypeError(f"add() requires ObservableSet, got {type(self._wrapper).__name__}")
            self._wrapper.add(item)

        def discard(self, item: Any) -> None:
            """Discard item from set (delegates to ObservableSet)."""
            if not isinstance(self._wrapper, ObservableSet):
                raise TypeError(f"discard() requires ObservableSet, got {type(self._wrapper).__name__}")
            self._wrapper.discard(item)

        def pop(self, index: int = -1) -> Any:
            """Remove and return item (delegates to ObservableList or ObservableSet)."""
            if isinstance(self._wrapper, ObservableList):
                return self._wrapper.pop(index)
            if isinstance(self._wrapper, ObservableSet):
                return self._wrapper.pop()  # Sets don't take an index
            raise TypeError(f"pop() requires ObservableList/ObservableSet, got {type(self._wrapper).__name__}")

        def clear(self) -> None:
            """Remove all items (delegates to ObservableList, ObservableDict, or ObservableSet)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict, ObservableSet)):
                self._wrapper.clear()
            else:
                raise TypeError(f"clear() requires ObservableList/ObservableDict/ObservableSet, got {type(self._wrapper).__name__}")

        def __len__(self) -> int:
            """Return length (delegates to ObservableList, ObservableDict, or ObservableSet)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict, ObservableSet)):
                return len(self._wrapper)
            raise TypeError(f"len() requires ObservableList/ObservableDict/ObservableSet, got {type(self._wrapper).__name__}")

        def __iter__(self) -> Iterator[Any]:
            """Iterate (delegates to ObservableList, ObservableDict, or ObservableSet)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict, ObservableSet)):
                return iter(self._wrapper)
            raise TypeError(f"iter() requires ObservableList/ObservableDict/ObservableSet, got {type(self._wrapper).__name__}")

        def __contains__(self, item: Any) -> bool:
            """Check membership (delegates to ObservableList, ObservableDict, or ObservableSet)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict, ObservableSet)):
                return item in self._wrapper
            raise TypeError(f"'in' requires ObservableList/ObservableDict/ObservableSet, got {type(self._wrapper).__name__}")

        def __getitem__(self, key: Any) -> Any:
            """Get item at index/key (delegates to ObservableList or ObservableDict)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict)):
                return self._wrapper[key]
            raise TypeError(f"__getitem__ requires ObservableList/ObservableDict, got {type(self._wrapper).__name__}")

        def __setitem__(self, key: Any, value: Any) -> None:
            """Set item at index/key (delegates to ObservableList or ObservableDict)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict)):
                self._wrapper[key] = value
            else:
                raise TypeError(f"__setitem__ requires ObservableList/ObservableDict, got {type(self._wrapper).__name__}")

        def __delitem__(self, key: Any) -> None:
            """Delete item at index/key (delegates to ObservableList or ObservableDict)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict)):
                del self._wrapper[key]
            else:
                raise TypeError(f"__delitem__ requires ObservableList/ObservableDict, got {type(self._wrapper).__name__}")

        # Dict-specific methods
        def keys(self) -> list[Any]:
            """Return keys (delegates to ObservableDict)."""
            if not isinstance(self._wrapper, ObservableDict):
                raise TypeError(f"keys() requires ObservableDict, got {type(self._wrapper).__name__}")
            return self._wrapper.keys()

        def values(self) -> list[Any]:
            """Return values (delegates to ObservableDict)."""
            if not isinstance(self._wrapper, ObservableDict):
                raise TypeError(f"values() requires ObservableDict, got {type(self._wrapper).__name__}")
            return self._wrapper.values()

        def items(self) -> list[tuple[Any, Any]]:
            """Return items (delegates to ObservableDict)."""
            if not isinstance(self._wrapper, ObservableDict):
                raise TypeError(f"items() requires ObservableDict, got {type(self._wrapper).__name__}")
            return self._wrapper.items()

        def get(self, key: Any, default: Any = None) -> Any:
            """Get value for key with optional default (delegates to ObservableDict)."""
            if not isinstance(self._wrapper, ObservableDict):
                raise TypeError(f"get() requires ObservableDict, got {type(self._wrapper).__name__}")
            return self._wrapper.get(key, default)

        def update(self, other: dict[Any, Any]) -> None:
            """Update with items from other dict (delegates to ObservableDict)."""
            if not isinstance(self._wrapper, ObservableDict):
                raise TypeError(f"update() requires ObservableDict, got {type(self._wrapper).__name__}")
            self._wrapper.update(other)


# Alias for Variable - shorter name, same class
# Var[T] works identically to Variable[T]
Var = Variable


class RecordVariable[T](Variable[T, None]):
    """Variable specifically for Widget[T] records.

    Inherits from Variable so isinstance(x, Variable) checks work.
    Has properly typed `observable` that returns `ObservableProxy[T]`
    instead of the union type, so pyright understands field access.

    Supports direct field access: self.record.name = "x" forwards to the proxy.
    """

    # Attributes that should be looked up on RecordVariable/Variable, not forwarded to proxy
    _RECORD_VARIABLE_ATTRS: set[str] = {
        "_wrapper",
        "_widget",
        "value",
        "observable",
        "is_dirty",
        "reset_dirty",
        "dirty_fields",
        "on_change",
        "add_validator",
        "remove_validator",
        "is_valid",
        "validation_errors",
        "validation_error_messages",
    }

    def __init__(self, wrapper: ObservableProxy[T]) -> None:
        super().__init__(wrapper, widget_type=None)

    @override
    def __getattribute__(self, name: str) -> Any:
        """Forward attribute access to proxy, prioritizing record fields over Variable methods.

        This ensures record fields like 'items', 'keys', 'values', 'get', 'update'
        are not shadowed by Variable's dict/list convenience methods.
        """
        # Always use parent for private attrs and known RecordVariable attrs
        if name.startswith("_") or name in RecordVariable._RECORD_VARIABLE_ATTRS:
            return object.__getattribute__(self, name)

        # Check if the proxy's target has this attribute (record field)
        wrapper: ObservableProxy[T] = object.__getattribute__(self, "_wrapper")
        target = wrapper.unwrap()
        if target is not None and hasattr(target, name):
            # Forward to proxy - it will return Observable/ObservableList/etc
            result = getattr(wrapper, name)
            # Unwrap Observable to return actual value (consistent with Variable.__getattr__)
            if isinstance(result, Observable):
                return cast(Any, result.get())
            return result

        # Fall back to parent class (Variable methods like append, extend for list operations)
        return object.__getattribute__(self, name)

    @property
    @override
    def observable(self) -> ObservableProxy[T]:
        """Get the underlying ObservableProxy (typed specifically for records)."""
        return cast(ObservableProxy[T], self._wrapper)

    @override
    def __call__(self) -> T:
        """Shorthand for .value - allows record() instead of record.value."""
        return self.value


def _try_get_variable(obj: Any, name: str) -> Variable[Any, Any] | None:
    """Try to get a Variable by exact name from an object.

    Args:
        obj: The object to check (parent widget or QApplication)
        name: The exact Variable name to find

    Returns:
        The Variable if found, None otherwise.
    """
    try:
        attr = getattr(obj, name, None)
        if isinstance(attr, Variable):
            return cast(Variable[Any, Any], attr)
    except Exception:
        # getattr can fail on some Qt objects
        pass
    return None


def _resolve_from_hierarchy(widget: Any, var_name: str) -> Variable[Any] | None:
    """Walk parent hierarchy to find matching Variable.

    Resolution order:
    1. widget.parent() (Qt parent)
    2. parent().parent(), etc.
    3. QApplication.instance()

    Args:
        widget: The widget instance to start from
        var_name: The exact Variable name to find

    Returns:
        The Variable found in the hierarchy, or None if not found.
        Returns the SAME Variable object (not a copy) so that all widgets
        in the hierarchy share one Variable instance.
    """
    from qtpy.QtWidgets import QApplication, QWidget

    # Walk parent chain
    current: Any = widget
    while True:
        if not isinstance(current, QWidget):
            break
        parent: Any = current.parent()
        if parent is None:
            break

        # Try to find Variable on parent
        var = _try_get_variable(parent, var_name)
        if var is not None:
            # Return the SAME Variable object so all hierarchy shares one instance
            return var

        current = parent

    # Fallback: check QApplication.instance()
    app = QApplication.instance()
    if app is not None:
        var = _try_get_variable(app, var_name)
        if var is not None:
            return var

    return None


class _RequiredBindingDescriptor[T]:  # pyright: ignore[reportUnusedClass] - used in widget.py
    """Descriptor for bare Variable[T] annotations that require a binding.

    When a widget declares `count: Variable[int]` (no = new()), this descriptor
    is created. It will:
    1. First check if a binding was explicitly provided by the parent
    2. Then walk the parent hierarchy to find a matching Variable
    3. Finally check QApplication.instance() for app-level Variables

    If no Variable is found, raises AttributeError.
    """

    def __init__(self, name: str, inner_type: type | None = None) -> None:
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

        # Check if Variable was created by explicit binding
        from .qt_pie_state import QtPieState

        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)  # type: ignore[attr-defined]
        qtpie_state = cast(Any, obj._qtpie)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

        if self._name in qtpie_state.variables:
            return qtpie_state.variables[self._name]

        # Try to resolve from parent hierarchy
        resolved = _resolve_from_hierarchy(obj, self._name)
        if resolved is not None:
            qtpie_state.register_variable(self._name, resolved)
            return resolved  # type: ignore[return-value]

        # Not found anywhere - raise error
        raise AttributeError(
            f"'{self._name}' requires a binding or matching Variable in parent hierarchy. "
            f'Use: child: {type(obj).__name__} = new({self._name}="_parent_var") '
            f"or ensure a parent widget has '{self._name}'"
        )

    def __set__(self, obj: object, value: T | Variable[T] | RecordVariable[T]) -> None:
        """Allow setting either a Variable/RecordVariable (for binding injection) or a value."""
        from .qt_pie_state import QtPieState

        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)  # type: ignore[attr-defined]
        qtpie_state = cast(Any, obj._qtpie)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

        if isinstance(value, (Variable, RecordVariable)):
            # Binding injection - store the Variable/RecordVariable directly
            qtpie_state.variables[self._name] = value
            qtpie_state.register_variable(self._name, value)
        else:
            # Value assignment - get or create Variable first
            if self._name not in qtpie_state.variables:
                # Need to create a Variable - but we don't have a binding!
                # Create one with the provided value as default
                wrapper = _create_observable_for_type(self._inner_type, value)
                var: Variable[T] = Variable(wrapper)
                qtpie_state.register_variable(self._name, var)
            else:
                qtpie_state.variables[self._name].value = value


class _VariableDescriptor[T]:
    """Descriptor that returns per-instance Variable objects.

    This is an internal class. Users see Variable[T] in type hints.
    """

    def __init__(
        self,
        default: T,
        name: str,
        inner_type: type | types.UnionType | None = None,
        widget_type: type | None = None,
        widget_args: tuple[Any, ...] = (),
        widget_kwargs: dict[str, Any] | None = None,
        label: str | None = None,
        grid: tuple[int, ...] | None = None,
        exclude_from_layout: bool = False,
        validators: list[str] | None = None,
        object_name: str | None = None,
        css_classes: list[str] | None = None,
        # Variable[T, Dock[W]] support
        dock_info: dict[str, Any] | None = None,
        # Nested layout support
        target_layout: str | None = None,
        # Constructor kwargs for inner type T (for Variable[T] without widget)
        inner_kwargs: dict[str, Any] | None = None,
        # Setting[T] support - if set, creates Setting instead of Variable
        persist_key: str | None = None,
        # Callback for value changes
        on_change: str | Callable[..., Any] | None = None,
        # List-specific callbacks
        on_insert: str | Callable[..., Any] | None = None,
        on_remove: str | Callable[..., Any] | None = None,
        on_replace: str | Callable[..., Any] | None = None,
        on_clear: str | Callable[..., Any] | None = None,
        # Set-specific callbacks
        on_add: str | Callable[..., Any] | None = None,
        # Dict-specific callbacks
        on_set: str | Callable[..., Any] | None = None,
    ) -> None:
        self._default = default
        self._name = name
        self._inner_type = inner_type
        self._widget_type = widget_type
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        # Layout params for form/grid layouts (not passed to widget constructor)
        self.label = label
        self.grid = grid
        self.exclude_from_layout = exclude_from_layout
        # Target layout for nested layouts
        self.target_layout = target_layout
        # Validator method names to auto-register
        self.validators = validators or []
        # Widget objectName and CSS classes
        self._object_name = object_name
        self._css_classes = css_classes or []
        # Dock info for Variable[T, Dock[W]] - contains dock_area, dock_title, etc.
        self.dock_info = dock_info
        # Constructor kwargs for inner type T (may contain string refs to other fields)
        self._inner_kwargs = inner_kwargs or {}
        # Setting persistence key - if set, creates Setting instead of Variable
        self._persist_key = persist_key
        # Callback for value changes - method name or callable
        self._on_change = on_change
        # List-specific callbacks
        self._on_insert = on_insert
        self._on_remove = on_remove
        self._on_replace = on_replace
        self._on_clear = on_clear
        # Set-specific callbacks
        self._on_add = on_add
        # Dict-specific callbacks
        self._on_set = on_set

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
            # Resolve string references in inner_kwargs to actual values from the widget
            resolved_kwargs: dict[str, Any] = {}
            for k, v in self._inner_kwargs.items():
                if isinstance(v, str):
                    # String reference - resolve to the actual value on obj
                    ref_attr = getattr(obj, v, None)
                    if ref_attr is not None:
                        # If it's a Variable, get its .value
                        if isinstance(ref_attr, Variable):
                            resolved_kwargs[k] = ref_attr.value  # pyright: ignore[reportUnknownMemberType]
                        else:
                            resolved_kwargs[k] = ref_attr
                    else:
                        resolved_kwargs[k] = v  # Keep as-is if not found
                else:
                    resolved_kwargs[k] = v

            if self._persist_key is not None:
                # Setting mode: load from QSettings, create Setting
                from .setting import Setting
                from .settings_backend import get_settings_backend

                backend = get_settings_backend()
                initial = backend.get(self._persist_key, self._default, self._inner_type)
                wrapper = _create_observable_for_type(self._inner_type, initial, resolved_kwargs)
                var: Variable[T] = Setting(
                    wrapper,
                    key=self._persist_key,
                    type_hint=self._inner_type,
                    widget_type=self._widget_type,
                )
            else:
                # Normal Variable mode
                wrapper = _create_observable_for_type(self._inner_type, self._default, resolved_kwargs)
                var = Variable(wrapper, widget_type=self._widget_type)
            qtpie_state.register_variable(self._name, var)

            # Wire up callbacks if specified
            if self._on_change is not None:
                _wire_on_change_callback(obj, var, self._on_change)
            if self._on_insert is not None:
                _wire_on_insert_callback(obj, var, self._on_insert)
            if self._on_remove is not None:
                _wire_on_remove_callback(obj, var, self._on_remove)
            if self._on_add is not None:
                _wire_on_add_callback(obj, var, self._on_add)
            if self._on_set is not None:
                _wire_on_set_callback(obj, var, self._on_set)
            # Note: onReplace and onClear are handled specially via value assignment

            # If widget_type is set, create the widget and bind it
            if self._widget_type is not None:
                from .bindings import bind

                # Compute objectName with priority: new()(name=) > @widget(name=) > field name (stripped)
                parent_config = getattr(type(obj), "_qtpie_config", None)
                parent_decorator_name = parent_config.object_name if parent_config else None
                if self._object_name is not None:
                    computed_object_name = self._object_name
                elif parent_decorator_name is not None:
                    computed_object_name = parent_decorator_name
                else:
                    # Strip leading underscore from field name
                    computed_object_name = self._name[1:] if self._name.startswith("_") else self._name

                # Check if inner_type is list[X] or dict[K, V] - create repeater
                inner_origin = get_origin(self._inner_type)
                if inner_origin is list:
                    from typing import get_args as typing_get_args

                    from .widget_repeater import WidgetRepeater

                    # Extract item type X from list[X]
                    type_args = typing_get_args(self._inner_type)
                    item_type = type_args[0] if type_args else None

                    # Extract bind= and sort= from widget_kwargs for WidgetRepeater
                    widget_kwargs_copy = dict(self._widget_kwargs)
                    bind_expr = widget_kwargs_copy.pop("bind", "{#self}")
                    sort_key = widget_kwargs_copy.pop("sort", None)

                    # Create WidgetRepeater instead of single widget
                    widget_instance = WidgetRepeater(  # pyright: ignore[reportUnknownVariableType]
                        observable_list=wrapper,  # type: ignore[arg-type]
                        item_type=item_type,
                        widget_type=self._widget_type,
                        widget_args=self._widget_args,
                        widget_kwargs=widget_kwargs_copy,
                        bind_expr=bind_expr,
                        sort=sort_key,
                        object_name=computed_object_name,
                        css_classes=self._css_classes,
                    )
                elif inner_origin is dict:
                    from typing import get_args as typing_get_args

                    from .dict_widget_repeater import DictWidgetRepeater

                    # Extract K, V from dict[K, V]
                    type_args = typing_get_args(self._inner_type)
                    key_type = type_args[0] if len(type_args) > 0 else None
                    value_type = type_args[1] if len(type_args) > 1 else None

                    # Extract bind= and sort= from widget_kwargs for DictWidgetRepeater
                    widget_kwargs_copy = dict(self._widget_kwargs)
                    bind_expr = widget_kwargs_copy.pop("bind", "{#key} = {#value}")
                    sort_key = widget_kwargs_copy.pop("sort", None)

                    # Create DictWidgetRepeater instead of single widget
                    widget_instance = DictWidgetRepeater(  # pyright: ignore[reportUnknownVariableType]
                        observable_dict=wrapper,  # type: ignore[arg-type]
                        key_type=key_type,
                        value_type=value_type,
                        widget_type=self._widget_type,
                        widget_args=self._widget_args,
                        widget_kwargs=widget_kwargs_copy,
                        bind_expr=bind_expr,
                        sort=sort_key,
                        object_name=computed_object_name,
                        css_classes=self._css_classes,
                    )
                elif inner_origin is set:
                    from typing import get_args as typing_get_args

                    from .set_widget_repeater import SetWidgetRepeater

                    # Extract item type T from set[T]
                    type_args = typing_get_args(self._inner_type)
                    item_type = type_args[0] if type_args else None

                    # Extract bind= and sort= from widget_kwargs for SetWidgetRepeater
                    widget_kwargs_copy = dict(self._widget_kwargs)
                    bind_expr = widget_kwargs_copy.pop("bind", "{#self}")
                    sort_key = widget_kwargs_copy.pop("sort", None)

                    # Create SetWidgetRepeater instead of single widget
                    widget_instance = SetWidgetRepeater(  # pyright: ignore[reportUnknownVariableType]
                        observable_set=wrapper,  # type: ignore[arg-type]
                        item_type=item_type,
                        widget_type=self._widget_type,
                        widget_args=self._widget_args,
                        widget_kwargs=widget_kwargs_copy,
                        bind_expr=bind_expr,
                        sort=sort_key,
                        object_name=computed_object_name,
                        css_classes=self._css_classes,
                    )
                else:
                    # Regular widget creation
                    # Extract bind= from widget_kwargs (don't pass to widget constructor)
                    widget_kwargs_copy = dict(self._widget_kwargs)
                    bind_expr = widget_kwargs_copy.pop("bind", None)

                    # Extract signal connections (e.g., returnPressed="add_item")
                    signal_connections: dict[str, str | Callable[..., Any]] = {}
                    signal_keys_to_remove: list[str] = []
                    for key, value in widget_kwargs_copy.items():
                        if is_signal_on_type(key, self._widget_type):
                            if isinstance(value, str) or callable(value):
                                signal_connections[key] = value
                                signal_keys_to_remove.append(key)
                    for key in signal_keys_to_remove:
                        del widget_kwargs_copy[key]

                    # Extract property bindings (visible=, enabled=) - don't pass to widget constructor
                    bindable_props = {"visible", "enabled", "windowModified", "acceptDrops", "updatesEnabled", "checked"}
                    property_bindings: dict[str, str] = {}
                    prop_keys_to_remove: list[str] = []
                    for key, value in widget_kwargs_copy.items():
                        if key in bindable_props and isinstance(value, str):
                            property_bindings[key] = value
                            prop_keys_to_remove.append(key)
                    for key in prop_keys_to_remove:
                        del widget_kwargs_copy[key]

                    # Extract format string kwargs (e.g., label="{kind}", placeholderText="{name}")
                    # These need reactive binding, not direct passing to widget constructor
                    from .bindings import is_format_string

                    format_string_kwargs: dict[str, str] = {}
                    format_keys_to_remove: list[str] = []
                    for key, value in widget_kwargs_copy.items():
                        if isinstance(value, str) and is_format_string(value):
                            format_string_kwargs[key] = value
                            format_keys_to_remove.append(key)
                    for key in format_keys_to_remove:
                        del widget_kwargs_copy[key]

                    # Extract validator= for input validation (QLineEdit, QComboBox, etc.)
                    validator_spec = widget_kwargs_copy.pop("validator", None)

                    # Extract width= and height= for initial size (applied via resize())
                    initial_width = widget_kwargs_copy.pop("width", None)
                    initial_height = widget_kwargs_copy.pop("height", None)

                    try:
                        widget_instance = self._widget_type(*self._widget_args, **widget_kwargs_copy)
                    except (TypeError, AttributeError) as e:
                        raise TypeError(f"Failed to create {self._widget_type.__name__} for Variable '{self._name}': {e}\n  args={self._widget_args}, kwargs={widget_kwargs_copy}") from e

                    # Apply objectName (computed earlier with priority logic)
                    widget_instance.setObjectName(computed_object_name)

                    # Apply initial size (width=/height=) via resize()
                    # Float values (0.0-1.0) are interpreted as percentage of window size.
                    if initial_width is not None or initial_height is not None:
                        # Check if we need to resolve fractional values
                        needs_window = (isinstance(initial_width, float) and 0.0 < initial_width < 1.0) or (isinstance(initial_height, float) and 0.0 < initial_height < 1.0)

                        if needs_window:
                            # Defer until window is available for fractional sizing
                            from qtpy.QtCore import QTimer
                            from qtpy.QtWidgets import QWidget as QW

                            def apply_size(
                                w: int | float | None = initial_width,
                                h: int | float | None = initial_height,
                                wgt: QW = widget_instance,
                            ) -> None:
                                win = wgt.window()
                                if isinstance(w, float) and 0.0 < w < 1.0:
                                    w = int(win.width() * w)
                                if isinstance(h, float) and 0.0 < h < 1.0:
                                    h = int(win.height() * h)
                                final_w = int(w) if w is not None else wgt.width()
                                final_h = int(h) if h is not None else wgt.height()
                                wgt.resize(final_w, final_h)

                            QTimer.singleShot(0, apply_size)
                        else:
                            # Absolute pixel values - apply immediately
                            w = int(initial_width) if initial_width is not None else widget_instance.width()
                            h = int(initial_height) if initial_height is not None else widget_instance.height()
                            widget_instance.resize(w, h)

                    # Apply CSS classes if specified
                    if self._css_classes:
                        from .styles import set_classes

                        set_classes(widget_instance, self._css_classes)

                    # Apply input validator if specified
                    if validator_spec is not None and hasattr(widget_instance, "setValidator"):
                        from .input_validator import apply_validator

                        apply_validator(widget_instance, validator_spec)

                    # Connect extracted signals to parent widget methods
                    for signal_name, handler_spec in signal_connections.items():
                        signal = getattr(widget_instance, signal_name, None)
                        if signal is not None:
                            if isinstance(handler_spec, str):
                                # String handler - resolve on parent widget
                                # Parse "method_name" or "method_name(...)"
                                if "(" in handler_spec:
                                    method_name = handler_spec[: handler_spec.index("(")]
                                else:
                                    method_name = handler_spec
                                resolved_handler = getattr(obj, method_name, None)
                                if resolved_handler is None:
                                    raise RuntimeError(f"Handler '{method_name}' not found on {type(obj).__name__} for signal connection '{signal_name}=\"{handler_spec}\"'")
                                signal.connect(resolved_handler)
                            else:
                                # Direct callable - connect directly
                                signal.connect(handler_spec)

                    # Apply binding - format string or simple bind
                    if bind_expr is not None and "{" in bind_expr:
                        from .bindings import create_format_binding
                        from .bindings.registry import get_binding_registry

                        registry = get_binding_registry()
                        default_prop = registry.get_default_prop(widget_instance)
                        adapter = registry.get(widget_instance, default_prop)
                        if adapter is not None and adapter.setter is not None:
                            setter = adapter.setter

                            def make_setter(s: Any, w: Any) -> Any:
                                def bound_setter(val: Any) -> None:
                                    s(w, val)

                                return bound_setter

                            create_format_binding(obj, bind_expr, make_setter(setter, widget_instance), variable=var)  # type: ignore[arg-type]
                    else:
                        # Auto-bind for:
                        # 1. Primitive types (str, int, bool, etc.) - bound to widget's default property
                        # 2. Complex types with Widget[T] subclass - bound via shared proxy
                        # Skip binding for complex types with plain QWidget (no meaningful binding)
                        from .bindings.bind import is_widget_with_record

                        should_bind = is_primitive_type(self._inner_type) or is_widget_with_record(widget_instance)
                        if should_bind:
                            bind(var).to(widget_instance)

                    # Apply property bindings (visible=, enabled=) after widget is created and bound
                    if property_bindings:
                        from .bindings import is_format_string
                        from .bindings.expression import create_expression_binding
                        from .bindings.path import resolve_binding_source
                        from .bindings.property_bindings import get_widget_property_setter

                        for prop_name, bind_expr_val in property_bindings.items():
                            prop_setter = get_widget_property_setter(widget_instance, prop_name)
                            if prop_setter is None:
                                # Fall back to setXxx method
                                setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
                                prop_setter = getattr(widget_instance, setter_name, None)
                                if prop_setter is None or not callable(prop_setter):
                                    continue

                            setter_fn = cast(Callable[[Any], None], prop_setter)

                            if is_format_string(bind_expr_val):
                                # Expression binding like "{_count > 0}"
                                create_expression_binding(obj, bind_expr_val, setter_fn)
                            else:
                                # Simple variable reference like "_is_visible"
                                source = resolve_binding_source(obj, bind_expr_val)  # type: ignore[arg-type]
                                if source is None:
                                    continue

                                if isinstance(source, Variable):
                                    setter_fn(source.value)  # pyright: ignore[reportUnknownMemberType]
                                    source.on_change(setter_fn)
                                elif isinstance(source, Observable):
                                    setter_fn(source.get())
                                    source.on_change(setter_fn)

                    # Apply format string kwargs (e.g., label="{kind}", placeholderText="{name}")
                    if format_string_kwargs:
                        from .bindings import create_format_binding

                        for kwarg_name, format_template in format_string_kwargs.items():
                            # Find the setter for this kwarg (e.g., label -> setLabel, placeholderText -> setPlaceholderText)
                            setter_name = f"set{kwarg_name[0].upper()}{kwarg_name[1:]}"
                            setter_method = getattr(widget_instance, setter_name, None)
                            if setter_method is not None and callable(setter_method):
                                create_format_binding(obj, format_template, setter_method)  # type: ignore[arg-type]

                var.widget = widget_instance  # Use setter

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


def _resolve_var_for_state_expression(state_obj: Any, var_name: str) -> Any | None:
    """Resolve a variable for State expression context, walking state_parent hierarchy.

    Returns the resolved value ready for use in eval context:
    - Variable -> unwrapped value
    - Event -> .emit method (so it can be called directly)
    - Other -> raw value

    Returns None if not found.
    """
    from .event import Event

    # Try on state_obj itself (exact name, then underscore prefix)
    for attr_name in [var_name, f"_{var_name}"]:
        if hasattr(state_obj, attr_name):
            raw_attr: Any = getattr(state_obj, attr_name)
            if isinstance(raw_attr, Variable):
                return cast(Any, raw_attr.value)  # pyright: ignore[reportUnknownMemberType]
            elif isinstance(raw_attr, Event):
                return raw_attr.emit
            else:
                return raw_attr

    # Walk state_parent hierarchy
    from .state import State

    if isinstance(state_obj, State):
        current: State | None = state_obj.state_parent
        while current is not None:
            for attr_name in [var_name, f"_{var_name}"]:
                if hasattr(current, attr_name):
                    raw_attr = getattr(current, attr_name)
                    if isinstance(raw_attr, Variable):
                        return cast(Any, raw_attr.value)  # pyright: ignore[reportUnknownMemberType]
                    elif isinstance(raw_attr, Event):
                        return raw_attr.emit
                    else:
                        return raw_attr
            current = current.state_parent

    return None


def _resolve_variable_object_for_state(state_obj: Any, var_name: str) -> Variable[Any, Any] | None:
    """Resolve a Variable object (not its value) for assignment support in State.

    Returns the Variable object itself, not its value.
    Returns None if not found or not a Variable.
    """
    # Try on state_obj itself (exact name, then underscore prefix)
    for attr_name in [var_name, f"_{var_name}"]:
        if hasattr(state_obj, attr_name):
            raw_attr: Any = getattr(state_obj, attr_name)
            if isinstance(raw_attr, Variable):
                return raw_attr  # pyright: ignore[reportUnknownVariableType]

    # Walk state_parent hierarchy
    from .state import State

    if isinstance(state_obj, State):
        current: State | None = state_obj.state_parent
        while current is not None:
            for attr_name in [var_name, f"_{var_name}"]:
                if hasattr(current, attr_name):
                    raw_attr = getattr(current, attr_name)
                    if isinstance(raw_attr, Variable):
                        return raw_attr  # pyright: ignore[reportUnknownVariableType]
            current = current.state_parent

    return None


def _create_state_expression_handler(
    state_obj: Any,
    expression: str,
) -> Callable[..., Any]:
    """Create a handler from an expression string for State onChange callbacks.

    Args:
        state_obj: The State object that provides the context.
        expression: The expression string like "{on_changed()}" or "{handle(#args)}".

    Returns:
        A handler function that can be registered as an onChange callback.

    The expression is evaluated in the state_obj's namespace when the callback fires.
    Supports:
        - Method calls: {on_clicked()}, {handle_value(123)}
        - Event emissions: {on_data_changed()}, {on_save(#args)}
        - Full Python expressions with state variables
        - #args placeholder to pass callback arguments: {handle(#args)}
        - #self placeholder for the state_obj instance
        - Assignments to Variables: {count = 42}, {count += 1}
    """
    from .bindings.format_binding import _BUILTINS, _extract_ast_names, _parse_format_fields  # pyright: ignore[reportPrivateUsage]
    from .signals.expression_handler import _extract_assignment_target, _is_statement  # pyright: ignore[reportPrivateUsage]

    # Parse the expression to get the inner content
    fields = _parse_format_fields(expression)
    if not fields:
        raise ValueError(f"Invalid signal expression: {expression}")

    # We expect a single expression field
    expr = fields[0].expression

    # Check if expression uses special placeholders
    uses_args = "#args" in expr
    uses_self = "#self" in expr

    # Check if this is a statement (assignment, etc.)
    is_stmt = _is_statement(expr)

    # For assignments, check if target is a Variable
    assignment_info = _extract_assignment_target(expr) if is_stmt else None

    # Replace special placeholders before AST extraction (they're not valid Python)
    expr_for_ast = expr
    if uses_args:
        expr_for_ast = expr_for_ast.replace("#args", "_signal_args_placeholder_")
    if uses_self:
        expr_for_ast = expr_for_ast.replace("#self", "_state_ref_")

    # Extract variable names from the expression for context building
    # For assignments, we also need to extract names from the value expression
    if assignment_info:
        _, _, value_expr = assignment_info
        value_expr_for_ast = value_expr
        if uses_args:
            value_expr_for_ast = value_expr_for_ast.replace("#args", "_signal_args_placeholder_")
        if uses_self:
            value_expr_for_ast = value_expr_for_ast.replace("#self", "_state_ref_")
        var_names = _extract_ast_names(value_expr_for_ast) - _BUILTINS
    else:
        var_names = _extract_ast_names(expr_for_ast) - _BUILTINS
    # Remove placeholder names we added
    var_names.discard("_signal_args_placeholder_")
    var_names.discard("_state_ref_")

    def handler(*signal_args: Any) -> Any:
        # Build context with state_obj's variables
        context: dict[str, Any] = {}

        # Add state_obj reference for #self placeholder
        if uses_self:
            context["state_ref"] = state_obj

        # Add #args support
        if uses_args:
            context["signal_args"] = signal_args

        # Add all variable values to context
        for var_name in var_names:
            resolved = _resolve_var_for_state_expression(state_obj, var_name)
            if resolved is not None:
                context[var_name] = resolved

        # Replace special placeholders
        eval_expr = expr
        if uses_args:
            eval_expr = eval_expr.replace("#args", "*signal_args")
        if uses_self:
            eval_expr = eval_expr.replace("#self", "state_ref")

        # Execute/evaluate the expression
        try:
            if is_stmt and assignment_info:
                # Handle assignment to Variable specially
                target_name, operator, value_expr = assignment_info
                var_obj = _resolve_variable_object_for_state(state_obj, target_name)

                if var_obj is not None:
                    # Target is a Variable - update its .value
                    new_value = eval(value_expr, {"__builtins__": __builtins__}, context)  # noqa: S307

                    if operator == "=":
                        var_obj.value = new_value
                    elif operator == "+=":
                        var_obj.value = var_obj.value + new_value
                    elif operator == "-=":
                        var_obj.value = var_obj.value - new_value
                    elif operator == "*=":
                        var_obj.value = var_obj.value * new_value
                    elif operator == "/=":
                        var_obj.value = var_obj.value / new_value
                    elif operator == "//=":
                        var_obj.value = var_obj.value // new_value
                    elif operator == "%=":
                        var_obj.value = var_obj.value % new_value
                    elif operator == "**=":
                        var_obj.value = var_obj.value**new_value
                    elif operator == "|=":
                        var_obj.value = var_obj.value | new_value
                    elif operator == "&=":
                        var_obj.value = var_obj.value & new_value
                    elif operator == "^=":
                        var_obj.value = var_obj.value ^ new_value
                    elif operator == "<<=":
                        var_obj.value = var_obj.value << new_value
                    elif operator == ">>=":
                        var_obj.value = var_obj.value >> new_value
                    return None
                else:
                    # Not a Variable, use exec for regular statement
                    exec(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S102
                    return None
            elif is_stmt:
                # Statement but not a simple assignment we can handle
                exec(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S102
                return None
            else:
                # Regular expression
                result = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
                return result
        except Exception as e:
            raise RuntimeError(f"Error evaluating state expression '{expression}': {e}") from e

    return handler


def _wire_on_change_callback(
    obj: object,
    var: Variable[Any],
    on_change: str | Callable[..., Any],
) -> None:
    """Wire up an onChange callback to a Variable's underlying Observable.

    For State objects, if the callback method is not found on obj, it walks
    up the state_parent hierarchy to find it (lazily at emit time).
    If an Event is found, it emits.

    Supports three forms:
    - Method name: onChange="_some_function"
    - Event name: onChange="on_data_changed" (uses emit_event for hierarchy search)
    - Expression: onChange="{some_call(#args)}" (full expression support)

    Args:
        obj: The host object (Widget, State, etc.) that owns the method
        var: The Variable whose Observable to subscribe to
        on_change: Method name (str), expression (str), or callable to invoke on change
    """
    import inspect

    from .event import Event
    from .state import State, resolve_from_state_hierarchy

    observable = var.observable

    # Handle expression syntax: onChange="{expression(#args)}"
    if isinstance(on_change, str) and on_change.startswith("{") and on_change.endswith("}"):
        handler = _create_state_expression_handler(obj, on_change)
        if isinstance(observable, Observable):
            observable.on_change(handler)
        else:
            observable.on_change(lambda: handler())  # type: ignore[arg-type]
        return

    # For string callbacks on State, we need LAZY resolution because
    # the parent might not be set yet at wire time
    if isinstance(on_change, str) and isinstance(obj, State):
        callback_name = on_change
        state_obj = obj

        # Create lazy resolver that looks up callback at emit time
        def lazy_resolve_and_call(value: Any = None) -> None:
            # First try direct lookup on obj
            callback = getattr(state_obj, callback_name, None)

            # If not found, walk the parent hierarchy
            if callback is None:
                callback = resolve_from_state_hierarchy(state_obj, callback_name)

            if callback is None:
                return  # Not found anywhere - silently skip

            # Handle Event - emit it without arguments by default
            # Use expression syntax {on_event(#args)} to pass value
            if isinstance(callback, Event):
                callback.emit()
                return

            # Call the callback
            try:
                sig = inspect.signature(callback)
                params = [p for p in sig.parameters.values() if p.name != "self"]
                accepts_value = len(params) >= 1
            except (ValueError, TypeError):
                accepts_value = False

            if accepts_value and value is not None:
                callback(value)
            else:
                callback()

        # Wire up via Variable.on_change() so callbacks are tracked and re-registered
        # when replace_wrapper() is called (e.g., by selectedItem binding for complex objects)
        if isinstance(observable, Observable):
            var.on_change(lazy_resolve_and_call)
        elif isinstance(observable, ObservableProxy):
            # ObservableProxy - on_change() takes no args, get value from var
            var.on_change(lambda: lazy_resolve_and_call(var.value))  # type: ignore[arg-type]
        else:
            # Collection types - on_change() takes no args
            var.on_change(lambda: lazy_resolve_and_call())  # type: ignore[arg-type]
        return

    # Non-State case: direct callback lookup (original behavior)
    callback: Callable[..., Any] | None = None
    if isinstance(on_change, str):
        callback = getattr(obj, on_change, None)
        if callback is None:
            return  # Method doesn't exist - silently skip
    else:
        callback = on_change

    # Check callback signature to determine how to call it
    try:
        sig = inspect.signature(callback)
        # Count parameters excluding 'self' (for bound methods, self is already bound)
        params = [p for p in sig.parameters.values() if p.name != "self"]
        accepts_value = len(params) >= 1
    except (ValueError, TypeError):
        # Can't inspect - assume no value parameter
        accepts_value = False

    # Wire up via Variable.on_change() so callbacks are tracked and re-registered
    # when replace_wrapper() is called (e.g., by selectedItem binding for complex objects)
    if isinstance(observable, Observable):
        # Observable[T] - on_change(callback) passes new value
        if accepts_value:
            var.on_change(lambda v: callback(v))
        else:
            var.on_change(lambda _: callback())
    elif isinstance(observable, ObservableProxy):
        # ObservableProxy - on_change() takes no args, but we can get the value from var
        if accepts_value:
            # Get the current value from the Variable when callback fires
            var.on_change(lambda: callback(var.value))  # type: ignore[arg-type]
        else:
            var.on_change(callback)  # type: ignore[arg-type]
    else:
        # Collection types (ObservableList, ObservableDict, ObservableSet)
        # - on_change() takes no args
        var.on_change(callback)  # type: ignore[arg-type]


def _wire_on_insert_callback(
    obj: object,
    var: Variable[Any],
    on_insert: str | Callable[..., Any],
) -> None:
    """Wire up an onInsert callback to an ObservableList or ObservableDict.

    For State objects, resolution is lazy (at emit time) to support parent hierarchy.
    For ObservableList: callback receives (index: int, item: T)
    For ObservableDict: callback receives (key: K, value: V)

    Supports three forms:
    - Method name: onInsert="_some_function"
    - Event name: onInsert="on_item_added" (uses emit_event for hierarchy search)
    - Expression: onInsert="{some_call(#args)}" (full expression support)
    """
    import inspect

    from .event import Event
    from .state import State, resolve_from_state_hierarchy

    observable = var.observable

    # Handle expression syntax: onInsert="{expression(#args)}"
    if isinstance(on_insert, str) and on_insert.startswith("{") and on_insert.endswith("}"):
        handler = _create_state_expression_handler(obj, on_insert)
        if isinstance(observable, ObservableList):
            observable.on_insert(lambda idx, item: handler(item, idx))
        elif isinstance(observable, ObservableDict):
            observable.on_insert(lambda key, val: handler(key, val))
        return

    # For string callbacks on State, use LAZY resolution
    if isinstance(on_insert, str) and isinstance(obj, State):
        callback_name = on_insert
        state_obj = obj

        def lazy_resolve_and_call(index_or_key: Any, item_or_value: Any) -> None:
            callback = getattr(state_obj, callback_name, None)
            if callback is None:
                callback = resolve_from_state_hierarchy(state_obj, callback_name)
            if callback is None:
                return

            if isinstance(callback, Event):
                callback.emit()
                return

            try:
                sig = inspect.signature(callback)
                params = [p for p in sig.parameters.values() if p.name != "self"]
                num_params = len(params)
            except (ValueError, TypeError):
                num_params = 0

            if num_params >= 2:
                callback(item_or_value, index_or_key)
            elif num_params == 1:
                callback(item_or_value)
            else:
                callback()

        if isinstance(observable, ObservableList):
            observable.on_insert(lazy_resolve_and_call)
        elif isinstance(observable, ObservableDict):
            observable.on_insert(lazy_resolve_and_call)
        return

    # Non-State case: direct callback lookup (original behavior)
    if isinstance(on_insert, str):
        callback = getattr(obj, on_insert, None)
        if callback is None:
            return
    else:
        callback = on_insert

    if isinstance(observable, ObservableList):
        # ObservableList.on_insert(callback) passes (index, item)
        # Check if callback accepts args
        try:
            sig = inspect.signature(callback)
            params = [p for p in sig.parameters.values() if p.name != "self"]
            num_params = len(params)
        except (ValueError, TypeError):
            num_params = 0

        if num_params >= 2:
            observable.on_insert(lambda idx, item: callback(item, idx))
        elif num_params == 1:
            observable.on_insert(lambda idx, item: callback(item))
        else:
            observable.on_insert(lambda idx, item: callback())
    elif isinstance(observable, ObservableDict):
        # ObservableDict.on_insert(callback) passes (key, value)
        try:
            sig = inspect.signature(callback)
            params = [p for p in sig.parameters.values() if p.name != "self"]
            num_params = len(params)
        except (ValueError, TypeError):
            num_params = 0

        if num_params >= 2:
            observable.on_insert(lambda key, val: callback(key, val))
        elif num_params == 1:
            observable.on_insert(lambda key, val: callback(key))
        else:
            observable.on_insert(lambda key, val: callback())


def _wire_on_remove_callback(
    obj: object,
    var: Variable[Any],
    on_remove: str | Callable[..., Any],
) -> None:
    """Wire up an onRemove callback to an ObservableList, ObservableSet, or ObservableDict.

    For ObservableList: callback receives (index: int, item: T)
    For ObservableSet: callback receives (item: T)
    For ObservableDict: callback receives (key: K, value: V)

    Supports three forms:
    - Method name: onRemove="_some_function"
    - Event name: onRemove="on_item_removed" (uses emit_event for hierarchy search)
    - Expression: onRemove="{some_call(#args)}" (full expression support)
    """
    import inspect

    observable = var.observable

    # Handle expression syntax: onRemove="{expression(#args)}"
    if isinstance(on_remove, str) and on_remove.startswith("{") and on_remove.endswith("}"):
        handler = _create_state_expression_handler(obj, on_remove)
        if isinstance(observable, ObservableList):
            observable.on_remove(lambda idx, item: handler(item, idx))
        elif isinstance(observable, ObservableSet):
            observable.on_remove(lambda item: handler(item))
        elif isinstance(observable, ObservableDict):
            observable.on_remove(lambda key, val: handler(key, val))
        return

    if isinstance(on_remove, str):
        callback = getattr(obj, on_remove, None)
        if callback is None:
            return
    else:
        callback = on_remove

    try:
        sig = inspect.signature(callback)
        params = [p for p in sig.parameters.values() if p.name != "self"]
        num_params = len(params)
    except (ValueError, TypeError):
        num_params = 0

    if isinstance(observable, ObservableList):
        # ObservableList.on_remove(callback) passes (index, item)
        if num_params >= 2:
            observable.on_remove(lambda idx, item: callback(item, idx))
        elif num_params == 1:
            observable.on_remove(lambda idx, item: callback(item))
        else:
            observable.on_remove(lambda idx, item: callback())
    elif isinstance(observable, ObservableSet):
        # ObservableSet.on_remove(callback) passes (item,)
        if num_params >= 1:
            observable.on_remove(lambda item: callback(item))
        else:
            observable.on_remove(lambda item: callback())
    elif isinstance(observable, ObservableDict):
        # ObservableDict.on_remove(callback) passes (key, value)
        if num_params >= 2:
            observable.on_remove(lambda key, val: callback(key, val))
        elif num_params == 1:
            observable.on_remove(lambda key, val: callback(key))
        else:
            observable.on_remove(lambda key, val: callback())


def _wire_on_add_callback(
    obj: object,
    var: Variable[Any],
    on_add: str | Callable[..., Any],
) -> None:
    """Wire up an onAdd callback to an ObservableSet.

    Callback receives (item: T)

    Supports three forms:
    - Method name: onAdd="_some_function"
    - Event name: onAdd="on_item_added" (uses emit_event for hierarchy search)
    - Expression: onAdd="{some_call(#args)}" (full expression support)
    """
    import inspect

    observable = var.observable

    # Handle expression syntax: onAdd="{expression(#args)}"
    if isinstance(on_add, str) and on_add.startswith("{") and on_add.endswith("}"):
        handler = _create_state_expression_handler(obj, on_add)
        if isinstance(observable, ObservableSet):
            observable.on_add(lambda item: handler(item))
        return

    if isinstance(on_add, str):
        callback = getattr(obj, on_add, None)
        if callback is None:
            return
    else:
        callback = on_add

    if isinstance(observable, ObservableSet):
        try:
            sig = inspect.signature(callback)
            params = [p for p in sig.parameters.values() if p.name != "self"]
            num_params = len(params)
        except (ValueError, TypeError):
            num_params = 0

        if num_params >= 1:
            observable.on_add(lambda item: callback(item))
        else:
            observable.on_add(lambda item: callback())


def _wire_on_set_callback(
    obj: object,
    var: Variable[Any],
    on_set: str | Callable[..., Any],
) -> None:
    """Wire up an onSet callback to an ObservableDict.

    Callback receives (key: K, value: V)
    Note: Maps to on_insert which fires for both new keys and updates.

    Supports three forms:
    - Method name: onSet="_some_function"
    - Event name: onSet="on_item_set" (uses emit_event for hierarchy search)
    - Expression: onSet="{some_call(#args)}" (full expression support)
    """
    import inspect

    observable = var.observable

    # Handle expression syntax: onSet="{expression(#args)}"
    if isinstance(on_set, str) and on_set.startswith("{") and on_set.endswith("}"):
        handler = _create_state_expression_handler(obj, on_set)
        if isinstance(observable, ObservableDict):
            observable.on_insert(lambda key, val: handler(key, val))
        return

    if isinstance(on_set, str):
        callback = getattr(obj, on_set, None)
        if callback is None:
            return
    else:
        callback = on_set

    if isinstance(observable, ObservableDict):
        try:
            sig = inspect.signature(callback)
            params = [p for p in sig.parameters.values() if p.name != "self"]
            num_params = len(params)
        except (ValueError, TypeError):
            num_params = 0

        if num_params >= 2:
            observable.on_insert(lambda key, val: callback(key, val))
        elif num_params == 1:
            observable.on_insert(lambda key, val: callback(key))
        else:
            observable.on_insert(lambda key, val: callback())


def create_variable_descriptor(
    default: Any,
    name: str,
    inner_type: type | types.UnionType | None = None,
    widget_type: type | None = None,
    widget_args: tuple[Any, ...] = (),
    widget_kwargs: dict[str, Any] | None = None,
    label: str | None = None,
    grid: tuple[int, ...] | None = None,
    exclude_from_layout: bool = False,
    validators: list[Any] | None = None,
    object_name: str | None = None,
    css_classes: list[str] | None = None,
    dock_info: dict[str, Any] | None = None,
    target_layout: str | None = None,
    inner_kwargs: dict[str, Any] | None = None,
    persist_key: str | None = None,
    on_change: str | Callable[..., Any] | None = None,
    on_insert: str | Callable[..., Any] | None = None,
    on_remove: str | Callable[..., Any] | None = None,
    on_replace: str | Callable[..., Any] | None = None,
    on_clear: str | Callable[..., Any] | None = None,
    on_add: str | Callable[..., Any] | None = None,
    on_set: str | Callable[..., Any] | None = None,
) -> Any:
    """Create a variable descriptor. Used by NewField."""
    return _VariableDescriptor(
        default,
        name,
        inner_type,
        widget_type,
        widget_args,
        widget_kwargs,
        label,
        grid,
        exclude_from_layout,
        validators,
        object_name,
        css_classes,
        dock_info,
        target_layout,
        inner_kwargs,
        persist_key,
        on_change,
        on_insert,
        on_remove,
        on_replace,
        on_clear,
        on_add,
        on_set,
    )


def _get_variable_observable(obj: object, binding: str) -> Observable[Any] | None:  # pyright: ignore[reportUnusedFunction] - used in window.py
    """Get the Observable for a Variable by name.

    Searches the object itself, then parent hierarchy, then QApplication.

    Args:
        obj: The widget instance (Window or Widget)
        binding: The Variable name (e.g., "_show_dock")

    Returns:
        The Observable if found, None otherwise
    """
    from qtpy.QtWidgets import QApplication

    def _try_get_observable(target: object, name: str) -> Observable[Any] | None:
        """Try to get an Observable from a target object."""
        var = getattr(target, name, None)
        if var is None:
            return None

        # If it's a Variable, get its observable (use public property)
        if isinstance(var, Variable):
            wrapper = cast(AnyObservable[Any], var.observable)  # pyright: ignore[reportUnknownMemberType] - Variable[T] has partially unknown T
            # For Observable (primitive types), return it directly
            if isinstance(wrapper, Observable):
                return wrapper
            # For ObservableProxy (complex types), return its reference_observable
            # This allows tracking when the whole object changes (e.g., None -> Request)
            if isinstance(wrapper, ObservableProxy):
                return wrapper.reference_observable
            # Other types (ObservableList, etc.) not supported for selection binding
            return None

        # If it's an Observable directly
        if isinstance(var, Observable):
            return cast(Observable[Any], var)

        return None

    # Try the object itself first
    result = _try_get_observable(obj, binding)
    if result is not None:
        return result

    # Search up the Qt parent hierarchy
    current: Any = obj
    while hasattr(current, "parent") and callable(current.parent):
        try:
            parent: Any = current.parent()
        except RuntimeError:
            # parent() can fail if __init__ hasn't completed yet
            break
        if parent is None:
            break

        result = _try_get_observable(parent, binding)
        if result is not None:
            return result

        current = parent

    # Fallback: check QApplication.instance()
    app = QApplication.instance()
    if app is not None:
        result = _try_get_observable(app, binding)
        if result is not None:
            return result

    return None


def _get_variable(obj: object, binding: str) -> Variable[Any, Any] | None:  # pyright: ignore[reportUnusedFunction] - used in dock_widget_repeater.py
    """Get a Variable by name.

    Searches the object itself, then parent hierarchy, then QApplication.

    Args:
        obj: The widget instance (Window or Widget)
        binding: The Variable name (e.g., "current_request")

    Returns:
        The Variable if found, None otherwise
    """
    from qtpy.QtWidgets import QApplication

    def _try_get_variable(target: object, name: str) -> Variable[Any, Any] | None:
        """Try to get a Variable from a target object."""
        var = getattr(target, name, None)
        if isinstance(var, Variable):
            return cast(Variable[Any, Any], var)
        return None

    # Try the object itself first
    result = _try_get_variable(obj, binding)
    if result is not None:
        return result

    # Search up the Qt parent hierarchy
    current: Any = obj
    while hasattr(current, "parent") and callable(current.parent):
        try:
            parent: Any = current.parent()
        except RuntimeError:
            break
        if parent is None:
            break

        result = _try_get_variable(parent, binding)
        if result is not None:
            return result

        current = parent

    # Fallback: check QApplication.instance()
    app = QApplication.instance()
    if app is not None:
        result = _try_get_variable(app, binding)
        if result is not None:
            return result

    return None
