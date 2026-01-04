"""ObservableList - A reactive list that notifies on changes."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import overload, override

from .observable import Observable, ValidatorFn


class ObservableList[T]:
    """A list that notifies listeners when it changes."""

    def __init__(self, items: list[T] | None = None, *, dirty_tracking: bool = True, validation: bool = True) -> None:
        self._items: list[T] = list(items) if items else []
        self._clean_items: list[T] = list(self._items)
        self._callbacks: list[Callable[[], None]] = []
        self._is_dirty: Observable[bool] | None = Observable[bool](False, dirty_tracking=False, validation=False) if dirty_tracking else None

        # Validation
        self._validators: dict[str, ValidatorFn[list[T]]] = {}
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
        """Register a callback to be called when the list changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Dirty state - usable as bool or Observable."""
        if self._is_dirty is None:
            raise RuntimeError("Dirty tracking not enabled for this ObservableList")
        return self._is_dirty

    def reset_dirty(self) -> None:
        """Mark current state as clean."""
        self._clean_items = list(self._items)
        if self._is_dirty is not None:
            self._is_dirty.set(False)

    # List read operations
    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> list[T]: ...
    def __getitem__(self, index: int | slice) -> T | list[T]:
        return self._items[index]

    def __contains__(self, item: object) -> bool:
        return item in self._items

    def index(self, item: T, start: int = 0, stop: int | None = None) -> int:
        """Return index of item."""
        if stop is None:
            return self._items.index(item, start)
        return self._items.index(item, start, stop)

    def count(self, item: T) -> int:
        """Return count of item."""
        return self._items.count(item)

    # List write operations - all notify
    def append(self, item: T) -> None:
        """Append item to end."""
        self._items.append(item)
        self._notify()

    def extend(self, items: list[T]) -> None:
        """Extend list with items."""
        self._items.extend(items)
        self._notify()

    def insert(self, index: int, item: T) -> None:
        """Insert item at index."""
        self._items.insert(index, item)
        self._notify()

    def remove(self, item: T) -> None:
        """Remove first occurrence of item."""
        self._items.remove(item)
        self._notify()

    def pop(self, index: int = -1) -> T:
        """Remove and return item at index."""
        item = self._items.pop(index)
        self._notify()
        return item

    def clear(self) -> None:
        """Remove all items."""
        self._items.clear()
        self._notify()

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: list[T]) -> None: ...
    def __setitem__(self, index: int | slice, value: T | list[T]) -> None:
        self._items[index] = value  # type: ignore[index, assignment]
        self._notify()

    def __delitem__(self, index: int | slice) -> None:
        del self._items[index]
        self._notify()

    # Utility
    @override
    def __repr__(self) -> str:
        return f"ObservableList({self._items!r})"

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ObservableList):
            return self._items == other._items  # pyright: ignore[reportUnknownMemberType]
        if isinstance(other, list):
            return self._items == other
        return NotImplemented

    def to_list(self) -> list[T]:
        """Return a copy of the internal list."""
        return list(self._items)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[list[T]]) -> None:
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
            raise RuntimeError("Validation not enabled for this ObservableList")
        return self._is_valid

    @property
    def validation_errors(self) -> Observable[dict[str, list[str]]]:
        """Errors by validator name. Bindable."""
        if self._validation_errors is None:
            raise RuntimeError("Validation not enabled for this ObservableList")
        return self._validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Bindable."""
        if self._validation_error_messages is None:
            raise RuntimeError("Validation not enabled for this ObservableList")
        return self._validation_error_messages
