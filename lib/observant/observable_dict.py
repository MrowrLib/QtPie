"""ObservableDict - A reactive dict that notifies on changes."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import overload, override

from .observable import Observable, ValidatorFn


class ObservableDict[K, V]:
    """A dict that notifies listeners when it changes."""

    def __init__(self, items: dict[K, V] | None = None, *, dirty_tracking: bool = True, validation: bool = True) -> None:
        self._items: dict[K, V] = dict(items) if items else {}
        self._clean_items: dict[K, V] = dict(self._items)
        self._callbacks: list[Callable[[], None]] = []
        self._is_dirty: Observable[bool] | None = Observable[bool](False, dirty_tracking=False, validation=False) if dirty_tracking else None

        # Validation
        self._validators: dict[str, ValidatorFn[dict[K, V]]] = {}
        if validation:
            self._validation_errors: Observable[dict[str, list[str]]] | None = Observable({}, dirty_tracking=False, validation=False)
            self._validation_error_messages: Observable[list[str]] | None = Observable([], dirty_tracking=False, validation=False)
            self._is_valid: Observable[bool] | None = Observable(True, dirty_tracking=False, validation=False)
        else:
            self._validation_errors = None
            self._validation_error_messages = None
            self._is_valid = None

    def _notify(self) -> None:
        """Notify listeners and update dirty state."""
        if self._is_dirty is not None:
            now_dirty = self._items != self._clean_items
            if self._is_dirty.get() != now_dirty:
                self._is_dirty.set(now_dirty)

        self._validate()

        for callback in self._callbacks:
            callback()

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when the dict changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Dirty state - usable as bool or Observable."""
        if self._is_dirty is None:
            raise RuntimeError("Dirty tracking not enabled for this ObservableDict")
        return self._is_dirty

    def reset_dirty(self) -> None:
        """Mark current state as clean."""
        self._clean_items = dict(self._items)
        if self._is_dirty is not None:
            self._is_dirty.set(False)

    # Dict read operations
    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[K]:
        return iter(self._items)

    def __contains__(self, key: object) -> bool:
        return key in self._items

    @overload
    def get(self, key: K) -> V | None: ...
    @overload
    def get(self, key: K, default: V) -> V: ...
    @overload
    def get(self, key: K, default: None) -> V | None: ...
    def get(self, key: K, default: V | None = None) -> V | None:
        return self._items.get(key, default)

    def __getitem__(self, key: K) -> V:
        return self._items[key]

    def keys(self) -> list[K]:
        """Return list of keys."""
        return list(self._items.keys())

    def values(self) -> list[V]:
        """Return list of values."""
        return list(self._items.values())

    def items(self) -> list[tuple[K, V]]:
        """Return list of (key, value) tuples."""
        return list(self._items.items())

    # Dict write operations - all notify
    def __setitem__(self, key: K, value: V) -> None:
        self._items[key] = value
        self._notify()

    def __delitem__(self, key: K) -> None:
        del self._items[key]
        self._notify()

    def pop(self, key: K, *default: V) -> V:
        """Remove and return value for key."""
        if default:
            result = self._items.pop(key, default[0])
        else:
            result = self._items.pop(key)
        self._notify()
        return result

    def popitem(self) -> tuple[K, V]:
        """Remove and return (key, value) pair."""
        item = self._items.popitem()
        self._notify()
        return item

    def clear(self) -> None:
        """Remove all items."""
        self._items.clear()
        self._notify()

    def update(self, other: dict[K, V]) -> None:
        """Update with items from other dict."""
        self._items.update(other)
        self._notify()

    def setdefault(self, key: K, default: V) -> V:
        """Set default value for key if not present."""
        if key not in self._items:
            self._items[key] = default
            self._notify()
            return default
        return self._items[key]

    # Utility
    @override
    def __repr__(self) -> str:
        return f"ObservableDict({self._items!r})"

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ObservableDict):
            return self._items == other._items  # pyright: ignore[reportUnknownMemberType]
        if isinstance(other, dict):
            return self._items == other
        return NotImplemented

    def to_dict(self) -> dict[K, V]:
        """Return a copy of the internal dict."""
        return dict(self._items)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[dict[K, V]]) -> None:
        """Add a named validator. Validator returns None (valid) or str/list[str] (errors)."""
        self._validators[name] = validator
        self._validate()

    def _validate(self) -> None:
        """Run all validators and update state."""
        if self._is_valid is None or not self._validators:
            return  # Validation disabled or no validators

        errors_dict: dict[str, list[str]] = {}
        all_messages: list[str] = []

        for name, validator in self._validators.items():
            result = validator(self._items)
            if result is None:
                errors_dict[name] = []
            elif isinstance(result, str):
                errors_dict[name] = [result]
                all_messages.append(result)
            else:  # list[str]
                errors_dict[name] = list(result)
                all_messages.extend(result)

        assert self._validation_errors is not None
        assert self._validation_error_messages is not None
        self._validation_errors.set(errors_dict)
        self._validation_error_messages.set(all_messages)

        is_valid = len(all_messages) == 0
        if self._is_valid.get() != is_valid:
            self._is_valid.set(is_valid)

    @property
    def is_valid(self) -> Observable[bool]:
        """Validity state. Bindable."""
        if self._is_valid is None:
            raise RuntimeError("Validation not enabled for this ObservableDict")
        return self._is_valid

    @property
    def validation_errors(self) -> Observable[dict[str, list[str]]]:
        """Errors by validator name. Bindable."""
        if self._validation_errors is None:
            raise RuntimeError("Validation not enabled for this ObservableDict")
        return self._validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Bindable."""
        if self._validation_error_messages is None:
            raise RuntimeError("Validation not enabled for this ObservableDict")
        return self._validation_error_messages
