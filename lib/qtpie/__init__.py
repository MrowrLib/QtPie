"""QtPie - Declarative UI framework for Qt."""

from .action import action
from .app import App, run_app
from .bindings import bind, register_binding
from .dict_widget_repeater import DictWidgetRepeater
from .entrypoint import entrypoint
from .menu import menu
from .new import new
from .new_fields import new_fields
from .separator import separator
from .slot import slot
from .styles import ColorScheme, enable_dark_mode, enable_light_mode, set_color_scheme
from .variable import RecordVariable, Variable
from .widget import Widget, widget
from .widget_base import WidgetBase
from .widget_repeater import WidgetRepeater
from .window import Window, window

__all__ = [
    "App",
    "ColorScheme",
    "DictWidgetRepeater",
    "RecordVariable",
    "Variable",
    "Widget",
    "WidgetBase",
    "WidgetRepeater",
    "action",
    "bind",
    "enable_dark_mode",
    "enable_light_mode",
    "entrypoint",
    "menu",
    "new",
    "new_fields",
    "register_binding",
    "run_app",
    "separator",
    "set_color_scheme",
    "slot",
    "widget",
    "Window",
    "window",
]
