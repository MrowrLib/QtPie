"""ObservableList - A reactive list that notifies on changes."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import overload, override

from .observable import Observable, ValidatorFn

logger = logging.getLogger("qtpie.observant.list")


class ObservableList[T]:
    """A list that notifies listeners when it changes."""

    def __init__(self, items: list[T] | None = None, *, dirty_tracking: bool = True, validation: bool = True) -> None:
        self._items: list[T] = list(items) if items else []
        self._clean_items: list[T] = list(self._items)
        self._callbacks: list[Callable[[], None]] = []
        self._is_dirty: Observable[bool] | None = Observable[bool](False, dirty_tracking=False, validation=False) if dirty_tracking else None

        # Granular callbacks for efficient UI sync
        self._insert_callbacks: list[Callable[[int, T], None]] = []
        self._remove_callbacks: list[Callable[[int, T], None]] = []
        self._replace_callbacks: list[Callable[[int, T, T], None]] = []
        self._clear_callbacks: list[Callable[[list[T]], None]] = []

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

        callback_count = len(self._callbacks)
        if callback_count > 0:
            logger.debug("ObservableList._notify: firing %d on_change callbacks", callback_count)
        for callback in self._callbacks:
            callback()

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when the list changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug("ObservableList.on_change: registered callback (total=%d)", len(self._callbacks))

    def on_insert(self, callback: Callable[[int, T], None]) -> None:
        """Register callback for item insertion: callback(index, item)."""
        if callback not in self._insert_callbacks:
            self._insert_callbacks.append(callback)

    def on_remove(self, callback: Callable[[int, T], None]) -> None:
        """Register callback for item removal: callback(index, item)."""
        if callback not in self._remove_callbacks:
            self._remove_callbacks.append(callback)

    def on_replace(self, callback: Callable[[int, T, T], None]) -> None:
        """Register callback for item replacement: callback(index, old_item, new_item)."""
        if callback not in self._replace_callbacks:
            self._replace_callbacks.append(callback)

    def on_clear(self, callback: Callable[[list[T]], None]) -> None:
        """Register callback for list clear: callback(removed_items)."""
        if callback not in self._clear_callbacks:
            self._clear_callbacks.append(callback)

    def _notify_insert(self, index: int, item: T) -> None:
        """Fire insert callbacks."""
        if self._insert_callbacks:
            logger.debug("ObservableList._notify_insert: index=%d, callbacks=%d", index, len(self._insert_callbacks))
        for cb in self._insert_callbacks:
            cb(index, item)

    def _notify_remove(self, index: int, item: T) -> None:
        """Fire remove callbacks."""
        if self._remove_callbacks:
            logger.debug("ObservableList._notify_remove: index=%d, callbacks=%d", index, len(self._remove_callbacks))
        for cb in self._remove_callbacks:
            cb(index, item)

    def _notify_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Fire replace callbacks."""
        if self._replace_callbacks:
            logger.debug("ObservableList._notify_replace: index=%d, callbacks=%d", index, len(self._replace_callbacks))
        for cb in self._replace_callbacks:
            cb(index, old_item, new_item)

    def _notify_clear(self, removed_items: list[T]) -> None:
        """Fire clear callbacks."""
        if self._clear_callbacks:
            logger.debug("ObservableList._notify_clear: removed=%d items, callbacks=%d", len(removed_items), len(self._clear_callbacks))
        for cb in self._clear_callbacks:
            cb(removed_items)

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
        index = len(self._items)
        self._items.append(item)
        self._notify_insert(index, item)
        self._notify()

    def extend(self, items: list[T]) -> None:
        """Extend list with items."""
        start_index = len(self._items)
        self._items.extend(items)
        for i, item in enumerate(items):
            self._notify_insert(start_index + i, item)
        self._notify()

    def insert(self, index: int, item: T) -> None:
        """Insert item at index."""
        self._items.insert(index, item)
        self._notify_insert(index, item)
        self._notify()

    def remove(self, item: T) -> None:
        """Remove first occurrence of item."""
        index = self._items.index(item)
        self._items.remove(item)
        self._notify_remove(index, item)
        self._notify()

    def pop(self, index: int = -1) -> T:
        """Remove and return item at index."""
        # Normalize negative index
        actual_index = index if index >= 0 else len(self._items) + index
        item = self._items.pop(index)
        self._notify_remove(actual_index, item)
        self._notify()
        return item

    def clear(self) -> None:
        """Remove all items."""
        removed = list(self._items)
        self._items.clear()
        self._notify_clear(removed)
        self._notify()

    def replace(self, items: list[T]) -> None:
        """Replace all items atomically.

        This replaces the entire list and fires a single clear callback.
        Unlike clear() + extend(), this ensures rowCount() is correct when
        callbacks fire (important for Qt model bindings).
        """
        removed = list(self._items)
        self._items.clear()
        self._items.extend(items)
        # Fire clear callback AFTER items are added - this way rowCount() returns
        # the correct count when ReactiveListModel emits modelReset
        self._notify_clear(removed)
        self._notify()

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: list[T]) -> None: ...
    def __setitem__(self, index: int | slice, value: T | list[T]) -> None:
        if isinstance(index, int):
            old_item = self._items[index]
            self._items[index] = value  # type: ignore[index, assignment]
            self._notify_replace(index, old_item, value)  # type: ignore[arg-type]
        else:
            # Slice assignment - complex, just use generic notify
            self._items[index] = value  # type: ignore[index, assignment]
        self._notify()

    def __delitem__(self, index: int | slice) -> None:
        if isinstance(index, int):
            item = self._items[index]
            # Normalize negative index
            actual_index = index if index >= 0 else len(self._items) + index
            del self._items[index]
            self._notify_remove(actual_index, item)
        else:
            # Slice deletion - complex, just use generic notify
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

    def remove_validator(self, name: str) -> None:
        """Remove a named validator."""
        if name in self._validators:
            del self._validators[name]
            self._validate()

    def _validate(self) -> None:
        """Run all validators and update state."""
        if self._is_valid is None:
            return  # Validation disabled

        if not self._validators:
            # No validators = always valid
            assert self._validation_errors is not None
            assert self._validation_error_messages is not None
            self._validation_errors.set({})
            self._validation_error_messages.set([])
            if not self._is_valid.get():
                self._is_valid.set(True)
            return

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
