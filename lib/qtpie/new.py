"""new() - Factory function for QtPie field initialization."""

from typing import Any

from .new_field import NewField


def new(*args: Any, layout: bool | Any = None, **kwargs: Any) -> Any:
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

    Args:
        layout: For QWidget types: False excludes from auto-layout (default None = include).
                For non-QWidget types: passed through to constructor as-is.

    Returns:
        A NewField that @new_fields will process.
    """
    if layout is not None:
        kwargs["layout"] = layout
    return NewField(*args, **kwargs)
