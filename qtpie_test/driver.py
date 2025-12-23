"""QtDriver - A strongly-typed, modern wrapper around pytest-qt."""

from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QWidget


class QtDriver:
    """
    A strongly-typed test driver for Qt applications.

    Wraps pytest-qt's QtBot with a cleaner, fully-typed API.
    """

    def __init__(self, qtbot: QtBot) -> None:
        self._qtbot = qtbot

    def track(self, *widgets: QWidget) -> None:
        """
        Track widgets for automatic cleanup after the test.

        Args:
            *widgets: One or more widgets to track.
        """
        for widget in widgets:
            self._qtbot.addWidget(widget)

    def click(
        self,
        widget: QWidget,
        *,
        button: Qt.MouseButton = Qt.MouseButton.LeftButton,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
    ) -> None:
        """
        Click on a widget.

        Args:
            widget: The widget to click.
            button: Mouse button to use (default: left).
            modifiers: Keyboard modifiers held during click (default: none).
        """
        QTest.mouseClick(widget, button, modifiers)

    def double_click(
        self,
        widget: QWidget,
        *,
        button: Qt.MouseButton = Qt.MouseButton.LeftButton,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
    ) -> None:
        """
        Double-click on a widget.

        Args:
            widget: The widget to double-click.
            button: Mouse button to use (default: left).
            modifiers: Keyboard modifiers held during click (default: none).
        """
        QTest.mouseDClick(widget, button, modifiers)
