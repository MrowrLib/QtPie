# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false
"""Tests for signal-to-signal connections via string handler."""

import pytest
from assertpy import assert_that
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QPushButton, QSlider

from qtpie import Widget, new, widget
from qtpie.testing import QtDriver


class TestSignalEmit:
    """Test connecting widget signals to custom signals via string handler."""

    def test_clicked_emits_signal(self, qt: QtDriver) -> None:
        """Button click emits a custom signal when handler is signal name."""
        signal_emitted = False

        @widget
        class MyWidget(Widget):
            button_pressed = Signal()
            _button: QPushButton = new("Click", clicked="button_pressed")

        w = qt.track(MyWidget())

        def on_signal() -> None:
            nonlocal signal_emitted
            signal_emitted = True

        w.button_pressed.connect(on_signal)
        w._button.click()

        assert_that(signal_emitted).is_true()

    def test_signal_args_forwarded(self, qt: QtDriver) -> None:
        """Signal arguments are forwarded when connecting signal-to-signal."""
        received_value: int | None = None

        @widget
        class MyWidget(Widget):
            value_changed = Signal(int)
            _slider: QSlider = new(valueChanged="value_changed")

        w = qt.track(MyWidget())

        def on_value(val: int) -> None:
            nonlocal received_value
            received_value = val

        w.value_changed.connect(on_value)
        w._slider.setValue(42)

        assert_that(received_value).is_equal_to(42)

    def test_signal_ignores_extra_args(self, qt: QtDriver) -> None:
        """Target signal with fewer args ignores extra source args."""
        signal_emitted = False

        @widget
        class MyWidget(Widget):
            # clicked emits bool, but our signal takes no args
            simple_clicked = Signal()
            _button: QPushButton = new("Click", clicked="simple_clicked")

        w = qt.track(MyWidget())

        def on_signal() -> None:
            nonlocal signal_emitted
            signal_emitted = True

        w.simple_clicked.connect(on_signal)
        w._button.click()

        assert_that(signal_emitted).is_true()

    def test_method_handler_still_works(self, qt: QtDriver) -> None:
        """Existing method handler behavior is unchanged."""
        method_called = False

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                nonlocal method_called
                method_called = True

        w = qt.track(MyWidget())
        w._button.click()

        assert_that(method_called).is_true()

    def test_lambda_handler_still_works(self, qt: QtDriver) -> None:
        """Existing lambda handler behavior is unchanged."""
        lambda_called = False

        def set_called() -> None:
            nonlocal lambda_called
            lambda_called = True

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click", clicked=set_called)

        w = qt.track(MyWidget())
        w._button.click()

        assert_that(lambda_called).is_true()

    def test_invalid_handler_raises(self, qt: QtDriver) -> None:
        """Nonexistent handler name raises AttributeError."""

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click", clicked="nonexistent")

        with pytest.raises(AttributeError, match="nonexistent"):
            qt.track(MyWidget())

    def test_non_callable_non_signal_raises(self, qt: QtDriver) -> None:
        """Handler pointing to non-callable, non-signal attribute raises."""

        @widget
        class MyWidget(Widget):
            some_value: int = 42
            _button: QPushButton = new("Click", clicked="some_value")

        with pytest.raises(AttributeError, match="not callable or a Signal"):
            qt.track(MyWidget())


class TestSignalEmitWithArgs:
    """Test signal forwarding with various argument configurations."""

    def test_multiple_args_forwarded(self, qt: QtDriver) -> None:
        """Multiple signal arguments are forwarded correctly."""
        received_min: int | None = None
        received_max: int | None = None

        @widget
        class MyWidget(Widget):
            range_changed = Signal(int, int)
            _slider: QSlider = new(rangeChanged="range_changed")

        w = qt.track(MyWidget())

        def on_range(min_val: int, max_val: int) -> None:
            nonlocal received_min, received_max
            received_min = min_val
            received_max = max_val

        w.range_changed.connect(on_range)
        w._slider.setRange(10, 100)

        assert_that(received_min).is_equal_to(10)
        assert_that(received_max).is_equal_to(100)


class TestParentChildSignalFlow:
    """Test the full parent-child signal flow pattern."""

    def test_child_button_triggers_parent_handler(self, qt: QtDriver) -> None:
        """Button click in child widget triggers parent's connected handler."""
        parent_handler_called = False

        @widget
        class Counter(Widget):
            increment_requested = Signal()
            _button: QPushButton = new("+", clicked="increment_requested")

        @widget
        class App(Widget):
            counter: Counter = new(increment_requested="_on_increment")

            def _on_increment(self) -> None:
                nonlocal parent_handler_called
                parent_handler_called = True

        app = qt.track(App())
        app.counter._button.click()

        assert_that(parent_handler_called).is_true()

    def test_child_signal_with_args_to_parent(self, qt: QtDriver) -> None:
        """Child signal with arguments forwards to parent handler."""
        received_value: int | None = None

        @widget
        class ValueEditor(Widget):
            value_changed = Signal(int)
            _slider: QSlider = new(valueChanged="value_changed")

        @widget
        class App(Widget):
            editor: ValueEditor = new(value_changed="_on_value_changed")

            def _on_value_changed(self, value: int) -> None:
                nonlocal received_value
                received_value = value

        app = qt.track(App())
        app.editor._slider.setValue(42)

        assert_that(received_value).is_equal_to(42)

    def test_child_signal_to_parent_signal(self, qt: QtDriver) -> None:
        """Child signal can connect to parent's signal (signal chain)."""
        final_handler_called = False

        @widget
        class Counter(Widget):
            increment_requested = Signal()
            _button: QPushButton = new("+", clicked="increment_requested")

        @widget
        class App(Widget):
            # Parent also has a signal that re-emits
            app_incremented = Signal()
            counter: Counter = new(increment_requested="app_incremented")

        app = qt.track(App())

        def on_app_signal() -> None:
            nonlocal final_handler_called
            final_handler_called = True

        app.app_incremented.connect(on_app_signal)
        app.counter._button.click()

        assert_that(final_handler_called).is_true()
