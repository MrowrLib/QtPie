"""ObservableList - A reactive list that notifies on changes."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import overload, override

from .observable import Observable


class ObservableList[T]:
    """A list that notifies listeners when it changes."""

    def __init__(self, items: list[T] | None = None, *, dirty_tracking: bool = True) -> None:
        self._items: list[T] = list(items) if items else []
        self._clean_items: list[T] = list(self._items)
        self._callbacks: list[Callable[[], None]] = []
        self._is_dirty: Observable[bool] | None = Observable[bool](False, dirty_tracking=False) if dirty_tracking else None

    def _notify(self) -> None:
        """Notify listeners and update dirty state."""
        if self._is_dirty is not None:
            now_dirty = self._items != self._clean_items
            if self._is_dirty.get() != now_dirty:
                self._is_dirty.set(now_dirty)

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
