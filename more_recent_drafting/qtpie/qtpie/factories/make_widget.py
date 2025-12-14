from dataclasses import field
from typing import Any, Callable, TypeVar, cast

from qtpie.factories.make import (
    BIND_METADATA_KEY,
    BIND_PROP_METADATA_KEY,
    SIGNALS_METADATA_KEY,
)
from qtpie.styles.style_class import QtStyleClass
from qtpy.QtWidgets import QWidget

W = TypeVar("W", bound=QWidget)

WidgetOptionsType = str | list[str] | tuple[str, list[str]] | None


def _create_widget[W](
    widget_class: type[W],
    widget_options: WidgetOptionsType = None,
    *args: Any,
    **kwargs: Any,
) -> W:
    widget = widget_class(*args, **kwargs)
    qwidget = cast(QWidget, widget)

    if widget_options is not None:
        if isinstance(widget_options, str):
            qwidget.setObjectName(widget_options)
        elif isinstance(widget_options, list):
            QtStyleClass.add_classes(qwidget, widget_options)
        elif len(widget_options) == 2:
            name, classes = widget_options
            if name:
                qwidget.setObjectName(name)
            if classes:
                QtStyleClass.add_classes(qwidget, classes)

    return widget


def make_widget[W](
    widget_class: type[W],
    widget_options: WidgetOptionsType = None,
    *args: Any,
    bind: str | None = None,
    bind_prop: str | None = None,
    **kwargs: Any,
) -> W:
    """
    Creates a factory for a QWidget with optional styling, binding, and signal connections.

    Usage:
        # With classes:
        btn: QPushButton = make_widget(QPushButton, ["btn-primary"], "Click Me")

        # With name and classes:
        btn: QPushButton = make_widget(QPushButton, ("myBtn", ["btn-primary"]), "Click")

        # With model binding:
        txt: QLineEdit = make_widget(QLineEdit, ["input"], bind="name")

        # With signal connections:
        btn: QPushButton = make_widget(QPushButton, ["btn"], "Click", clicked="on_click")

        # Combined:
        slider: QSlider = make_widget(
            QSlider,
            ["slider-class"],
            bind="age",
            valueChanged="on_age_changed"
        )
    """
    # Separate potential signal kwargs from widget property kwargs
    potential_signals: dict[str, str | Callable[..., Any]] = {}
    widget_kwargs: dict[str, Any] = {}

    for key, value in kwargs.items():
        if isinstance(value, str) or callable(value):
            potential_signals[key] = value
        else:
            widget_kwargs[key] = value

    factory_fn: Callable[[], W] = lambda: _create_widget(  # noqa: E731
        widget_class, widget_options, *args, **widget_kwargs
    )

    metadata: dict[str, Any] = {}

    if bind is not None:
        metadata[BIND_METADATA_KEY] = bind
        if bind_prop is not None:
            metadata[BIND_PROP_METADATA_KEY] = bind_prop

    if potential_signals:
        metadata[SIGNALS_METADATA_KEY] = potential_signals

    return field(default_factory=factory_fn, metadata=metadata)


def make_form_row_widget[W](
    form_field_name: str,
    widget_class: type[W],
    widget_options: WidgetOptionsType = None,
    *args: Any,
    **kwargs: Any,
) -> W:
    """
    Verbose version that requires widget_options explicitly.
    Adds 'form_field_name' as a Qt property.
    """

    def factory() -> W:
        widget = _create_widget(widget_class, widget_options, *args, **kwargs)
        if isinstance(widget, QWidget):
            widget.setProperty("form_field_name", form_field_name)
        return widget

    return field(default_factory=factory)


def make_form_row[W](
    form_field_name: str,
    widget_class: type[W],
    *args: Any,
    **kwargs: Any,
) -> W:
    """
    Concise version like `make()`: no widget_options required.
    Adds 'form_field_name' to any QWidget created.
    """

    def factory() -> W:
        widget = widget_class(*args, **kwargs)
        if isinstance(widget, QWidget):
            widget.setProperty("form_field_name", form_field_name)
        return widget

    return field(default_factory=factory)
