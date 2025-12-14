from dataclasses import field
from typing import Any, Callable, TypeVar, cast

from PySide6.QtWidgets import QWidget

from qtpie.styles import QtStyleClass

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
    **kwargs: Any,
) -> W:
    factory_fn: Callable[[], W] = lambda: _create_widget(widget_class, widget_options, *args, **kwargs)
    return field(default_factory=factory_fn)


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
