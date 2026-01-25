"""Frame - QFrame with QtPie declarative features."""

from typing import Any

from qtpy.QtWidgets import QFrame

from .widget import widget
from .widget_base import WidgetBase


class Frame[T = None](QFrame, WidgetBase[T]):
    """QFrame with QtPie declarative features.

    Use this as a base for styled frame/panel components.
    Supports frameShape, frameShadow, lineWidth and other QFrame properties,
    plus full QSS styling support.

    Example:
        @frame
        class Card(Frame):
            _title: QLabel = new("Title")
            _content: QLabel = new("Content")

        @frame(frameShape=QFrame.Shape.Box)
        class StyledCard(Frame):
            _content: QLabel = new("Styled content")

    With record type:
        @frame
        class PersonCard(Frame[Person]):
            name: QLineEdit = new()  # Auto-binds to record.name
            age: QSpinBox = new()    # Auto-binds to record.age
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Check that @frame decorator was applied."""
        if not self._qtpie_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @frame. Add @frame above your class definition.")
        # This should never run - @frame replaces __init__
        super().__init__(*args, **kwargs)  # pragma: no cover


# @frame decorator - alias for @widget
# Frame classes use @frame decorator just like Widget classes use @widget
frame = widget
