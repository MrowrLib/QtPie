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
from .event import Event
from .layout import Stretch
from .menu import Menu, MenuConfig, Section, Separator, menu
from .messagebox import MessageBoxResult, confirm, messagebox
from .new import new, none
from .new_field import ColumnResizeMode
from .new_fields import new_fields
from .ref import Ref, ref
from .set_widget_repeater import SetWidgetRepeater
from .setting import Setting
from .slot import slot
from .state import Service, State, service, state
from .styles import (
    ColorScheme,
    enable_dark_mode,
    enable_light_mode,
    get_theme,
    get_themes,
    get_zoom,
    is_dark_mode,
    is_dark_theme,
    is_light_mode,
    set_color_scheme,
    set_theme,
    set_zoom,
)
from .translations import Translatable, set_language, t
from .variable import RecordVariable, Var, Variable
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
    "ColumnResizeMode",
    "Dialog",
    "Event",
    "DialogButton",
    "DialogButtons",
    "DialogConfig",
    "DialogResult",
    "Dock",
    "EmbedConfig",
    "MessageBoxResult",
    "Stretch",
    "app",
    "buttons",
    "confirm",
    "create_instance",
    "dialog",
    "DictWidgetRepeater",
    "DockWidgetRepeater",
    "embed",
    "Menu",
    "MenuConfig",
    "messagebox",
    "RecordVariable",
    "Ref",
    "Section",
    "Separator",
    "Service",
    "State",
    "service",
    "state",
    "SetWidgetRepeater",
    "Setting",
    "Translatable",
    "Var",
    "Variable",
    "Widget",
    "WidgetBase",
    "WidgetRepeater",
    "bind",
    "enable_dark_mode",
    "enable_light_mode",
    "entrypoint",
    "is_dark_mode",
    "is_light_mode",
    "get_theme",
    "get_themes",
    "get_zoom",
    "is_dark_theme",
    "menu",
    "new",
    "new_fields",
    "none",
    "ref",
    "register_binding",
    "run_app",
    "set_color_scheme",
    "set_language",
    "set_theme",
    "set_zoom",
    "slot",
    "t",
    "widget",
    "Window",
    "window",
]
