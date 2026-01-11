"""Shared setter utilities for bindings."""

from collections.abc import Callable
from typing import Any

from qtpy.QtWidgets import QWidget


def make_bound_setter(setter: Callable[[Any, Any], None], widget: QWidget) -> Callable[[Any], None]:
    """Create a bound setter function that captures the widget reference.

    Args:
        setter: A setter function that takes (widget, value)
        widget: The widget to bind to

    Returns:
        A function that takes just (value) and calls setter(widget, value)
    """

    def bound_setter(val: Any) -> None:
        setter(widget, val)

    return bound_setter
