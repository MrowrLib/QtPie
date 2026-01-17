"""QtPie - Declarative UI framework for Qt."""

from . import debug as _debug  # noqa: F401 # pyright: ignore[reportUnusedImport] - import for side effect
from .app import App, AppBase, AppConfig, app, run_app
from .bindings import bind, register_binding
from .create import create_instance
from .dialog import ButtonInfo, Dialog, DialogButton, DialogButtons, DialogConfig, DialogResult, buttons, dialog
from .dict_widget_repeater import DictWidgetRepeater
from .dock import Dock
from .dock_widget_repeater import DockWidgetRepeater
from .embed import EmbedConfig, embed
from .entrypoint import entrypoint
from .layout import Stretch
from .menu import Menu, MenuConfig, Section, Separator, menu
from .new import new, none
from .new_fields import new_fields
from .ref import Ref, ref
from .set_widget_repeater import SetWidgetRepeater
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
    "AppBase",
    "AppConfig",
    "ButtonInfo",
    "ColorScheme",
    "Dialog",
    "DialogButton",
    "DialogButtons",
    "DialogConfig",
    "DialogResult",
    "Dock",
    "EmbedConfig",
    "Stretch",
    "app",
    "buttons",
    "create_instance",
    "dialog",
    "DictWidgetRepeater",
    "DockWidgetRepeater",
    "embed",
    "Menu",
    "MenuConfig",
    "RecordVariable",
    "Ref",
    "Section",
    "Separator",
    "SetWidgetRepeater",
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
    "none",
    "ref",
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
