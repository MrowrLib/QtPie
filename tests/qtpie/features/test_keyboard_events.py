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
"""Tests for keyboard event handlers (onKeyPress, onKeyRelease, onEnterKey, onDeleteKey).

These are pseudo-signals that trigger on keyboard events via event filters.
"""

import pytest
from assertpy import assert_that
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLabel, QLineEdit

from qtpie import new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


def send_key_press(target: QLabel | QLineEdit, key: Qt.Key, modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
    """Send a KeyPress event to a widget."""
    event = QKeyEvent(QEvent.Type.KeyPress, key, modifiers)
    QCoreApplication.sendEvent(target, event)


def send_key_release(target: QLabel | QLineEdit, key: Qt.Key, modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
    """Send a KeyRelease event to a widget."""
    event = QKeyEvent(QEvent.Type.KeyRelease, key, modifiers)
    QCoreApplication.sendEvent(target, event)


# =============================================================================
# onKeyPress Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestKeyPressEvent:
    """Key press event handlers."""

    def test_on_key_press_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onKeyPress='method_name' calls method when key is pressed."""
        pressed_keys = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress="on_key")

            def on_key(self, event: QKeyEvent) -> None:
                pressed_keys.append(event.key())

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_A)

        assert_that(pressed_keys).is_length(1)
        assert_that(pressed_keys[0]).is_equal_to(Qt.Key.Key_A)

    def test_on_key_press_with_modifiers(self, base_class, decorator, qt: QtDriver) -> None:
        """onKeyPress receives modifier keys."""
        key_events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress="on_key")

            def on_key(self, event: QKeyEvent) -> None:
                key_events.append((event.key(), event.modifiers()))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

        assert_that(key_events).is_length(1)
        assert_that(key_events[0][0]).is_equal_to(Qt.Key.Key_S)
        assert_that(key_events[0][1]).is_equal_to(Qt.KeyboardModifier.ControlModifier)

    def test_on_key_press_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onKeyPress=lambda receives the key event."""
        press_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress=lambda e: press_count.__setitem__(0, press_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(press_count[0]).is_equal_to(1)


# =============================================================================
# onKeyRelease Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestKeyReleaseEvent:
    """Key release event handlers."""

    def test_on_key_release_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onKeyRelease='method_name' calls method when key is released."""
        released_keys = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyRelease="on_key")

            def on_key(self, event: QKeyEvent) -> None:
                released_keys.append(event.key())

        instance = create_and_track(qt, TestClass, base_class)
        send_key_release(instance.line_edit, Qt.Key.Key_Escape)

        assert_that(released_keys).is_length(1)
        assert_that(released_keys[0]).is_equal_to(Qt.Key.Key_Escape)


# =============================================================================
# Both KeyPress and KeyRelease
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestKeyPressAndRelease:
    """Combined key press and release handlers."""

    def test_both_key_press_and_release(self, base_class, decorator, qt: QtDriver) -> None:
        """Both onKeyPress and onKeyRelease can be set on the same widget."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress="on_press", onKeyRelease="on_release")

            def on_press(self, event: QKeyEvent) -> None:
                events.append(("press", event.key()))

            def on_release(self, event: QKeyEvent) -> None:
                events.append(("release", event.key()))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Space)
        send_key_release(instance.line_edit, Qt.Key.Key_Space)

        assert_that(events).is_length(2)
        assert_that(events[0]).is_equal_to(("press", Qt.Key.Key_Space))
        assert_that(events[1]).is_equal_to(("release", Qt.Key.Key_Space))


# =============================================================================
# onEnterKey Event (Key_Return and Key_Enter)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestEnterKeyEvent:
    """Enter key shortcut event handlers."""

    def test_on_enter_key_calls_method_on_return(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey='method_name' calls method when Return key is pressed."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self) -> None:
                enter_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(enter_count[0]).is_equal_to(1)

    def test_on_enter_key_calls_method_on_enter(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey='method_name' calls method when Enter key (numpad) is pressed."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self) -> None:
                enter_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Enter)

        assert_that(enter_count[0]).is_equal_to(1)

    def test_on_enter_key_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey=lambda works without event parameter."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey=lambda: enter_count.__setitem__(0, enter_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(enter_count[0]).is_equal_to(1)

    def test_on_enter_key_does_not_fire_on_other_keys(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey does not fire when other keys are pressed."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self) -> None:
                enter_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_A)
        send_key_press(instance.line_edit, Qt.Key.Key_Space)
        send_key_press(instance.line_edit, Qt.Key.Key_Escape)

        assert_that(enter_count[0]).is_equal_to(0)


# =============================================================================
# onDeleteKey Event
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDeleteKeyEvent:
    """Delete key shortcut event handlers."""

    def test_on_delete_key_calls_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onDeleteKey='method_name' calls method when Delete key is pressed."""
        delete_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onDeleteKey="on_delete")

            def on_delete(self) -> None:
                delete_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Delete)

        assert_that(delete_count[0]).is_equal_to(1)

    def test_on_delete_key_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onDeleteKey=lambda works without event parameter."""
        delete_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onDeleteKey=lambda: delete_count.__setitem__(0, delete_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Delete)

        assert_that(delete_count[0]).is_equal_to(1)

    def test_on_delete_key_does_not_fire_on_other_keys(self, base_class, decorator, qt: QtDriver) -> None:
        """onDeleteKey does not fire when other keys are pressed."""
        delete_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onDeleteKey="on_delete")

            def on_delete(self) -> None:
                delete_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Backspace)
        send_key_press(instance.line_edit, Qt.Key.Key_A)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(delete_count[0]).is_equal_to(0)


# =============================================================================
# Combined Key Shortcuts
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestCombinedKeyShortcuts:
    """Combined key shortcut handlers."""

    def test_enter_and_delete_on_same_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Both onEnterKey and onDeleteKey can be set on the same widget."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter", onDeleteKey="on_delete")

            def on_enter(self) -> None:
                events.append("enter")

            def on_delete(self) -> None:
                events.append("delete")

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)
        send_key_press(instance.line_edit, Qt.Key.Key_Delete)

        assert_that(events).is_length(2)
        assert_that(events[0]).is_equal_to("enter")
        assert_that(events[1]).is_equal_to("delete")

    def test_key_shortcuts_with_key_press(self, base_class, decorator, qt: QtDriver) -> None:
        """Key shortcuts work alongside onKeyPress handler."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress="on_key", onEnterKey="on_enter")

            def on_key(self, event: QKeyEvent) -> None:
                events.append(("keypress", event.key()))

            def on_enter(self) -> None:
                events.append(("enter", None))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        # Both handlers should fire for Enter key
        assert_that(events).is_length(2)
        assert_that(events[0]).is_equal_to(("keypress", Qt.Key.Key_Return))
        assert_that(events[1]).is_equal_to(("enter", None))


# =============================================================================
# Event Consumption (return True to stop propagation)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestEventConsumption:
    """Event consumption - handlers returning True stop propagation."""

    def test_on_enter_key_return_true_consumes_event(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey handler returning True consumes the event."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self) -> bool:
                enter_count[0] += 1
                return True  # Consume the event

        instance = create_and_track(qt, TestClass, base_class)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.sendEvent(instance.line_edit, event)

        assert_that(enter_count[0]).is_equal_to(1)
        # Event should be accepted (consumed)
        assert_that(event.isAccepted()).is_true()

    def test_on_enter_key_return_none_does_not_consume(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey handler returning None does not consume the event."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self) -> None:
                enter_count[0] += 1
                # Return None (implicit) - don't consume

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(enter_count[0]).is_equal_to(1)

    def test_on_enter_key_return_false_does_not_consume(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey handler returning False does not consume the event."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self) -> bool:
                enter_count[0] += 1
                return False  # Explicitly don't consume

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(enter_count[0]).is_equal_to(1)

    def test_on_key_press_return_true_consumes_event(self, base_class, decorator, qt: QtDriver) -> None:
        """onKeyPress handler returning True consumes the event."""
        press_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress="on_key")

            def on_key(self, event: QKeyEvent) -> bool:
                press_count[0] += 1
                return True  # Consume

        instance = create_and_track(qt, TestClass, base_class)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.sendEvent(instance.line_edit, event)

        assert_that(press_count[0]).is_equal_to(1)
        assert_that(event.isAccepted()).is_true()

    def test_on_key_press_consume_prevents_enter_key_handler(self, base_class, decorator, qt: QtDriver) -> None:
        """When onKeyPress consumes the event, onEnterKey doesn't fire."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress="on_key", onEnterKey="on_enter")

            def on_key(self, event: QKeyEvent) -> bool:
                events.append("keypress")
                return True  # Consume - should prevent onEnterKey

            def on_enter(self) -> None:
                events.append("enter")

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        # Only keypress should fire, enter should be blocked
        assert_that(events).is_length(1)
        assert_that(events[0]).is_equal_to("keypress")

    def test_on_key_press_not_consume_allows_enter_key_handler(self, base_class, decorator, qt: QtDriver) -> None:
        """When onKeyPress doesn't consume, onEnterKey also fires."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onKeyPress="on_key", onEnterKey="on_enter")

            def on_key(self, event: QKeyEvent) -> bool:
                events.append("keypress")
                return False  # Don't consume

            def on_enter(self) -> None:
                events.append("enter")

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        # Both should fire
        assert_that(events).is_length(2)
        assert_that(events[0]).is_equal_to("keypress")
        assert_that(events[1]).is_equal_to("enter")

    def test_on_delete_key_return_true_consumes(self, base_class, decorator, qt: QtDriver) -> None:
        """onDeleteKey handler returning True consumes the event."""
        delete_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onDeleteKey="on_delete")

            def on_delete(self) -> bool:
                delete_count[0] += 1
                return True

        instance = create_and_track(qt, TestClass, base_class)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.sendEvent(instance.line_edit, event)

        assert_that(delete_count[0]).is_equal_to(1)
        assert_that(event.isAccepted()).is_true()


# =============================================================================
# Optional Event Parameter
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestOptionalEventParameter:
    """Handlers can optionally accept the event as a parameter."""

    def test_on_enter_key_with_event_parameter(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey handler can accept the event parameter."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self, event: QKeyEvent) -> None:
                events.append(event.key())

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(events).is_length(1)
        assert_that(events[0]).is_equal_to(Qt.Key.Key_Return)

    def test_on_enter_key_without_event_parameter(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey handler works without event parameter."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self) -> None:
                enter_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(enter_count[0]).is_equal_to(1)

    def test_on_delete_key_with_event_parameter(self, base_class, decorator, qt: QtDriver) -> None:
        """onDeleteKey handler can accept the event parameter."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onDeleteKey="on_delete")

            def on_delete(self, event: QKeyEvent) -> None:
                events.append(event.key())

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Delete)

        assert_that(events).is_length(1)
        assert_that(events[0]).is_equal_to(Qt.Key.Key_Delete)

    def test_on_enter_key_with_event_and_return_true(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey handler can accept event AND return True to consume."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey="on_enter")

            def on_enter(self, event: QKeyEvent) -> bool:
                events.append(("enter", event.modifiers()))
                return True  # Consume

        instance = create_and_track(qt, TestClass, base_class)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
        QCoreApplication.sendEvent(instance.line_edit, event)

        assert_that(events).is_length(1)
        assert_that(events[0][0]).is_equal_to("enter")
        assert_that(events[0][1]).is_equal_to(Qt.KeyboardModifier.ShiftModifier)
        assert_that(event.isAccepted()).is_true()

    def test_on_enter_key_lambda_with_event(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey lambda can accept the event parameter."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey=lambda e: events.append(e.key()))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Enter)

        assert_that(events).is_length(1)
        assert_that(events[0]).is_equal_to(Qt.Key.Key_Enter)

    def test_on_enter_key_lambda_without_event(self, base_class, decorator, qt: QtDriver) -> None:
        """onEnterKey lambda works without event parameter."""
        enter_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onEnterKey=lambda: enter_count.__setitem__(0, enter_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_key_press(instance.line_edit, Qt.Key.Key_Return)

        assert_that(enter_count[0]).is_equal_to(1)
