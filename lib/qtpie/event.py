"""Event - Pure Python event emitter for QtPie.

Event[T] provides a unified event API across QtPie:
- In State context: Creates a pure Python event emitter
- In Widget context: Event[T] annotation creates a real Qt Signal

Usage (annotation-only, no assignment needed):
    @state
    class MyState(State):
        on_save: Event           # No args
        on_changed: Event[int]   # Single arg

    @widget
    class MyWidget(Widget):
        on_click: Event[int]     # Creates real Qt Signal(int)
"""

from collections.abc import Callable
from typing import Any

__all__ = ["Event", "is_event_hint", "extract_event_args"]


class Event[T = None]:
    """Pure Python event emitter - like Qt Signal but no Qt dependency.

    In Widget context, Event[T] annotation creates a real Qt Signal via __init_subclass__.
    In State context, Event[T] annotation creates this pure Python emitter.

    Usage (annotation-only, no assignment needed):
        on_save: Event           # No args (T defaults to None)
        on_changed: Event[int]   # Single arg
        on_update: Event[tuple[int, str]]  # Multiple args (use tuple)
    """

    def __init__(self) -> None:
        self._handlers: list[Callable[..., Any]] = []

    def connect(self, handler: Callable[..., object]) -> None:
        """Connect a handler to this event."""
        self._handlers.append(handler)

    def disconnect(self, handler: Callable[..., object]) -> None:
        """Disconnect a handler from this event."""
        self._handlers.remove(handler)

    def emit(self, *args: object) -> None:
        """Emit this event, calling all connected handlers."""
        for handler in self._handlers:
            handler(*args)


def is_event_hint(hint: object) -> bool:
    """Check if a type hint is Event[T] or Event.

    Handles both string annotations and actual type hints.
    """
    # Handle string annotations (forward references)
    if isinstance(hint, str):
        return hint.startswith("Event[") or hint == "Event"

    # Handle actual type hints - check for generic origin
    origin = getattr(hint, "__origin__", None)
    if origin is not None:
        # It's a generic like Event[int]
        return origin is Event

    # Plain Event (no type param)
    return hint is Event


def extract_event_args(hint: object) -> tuple[type, ...]:
    """Extract types from Event[T] to pass to Signal().

    Returns tuple of types:
    - Event -> ()
    - Event[int] -> (int,)
    - Event[tuple[int, str]] -> (int, str)  # Unpacked

    Args:
        hint: The type hint (string or actual type)

    Returns:
        Tuple of types suitable for Signal(*args)
    """
    # Handle string annotations
    if isinstance(hint, str):
        if hint == "Event":
            return ()
        # Parse Event[...] from string
        if hint.startswith("Event[") and hint.endswith("]"):
            type_str = hint[6:-1].strip()
            return _parse_type_string(type_str)
        return ()

    # Handle actual type hints
    origin = getattr(hint, "__origin__", None)
    if origin is Event:
        args = getattr(hint, "__args__", ())
        if not args:
            return ()
        arg = args[0]
        # Check if it's a tuple type (multiple args)
        tuple_origin = getattr(arg, "__origin__", None)
        if tuple_origin is tuple:
            return getattr(arg, "__args__", ())
        return (arg,)

    # Plain Event - no args
    return ()


def _parse_type_string(type_str: str) -> tuple[type, ...]:
    """Parse a type string into actual types.

    Handles basic types and tuple[...] syntax.
    """
    type_str = type_str.strip()

    # Handle tuple[int, str] -> (int, str)
    if type_str.startswith("tuple[") and type_str.endswith("]"):
        inner = type_str[6:-1]
        parts = _split_type_args(inner)
        return tuple(_str_to_type(p.strip()) for p in parts)

    # Single type
    return (_str_to_type(type_str),) if type_str else ()


def _split_type_args(s: str) -> list[str]:
    """Split type arguments respecting nested brackets."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0

    for char in s:
        if char == "[":
            depth += 1
            current.append(char)
        elif char == "]":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)

    if current:
        parts.append("".join(current))

    return parts


def _str_to_type(s: str) -> type:
    """Convert a type string to an actual type."""
    s = s.strip()
    type_map: dict[str, type] = {
        "int": int,
        "str": str,
        "bool": bool,
        "float": float,
        "bytes": bytes,
        "object": object,
        "None": type(None),
    }
    return type_map.get(s, object)
