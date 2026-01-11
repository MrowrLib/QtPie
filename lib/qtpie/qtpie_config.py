"""Shared QtPie configuration class used by Widget and WidgetBase."""

from typing import Any

from .layout import LayoutType
from .new_field import NewField

__all__ = ["_QtPieConfig"]


class _QtPieConfig:
    """Class-level QtPie configuration."""

    __slots__ = (
        "layout",
        "margins",
        "fields",
        "variable_names",
        "init_wrapped",
        "record_type",
        "record_default",
        "auto_bind",
        "widget_props",
        "object_name",
        "css_classes",
        "required_bindings",
    )

    def __init__(self) -> None:
        self.layout: LayoutType = "vertical"
        self.margins: int | tuple[int, int, int, int] | None = None
        self.fields: dict[str, NewField] = {}
        self.variable_names: list[str] = []
        self.init_wrapped: bool = False
        self.record_type: type[Any] | None = None  # T from Widget[T] or WidgetBase[T]
        self.record_default: Any | None = None  # Initial record value from @widget(record=...)
        self.auto_bind: bool = True  # Auto-bind QWidget fields to matching Variables/record fields
        self.widget_props: dict[str, Any] = {}  # Extra props like windowTitle -> setWindowTitle()
        self.object_name: str | None = None  # objectName for the widget
        self.css_classes: list[str] = []  # CSS classes for the widget
        self.required_bindings: set[str] = set()  # Bare Variable[T] fields that must be provided
