"""
Qt Signal-Slot Typing Utilities

This module provides type definitions and utilities for properly typing Qt signal-slot connections
to satisfy Pylance's strict type checking while working with Qt's dynamic signal-slot system.
"""

from typing import Callable, TypeVar, Generic, Protocol, Any, cast, ParamSpec

# Type variables for generic signal handlers
T = TypeVar("T")
P = ParamSpec("P")


class BoolSignalHandler(Protocol):
    """Protocol for handlers of signals that emit a boolean value."""

    def __call__(self, checked: bool) -> None: ...


class VoidSignalHandler(Protocol):
    """Protocol for handlers of signals that emit no values."""

    def __call__(self) -> None: ...


class IntSignalHandler(Protocol):
    """Protocol for handlers of signals that emit an integer value."""

    def __call__(self, value: int) -> None: ...


class PointSignalHandler(Protocol):
    """Protocol for handlers of signals that emit a point value."""

    def __call__(
        self, point: Any
    ) -> None: ...  # Use Any for QPoint to avoid import cycles


class GenericSignalHandler(Protocol, Generic[P]):
    """Generic protocol for signal handlers with arbitrary parameters."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None: ...


def signal_handler_for(func: Callable[P, None]) -> Callable[P, None]:
    """
    Identity function that helps Pylance understand the type of a signal handler.

    Example:
        @signal_handler_for
        def my_handler(value: bool) -> None:
            print(f"Value changed: {value}")

        widget.some_signal.connect(my_handler)  # No type errors
    """
    return func


def as_bool_handler(func: Callable[[bool], None]) -> BoolSignalHandler:
    """Cast a function to a boolean signal handler to satisfy Pylance."""
    return cast(BoolSignalHandler, func)


def as_void_handler(func: Callable[[], None]) -> VoidSignalHandler:
    """Cast a function to a void signal handler to satisfy Pylance."""
    return cast(VoidSignalHandler, func)


def as_int_handler(func: Callable[[int], None]) -> IntSignalHandler:
    """Cast a function to an int signal handler to satisfy Pylance."""
    return cast(IntSignalHandler, func)


def as_generic_handler(func: Callable[..., None]) -> GenericSignalHandler:
    """Cast a function to a generic signal handler to satisfy Pylance."""
    return cast(GenericSignalHandler, func)
