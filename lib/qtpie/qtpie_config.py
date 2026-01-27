"""Shared QtPie configuration class used by Widget and WidgetBase."""

from typing import Any

from qtpy.QtCore import Qt

from .layout import FieldGrowthPolicy, LayoutType, RowWrapPolicy, SizeConstraint
from .new_field import NewField
from .utils.layouts import IconType

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
        "icon",
        "size",
        "signal_connections",
        "event_new_fields",
        "attributes",
        # Layout configuration
        "spacing",
        "size_constraint",
        "horizontal_spacing",
        "vertical_spacing",
        "row_wrap_policy",
        "label_alignment",
        "form_alignment",
        "field_growth_policy",
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
        self.icon: IconType = None  # Window icon (resolved at runtime)
        self.size: tuple[int, int] | None = None  # Initial size (width, height)
        self.signal_connections: dict[str, str] = {}  # Signal connections from decorator
        self.event_new_fields: dict[str, NewField] = {}  # Event[T] fields with new(on=...)
        self.attributes: dict[Qt.WidgetAttribute, bool] = {}  # Widget attributes to set
        # Layout configuration
        self.spacing: int | None = None  # layout.setSpacing()
        self.size_constraint: SizeConstraint | None = None  # layout.setSizeConstraint()
        self.horizontal_spacing: int | None = None  # QGridLayout/QFormLayout.setHorizontalSpacing()
        self.vertical_spacing: int | None = None  # QGridLayout/QFormLayout.setVerticalSpacing()
        self.row_wrap_policy: RowWrapPolicy | None = None  # QFormLayout.setRowWrapPolicy()
        self.label_alignment: Qt.AlignmentFlag | None = None  # QFormLayout.setLabelAlignment()
        self.form_alignment: Qt.AlignmentFlag | None = None  # QFormLayout.setFormAlignment()
        self.field_growth_policy: FieldGrowthPolicy | None = None  # QFormLayout.setFieldGrowthPolicy()
