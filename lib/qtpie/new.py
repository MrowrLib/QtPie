"""new() and none() - Factory functions for QtPie field initialization."""

from typing import Any

from .new_field import NewField


class _NoneSentinel:
    """Sentinel for opting out of auto-new()."""

    pass


_NONE_SENTINEL = _NoneSentinel()


def none() -> Any:
    """Opt-out of auto-new() for bare annotations.

    Use this when you want a bare type annotation without auto-instantiation:
        _placeholder: QLabel = none()  # Type hint only, no instance created

    This is only needed when you DON'T want the default auto-new() behavior.
    Bare annotations auto-instantiate by default:
        _label: QLabel           # Auto-creates QLabel()
        _label: QLabel = none()  # No instance created (type hint only)

    Returns:
        A sentinel value that tells QtPie to skip instantiation.
    """
    return _NONE_SENTINEL


def new(*args: Any, **kwargs: Any) -> Any:
    """Create a field for deferred instantiation.

    For Variable[T] fields, pass the default value directly:
        _name: Variable[str] = new("")
        _count: Variable[int] = new(0)
        _ratio: Variable[float] = new(1.5)
        _enabled: Variable[bool] = new(True)

    Or use default= kwarg (equivalent):
        _name: Variable[str] = new(default="")

    For non-Variable types, pass constructor args/kwargs:
        _label: QLabel = new("Hello, World!")
        _config: Config = new(host="localhost", port=8080)

    Returns:
        A NewField that @new_fields will process.
    """
    return NewField(*args, **kwargs)
