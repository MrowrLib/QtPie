"""ObservableSet - A reactive set that notifies on changes."""

from collections.abc import Callable, Iterator
from typing import override

from .observable import Observable, ValidatorFn


class ObservableSet[T]:
    """A set that notifies listeners when it changes."""

    def __init__(self, items: set[T] | None = None, *, dirty_tracking: bool = True, validation: bool = True) -> None:
        self._items: set[T] = set(items) if items else set()
        self._clean_items: set[T] = set(self._items)
        self._callbacks: list[Callable[[], None]] = []
        self._is_dirty: Observable[bool] | None = Observable[bool](False, dirty_tracking=False, validation=False) if dirty_tracking else None

        # Granular callbacks for efficient UI sync
        self._add_callbacks: list[Callable[[T], None]] = []
        self._remove_callbacks: list[Callable[[T], None]] = []
        self._clear_callbacks: list[Callable[[set[T]], None]] = []

        # Validation
        self._validators: dict[str, ValidatorFn[set[T]]] = {}
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
        """Register a callback to be called when the set changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def on_add(self, callback: Callable[[T], None]) -> None:
        """Register callback for item addition: callback(item)."""
        if callback not in self._add_callbacks:
            self._add_callbacks.append(callback)

    def on_remove(self, callback: Callable[[T], None]) -> None:
        """Register callback for item removal: callback(item)."""
        if callback not in self._remove_callbacks:
            self._remove_callbacks.append(callback)

    def on_clear(self, callback: Callable[[set[T]], None]) -> None:
        """Register callback for set clear: callback(removed_items)."""
        if callback not in self._clear_callbacks:
            self._clear_callbacks.append(callback)

    def _notify_add(self, item: T) -> None:
        """Fire add callbacks."""
        for cb in self._add_callbacks:
            cb(item)

    def _notify_remove(self, item: T) -> None:
        """Fire remove callbacks."""
        for cb in self._remove_callbacks:
            cb(item)

    def _notify_clear(self, removed_items: set[T]) -> None:
        """Fire clear callbacks."""
        for cb in self._clear_callbacks:
            cb(removed_items)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Dirty state - usable as bool or Observable."""
        if self._is_dirty is None:
            raise RuntimeError("Dirty tracking not enabled for this ObservableSet")
        return self._is_dirty

    def reset_dirty(self) -> None:
        """Mark current state as clean."""
        self._clean_items = set(self._items)
        if self._is_dirty is not None:
            self._is_dirty.set(False)

    # Set read operations
    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __contains__(self, item: object) -> bool:
        return item in self._items

    def issubset(self, other: set[T]) -> bool:
        """Test whether every element in the set is in other."""
        return self._items.issubset(other)

    def issuperset(self, other: set[T]) -> bool:
        """Test whether every element in other is in the set."""
        return self._items.issuperset(other)

    def isdisjoint(self, other: set[T]) -> bool:
        """Return True if the set has no elements in common with other."""
        return self._items.isdisjoint(other)

    def union(self, *others: set[T]) -> set[T]:
        """Return a new set with elements from the set and all others."""
        return self._items.union(*others)

    def intersection(self, *others: set[T]) -> set[T]:
        """Return a new set with elements common to the set and all others."""
        return self._items.intersection(*others)

    def difference(self, *others: set[T]) -> set[T]:
        """Return a new set with elements in the set that are not in the others."""
        return self._items.difference(*others)

    def symmetric_difference(self, other: set[T]) -> set[T]:
        """Return a new set with elements in either the set or other but not both."""
        return self._items.symmetric_difference(other)

    # Set write operations - all notify
    def add(self, item: T) -> None:
        """Add an element to the set."""
        if item not in self._items:
            self._items.add(item)
            self._notify_add(item)
            self._notify()

    def remove(self, item: T) -> None:
        """Remove an element from the set. Raises KeyError if not present."""
        self._items.remove(item)
        self._notify_remove(item)
        self._notify()

    def discard(self, item: T) -> None:
        """Remove an element from the set if it is present."""
        if item in self._items:
            self._items.discard(item)
            self._notify_remove(item)
            self._notify()

    def pop(self) -> T:
        """Remove and return an arbitrary element. Raises KeyError if empty."""
        item = self._items.pop()
        self._notify_remove(item)
        self._notify()
        return item

    def clear(self) -> None:
        """Remove all elements from the set."""
        removed = set(self._items)
        self._items.clear()
        self._notify_clear(removed)
        self._notify()

    def replace(self, items: set[T]) -> None:
        """Replace all items atomically.

        This replaces the entire set and fires a single clear callback.
        Unlike clear() + update(), this ensures len() is correct when
        callbacks fire (important for Qt model bindings).
        """
        removed = set(self._items)
        self._items.clear()
        self._items.update(items)
        # Fire clear callback AFTER items are added
        self._notify_clear(removed)
        self._notify()

    def update(self, *others: set[T]) -> None:
        """Update the set, adding elements from all others."""
        for other in others:
            for item in other:
                if item not in self._items:
                    self._items.add(item)
                    self._notify_add(item)
        self._notify()

    def intersection_update(self, *others: set[T]) -> None:
        """Update the set, keeping only elements found in it and all others."""
        to_remove = self._items - self._items.intersection(*others)
        for item in to_remove:
            self._items.discard(item)
            self._notify_remove(item)
        self._notify()

    def difference_update(self, *others: set[T]) -> None:
        """Update the set, removing elements found in others."""
        for other in others:
            for item in other:
                if item in self._items:
                    self._items.discard(item)
                    self._notify_remove(item)
        self._notify()

    def symmetric_difference_update(self, other: set[T]) -> None:
        """Update the set, keeping only elements found in either set, but not in both."""
        to_add = other - self._items
        to_remove = self._items & other
        for item in to_remove:
            self._items.discard(item)
            self._notify_remove(item)
        for item in to_add:
            self._items.add(item)
            self._notify_add(item)
        self._notify()

    # Utility
    @override
    def __repr__(self) -> str:
        return f"ObservableSet({self._items!r})"

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ObservableSet):
            return self._items == other._items  # pyright: ignore[reportUnknownMemberType]
        if isinstance(other, set):
            return self._items == other
        return NotImplemented

    def to_set(self) -> set[T]:
        """Return a copy of the internal set."""
        return set(self._items)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, name: str, validator: ValidatorFn[set[T]]) -> None:
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
            raise RuntimeError("Validation not enabled for this ObservableSet")
        return self._is_valid

    @property
    def validation_errors(self) -> Observable[dict[str, list[str]]]:
        """Errors by validator name. Bindable."""
        if self._validation_errors is None:
            raise RuntimeError("Validation not enabled for this ObservableSet")
        return self._validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Bindable."""
        if self._validation_error_messages is None:
            raise RuntimeError("Validation not enabled for this ObservableSet")
        return self._validation_error_messages
