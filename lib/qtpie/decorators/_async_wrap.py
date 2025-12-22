"""Internal utilities for auto-wrapping async methods in Qt classes."""

import asyncio
from typing import Any

# Conditional import for qasync (may not be installed)
try:
    from qasync import asyncClose  # type: ignore[import-untyped]
except ImportError:
    asyncClose = None  # type: ignore[assignment, misc]

# Methods that should be wrapped with asyncClose (blocking until complete)
ASYNC_CLOSE_METHODS = ("closeEvent",)


def wrap_async_methods(cls: type[Any]) -> None:
    """
    Auto-wrap async Qt virtual methods with appropriate qasync decorators.

    For methods like closeEvent, uses asyncClose (blocking) so cleanup
    completes before the window is destroyed.

    Modifies the class in-place.
    """
    if asyncClose is None:
        # qasync not installed - skip wrapping
        return

    for method_name in ASYNC_CLOSE_METHODS:
        method = getattr(cls, method_name, None)
        if method is not None and asyncio.iscoroutinefunction(method):
            wrapped = asyncClose(method)  # type: ignore[reportUnknownVariableType]
            setattr(cls, method_name, wrapped)
