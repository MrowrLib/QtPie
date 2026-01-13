# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownArgumentType=false
"""Tests for signal-to-signal connections via string handler."""

import pytest
from assertpy import assert_that
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QPushButton, QSlider

from qtpie import Variable, Widget, Window, new, widget, window
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

    def test_invalid_handler_uses_lazy_resolution(self, qt: QtDriver) -> None:
        """Nonexistent handler is deferred until emit (lazy resolution for hierarchy search).

        With lazy hierarchy resolution, nonexistent handlers don't error at init time.
        The widget is created successfully, and the error only occurs at emit time.
        Note: Qt's event loop catches exceptions from signal handlers, so we can't
        easily test the exception with pytest.raises.
        """

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click", clicked="nonexistent")

        # Widget is created successfully - error deferred to emit time
        w = qt.track(MyWidget())
        assert w._button is not None

    def test_non_callable_non_signal_raises(self, qt: QtDriver) -> None:
        """Handler pointing to non-callable, non-signal attribute raises at init.

        Note: If the handler name exists on the widget (but isn't callable/signal),
        the error is raised at init. Only nonexistent handlers use lazy resolution.
        """

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


# =============================================================================
# Expression-based Signal Handlers (e.g., clicked="{custom_signal(123)}")
# =============================================================================


class TestWidgetSignalExpressions:
    """Test expression-based signal handlers in Widget."""

    def test_expression_calls_method(self, qt: QtDriver) -> None:
        """Expression like {on_click()} calls the method."""
        method_called = False

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click", clicked="{on_click()}")

            def on_click(self) -> None:
                nonlocal method_called
                method_called = True

        w = qt.track(MyWidget())
        w._button.click()

        assert_that(method_called).is_true()

    def test_expression_emits_signal_with_literal(self, qt: QtDriver) -> None:
        """Expression like {custom_signal(123)} emits signal with literal value."""
        received_value: int | None = None

        @widget
        class MyWidget(Widget):
            custom_signal = Signal(int)
            _button: QPushButton = new("Click", clicked="{custom_signal(123)}")

        w = qt.track(MyWidget())

        def on_signal(val: int) -> None:
            nonlocal received_value
            received_value = val

        w.custom_signal.connect(on_signal)
        w._button.click()

        assert_that(received_value).is_equal_to(123)

    def test_expression_uses_variable_value(self, qt: QtDriver) -> None:
        """Expression can reference Variable values."""
        received_values: list[int] = []

        @widget
        class MyWidget(Widget):
            custom_signal = Signal(int, int)
            _some_number: Variable[int] = new(42)
            simple_number: int = 99
            _button: QPushButton = new("Click", clicked="{custom_signal(some_number, simple_number)}")

        w = qt.track(MyWidget())

        def on_signal(a: int, b: int) -> None:
            received_values.extend([a, b])

        w.custom_signal.connect(on_signal)
        w._button.click()

        assert_that(received_values).is_equal_to([42, 99])

    def test_expression_with_args_placeholder(self, qt: QtDriver) -> None:
        """Expression with #args passes signal arguments."""
        received_value: int | None = None

        @widget
        class MyWidget(Widget):
            _slider: QSlider = new(valueChanged="{on_value(#args)}")

            def on_value(self, val: int) -> None:
                nonlocal received_value
                received_value = val

        w = qt.track(MyWidget())
        w._slider.setValue(77)

        assert_that(received_value).is_equal_to(77)


class TestWindowSignalExpressions:
    """Test expression-based signal handlers in Window."""

    def test_expression_calls_method(self, qt: QtDriver) -> None:
        """Expression like {on_click()} calls the method."""
        method_called = False

        @window(title="Test")
        class MyWindow(Window):
            _button: QPushButton = new("Click", clicked="{on_click()}")

            def on_click(self) -> None:
                nonlocal method_called
                method_called = True

        w = qt.track(MyWindow())
        w._button.click()

        assert_that(method_called).is_true()

    def test_expression_emits_signal_with_literal(self, qt: QtDriver) -> None:
        """Expression like {custom_signal(123)} emits signal with literal value."""
        received_value: int | None = None

        @window(title="Test")
        class MyWindow(Window):
            custom_signal = Signal(int)
            _button: QPushButton = new("Click", clicked="{custom_signal(123)}")

        w = qt.track(MyWindow())

        def on_signal(val: int) -> None:
            nonlocal received_value
            received_value = val

        w.custom_signal.connect(on_signal)
        w._button.click()

        assert_that(received_value).is_equal_to(123)

    def test_expression_uses_variable_value(self, qt: QtDriver) -> None:
        """Expression can reference Variable values."""
        received_values: list[int] = []

        @window(title="Test")
        class MyWindow(Window):
            custom_signal = Signal(int, int)
            _some_number: Variable[int] = new(42)
            simple_number: int = 99
            _button: QPushButton = new("Click", clicked="{custom_signal(some_number, simple_number)}")

        w = qt.track(MyWindow())

        def on_signal(a: int, b: int) -> None:
            received_values.extend([a, b])

        w.custom_signal.connect(on_signal)
        w._button.click()

        assert_that(received_values).is_equal_to([42, 99])

    def test_expression_with_args_placeholder(self, qt: QtDriver) -> None:
        """Expression with #args passes signal arguments."""
        received_value: int | None = None

        @window(title="Test")
        class MyWindow(Window):
            _slider: QSlider = new(valueChanged="{on_value(#args)}")

            def on_value(self, val: int) -> None:
                nonlocal received_value
                received_value = val

        w = qt.track(MyWindow())
        w._slider.setValue(77)

        assert_that(received_value).is_equal_to(77)


class TestAppSignalExpressions:
    """Test expression-based signal handlers in App (using QObject + AppBase for signal support)."""

    def test_expression_calls_method(self, qt: QtDriver) -> None:
        """Expression like {on_click()} calls the method."""
        from qtpy.QtCore import QObject

        from qtpie import AppBase, app

        method_called = False

        @app(show=False, system_tray=False, window=False)
        class MyApp(QObject, AppBase):
            _button: QPushButton = new("Click", clicked="{on_click()}")

            def on_click(self) -> None:
                nonlocal method_called
                method_called = True

        a = MyApp()
        a._button.click()

        assert_that(method_called).is_true()

    def test_expression_emits_signal_with_literal(self, qt: QtDriver) -> None:
        """Expression like {custom_signal(123)} emits signal with literal value."""
        from qtpy.QtCore import QObject

        from qtpie import AppBase, app

        received_value: int | None = None

        @app(show=False, system_tray=False, window=False)
        class MyApp(QObject, AppBase):
            custom_signal = Signal(int)
            _button: QPushButton = new("Click", clicked="{custom_signal(123)}")

        a = MyApp()

        def on_signal(val: int) -> None:
            nonlocal received_value
            received_value = val

        a.custom_signal.connect(on_signal)
        a._button.click()

        assert_that(received_value).is_equal_to(123)

    def test_expression_uses_variable_value(self, qt: QtDriver) -> None:
        """Expression can reference Variable values."""
        from qtpy.QtCore import QObject

        from qtpie import AppBase, app

        received_values: list[int] = []

        @app(show=False, system_tray=False, window=False)
        class MyApp(QObject, AppBase):
            custom_signal = Signal(int, int)
            _some_number: Variable[int] = new(42)
            simple_number: int = 99
            _button: QPushButton = new("Click", clicked="{custom_signal(some_number, simple_number)}")

        a = MyApp()

        def on_signal(a_val: int, b_val: int) -> None:
            received_values.extend([a_val, b_val])

        a.custom_signal.connect(on_signal)
        a._button.click()

        assert_that(received_values).is_equal_to([42, 99])

    def test_expression_with_args_placeholder(self, qt: QtDriver) -> None:
        """Expression with #args passes signal arguments."""
        from qtpy.QtCore import QObject

        from qtpie import AppBase, app

        received_value: int | None = None

        @app(show=False, system_tray=False, window=False)
        class MyApp(QObject, AppBase):
            _slider: QSlider = new(valueChanged="{on_value(#args)}")

            def on_value(self, val: int) -> None:
                nonlocal received_value
                received_value = val

        a = MyApp()
        a._slider.setValue(77)

        assert_that(received_value).is_equal_to(77)
