"""QtPie - A tasty way to build Qt apps."""

from qtpie.bindings import bind, register_binding
from qtpie.decorators.action import action
from qtpie.decorators.menu import menu
from qtpie.decorators.widget import widget
from qtpie.decorators.window import window
from qtpie.factories.make import make, make_later
from qtpie.factories.stretch import stretch
from qtpie.widget_base import ModelWidget, Widget

__all__ = [
    "ModelWidget",  # Backwards compatibility alias
    "Widget",
    "action",
    "bind",
    "make",
    "make_later",
    "menu",
    "register_binding",
    "stretch",
    "widget",
    "window",
]
