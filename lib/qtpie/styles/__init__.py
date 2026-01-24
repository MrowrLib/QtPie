"""Stylesheet utilities for QtPie."""

from qtpie.styles.classes import (
    add_class,
    add_classes,
    get_classes,
    get_field_property,
    has_any_class,
    has_class,
    remove_class,
    replace_class,
    set_classes,
    set_field_property,
    toggle_class,
)
from qtpie.styles.color_scheme import (
    ColorScheme,
    apply_deferred_color_scheme,
    enable_dark_mode,
    enable_light_mode,
    get_configured_color_scheme,
    is_dark_mode,
    is_light_mode,
    set_color_scheme,
)
from qtpie.styles.compiler import compile_scss
from qtpie.styles.loader import load_stylesheet
from qtpie.styles.theme_runtime import (
    get_theme,
    get_themes,
    is_dark_theme,
    set_theme,
)
from qtpie.styles.theme_watcher import ThemeWatcher
from qtpie.styles.themes import Theme, ThemeMode, ThemeSet
from qtpie.styles.watcher import (
    QssWatcher,
    ScssWatcher,
    watch_qss,
    watch_scss,
    watch_styles,
)
from qtpie.styles.zoom import (
    clear_scss_variables,
    get_base_font_size,
    get_scss_variables,
    get_zoom,
    register_recompile_callback,
    set_base_font_size,
    set_scss_variable,
    set_scss_variables,
    set_zoom,
)

__all__ = [
    # Class helpers
    "add_class",
    "add_classes",
    "get_classes",
    "get_field_property",
    "has_any_class",
    "has_class",
    "remove_class",
    "replace_class",
    "set_classes",
    "set_field_property",
    "toggle_class",
    # Color scheme
    "ColorScheme",
    "apply_deferred_color_scheme",
    "enable_dark_mode",
    "enable_light_mode",
    "get_configured_color_scheme",
    "is_dark_mode",
    "is_light_mode",
    "set_color_scheme",
    # Compiler
    "compile_scss",
    # Loader
    "load_stylesheet",
    # Themes
    "Theme",
    "ThemeMode",
    "ThemeSet",
    "ThemeWatcher",
    "get_theme",
    "get_themes",
    "is_dark_theme",
    "set_theme",
    # Watchers
    "QssWatcher",
    "ScssWatcher",
    "watch_qss",
    "watch_scss",
    "watch_styles",
    # Zoom
    "clear_scss_variables",
    "get_base_font_size",
    "get_scss_variables",
    "get_zoom",
    "register_recompile_callback",
    "set_base_font_size",
    "set_scss_variable",
    "set_scss_variables",
    "set_zoom",
]
