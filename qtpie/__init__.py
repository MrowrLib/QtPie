"""QtPie - A tasty way to build Qt apps."""

from qtpie.bindings import bind, register_binding
from qtpie.decorators.action import action
from qtpie.decorators.menu import menu
from qtpie.decorators.widget import widget
from qtpie.decorators.window import window
from qtpie.factories.make import make, make_later
from qtpie.model_widget import ModelWidget

__all__ = [
    "ModelWidget",
    "action",
    "bind",
    "make",
    "make_later",
    "menu",
    "register_binding",
    "widget",
    "window",
]
