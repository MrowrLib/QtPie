"""QtPie - Declarative UI framework for Qt."""

from .app import App, run_app
from .bindings import bind, register_binding
from .dict_widget_repeater import DictWidgetRepeater
from .entrypoint import entrypoint
from .menu import Menu, MenuConfig, Section, Separator, menu
from .new import new
from .new_fields import new_fields
from .slot import slot
from .styles import ColorScheme, enable_dark_mode, enable_light_mode, set_color_scheme
from .translations import Translatable, set_language, t
from .variable import RecordVariable, Variable
from .widget import Widget, widget
from .widget_base import WidgetBase
from .widget_repeater import WidgetRepeater
from .window import Window, window

__all__ = [
    "App",
    "ColorScheme",
    "DictWidgetRepeater",
    "Menu",
    "MenuConfig",
    "RecordVariable",
    "Section",
    "Separator",
    "Translatable",
    "Variable",
    "Widget",
    "WidgetBase",
    "WidgetRepeater",
    "bind",
    "enable_dark_mode",
    "enable_light_mode",
    "entrypoint",
    "menu",
    "new",
    "new_fields",
    "register_binding",
    "run_app",
    "set_color_scheme",
    "set_language",
    "slot",
    "t",
    "widget",
    "Window",
    "window",
]
