# pyright: reportPrivateUsage=false
# pyright: reportUnusedImport=false
"""Shared fixtures for feature tests."""

from typing import Any

import pytest
from PySide6.QtWidgets import QLabel

from qtpie import AppBase, Menu, Widget, WidgetBase, Window, app, menu, widget, window
from qtpie.testing import QtDriver


# WidgetBase test class - combines QLabel with WidgetBase mixin
class WidgetBaseLabel[T = None](QLabel, WidgetBase[T]):
    """Test class for WidgetBase - a QLabel with QtPie features."""

    pass


# Class types that support QWidget children and layouts (Widget, Window, App)
WIDGET_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(AppBase, app, id="App"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# All class types including Menu (for features that work on all)
ALL_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Menu, menu, id="Menu"),
    pytest.param(AppBase, app, id="App"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# Widget only - for features that only work on basic Widget (not Window/App)
# Used for layout tests where Window has central_widget and App doesn't have layout()
WIDGET_ONLY = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# Widget and Window only - for features that work on QWidget-based classes
# Used for name=/classes= tests since App is not a QWidget
QWIDGET_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# Window and App only - for features that require QMainWindow (docks, menus, etc.)
# App internally creates a Window, so docks work on both
WINDOW_CLASS_TYPES = [
    pytest.param(Window, window, id="Window"),
    pytest.param(AppBase, app, id="App"),
]


def create_and_track(
    qt: QtDriver,
    decorated_class: type,
    base_class: type,
) -> Any:
    """Create an instance and track it appropriately based on type.

    - Widget, Window, Menu, WidgetBaseLabel: QWidget-based, tracked with qt.track()
    - AppBase: Not a QWidget, just instantiated directly
    """
    instance = decorated_class()

    if base_class is AppBase:
        # AppBase is not a QWidget, but if it has a window, track that
        if hasattr(instance, "window") and instance.window is not None:
            qt.track(instance.window)
    else:
        # Widget, Window, Menu, WidgetBaseLabel are all QWidgets
        qt.track(instance)

    return instance


def get_main_window(instance: Any, base_class: type) -> Window:
    """Get the QMainWindow from an instance.

    - Window: returns the instance itself
    - AppBase: returns instance.window
    """
    if base_class is AppBase:
        return instance.window  # type: ignore[return-value]
    return instance  # type: ignore[return-value]
