"""QtPie - A tasty way to build Qt apps."""

from qtpie.app import App, run_app
from qtpie.bindings import bind, register_binding
from qtpie.decorators.action import action
from qtpie.decorators.entry_point import entry_point
from qtpie.decorators.menu import menu
from qtpie.decorators.widget import widget
from qtpie.decorators.window import window
from qtpie.factories.make import make, make_later
from qtpie.factories.separator import separator
from qtpie.factories.spacer import spacer
from qtpie.styles import (
    ColorScheme,
    enable_dark_mode,
    enable_light_mode,
    set_color_scheme,
)
from qtpie.widget_base import ModelWidget, Widget

__all__ = [
    "App",
    "ColorScheme",
    "ModelWidget",  # Backwards compatibility alias
    "Widget",
    "action",
    "bind",
    "enable_dark_mode",
    "enable_light_mode",
    "entry_point",
    "make",
    "make_later",
    "menu",
    "register_binding",
    "run_app",
    "separator",
    "set_color_scheme",
    "spacer",
    "widget",
    "window",
]
