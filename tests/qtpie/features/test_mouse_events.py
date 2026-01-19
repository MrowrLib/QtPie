# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportCallIssue=false
# pyright: reportArgumentType=false
# pyright: reportUnknownVariableType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownLambdaType=false
"""Tests for mouse event handlers (onMouseEnter, onMouseLeave, onMousePress, etc.).

These are pseudo-signals that trigger on mouse events via event filters.
"""

import pytest
from assertpy import assert_that
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QEnterEvent, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QLabel, QPushButton

from qtpie import new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


def send_mouse_enter(target: QLabel | QPushButton) -> None:
    """Send a mouse Enter event to a widget."""
    # QEnterEvent requires local position, scene position, and global position
    event = QEnterEvent(QPointF(10, 10), QPointF(10, 10), QPointF(100, 100))
    QCoreApplication.sendEvent(target, event)


def send_mouse_leave(target: QLabel | QPushButton) -> None:
    """Send a mouse Leave event to a widget."""
    event = QEvent(QEvent.Type.Leave)
    QCoreApplication.sendEvent(target, event)


def send_mouse_press(target: QLabel | QPushButton, button: Qt.MouseButton = Qt.MouseButton.LeftButton) -> None:
    """Send a MouseButtonPress event to a widget."""
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(10, 10),  # local pos
        QPointF(100, 100),  # global pos
        button,
        button,
        Qt.KeyboardModifier.NoModifier,
    )
    QCoreApplication.sendEvent(target, event)


def send_mouse_release(target: QLabel | QPushButton, button: Qt.MouseButton = Qt.MouseButton.LeftButton) -> None:
    """Send a MouseButtonRelease event to a widget."""
    event = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(10, 10),
        QPointF(100, 100),
        button,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QCoreApplication.sendEvent(target, event)


def send_mouse_double_click(target: QLabel | QPushButton, button: Qt.MouseButton = Qt.MouseButton.LeftButton) -> None:
    """Send a MouseButtonDblClick event to a widget."""
    event = QMouseEvent(
        QEvent.Type.MouseButtonDblClick,
        QPointF(10, 10),
        QPointF(100, 100),
        button,
        button,
        Qt.KeyboardModifier.NoModifier,
    )
    QCoreApplication.sendEvent(target, event)


def send_mouse_move(target: QLabel | QPushButton, pos: QPointF | None = None) -> None:
    """Send a MouseMove event to a widget."""
    local_pos = pos or QPointF(20, 20)
    event = QMouseEvent(
        QEvent.Type.MouseMove,
        local_pos,
        QPointF(100, 100),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QCoreApplication.sendEvent(target, event)


def send_wheel(target: QLabel | QPushButton, delta: int = 120) -> None:
    """Send a Wheel event to a widget."""
    event = QWheelEvent(
        QPointF(10, 10),  # pos
        QPointF(100, 100),  # globalPos
        QPoint(0, 0),  # pixelDelta
        QPoint(0, delta),  # angleDelta
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,  # inverted
    )
    QCoreApplication.sendEvent(target, event)


# =============================================================================
# onMouseEnter / onMouseLeave Events
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMouseEnterLeaveEvents:
    """Mouse enter and leave event handlers."""

    def test_on_mouse_enter_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onMouseEnter='method_name' calls method when mouse enters widget."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMouseEnter="on_enter")

            def on_enter(self) -> None:
                enter_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_mouse_enter(instance.label)

        assert_that(enter_count[0]).is_equal_to(1)

    def test_on_mouse_leave_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onMouseLeave='method_name' calls method when mouse leaves widget."""
        leave_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMouseLeave="on_leave")

            def on_leave(self) -> None:
                leave_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_mouse_leave(instance.label)

        assert_that(leave_count[0]).is_equal_to(1)

    def test_both_enter_and_leave(self, base_class, decorator, qt: QtDriver) -> None:
        """Both onMouseEnter and onMouseLeave can be set on the same widget."""
        events = []

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMouseEnter="on_enter", onMouseLeave="on_leave")

            def on_enter(self) -> None:
                events.append("enter")

            def on_leave(self) -> None:
                events.append("leave")

        instance = create_and_track(qt, TestClass, base_class)
        send_mouse_enter(instance.label)
        send_mouse_leave(instance.label)

        assert_that(events).is_equal_to(["enter", "leave"])


# =============================================================================
# onMousePress / onMouseRelease Events
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMousePressReleaseEvents:
    """Mouse press and release event handlers."""

    def test_on_mouse_press_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onMousePress='method_name' calls method when mouse button is pressed."""
        press_events = []

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMousePress="on_press")

            def on_press(self, event: QMouseEvent) -> None:
                press_events.append(event.button())

        instance = create_and_track(qt, TestClass, base_class)
        send_mouse_press(instance.label, Qt.MouseButton.LeftButton)

        assert_that(press_events).is_length(1)
        assert_that(press_events[0]).is_equal_to(Qt.MouseButton.LeftButton)

    def test_on_mouse_release_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onMouseRelease='method_name' calls method when mouse button is released."""
        release_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMouseRelease="on_release")

            def on_release(self, event: QMouseEvent) -> None:
                release_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_mouse_release(instance.label)

        assert_that(release_count[0]).is_equal_to(1)

    def test_on_mouse_press_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onMousePress=lambda receives the mouse event."""
        press_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMousePress=lambda e: press_count.__setitem__(0, press_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_mouse_press(instance.label)

        assert_that(press_count[0]).is_equal_to(1)


# =============================================================================
# onMouseDoubleClick Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMouseDoubleClickEvent:
    """Mouse double click event handlers."""

    def test_on_mouse_double_click_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onMouseDoubleClick='method_name' calls method on double click."""
        double_click_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMouseDoubleClick="on_dbl_click")

            def on_dbl_click(self, event: QMouseEvent) -> None:
                double_click_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_mouse_double_click(instance.label)

        assert_that(double_click_count[0]).is_equal_to(1)


# =============================================================================
# onMouseMove Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMouseMoveEvent:
    """Mouse move event handlers."""

    def test_on_mouse_move_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onMouseMove='method_name' calls method when mouse moves.

        Note: Mouse tracking is automatically enabled when onMouseMove is set.
        """
        move_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMouseMove="on_move")

            def on_move(self, event: QMouseEvent) -> None:
                move_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        # Mouse tracking should be auto-enabled when onMouseMove handler is attached
        assert_that(instance.label.hasMouseTracking()).is_true()
        send_mouse_move(instance.label, QPointF(50, 75))

        assert_that(move_count[0]).is_equal_to(1)


# =============================================================================
# onWheel Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestWheelEvent:
    """Mouse wheel event handlers."""

    def test_on_wheel_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onWheel='method_name' calls method when wheel is scrolled."""
        wheel_deltas = []

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onWheel="on_scroll")

            def on_scroll(self, event: QWheelEvent) -> None:
                wheel_deltas.append(event.angleDelta().y())

        instance = create_and_track(qt, TestClass, base_class)
        send_wheel(instance.label, delta=240)

        assert_that(wheel_deltas).is_length(1)
        assert_that(wheel_deltas[0]).is_equal_to(240)


# =============================================================================
# Multiple Mouse Events on Same Widget
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMultipleMouseEvents:
    """Multiple mouse event handlers on the same widget."""

    def test_all_mouse_events_on_same_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """All mouse event handlers can be attached to the same widget."""
        events = []

        @decorator
        class TestClass(base_class):
            label: QLabel = new(
                "Test",
                onMouseEnter="on_enter",
                onMouseLeave="on_leave",
                onMousePress="on_press",
                onMouseRelease="on_release",
            )

            def on_enter(self) -> None:
                events.append("enter")

            def on_leave(self) -> None:
                events.append("leave")

            def on_press(self, event: QMouseEvent) -> None:
                events.append("press")

            def on_release(self, event: QMouseEvent) -> None:
                events.append("release")

        instance = create_and_track(qt, TestClass, base_class)

        send_mouse_enter(instance.label)
        send_mouse_press(instance.label)
        send_mouse_release(instance.label)
        send_mouse_leave(instance.label)

        assert_that(events).is_equal_to(["enter", "press", "release", "leave"])
