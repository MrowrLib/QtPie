# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
"""Tests for create() - runtime instantiation with new()-like features.

create_instance() is the top-level function.
Widget, Window, App, and Menu all have a .create() method that wraps it.
"""

import pytest
from assertpy import assert_that
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QLabel, QPushButton

from qtpie import Widget, widget
from qtpie.create import create_instance
from qtpie.testing import QtDriver

# =============================================================================
# Signal Connections via create_instance()
# =============================================================================


class TestSignalToMethod:
    """Test connecting signals to methods by name."""

    def test_signal_connects_to_method(self, qt: QtDriver) -> None:
        """Signal connected to method by name string."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class Parent:
            def __init__(self) -> None:
                self.action_called = False
                self.child = create_instance(self, ChildWidget, on_action="on_action")

            def on_action(self) -> None:
                self.action_called = True

        parent = Parent()
        qt.track(parent.child)

        parent.child.on_action.emit()
        assert_that(parent.action_called).is_true()

    def test_multiple_signals(self, qt: QtDriver) -> None:
        """Multiple signals can be connected."""

        @widget
        class ChildWidget(Widget):
            on_action1 = Signal()
            on_action2 = Signal()

        class Parent:
            def __init__(self) -> None:
                self.calls: list[str] = []
                self.child = create_instance(
                    self,
                    ChildWidget,
                    on_action1="handler1",
                    on_action2="handler2",
                )

            def handler1(self) -> None:
                self.calls.append("handler1")

            def handler2(self) -> None:
                self.calls.append("handler2")

        parent = Parent()
        qt.track(parent.child)

        parent.child.on_action1.emit()
        parent.child.on_action2.emit()
        assert_that(parent.calls).is_equal_to(["handler1", "handler2"])


class TestSignalToLambda:
    """Test connecting signals to lambdas/callables."""

    def test_signal_connects_to_lambda(self, qt: QtDriver) -> None:
        """Signal connected to lambda."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        result: list[str] = []

        # Lambda doesn't need a real context
        child = create_instance(None, ChildWidget, on_action=lambda: result.append("called"))
        qt.track(child)

        child.on_action.emit()
        assert_that(result).is_equal_to(["called"])

    def test_signal_connects_to_callable(self, qt: QtDriver) -> None:
        """Signal connected to callable object."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class CallableHandler:
            def __init__(self) -> None:
                self.called = False

            def __call__(self) -> None:
                self.called = True

        handler = CallableHandler()
        child = create_instance(None, ChildWidget, on_action=handler)
        qt.track(child)

        child.on_action.emit()
        assert_that(handler.called).is_true()


class TestSignalToSignal:
    """Test connecting signals to other signals."""

    def test_signal_connects_to_signal(self, qt: QtDriver) -> None:
        """Signal can be connected to another signal on the context."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class ParentQObject(QObject):
            forwarded = Signal()

            def __init__(self) -> None:
                super().__init__()
                self.received = False
                self.child = create_instance(self, ChildWidget, on_action="forwarded")
                self.forwarded.connect(self._on_forwarded)

            def _on_forwarded(self) -> None:
                self.received = True

        parent = ParentQObject()
        qt.track(parent.child)

        parent.child.on_action.emit()
        assert_that(parent.received).is_true()


class TestSignalErrors:
    """Test error handling for signal connections."""

    def test_missing_handler_raises(self, qt: QtDriver) -> None:
        """Missing handler raises AttributeError with helpful message."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class Parent:
            pass

        parent = Parent()

        with pytest.raises(AttributeError, match="nonexistent"):
            create_instance(parent, ChildWidget, on_action="nonexistent")

    def test_non_callable_handler_raises(self, qt: QtDriver) -> None:
        """Non-callable, non-signal handler raises AttributeError."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class Parent:
            not_callable = "just a string"

        parent = Parent()

        with pytest.raises(AttributeError, match="not callable"):
            create_instance(parent, ChildWidget, on_action="not_callable")


# =============================================================================
# Widget.build() method
# =============================================================================


class TestWidgetBuildMethod:
    """Test the .build() method on Widget."""

    def test_widget_build_method(self, qt: QtDriver) -> None:
        """Widget.build() connects signals to parent widget methods."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        @widget
        class ParentWidget(Widget):
            def __init__(self) -> None:
                super().__init__()
                self.action_called = False
                self.child = self.build(ChildWidget, on_action="on_action")

            def on_action(self) -> None:
                self.action_called = True

        parent = ParentWidget()
        qt.track(parent)

        parent.child.on_action.emit()
        assert_that(parent.action_called).is_true()


# =============================================================================
# Constructor Args
# =============================================================================


class TestConstructorArgs:
    """Test that constructor args are passed through."""

    def test_positional_args(self, qt: QtDriver) -> None:
        """Positional args are passed to constructor."""
        label = create_instance(None, QLabel, "Hello World")
        qt.track(label)

        assert_that(label.text()).is_equal_to("Hello World")

    def test_keyword_args(self, qt: QtDriver) -> None:
        """Non-signal/prop kwargs are passed to constructor."""
        btn = create_instance(None, QPushButton, text="Click Me")
        qt.track(btn)

        assert_that(btn.text()).is_equal_to("Click Me")


# =============================================================================
# Widget Props (setXxx methods)
# =============================================================================


class TestWidgetProps:
    """Test that widget properties are applied via setXxx methods."""

    def test_enabled_prop(self, qt: QtDriver) -> None:
        """enabled= calls setEnabled()."""
        btn = create_instance(None, QPushButton, "Click", enabled=False)
        qt.track(btn)

        assert_that(btn.isEnabled()).is_false()

    def test_visible_prop(self, qt: QtDriver) -> None:
        """visible= calls setVisible()."""
        label = create_instance(None, QLabel, "Hidden", visible=False)
        qt.track(label)

        assert_that(label.isVisible()).is_false()

    def test_toolTip_prop(self, qt: QtDriver) -> None:
        """toolTip= calls setToolTip()."""
        btn = create_instance(None, QPushButton, "Hover me", toolTip="This is a tooltip")
        qt.track(btn)

        assert_that(btn.toolTip()).is_equal_to("This is a tooltip")

    def test_objectName_via_name(self, qt: QtDriver) -> None:
        """name= sets objectName."""
        label = create_instance(None, QLabel, "Test", name="my-label")
        qt.track(label)

        assert_that(label.objectName()).is_equal_to("my-label")


# =============================================================================
# CSS Classes
# =============================================================================


class TestCssClasses:
    """Test CSS class application."""

    def test_single_class(self, qt: QtDriver) -> None:
        """classes= with single class."""
        label = create_instance(None, QLabel, "Test", classes=["highlight"])
        qt.track(label)

        # Classes are stored in "class" property (for QSS selector matching)
        assert_that(label.property("class")).contains("highlight")

    def test_multiple_classes(self, qt: QtDriver) -> None:
        """classes= with multiple classes."""
        label = create_instance(None, QLabel, "Test", classes=["highlight", "large", "bold"])
        qt.track(label)

        classes = label.property("class")
        assert_that(classes).contains("highlight")
        assert_that(classes).contains("large")
        assert_that(classes).contains("bold")
