"""Observable - A reactive value that notifies on change."""

from collections.abc import Callable


class Observable[T]:
    """A value that notifies listeners when it changes."""

    def __init__(self, value: T) -> None:
        self._value = value
        self._callbacks: list[Callable[[T], None]] = []

    def get(self) -> T:
        """Get the current value."""
        return self._value

    def set(self, value: T) -> None:
        """Set a new value and notify listeners."""
        self._value = value
        for callback in self._callbacks:
            callback(value)

    def on_change(self, callback: Callable[[T], None]) -> None:
        """Register a callback to be called when the value changes."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
