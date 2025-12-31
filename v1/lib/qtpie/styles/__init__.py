"""Stylesheet utilities for QtPie."""

from qtpie.styles.classes import (
    add_class,
    add_classes,
    get_classes,
    has_any_class,
    has_class,
    remove_class,
    replace_class,
    set_classes,
    toggle_class,
)
from qtpie.styles.color_scheme import (
    ColorScheme,
    enable_dark_mode,
    enable_light_mode,
    set_color_scheme,
)
from qtpie.styles.compiler import compile_scss
from qtpie.styles.loader import load_stylesheet
from qtpie.styles.watcher import (
    QssWatcher,
    ScssWatcher,
    watch_qss,
    watch_scss,
    watch_styles,
)

__all__ = [
    # Class helpers
    "add_class",
    "add_classes",
    "get_classes",
    "has_any_class",
    "has_class",
    "remove_class",
    "replace_class",
    "set_classes",
    "toggle_class",
    # Color scheme
    "ColorScheme",
    "enable_dark_mode",
    "enable_light_mode",
    "set_color_scheme",
    # Compiler
    "compile_scss",
    # Loader
    "load_stylesheet",
    # Watchers
    "QssWatcher",
    "ScssWatcher",
    "watch_qss",
    "watch_scss",
    "watch_styles",
]
