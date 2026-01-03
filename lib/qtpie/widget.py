# pyright: reportPrivateUsage=false
"""Widget - QWidget container with automatic layout."""

from collections.abc import Callable
from typing import Any, overload

from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from .layout import LayoutType
from .new_field import NewField
from .new_fields import new_fields


class Widget(QWidget):
    """QWidget container with automatic layout and QtPie features.

    Usage:
        @widget(layout="horizontal", margins=10)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click")

            def __setup__(self):
                self._button.clicked.connect(self._on_click)

    Or with defaults (vertical layout, no margins):
        @widget
        class MyWidget(Widget):
            _label: QLabel = new("Hello")
    """

    # Class-level config (set by @widget decorator)
    _qtpie_layout: LayoutType = "vertical"
    _qtpie_margins: int | tuple[int, int, int, int] | None = None
    _qtpie_fields: dict[str, NewField]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Collect NewField instances BEFORE new_fields processes them
        cls._qtpie_fields = {}
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, NewField):
                cls._qtpie_fields[name] = value

        # Apply @new_fields to handle Variable and non-Variable instantiation
        new_fields(cls)


@overload
def widget(cls: type[Widget]) -> type[Widget]: ...


@overload
def widget(
    cls: None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
) -> Callable[[type[Widget]], type[Widget]]: ...


def widget(
    cls: type[Widget] | None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
) -> type[Widget] | Callable[[type[Widget]], type[Widget]]:
    """Decorator to configure Widget layout.

    Usage:
        @widget
        class MyWidget(Widget):
            ...

        @widget(layout="horizontal", margins=10)
        class MyWidget(Widget):
            ...

    Args:
        layout: "vertical" | "horizontal" | "form" | "grid" | None
                Default is "vertical". None disables auto-layout.
        margins: int | tuple[int, int, int, int] | None
                 Layout margins. int applies to all sides.
    """

    def decorator(cls: type[Widget]) -> type[Widget]:
        # Store layout config on the class
        cls._qtpie_layout = layout
        cls._qtpie_margins = margins

        # Wrap __init__ to set up layout
        _wrap_init_for_layout(cls)

        return cls

    if cls is not None:
        # Called as @widget without parentheses
        return decorator(cls)

    # Called as @widget(...) with arguments
    return decorator


def _wrap_init_for_layout(cls: type[Widget]) -> None:
    """Wrap __init__ to create layout, add child widgets, and call __setup__."""
    if getattr(cls, "_qtpie_layout_wrapped", False):
        return

    original_init = cls.__init__

    # Capture config at decoration time
    layout_type: LayoutType = cls._qtpie_layout
    margins_config: int | tuple[int, int, int, int] | None = cls._qtpie_margins
    fields_config: dict[str, NewField] = cls._qtpie_fields

    def wrapped_init(self: Widget, *args: Any, **kwargs: Any) -> None:
        # Call original __init__ (which instantiates fields via new_fields)
        original_init(self, *args, **kwargs)

        # Set up layout if configured
        if layout_type is not None:
            # Create the layout
            qt_layout = _create_layout(layout_type)
            if qt_layout is not None:
                self.setLayout(qt_layout)

                # Apply margins
                if margins_config is not None:
                    if isinstance(margins_config, int):
                        qt_layout.setContentsMargins(margins_config, margins_config, margins_config, margins_config)
                    else:
                        qt_layout.setContentsMargins(*margins_config)

                # Add child widgets to layout (in field definition order)
                for name, field in fields_config.items():
                    # Skip if marked for exclusion
                    if field.exclude_from_layout:
                        continue

                    # Get the instantiated widget
                    widget_instance = getattr(self, name, None)
                    if widget_instance is None:
                        continue

                    # Only add QWidget instances
                    if not isinstance(widget_instance, QWidget):
                        continue

                    # Add to layout based on layout type
                    _add_to_layout(qt_layout, widget_instance, layout_type)

        # Call __setup__ hook if defined (after layout is ready)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_layout_wrapped = True  # type: ignore[attr-defined]


def _create_layout(layout_type: LayoutType) -> QLayout | None:
    """Create a Qt layout based on type."""
    if layout_type == "vertical":
        return QVBoxLayout()
    elif layout_type == "horizontal":
        return QHBoxLayout()
    elif layout_type == "form":
        return QFormLayout()
    elif layout_type == "grid":
        return QGridLayout()
    return None


def _add_to_layout(layout: QLayout, widget_instance: QWidget, layout_type: LayoutType) -> None:
    """Add a widget to the layout."""
    if layout_type in ("vertical", "horizontal"):
        layout.addWidget(widget_instance)  # type: ignore[union-attr]
    elif layout_type == "form":
        # For form layout, add without label for now
        # (labels will be supported via new() metadata later)
        layout.addRow(widget_instance)  # type: ignore[union-attr]
    elif layout_type == "grid":
        # For grid layout, auto-position for now
        # (explicit positions will be supported via new() metadata later)
        layout.addWidget(widget_instance)  # type: ignore[union-attr]
