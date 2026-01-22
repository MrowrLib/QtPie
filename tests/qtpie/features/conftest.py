# pyright: reportPrivateUsage=false
# pyright: reportUnusedImport=false
"""Shared fixtures for feature tests."""

from typing import Any

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QLabel

from qtpie import AppBase, Dialog, Menu, State, Widget, WidgetBase, Window, app, dialog, menu, state, widget, window
from qtpie.testing import QtDriver


# WidgetBase test class - combines QLabel with WidgetBase mixin
class WidgetBaseLabel[T = None](QLabel, WidgetBase[T]):
    """Test class for WidgetBase - a QLabel with QtPie features."""

    pass


# AppBase test class - combines QObject with AppBase for signal support
# AppBase alone doesn't inherit from QObject, so Signals don't work
class AppBaseWithSignals[T = None](QObject, AppBase[T]):
    """Test class for AppBase with QObject for signal support."""

    pass


# Class types that support QWidget children and layouts (Widget, Window, Dialog, App)
WIDGET_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Dialog, dialog, id="Dialog"),
    pytest.param(AppBase, app, id="App"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# All class types including Menu (for features that work on all)
ALL_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Dialog, dialog, id="Dialog"),
    pytest.param(Menu, menu, id="Menu"),
    pytest.param(AppBase, app, id="App"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# Widget only - for features that only work on basic Widget (not Window/App/Dialog)
# Used for layout tests where Window has central_widget and App doesn't have layout()
WIDGET_ONLY = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# Widget, Window, and Dialog - for features that work on QWidget-based classes
# Used for name=/classes= tests since App is not a QWidget
QWIDGET_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Dialog, dialog, id="Dialog"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]

# Window and App only - for features that require QMainWindow (docks, menus, etc.)
# App internally creates a Window, so docks work on both
# Note: Dialog is NOT included here - it's QDialog, not QMainWindow
WINDOW_CLASS_TYPES = [
    pytest.param(Window, window, id="Window"),
    pytest.param(AppBase, app, id="App"),
]

# Classes that support Widget[T] record binding (excludes WidgetBaseLabel which is a mixin)
RECORD_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Dialog, dialog, id="Dialog"),
    pytest.param(AppBase, app, id="App"),
]

# All class types including State - for features that work on all Variable hosts
# State is not a QWidget, so it doesn't need tracking
ALL_CLASS_TYPES_WITH_STATE = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Dialog, dialog, id="Dialog"),
    pytest.param(Menu, menu, id="Menu"),
    pytest.param(AppBase, app, id="App"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
    pytest.param(State, state, id="State"),
]

# Classes that support Qt Signals (QObject subclasses)
# AppBase alone doesn't inherit from QObject, so we use AppBaseWithSignals
# State creates pure Python Events, not Qt Signals, so it's excluded
SIGNAL_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Dialog, dialog, id="Dialog"),
    pytest.param(Menu, menu, id="Menu"),
    pytest.param(AppBaseWithSignals, app, id="App"),
    pytest.param(WidgetBaseLabel, widget, id="WidgetBase"),
]


def create_and_track(
    qt: QtDriver,
    decorated_class: type,
    base_class: type,
    **kwargs: Any,
) -> Any:
    """Create an instance and track it appropriately based on type.

    - Widget, Window, Menu, WidgetBaseLabel: QWidget-based, tracked with qt.track()
    - AppBase: Not a QWidget, but if it has a window, track that
    - Service: Not a QWidget at all, just instantiated directly

    Args:
        qt: QtDriver instance for tracking
        decorated_class: The decorated class to instantiate
        base_class: The base class (used to determine tracking behavior)
        **kwargs: Additional kwargs passed to the constructor (e.g., Variable values)
    """
    instance = decorated_class(**kwargs)

    if base_class is State:
        # State is not a QWidget, just return the instance
        pass
    elif base_class is AppBase or base_class is AppBaseWithSignals:
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
