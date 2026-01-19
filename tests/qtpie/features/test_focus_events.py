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
"""Tests for onFocus/onBlur event handlers.

These are pseudo-signals that trigger on focus events via event filters.
"""

import pytest
from assertpy import assert_that
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QLineEdit, QPushButton

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


def send_focus_in(widget: QLineEdit | QPushButton) -> None:
    """Send a FocusIn event to a widget."""
    event = QFocusEvent(QEvent.Type.FocusIn)
    QCoreApplication.sendEvent(widget, event)


def send_focus_out(widget: QLineEdit | QPushButton) -> None:
    """Send a FocusOut event to a widget."""
    event = QFocusEvent(QEvent.Type.FocusOut)
    QCoreApplication.sendEvent(widget, event)


# =============================================================================
# Method Name Connection (onFocus="method_name")
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFocusMethodNameConnection:
    """Focus events connected via method name string."""

    def test_on_focus_connects_to_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onFocus='method_name' calls method when widget gains focus."""
        focus_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onFocus="on_focus_in")

            def on_focus_in(self) -> None:
                focus_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_focus_in(instance.line_edit)

        assert_that(focus_count[0]).is_equal_to(1)

    def test_on_blur_connects_to_method(self, base_class, decorator, qt: QtDriver) -> None:
        """onBlur='method_name' calls method when widget loses focus."""
        blur_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onBlur="on_focus_out")

            def on_focus_out(self) -> None:
                blur_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_focus_out(instance.line_edit)

        assert_that(blur_count[0]).is_equal_to(1)

    def test_both_on_focus_and_on_blur(self, base_class, decorator, qt: QtDriver) -> None:
        """Both onFocus and onBlur can be set on the same widget."""
        events = []

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onFocus="on_focus_in", onBlur="on_focus_out")

            def on_focus_in(self) -> None:
                events.append("in")

            def on_focus_out(self) -> None:
                events.append("out")

        instance = create_and_track(qt, TestClass, base_class)
        send_focus_in(instance.line_edit)
        send_focus_out(instance.line_edit)

        assert_that(events).is_equal_to(["in", "out"])


# =============================================================================
# Lambda Connection (onFocus=lambda: ...)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFocusLambdaConnection:
    """Focus events connected via lambda function."""

    def test_on_focus_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onFocus=lambda: ... connects focus event to lambda."""
        focus_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onFocus=lambda: focus_count.__setitem__(0, focus_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_focus_in(instance.line_edit)

        assert_that(focus_count[0]).is_equal_to(1)

    def test_on_blur_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onBlur=lambda: ... connects focus event to lambda."""
        blur_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onBlur=lambda: blur_count.__setitem__(0, blur_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        send_focus_out(instance.line_edit)

        assert_that(blur_count[0]).is_equal_to(1)


# =============================================================================
# Handler Can Access Self
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFocusHandlerAccessesSelf:
    """Focus handler has access to self and can modify widget state."""

    def test_focus_handler_can_access_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Connected method has access to self and Variables."""

        @decorator
        class TestClass(base_class):
            _focused: Variable[bool] = new(False)
            line_edit: QLineEdit = new(onFocus="on_focus_in")

            def on_focus_in(self) -> None:
                self._focused.value = True

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._focused.value).is_false()

        send_focus_in(instance.line_edit)

        assert_that(instance._focused.value).is_true()

    def test_on_blur_can_trigger_action(self, base_class, decorator, qt: QtDriver) -> None:
        """onBlur handler can perform actions like saving."""
        saved_values = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            line_edit: QLineEdit = new(bind="_name", onBlur="on_blur")

            def on_blur(self) -> None:
                saved_values.append(self._name.value)

        instance = create_and_track(qt, TestClass, base_class)
        instance.line_edit.setText("Alice")
        qt.process_events()
        send_focus_out(instance.line_edit)

        assert_that(saved_values).contains("Alice")


# =============================================================================
# Multiple Widgets
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFocusMultipleWidgets:
    """Multiple widgets with focus handlers."""

    def test_different_widgets_different_handlers(self, base_class, decorator, qt: QtDriver) -> None:
        """Each widget connects to its own focus handler."""
        focused = {"a": False, "b": False}

        @decorator
        class TestClass(base_class):
            input_a: QLineEdit = new(onFocus="on_focus_a")
            input_b: QLineEdit = new(onFocus="on_focus_b")

            def on_focus_a(self) -> None:
                focused["a"] = True

            def on_focus_b(self) -> None:
                focused["b"] = True

        instance = create_and_track(qt, TestClass, base_class)
        send_focus_in(instance.input_a)

        assert_that(focused["a"]).is_true()
        assert_that(focused["b"]).is_false()

        send_focus_in(instance.input_b)

        assert_that(focused["b"]).is_true()


# =============================================================================
# Hierarchy Resolution (focus handlers search up parent chain)
# =============================================================================


class TestFocusHierarchyResolution:
    """Focus handlers search up the parent hierarchy."""

    def test_focus_connects_to_parent_method(self, qt: QtDriver) -> None:
        """Focus handler string finds method on parent widget."""
        parent_called = [False]

        @widget
        class Child(Widget):
            line_edit: QLineEdit = new(onFocus="on_parent_focus")

        @widget
        class Parent(Widget):
            child: Child = new()

            def on_parent_focus(self) -> None:
                parent_called[0] = True

        parent = qt.track(Parent())
        send_focus_in(parent.child.line_edit)

        assert_that(parent_called[0]).is_true()

    def test_focus_connects_to_parent_signal(self, qt: QtDriver) -> None:
        """Focus handler can connect to parent's Signal."""
        from PySide6.QtCore import Signal

        parent_signal_emitted = [False]

        @widget
        class Child(Widget):
            line_edit: QLineEdit = new(onFocus="on_focused")

        @widget
        class Parent(Widget):
            on_focused = Signal()
            child: Child = new()

            def __setup__(self) -> None:
                self.on_focused.connect(self._handle_focused)

            def _handle_focused(self) -> None:
                parent_signal_emitted[0] = True

        parent = qt.track(Parent())
        send_focus_in(parent.child.line_edit)

        assert_that(parent_signal_emitted[0]).is_true()


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFocusEdgeCases:
    """Edge cases for focus event handlers."""

    def test_handler_not_called_until_focus(self, base_class, decorator, qt: QtDriver) -> None:
        """Handler is not called during initialization."""
        call_count = [0]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onFocus="on_focus")

            def on_focus(self) -> None:
                call_count[0] += 1

        create_and_track(qt, TestClass, base_class)
        # Widget not focused, handler should not be called
        assert_that(call_count[0]).is_equal_to(0)

    def test_focus_on_button(self, base_class, decorator, qt: QtDriver) -> None:
        """Focus events work on QPushButton too."""
        focus_count = [0]

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", onFocus="on_focus")

            def on_focus(self) -> None:
                focus_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        send_focus_in(instance.button)

        assert_that(focus_count[0]).is_equal_to(1)

    def test_focus_handler_can_modify_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Focus handler can modify the widget itself."""
        focus_called = [False]

        @decorator
        class TestClass(base_class):
            line_edit: QLineEdit = new(onFocus="on_focus")

            def on_focus(self) -> None:
                focus_called[0] = True
                self.line_edit.selectAll()

        instance = create_and_track(qt, TestClass, base_class)
        instance.line_edit.setText("Hello World")
        send_focus_in(instance.line_edit)

        # Verify handler was called and didn't crash
        assert_that(focus_called[0]).is_true()
