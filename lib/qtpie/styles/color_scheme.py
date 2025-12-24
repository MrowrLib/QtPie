"""Color scheme helpers for Qt applications."""

import os
import sys
from enum import Enum
from typing import cast

from qtpy.QtCore import Qt
from qtpy.QtGui import QGuiApplication
from qtpy.QtWidgets import QApplication


class ColorScheme(Enum):
    """Color scheme options for the application."""

    Dark = "dark"
    Light = "light"


# Stores color scheme when set before app exists (for macOS/Linux)
_deferred_color_scheme: ColorScheme | None = None


def get_configured_color_scheme() -> ColorScheme | None:
    """Get the configured color scheme."""
    return _deferred_color_scheme


def apply_deferred_color_scheme(app: QGuiApplication) -> None:
    """Apply any deferred color scheme that was set before the app existed."""
    global _deferred_color_scheme
    if _deferred_color_scheme is not None:
        qt_scheme = Qt.ColorScheme.Dark if _deferred_color_scheme == ColorScheme.Dark else Qt.ColorScheme.Light
        app.styleHints().setColorScheme(qt_scheme)
        _deferred_color_scheme = None


def set_color_scheme(
    scheme: ColorScheme,
    app: QGuiApplication | None = None,
) -> None:
    """
    Set the application color scheme.

    If an app instance is provided or one exists, uses the Qt 6.8+ runtime API.
    If no app exists yet, stores the preference and applies it when the app is created.

    Args:
        scheme: The color scheme to apply (Dark or Light).
        app: Optional app instance. If None, uses QApplication.instance().
    """
    global _deferred_color_scheme

    if app is None:
        instance = QApplication.instance()
        app = cast(QGuiApplication | None, instance)

    if app is None:
        # No app exists yet - store for later
        _deferred_color_scheme = scheme
        if sys.platform == "win32":
            # darkmode=0 is light, darkmode=2 is dark (Windows only)
            darkmode_value = "2" if scheme == ColorScheme.Dark else "0"
            os.environ["QT_QPA_PLATFORM"] = f"windows:darkmode={darkmode_value}"
    else:
        # App exists - use Qt 6.8+ runtime API
        qt_scheme = Qt.ColorScheme.Dark if scheme == ColorScheme.Dark else Qt.ColorScheme.Light
        app.styleHints().setColorScheme(qt_scheme)


def enable_dark_mode(app: QGuiApplication | None = None) -> None:
    """
    Enable dark mode for the application.

    If an app instance is provided or one exists, uses the Qt 6.8+ runtime API.
    If no app exists yet, sets environment variables for when the app is created.

    Args:
        app: Optional app instance. If None, uses QApplication.instance().
    """
    set_color_scheme(ColorScheme.Dark, app)


def enable_light_mode(app: QGuiApplication | None = None) -> None:
    """
    Enable light mode for the application.

    If an app instance is provided or one exists, uses the Qt 6.8+ runtime API.
    If no app exists yet, sets environment variables for when the app is created.

    Args:
        app: Optional app instance. If None, uses QApplication.instance().
    """
    set_color_scheme(ColorScheme.Light, app)
