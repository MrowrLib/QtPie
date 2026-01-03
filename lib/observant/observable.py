"""Observable - A reactive value that notifies on change."""

from __future__ import annotations

from collections.abc import Callable


class Observable[T]:
    """A value that notifies listeners when it changes."""

    def __init__(self, value: T, *, dirty_tracking: bool = True) -> None:
        self._value = value
        self._clean_value = value
        self._callbacks: list[Callable[[T], None]] = []
        # Nested Observable for dirty state (without its own dirty tracking to avoid recursion)
        self._is_dirty: Observable[bool] | None = Observable[bool](False, dirty_tracking=False) if dirty_tracking else None

    def get(self) -> T:
        """Get the current value."""
        return self._value

    def set(self, value: T) -> None:
        """Set a new value and notify listeners."""
        self._value = value

        # Update dirty state if tracking
        if self._is_dirty is not None:
            now_dirty = self._value != self._clean_value
            if self._is_dirty.get() != now_dirty:
                self._is_dirty.set(now_dirty)

        for callback in self._callbacks:
            callback(value)

    def on_change(self, callback: Callable[[T], None]) -> None:
        """Register a callback to be called when the value changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    @property
    def is_dirty(self) -> Observable[bool]:
        """Dirty state - usable as bool or Observable."""
        if self._is_dirty is None:
            raise RuntimeError("Dirty tracking not enabled for this Observable")
        return self._is_dirty

    def reset_dirty(self) -> None:
        """Mark current value as clean."""
        self._clean_value = self._value
        if self._is_dirty is not None:
            self._is_dirty.set(False)

    def __bool__(self) -> bool:
        """Allow Observable to be used in boolean context."""
        return bool(self._value)
