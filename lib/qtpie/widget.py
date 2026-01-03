# pyright: reportPrivateUsage=false
"""Widget - QWidget container with automatic layout."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    from .variable import Variable

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
from .variable import _VariableDescriptor


class _QtPieConfig:
    """Class-level QtPie configuration."""

    __slots__ = ("layout", "margins", "fields", "variable_names", "init_wrapped")

    def __init__(self) -> None:
        self.layout: LayoutType = "vertical"
        self.margins: int | tuple[int, int, int, int] | None = None
        self.fields: dict[str, NewField] = {}
        self.variable_names: list[str] = []
        self.init_wrapped: bool = False


class QtPieState:
    """Instance-level QtPie state."""

    __slots__ = ("variables", "_view_model", "_widget")

    def __init__(self, widget: Widget) -> None:
        self._widget = widget
        self.variables: dict[str, Variable[Any]] = {}
        self._view_model: QtPieViewModel | None = None

    @property
    def view_model(self) -> QtPieViewModel:
        if self._view_model is None:
            self._view_model = QtPieViewModel(self._widget)
        return self._view_model


class QtPieViewModel:
    """Auto-generated view model containing only Variable fields."""

    __slots__ = ("_widget",)

    def __init__(self, widget: Widget) -> None:
        object.__setattr__(self, "_widget", widget)

    def __getattr__(self, name: str) -> Variable[Any]:
        widget: Widget = object.__getattribute__(self, "_widget")
        # Get variable names from class config
        if name in type(widget)._qtpie.variable_names:
            return getattr(widget, name)
        raise AttributeError(f"ViewModel has no attribute {name!r}")


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

    # Class-level config namespace
    _qtpie: _QtPieConfig

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Create fresh config for this subclass
        cls._qtpie = _QtPieConfig()

        # Collect fields and variable names
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, NewField):
                cls._qtpie.fields[name] = value
            elif isinstance(value, _VariableDescriptor):
                cls._qtpie.variable_names.append(name)

        # Apply @new_fields to handle non-Variable instantiation
        new_fields(cls)

    @property
    def view_model(self) -> QtPieViewModel:
        """Access only the Variable fields of this widget."""
        # Instance _qtpie shadows the class _qtpie (config)
        state = self.__dict__.get("_qtpie")
        if state is None:
            state = QtPieState(self)
            self.__dict__["_qtpie"] = state
        return state.view_model


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
        # Store layout config
        cls._qtpie.layout = layout
        cls._qtpie.margins = margins

        # Wrap __init__ to set up layout
        _wrap_init_for_layout(cls)

        return cls

    if cls is not None:
        return decorator(cls)

    return decorator


def _wrap_init_for_layout(cls: type[Widget]) -> None:
    """Wrap __init__ to create layout, add child widgets, and call __setup__."""
    if cls._qtpie.init_wrapped:
        return

    original_init = cls.__init__

    # Capture config at decoration time
    config = cls._qtpie

    def wrapped_init(self: Widget, *args: Any, **kwargs: Any) -> None:
        # Call original __init__ (which instantiates fields via new_fields)
        original_init(self, *args, **kwargs)

        # Set up layout if configured
        if config.layout is not None:
            qt_layout = _create_layout(config.layout)
            if qt_layout is not None:
                self.setLayout(qt_layout)

                # Apply margins
                if config.margins is not None:
                    if isinstance(config.margins, int):
                        qt_layout.setContentsMargins(config.margins, config.margins, config.margins, config.margins)
                    else:
                        qt_layout.setContentsMargins(*config.margins)

                # Add child widgets to layout (in field definition order)
                for name, field in config.fields.items():
                    if field.exclude_from_layout:
                        continue

                    widget_instance = getattr(self, name, None)
                    if widget_instance is None:
                        continue

                    if not isinstance(widget_instance, QWidget):
                        continue

                    _add_to_layout(qt_layout, widget_instance, config.layout)

        # Call __setup__ hook if defined
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie.init_wrapped = True


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
        layout.addRow(widget_instance)  # type: ignore[union-attr]
    elif layout_type == "grid":
        layout.addWidget(widget_instance)  # type: ignore[union-attr]
