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
"""Tests for widget event handlers (onShow, onHide, onResize, onMove, onClose).

These are pseudo-signals that trigger on widget lifecycle events via event filters.
"""

import pytest
from assertpy import assert_that
from PySide6.QtCore import QCoreApplication, QPoint, QSize
from PySide6.QtGui import QCloseEvent, QHideEvent, QMoveEvent, QResizeEvent, QShowEvent
from PySide6.QtWidgets import QLabel, QPushButton

from qtpie import new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


def send_show_event(target: QLabel | QPushButton) -> None:
    """Send a Show event to a widget."""
    event = QShowEvent()
    QCoreApplication.sendEvent(target, event)


def send_hide_event(target: QLabel | QPushButton) -> None:
    """Send a Hide event to a widget."""
    event = QHideEvent()
    QCoreApplication.sendEvent(target, event)


def send_resize_event(target: QLabel | QPushButton, old_size: QSize | None = None, new_size: QSize | None = None) -> None:
    """Send a Resize event to a widget."""
    old = old_size or QSize(100, 100)
    new = new_size or QSize(200, 200)
    event = QResizeEvent(new, old)
    QCoreApplication.sendEvent(target, event)


def send_move_event(target: QLabel | QPushButton, old_pos: QPoint | None = None, new_pos: QPoint | None = None) -> None:
    """Send a Move event to a widget."""
    old = old_pos or QPoint(0, 0)
    new = new_pos or QPoint(50, 50)
    event = QMoveEvent(new, old)
    QCoreApplication.sendEvent(target, event)


def send_close_event(target: QLabel | QPushButton) -> None:
    """Send a Close event to a widget."""
    event = QCloseEvent()
    QCoreApplication.sendEvent(target, event)


# =============================================================================
# onShow / onHide Events
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestShowHideEvents:
    """Show and hide event handlers."""

    def test_on_show_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onShow='method_name' calls method when widget is shown."""
        show_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onShow="on_shown")

            def on_shown(self) -> None:
                show_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_show_event(instance.label)

        assert_that(show_count[0]).is_equal_to(1)

    def test_on_hide_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onHide='method_name' calls method when widget is hidden."""
        hide_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onHide="on_hidden")

            def on_hidden(self) -> None:
                hide_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_hide_event(instance.label)

        assert_that(hide_count[0]).is_equal_to(1)

    def test_on_show_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onShow=lambda connects show event to lambda."""
        show_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onShow=lambda: show_count.__setitem__(0, show_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_show_event(instance.label)

        assert_that(show_count[0]).is_equal_to(1)


# =============================================================================
# onResize Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestResizeEvent:
    """Resize event handlers."""

    def test_on_resize_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onResize='method_name' calls method when widget is resized."""
        resize_events = []

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onResize="on_resized")

            def on_resized(self, event: QResizeEvent) -> None:
                resize_events.append((event.size().width(), event.size().height()))

        instance = create_and_track(qt, TestClass, base_class)
        send_resize_event(instance.label, new_size=QSize(300, 400))

        assert_that(resize_events).is_length(1)
        assert_that(resize_events[0]).is_equal_to((300, 400))

    def test_on_resize_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onResize=lambda receives the resize event."""
        resize_count = [0]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onResize=lambda e: resize_count.__setitem__(0, resize_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_resize_event(instance.label)

        assert_that(resize_count[0]).is_equal_to(1)


# =============================================================================
# onMove Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMoveEvent:
    """Move event handlers."""

    def test_on_move_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onMove='method_name' calls method when widget is moved."""
        move_events = []

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onMove="on_moved")

            def on_moved(self, event: QMoveEvent) -> None:
                move_events.append((event.pos().x(), event.pos().y()))

        instance = create_and_track(qt, TestClass, base_class)
        send_move_event(instance.label, new_pos=QPoint(100, 200))

        assert_that(move_events).is_length(1)
        assert_that(move_events[0]).is_equal_to((100, 200))


# =============================================================================
# onClose Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestCloseEvent:
    """Close event handlers."""

    def test_on_close_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onClose='method_name' calls method when widget receives close event."""
        close_called = [False]

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onClose="on_closing")

            def on_closing(self, event: QCloseEvent) -> None:
                close_called[0] = True

        instance = create_and_track(qt, TestClass, base_class)
        send_close_event(instance.label)

        assert_that(close_called[0]).is_true()


# =============================================================================
# Multiple Events on Same Widget
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMultipleEventHandlers:
    """Multiple event handlers on the same widget."""

    def test_multiple_widget_events_on_same_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple widget event handlers can be attached to the same widget."""
        events = []

        @decorator
        class TestClass(base_class):
            label: QLabel = new("Test", onShow="on_show", onHide="on_hide", onResize="on_resize")

            def on_show(self) -> None:
                events.append("show")

            def on_hide(self) -> None:
                events.append("hide")

            def on_resize(self, event: QResizeEvent) -> None:
                events.append("resize")

        instance = create_and_track(qt, TestClass, base_class)

        send_show_event(instance.label)
        send_resize_event(instance.label)
        send_hide_event(instance.label)

        assert_that(events).is_equal_to(["show", "resize", "hide"])
