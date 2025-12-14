"""The make() factory function for creating widget instances."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field
from typing import Any

# Metadata keys used to store info for the @widget decorator
SIGNALS_METADATA_KEY = "qtpie_signals"
FORM_LABEL_METADATA_KEY = "qtpie_form_label"
GRID_POSITION_METADATA_KEY = "qtpie_grid_position"

# Type alias for grid position tuples
GridTuple = tuple[int, int] | tuple[int, int, int, int]


def make[T](
    class_type: Callable[..., T],
    *args: Any,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    **kwargs: Any,
) -> T:
    """
    Create a widget instance as a dataclass field default.

    This provides a cleaner syntax than field(default_factory=lambda: ...).

    Args:
        class_type: The widget class to instantiate.
        *args: Positional arguments passed to the constructor.
        form_label: Label text for form layouts. When set, creates a labeled row.
        grid: Position in grid layout as (row, col) or (row, col, rowspan, colspan).
        **kwargs: Keyword arguments - if value is a string or callable,
                  it's treated as a potential signal connection. Otherwise,
                  it's passed to the constructor.

    Examples:
        # Basic widget creation
        label: QLabel = make(QLabel, "Hello World")

        # With properties
        edit: QLineEdit = make(QLineEdit, placeholderText="Enter name")

        # With signal connections (string = method name)
        button: QPushButton = make(QPushButton, "Click", clicked="on_click")

        # With signal connections (callable)
        button: QPushButton = make(QPushButton, clicked=lambda: print("clicked!"))

        # Form layout with label
        name: QLineEdit = make(QLineEdit, form_label="Full Name")

        # Grid layout with position
        btn: QPushButton = make(QPushButton, "7", grid=(1, 0))
        display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))  # spans 4 cols

    Returns:
        At type-check time: T (the widget type)
        At runtime: a dataclass field with default_factory

    Note:
        The type lie (returning T but actually returning field()) is intentional
        to make the API ergonomic while maintaining type safety.
    """
    # Separate potential signal kwargs from widget property kwargs
    potential_signals: dict[str, str | Callable[..., Any]] = {}
    widget_kwargs: dict[str, Any] = {}

    for key, value in kwargs.items():
        if isinstance(value, str) or callable(value):
            # Could be a signal connection - store for later verification
            potential_signals[key] = value
        else:
            # Regular property - pass to constructor
            widget_kwargs[key] = value

    def factory_fn() -> T:
        return class_type(*args, **widget_kwargs)

    metadata: dict[str, Any] = {}
    if potential_signals:
        metadata[SIGNALS_METADATA_KEY] = potential_signals
    if form_label is not None:
        metadata[FORM_LABEL_METADATA_KEY] = form_label
    if grid is not None:
        metadata[GRID_POSITION_METADATA_KEY] = grid

    return field(default_factory=factory_fn, metadata=metadata if metadata else {})  # type: ignore[return-value]
