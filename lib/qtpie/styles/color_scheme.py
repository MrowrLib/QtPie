"""Color scheme helpers for Qt applications."""

from __future__ import annotations

import os
from enum import Enum
from typing import cast

from qtpy.QtCore import Qt
from qtpy.QtGui import QGuiApplication
from qtpy.QtWidgets import QApplication


class ColorScheme(Enum):
    """Color scheme options for the application."""

    Dark = "dark"
    Light = "light"


def set_color_scheme(
    scheme: ColorScheme,
    app: QGuiApplication | None = None,
) -> None:
    """
    Set the application color scheme.

    If an app instance is provided or one exists, uses the Qt 6.8+ runtime API.
    If no app exists yet, sets environment variables for when the app is created.

    Args:
        scheme: The color scheme to apply (Dark or Light).
        app: Optional app instance. If None, uses QApplication.instance().
    """
    if app is None:
        instance = QApplication.instance()
        app = cast(QGuiApplication | None, instance)

    if app is None:
        # No app exists yet - set env vars for when it's created
        # darkmode=0 is light, darkmode=2 is dark (Windows platform)
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
