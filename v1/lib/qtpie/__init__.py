"""QtPie - A tasty way to build Qt apps."""

from qtpie.app import App, run_app
from qtpie.bindings import bind, register_binding
from qtpie.decorators.action import action
from qtpie.decorators.entrypoint import entrypoint
from qtpie.decorators.menu import menu
from qtpie.decorators.slot import slot
from qtpie.decorators.stylesheet import stylesheet
from qtpie.decorators.widget import widget
from qtpie.decorators.window import window
from qtpie.factories.make import get_app, make, make_later
from qtpie.factories.separator import separator
from qtpie.factories.spacer import spacer
from qtpie.screen import center_on_screen
from qtpie.state import state
from qtpie.styles import (
    ColorScheme,
    enable_dark_mode,
    enable_light_mode,
    set_color_scheme,
)
from qtpie.translations import tr
from qtpie.widget_base import ModelWidget, Widget

__all__ = [
    "App",
    "ColorScheme",
    "ModelWidget",  # Backwards compatibility alias
    "Widget",
    "action",
    "bind",
    "center_on_screen",
    "enable_dark_mode",
    "enable_light_mode",
    "entrypoint",
    "get_app",
    "make",
    "make_later",
    "menu",
    "register_binding",
    "run_app",
    "separator",
    "set_color_scheme",
    "slot",
    "spacer",
    "state",
    "stylesheet",
    "tr",
    "widget",
    "window",
]
