"""The @slot decorator for async-compatible signal handlers."""

import asyncio
from collections.abc import Callable

from qtpy.QtCore import Slot

# Try to import qasync - it's optional
try:
    from qasync import asyncSlot  # type: ignore[import-untyped]
except ImportError:
    asyncSlot = None


def slot[F: Callable[..., object]](*args: object, **kwargs: object) -> Callable[[F], F] | F:
    """
    Smart slot decorator that handles both async and sync functions.

    For async functions, uses qasync.asyncSlot for non-blocking execution.
    For sync functions, uses Qt's @Slot decorator when type args are provided.

    Args:
        *args: Type arguments for Qt signal (e.g., str, int).
        **kwargs: Additional arguments for the Slot decorator.

    Examples:
        # Basic async slot (no signal arguments)
        @slot
        async def on_click(self) -> None:
            await asyncio.sleep(1)
            print("Done!")

        # Async slot with signal argument
        @slot(str)
        async def on_text_changed(self, text: str) -> None:
            result = await validate_async(text)
            self.show_result(result)

        # Multiple signal arguments
        @slot(int, str)
        async def on_data(self, index: int, value: str) -> None:
            await process_data(index, value)

        # Sync slot (optional, passes through)
        @slot
        def on_button(self) -> None:
            print("Clicked!")

        # Sync slot with type safety
        @slot(str)
        def on_text(self, text: str) -> None:
            print(f"Text: {text}")
    """

    def make_decorator[T: Callable[..., object]](
        slot_args: tuple[object, ...],
        slot_kwargs: dict[str, object],
    ) -> Callable[[T], T]:
        def decorator(fn: T) -> T:
            if asyncio.iscoroutinefunction(fn):
                # Async function - use asyncSlot if available
                if asyncSlot is not None:
                    return asyncSlot(*slot_args, **slot_kwargs)(fn)  # type: ignore[return-value]
                else:
                    raise RuntimeError("qasync is required for async slots. Install it with: pip install qasync")
            else:
                # Sync function - use Qt's Slot decorator if type args provided
                if slot_args or slot_kwargs:
                    return Slot(*slot_args, **slot_kwargs)(fn)  # type: ignore[return-value]
                # No args - just return the function as-is
                return fn

        return decorator

    # Handle both @slot and @slot() and @slot(str) syntaxes
    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], type):
        # Called without parentheses: @slot
        fn = args[0]
        return make_decorator((), {})(fn)  # type: ignore[return-value]

    # Called with parentheses: @slot() or @slot(str)
    return make_decorator(args, kwargs)  # type: ignore[return-value]
