"""WidgetBase - Mixin that adds QtPie features to any widget."""

from typing import Any

from .new_fields import new_fields


class WidgetBase:
    """Mixin that adds QtPie reactive features to any Qt widget.

    Use this when subclassing existing Qt widgets like QListView, QTableView, etc.

    Usage:
        class MyListView(QListView, WidgetBase):
            _items: Variable[list[str]] = new([])

            def __setup__(self):
                # Called after Qt's __init__ completes
                self._items = ["first", "second"]

    Features:
        - Auto-applies @new_fields (no decorator needed)
        - __setup__ lifecycle hook runs after __init__
        - Variable fields work automatically
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Auto-apply @new_fields to process Variable and other new() fields
        new_fields(cls)
        # Wrap __init__ to call __setup__ after initialization
        _wrap_init_for_setup(cls)


def _wrap_init_for_setup(cls: type) -> None:
    """Wrap __init__ to call __setup__ after initialization."""
    # Check if already wrapped
    if getattr(cls, "__setup_wrapped__", False):
        return

    original_init = cls.__init__ if hasattr(cls, "__init__") else None

    def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
        if original_init is not None:
            original_init(self, *args, **kwargs)
        # Call __setup__ if defined
        if hasattr(self, "__setup__"):
            self.__setup__()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls.__setup_wrapped__ = True  # type: ignore[attr-defined]
