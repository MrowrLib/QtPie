"""Variable - Per-instance reactive state in QtPie widgets."""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast, get_origin, overload, override

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ValidatorFn

# Union of all observable types
type AnyObservable[T] = Observable[T] | ObservableList[T] | ObservableDict[Any, T] | ObservableProxy[T]

# TypeVars for list/dict item types (used in overloads)
_ItemT = TypeVar("_ItemT")
_KeyT = TypeVar("_KeyT")
_ValT = TypeVar("_ValT")


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

    def __init__(self, wrapper: AnyObservable[T], widget_type: type | None = None) -> None:
        object.__setattr__(self, "_wrapper", wrapper)
        object.__setattr__(self, "_widget_type", widget_type)
        object.__setattr__(self, "_widget", None)  # Populated later when widget is created

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to ObservableProxy for field access.

        For Variable[Dog], self._dog.name returns dog.name (unwrapped value).
        Use .observable.name for the Observable itself.
        """
        # Only forward to proxy if we're wrapping an ObservableProxy
        wrapper: Any = object.__getattribute__(self, "_wrapper")
        if isinstance(wrapper, ObservableProxy):
            result = getattr(cast(Any, wrapper), name)
            # Unwrap Observable to return actual value
            if isinstance(result, Observable):
                return cast(Any, result.get())
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
        """Register a change callback on the underlying wrapper."""
        self._wrapper.on_change(callback)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[T]) -> None:
        """Add a named validator. Validator returns None (valid) or str/list[str] (errors)."""
        # type: ignore needed because AnyObservable union has different validator signatures
        self._wrapper.add_validator(name, validator)  # type: ignore[arg-type]

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
    # List/Dict delegation
    # Typed overloads provide intellisense for list/dict item types
    # -------------------------------------------------------------------------

    if TYPE_CHECKING:
        # List-specific methods
        def append(self: Variable[list[_ItemT], Any], item: _ItemT) -> None: ...
        def extend(self: Variable[list[_ItemT], Any], items: list[_ItemT]) -> None: ...
        def insert(self: Variable[list[_ItemT], Any], index: int, item: _ItemT) -> None: ...
        def remove(self: Variable[list[_ItemT], Any], item: _ItemT) -> None: ...

        # List pop
        @overload
        def pop(self: Variable[list[_ItemT], Any], index: int = -1) -> _ItemT: ...
        @overload
        def pop(self: Variable[dict[_KeyT, _ValT], Any], index: _KeyT) -> _ValT: ...  # pyright: ignore[reportInconsistentOverload]
        def pop(self, index: Any = -1) -> Any: ...

        # Shared list/dict methods with overloads
        @overload
        def clear(self: Variable[list[_ItemT], Any]) -> None: ...
        @overload
        def clear(self: Variable[dict[_KeyT, _ValT], Any]) -> None: ...
        def clear(self) -> None: ...

        @overload
        def __len__(self: Variable[list[_ItemT], Any]) -> int: ...
        @overload
        def __len__(self: Variable[dict[_KeyT, _ValT], Any]) -> int: ...
        def __len__(self) -> int: ...

        @overload
        def __iter__(self: Variable[list[_ItemT], Any]) -> Iterator[_ItemT]: ...
        @overload
        def __iter__(self: Variable[dict[_KeyT, _ValT], Any]) -> Iterator[_KeyT]: ...
        def __iter__(self) -> Iterator[Any]: ...

        @overload
        def __contains__(self: Variable[list[_ItemT], Any], item: _ItemT) -> bool: ...
        @overload
        def __contains__(self: Variable[dict[_KeyT, _ValT], Any], item: _KeyT) -> bool: ...  # pyright: ignore[reportInconsistentOverload]
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

        def pop(self, index: int = -1) -> Any:
            """Remove and return item at index (delegates to ObservableList)."""
            if not isinstance(self._wrapper, ObservableList):
                raise TypeError(f"pop() requires ObservableList, got {type(self._wrapper).__name__}")
            return self._wrapper.pop(index)

        def clear(self) -> None:
            """Remove all items (delegates to ObservableList or ObservableDict)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict)):
                self._wrapper.clear()
            else:
                raise TypeError(f"clear() requires ObservableList/ObservableDict, got {type(self._wrapper).__name__}")

        def __len__(self) -> int:
            """Return length (delegates to ObservableList or ObservableDict)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict)):
                return len(self._wrapper)
            raise TypeError(f"len() requires ObservableList/ObservableDict, got {type(self._wrapper).__name__}")

        def __iter__(self) -> Iterator[Any]:
            """Iterate (delegates to ObservableList or ObservableDict)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict)):
                return iter(self._wrapper)
            raise TypeError(f"iter() requires ObservableList/ObservableDict, got {type(self._wrapper).__name__}")

        def __contains__(self, item: Any) -> bool:
            """Check membership (delegates to ObservableList or ObservableDict)."""
            if isinstance(self._wrapper, (ObservableList, ObservableDict)):
                return item in self._wrapper
            raise TypeError(f"'in' requires ObservableList/ObservableDict, got {type(self._wrapper).__name__}")

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

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[T]) -> None:
        """Add a named validator. Validator returns None (valid) or str/list[str] (errors)."""
        self._wrapper.add_validator(name, validator)

    @property
    def is_valid(self) -> Observable[bool]:
        """Validity state. Bindable."""
        return cast(Observable[bool], self._wrapper.is_valid)

    @property
    def validation_errors(self) -> Observable[dict[str, list[str]]]:
        """Errors by validator name. Bindable."""
        return cast(Observable[dict[str, list[str]]], self._wrapper.validation_errors)

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Bindable."""
        return cast(Observable[list[str]], self._wrapper.validation_error_messages)

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

    def __init__(
        self,
        default: T,
        name: str,
        inner_type: type | None = None,
        widget_type: type | None = None,
        widget_args: tuple[Any, ...] = (),
        widget_kwargs: dict[str, Any] | None = None,
        label: str | None = None,
        grid: tuple[int, ...] | None = None,
        exclude_from_layout: bool = False,
        validators: list[str] | None = None,
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
        # Validator method names to auto-register
        self.validators = validators or []

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
            var: Variable[T] = Variable(wrapper, widget_type=self._widget_type)
            qtpie_state.register_variable(self._name, var)

            # If widget_type is set, create the widget and bind it
            if self._widget_type is not None:
                from .bindings import bind

                # Check if inner_type is list[X] or dict[K, V] - create repeater
                inner_origin = get_origin(self._inner_type)
                if inner_origin is list:
                    from typing import get_args as typing_get_args

                    from .widget_repeater import WidgetRepeater

                    # Extract item type X from list[X]
                    type_args = typing_get_args(self._inner_type)
                    item_type = type_args[0] if type_args else None

                    # Extract bind= from widget_kwargs for WidgetRepeater
                    widget_kwargs_copy = dict(self._widget_kwargs)
                    bind_expr = widget_kwargs_copy.pop("bind", "{#self}")

                    # Create WidgetRepeater instead of single widget
                    widget_instance = WidgetRepeater(  # pyright: ignore[reportUnknownVariableType]
                        observable_list=wrapper,  # type: ignore[arg-type]
                        item_type=item_type,
                        widget_type=self._widget_type,
                        widget_args=self._widget_args,
                        widget_kwargs=widget_kwargs_copy,
                        bind_expr=bind_expr,
                    )
                elif inner_origin is dict:
                    from typing import get_args as typing_get_args

                    from .dict_widget_repeater import DictWidgetRepeater

                    # Extract K, V from dict[K, V]
                    type_args = typing_get_args(self._inner_type)
                    key_type = type_args[0] if len(type_args) > 0 else None
                    value_type = type_args[1] if len(type_args) > 1 else None

                    # Extract bind= from widget_kwargs for DictWidgetRepeater
                    widget_kwargs_copy = dict(self._widget_kwargs)
                    bind_expr = widget_kwargs_copy.pop("bind", "{#key} = {#value}")

                    # Create DictWidgetRepeater instead of single widget
                    widget_instance = DictWidgetRepeater(  # pyright: ignore[reportUnknownVariableType]
                        observable_dict=wrapper,  # type: ignore[arg-type]
                        key_type=key_type,
                        value_type=value_type,
                        widget_type=self._widget_type,
                        widget_args=self._widget_args,
                        widget_kwargs=widget_kwargs_copy,
                        bind_expr=bind_expr,
                    )
                else:
                    # Regular widget creation
                    try:
                        widget_instance = self._widget_type(*self._widget_args, **self._widget_kwargs)
                    except (TypeError, AttributeError) as e:
                        raise TypeError(f"Failed to create {self._widget_type.__name__} for Variable '{self._name}': {e}\n  args={self._widget_args}, kwargs={self._widget_kwargs}") from e
                    bind(var).to(widget_instance)

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


def create_variable_descriptor(
    default: Any,
    name: str,
    inner_type: type | None = None,
    widget_type: type | None = None,
    widget_args: tuple[Any, ...] = (),
    widget_kwargs: dict[str, Any] | None = None,
    label: str | None = None,
    grid: tuple[int, ...] | None = None,
    exclude_from_layout: bool = False,
    validators: list[Any] | None = None,
) -> Any:
    """Create a variable descriptor. Used by NewField."""
    return _VariableDescriptor(default, name, inner_type, widget_type, widget_args, widget_kwargs, label, grid, exclude_from_layout, validators)
