# pyright: reportPrivateUsage=false
# pyright: reportUnusedImport=false
"""Shared fixtures for feature tests."""

from typing import Any

import pytest

from qtpie import AppBase, Menu, Widget, Window, app, menu, widget, window
from qtpie.testing import QtDriver

# Class types that support QWidget children and layouts (Widget, Window, App)
WIDGET_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(AppBase, app, id="App"),
]

# All class types including Menu (for features that work on all)
ALL_CLASS_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Menu, menu, id="Menu"),
    pytest.param(AppBase, app, id="App"),
]


def create_and_track(
    qt: QtDriver,
    decorated_class: type,
    base_class: type,
) -> Any:
    """Create an instance and track it appropriately based on type.

    - Widget, Window, Menu: QWidget-based, tracked with qt.track()
    - AppBase: Not a QWidget, just instantiated directly
    """
    instance = decorated_class()

    if base_class is AppBase:
        # AppBase is not a QWidget, but if it has a window, track that
        if hasattr(instance, "window") and instance.window is not None:
            qt.track(instance.window)
    else:
        # Widget, Window, Menu are all QWidgets
        qt.track(instance)

    return instance
