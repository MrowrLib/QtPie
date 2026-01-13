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
"""Tests for signal connections across Widget, Window, Menu, and App.

Tests method name strings, lambdas, and expression connections.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QPushButton

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track

# =============================================================================
# Method Name Connection (clicked="method_name")
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMethodNameConnection:
    """Signal connected via method name string."""

    def test_clicked_connects_to_method(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='method_name' connects button click to method."""
        click_count = [0]

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                click_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(click_count[0]).is_equal_to(1)

    def test_method_called_multiple_times(self, base_class, decorator, qt: QtDriver) -> None:
        """Method is called each time signal fires."""
        click_count = [0]

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                click_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()
        instance.button.click()
        instance.button.click()

        assert_that(click_count[0]).is_equal_to(3)

    def test_method_can_access_self(self, base_class, decorator, qt: QtDriver) -> None:
        """Connected method has access to self."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                self._count.value += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(instance._count.value).is_equal_to(1)


# =============================================================================
# Lambda Connection (clicked=lambda: ...)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestLambdaConnection:
    """Signal connected via lambda function."""

    def test_clicked_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked=lambda: ... connects button click to lambda."""
        click_count = [0]

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked=lambda: click_count.__setitem__(0, click_count[0] + 1))

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(click_count[0]).is_equal_to(1)

    def test_lambda_captures_outer_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Lambda can capture variables from outer scope."""
        results = []

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked=lambda: results.append("clicked"))

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(results).contains("clicked")


# =============================================================================
# Expression Connection (clicked="{method(args)}")
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestExpressionConnection:
    """Signal connected via expression string with arguments."""

    def test_expression_with_literal_arg(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{method(123)}' passes literal argument."""
        received_value = [None]

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked="{handle(42)}")

            def handle(self, value: int) -> None:
                received_value[0] = value

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(received_value[0]).is_equal_to(42)

    def test_expression_with_string_arg(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{method(\"hello\")}' passes string argument."""
        received_value = [None]

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked="{handle('hello')}")

            def handle(self, value: str) -> None:
                received_value[0] = value

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(received_value[0]).is_equal_to("hello")

    def test_expression_with_variable_reference(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{method(_var)}' passes current Variable value."""
        received_value = [None]

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("Alice")
            button: QPushButton = new("Click", clicked="{handle(_name)}")

            def handle(self, value: str) -> None:
                received_value[0] = value

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(received_value[0]).is_equal_to("Alice")

    def test_expression_with_multiple_args(self, base_class, decorator, qt: QtDriver) -> None:
        """clicked='{method(a, b)}' passes multiple arguments."""
        received_values = []

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked="{handle(1, 2)}")

            def handle(self, a: int, b: int) -> None:
                received_values.append((a, b))

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(received_values).contains((1, 2))


# =============================================================================
# Multiple Buttons
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestMultipleButtons:
    """Multiple buttons with different handlers."""

    def test_different_buttons_different_handlers(self, base_class, decorator, qt: QtDriver) -> None:
        """Each button connects to its own handler."""
        clicks = {"a": 0, "b": 0}

        @decorator
        class TestClass(base_class):
            button_a: QPushButton = new("A", clicked="on_click_a")
            button_b: QPushButton = new("B", clicked="on_click_b")

            def on_click_a(self) -> None:
                clicks["a"] += 1

            def on_click_b(self) -> None:
                clicks["b"] += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance.button_a.click()
        instance.button_b.click()
        instance.button_b.click()

        assert_that(clicks["a"]).is_equal_to(1)
        assert_that(clicks["b"]).is_equal_to(2)

    def test_multiple_buttons_same_handler(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple buttons can share the same handler."""
        click_count = [0]

        @decorator
        class TestClass(base_class):
            button_a: QPushButton = new("A", clicked="on_click")
            button_b: QPushButton = new("B", clicked="on_click")

            def on_click(self) -> None:
                click_count[0] += 1

        instance = create_and_track(qt, TestClass, base_class)
        instance.button_a.click()
        instance.button_b.click()

        assert_that(click_count[0]).is_equal_to(2)


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSignalEdgeCases:
    """Edge cases for signal connections."""

    def test_method_not_called_until_signal(self, base_class, decorator, qt: QtDriver) -> None:
        """Handler is not called during initialization."""
        call_count = [0]

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                call_count[0] += 1

        create_and_track(qt, TestClass, base_class)
        # Button not clicked, handler should not be called
        assert_that(call_count[0]).is_equal_to(0)

    def test_handler_can_modify_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Handler can modify other widgets."""

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                self.button.setText("Clicked!")

        instance = create_and_track(qt, TestClass, base_class)
        instance.button.click()

        assert_that(instance.button.text()).is_equal_to("Clicked!")

    def test_handler_can_disable_button(self, base_class, decorator, qt: QtDriver) -> None:
        """Handler can disable its own button."""

        @decorator
        class TestClass(base_class):
            button: QPushButton = new("Click Once", clicked="on_click")

            def on_click(self) -> None:
                self.button.setEnabled(False)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.button.isEnabled()).is_true()

        instance.button.click()
        assert_that(instance.button.isEnabled()).is_false()


# =============================================================================
# Signal Hierarchy Resolution (signals search up parent chain)
# =============================================================================


class TestSignalHierarchyResolution:
    """Signal connections search up the parent hierarchy."""

    def test_signal_connects_to_parent_method(self, qt: QtDriver) -> None:
        """Signal connection string finds method on parent widget."""
        from qtpie import Widget, widget

        parent_called = [False]

        @widget
        class Child(Widget):
            button: QPushButton = new("Click", clicked="on_parent_click")

        @widget
        class Parent(Widget):
            child: Child = new()

            def on_parent_click(self) -> None:
                parent_called[0] = True

        parent = qt.track(Parent())
        parent.child.button.click()

        assert_that(parent_called[0]).is_true()

    def test_signal_connects_to_grandparent_method(self, qt: QtDriver) -> None:
        """Signal connection walks up multiple parent levels."""
        from qtpie import Widget, widget

        grandparent_called = [False]

        @widget
        class GrandChild(Widget):
            button: QPushButton = new("Click", clicked="on_grandparent_click")

        @widget
        class Child(Widget):
            grandchild: GrandChild = new()

        @widget
        class GrandParent(Widget):
            child: Child = new()

            def on_grandparent_click(self) -> None:
                grandparent_called[0] = True

        grandparent = qt.track(GrandParent())
        grandparent.child.grandchild.button.click()

        assert_that(grandparent_called[0]).is_true()

    def test_signal_connects_to_parent_signal(self, qt: QtDriver) -> None:
        """Signal connection can connect to parent's Signal for signal-to-signal."""
        from PySide6.QtCore import Signal

        from qtpie import Widget, widget

        parent_signal_emitted = [False]

        @widget
        class Child(Widget):
            button: QPushButton = new("Click", clicked="on_action")

        @widget
        class Parent(Widget):
            on_action = Signal()
            child: Child = new()

            def __setup__(self) -> None:
                self.on_action.connect(self._handle_action)

            def _handle_action(self) -> None:
                parent_signal_emitted[0] = True

        parent = qt.track(Parent())
        parent.child.button.click()

        assert_that(parent_signal_emitted[0]).is_true()

    def test_closest_parent_method_wins(self, qt: QtDriver) -> None:
        """Closer parent's method takes precedence over further parent."""
        from qtpie import Widget, widget

        which_called = [None]

        @widget
        class GrandChild(Widget):
            button: QPushButton = new("Click", clicked="on_click")

        @widget
        class Child(Widget):
            grandchild: GrandChild = new()

            def on_click(self) -> None:
                which_called[0] = "child"

        @widget
        class GrandParent(Widget):
            child: Child = new()

            def on_click(self) -> None:
                which_called[0] = "grandparent"

        grandparent = qt.track(GrandParent())
        grandparent.child.grandchild.button.click()

        # Child is closer to GrandChild than GrandParent
        assert_that(which_called[0]).is_equal_to("child")

    def test_signal_method_returns_signal_object(self, qt: QtDriver) -> None:
        """self.signal(name) returns the signal from parent hierarchy."""
        from PySide6.QtCore import Signal

        from qtpie import Widget, widget

        @widget
        class Child(Widget):
            pass

        @widget
        class Parent(Widget):
            on_action = Signal()
            child: Child = new()

        parent = qt.track(Parent())
        sig = parent.child.signal("on_action")

        # Should be the same signal object
        assert sig is parent.on_action

    def test_emit_signal_emits_parent_signal(self, qt: QtDriver) -> None:
        """self.emit_signal(name) emits signal found in parent hierarchy."""
        from PySide6.QtCore import Signal

        from qtpie import Widget, widget

        signal_received = [False]

        @widget
        class Child(Widget):
            button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                self.emit_signal("on_action")

        @widget
        class Parent(Widget):
            on_action = Signal()
            child: Child = new()

            def __setup__(self) -> None:
                self.on_action.connect(self._handle)

            def _handle(self) -> None:
                signal_received[0] = True

        parent = qt.track(Parent())
        parent.child.button.click()

        assert_that(signal_received[0]).is_true()

    def test_signal_not_found_raises_error(self, qt: QtDriver) -> None:
        """signal() raises AttributeError if signal not found anywhere."""
        from qtpie import Widget, widget

        @widget
        class Child(Widget):
            pass

        @widget
        class Parent(Widget):
            child: Child = new()

        parent = qt.track(Parent())

        with pytest.raises(AttributeError, match="Signal 'nonexistent' not found"):
            parent.child.signal("nonexistent")


# Note: App signal hierarchy tests are complex because:
# 1. App (QApplication) is a singleton and can't be created multiple times
# 2. AppBase doesn't inherit from QObject so signals don't work
# 3. The Qt parent() hierarchy from Widget to App goes via window management, not parent()
#
# The signal hierarchy lookup for QApplication.instance() is implemented in
# resolve_signal_from_hierarchy() and will be tested in integration tests.
# For unit tests, we focus on Widget/Window hierarchy which is the primary use case.
