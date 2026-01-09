"""QtPie - Declarative UI framework for Qt."""

from .action import action
from .app import App, run_app
from .bindings import bind, register_binding
from .dict_widget_repeater import DictWidgetRepeater
from .entrypoint import entrypoint
from .menu import menu
from .new import new
from .new_fields import new_fields
from .newmenu import Menu, MenuConfig, Section, Separator, newmenu
from .separator import separator
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
    "action",
    "bind",
    "enable_dark_mode",
    "enable_light_mode",
    "entrypoint",
    "menu",
    "new",
    "new_fields",
    "newmenu",
    "register_binding",
    "run_app",
    "separator",
    "set_color_scheme",
    "set_language",
    "slot",
    "t",
    "widget",
    "Window",
    "window",
]
