"""Auto-wrap async Qt virtual methods with qasync decorators."""

import asyncio
from typing import Any

from qtpy.QtGui import QCloseEvent

# Try to import qasync - it's optional
try:
    from qasync import asyncClose  # type: ignore[import-untyped]
except ImportError:
    asyncClose = None


def wrap_async_methods(cls: type[Any]) -> None:
    """
    Auto-create closeEvent that calls async on_close hook.

    If a widget defines `async def on_close(self) -> None`, this function
    generates a proper closeEvent override that calls it with asyncClose.

    This avoids the pyright type error from directly overriding closeEvent
    with an async method (since async methods return Coroutine, not None).

    This is called automatically by the @widget decorator.

    Args:
        cls: The widget class to process.

    Example:
        @widget
        class MyWidget(Widget):
            async def on_close(self) -> None:
                await self.save_data()  # Completes before window closes

            # No need to override closeEvent - it's generated automatically!
    """
    if asyncClose is None:
        # qasync not installed - skip wrapping
        return

    # Check for async on_close hook - only if defined on THIS class, not inherited from Widget base
    on_close = cls.__dict__.get("on_close")  # Check class dict directly, not inherited
    if on_close is not None and asyncio.iscoroutinefunction(on_close):
        # Generate closeEvent that calls on_close
        # We need to wrap the async call with asyncClose

        # Create the async wrapper that calls on_close and accepts the event
        async def _async_close_handler(self: Any, event: QCloseEvent) -> None:
            await self.on_close()
            event.accept()

        # Wrap with asyncClose for blocking behavior
        wrapped_close_event = asyncClose(_async_close_handler)  # pyright: ignore[reportUnknownVariableType]

        # Set as closeEvent on the class
        cls.closeEvent = wrapped_close_event  # type: ignore[attr-defined]
