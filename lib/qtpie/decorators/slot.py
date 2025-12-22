"""The @slot decorator - smart async/sync slot wrapper."""

import asyncio
from collections.abc import Callable
from typing import overload

from qtpy.QtCore import Slot

# Conditional import for qasync (may not be installed)
try:
    from qasync import asyncSlot  # type: ignore[import-untyped]
except ImportError:
    asyncSlot = None  # type: ignore[assignment, misc]


@overload
def slot[F: Callable[..., object]](__fn: F) -> F: ...


@overload
def slot[F: Callable[..., object]](*args: type, **kwargs: object) -> Callable[[F], F]: ...


def slot[F: Callable[..., object]](*args: object, **kwargs: object) -> Callable[[F], F] | F:
    """
    Smart slot decorator that handles both async and sync functions.

    Works with or without parentheses:
        @slot
        async def on_click(self): ...

        @slot()
        async def on_click(self): ...

        @slot(str)
        async def on_message(self, text: str): ...

    For async functions:
        - Wraps with qasync.asyncSlot for proper Qt event loop integration
        - The coroutine runs in the background (non-blocking)

    For sync functions:
        - Wraps with Qt's @Slot decorator
        - If no args provided, returns the function as-is

    Args:
        *args: Qt type arguments forwarded to @Slot (e.g., str, int)
        **kwargs: Qt keyword arguments forwarded to @Slot
    """

    def make_decorator[T: Callable[..., object]](slot_args: tuple[object, ...], slot_kwargs: dict[str, object]) -> Callable[[T], T]:
        def decorator(fn: T) -> T:
            if asyncio.iscoroutinefunction(fn):
                # Async function - use asyncSlot if available
                if asyncSlot is not None:
                    return asyncSlot(*slot_args, **slot_kwargs)(fn)  # type: ignore[return-value]
                else:
                    raise RuntimeError("qasync is required for async slots. Install it with: pip install qasync")
            else:
                # Sync function - use Qt's Slot decorator or pass through
                if slot_args or slot_kwargs:
                    return Slot(*slot_args, **slot_kwargs)(fn)  # type: ignore[return-value]
                return fn

        return decorator

    # Check if called without parentheses: @slot
    # First arg would be the function itself (callable but not a type)
    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], type):
        fn = args[0]
        # No type args - create decorator with empty args
        return make_decorator((), {})(fn)  # type: ignore[arg-type, return-value]

    # Called with parentheses: @slot() or @slot(str)
    return make_decorator(args, kwargs)
