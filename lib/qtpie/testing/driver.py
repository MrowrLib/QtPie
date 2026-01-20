"""QtDriver - A strongly-typed, modern wrapper around pytest-qt."""

from typing import Any

from pytestqt.qtbot import QtBot
from qtpy.QtCore import QElapsedTimer, Qt
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QApplication, QWidget

from qtpie.variable import Variable


class QtDriver:
    """
    A strongly-typed test driver for Qt applications.

    Wraps pytest-qt's QtBot with a cleaner, fully-typed API.
    """

    def __init__(self, qtbot: QtBot) -> None:
        self._qtbot = qtbot

    def track[W: QWidget](self, widget: W) -> W:
        """
        Track a widget for automatic cleanup after the test.

        Args:
            widget: The widget to track.

        Returns:
            The same widget, for chaining.
        """
        self._qtbot.addWidget(widget)
        return widget

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

    def process_events(self) -> None:
        """
        Process pending Qt events.

        Useful for tests that need to wait for Qt signals to be processed.
        """
        app = QApplication.instance()
        if app is not None:
            app.processEvents()

    def wait_for_change(
        self,
        variable: Variable[Any],
        *,
        timeout_ms: int = 5000,
    ) -> bool:
        """
        Wait for a Variable's value to change.

        Processes Qt events (including qasync async tasks) while waiting for
        the Variable's on_change callback to fire. Useful for testing async
        operations that update Variables.

        Args:
            variable: The Variable to wait on.
            timeout_ms: Maximum time to wait in milliseconds (default: 5000).

        Returns:
            True if the Variable changed, False if timeout was reached.

        Example:
            request_widget.on_send_request.emit(request)
            assert qt.wait_for_change(request_widget.response)
            assert request_widget.response.value is not None
        """
        changed = False

        def on_changed(*_: Any) -> None:
            nonlocal changed
            changed = True

        variable.on_change(on_changed)

        timer = QElapsedTimer()
        timer.start()

        # Use processEvents() to drive both Qt events and qasync tasks
        # This is the same pattern qasync uses in asyncClose
        app = QApplication.instance()
        while not changed and timer.elapsed() < timeout_ms:
            if app is not None:
                app.processEvents()

        return changed
