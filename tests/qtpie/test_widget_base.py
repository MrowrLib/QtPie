# pyright: reportPrivateUsage=false
"""Tests for WidgetBase mixin."""

from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QListView, QPushButton, QWidget

from qtpie import Variable, WidgetBase, new
from qtpie.testing import QtDriver


class TestWidgetBaseWithMockWidget:
    """Test WidgetBase with plain Python classes (no Qt)."""

    def test_setup_called_after_init(self) -> None:
        """__setup__ is called after __init__ completes."""
        call_order: list[str] = []

        class MockWidget:
            def __init__(self) -> None:
                call_order.append("init")

        class MyWidget(MockWidget, WidgetBase):
            def __setup__(self) -> None:
                call_order.append("setup")

        MyWidget()
        assert_that(call_order).is_equal_to(["init", "setup"])

    def test_variable_works_without_decorator(self) -> None:
        """Variable fields work without explicit @new_fields decorator."""

        class MockWidget:
            pass

        class MyWidget(MockWidget, WidgetBase):
            _name: Variable[str] = new("")

        obj = MyWidget()
        obj._name.value = "hello"
        assert_that(obj._name.value).is_equal_to("hello")

    def test_variable_reactive_without_decorator(self) -> None:
        """Variable fields are reactive without explicit @new_fields."""

        class MockWidget:
            pass

        class MyWidget(MockWidget, WidgetBase):
            _count: Variable[int] = new(0)

        obj = MyWidget()
        received: list[int] = []
        obj._count.observable.on_change(lambda v: received.append(v))

        obj._count.value = 1
        obj._count.value = 2

        assert_that(received).is_equal_to([1, 2])

    def test_setup_can_access_variables(self) -> None:
        """__setup__ can read and write Variable fields."""

        class MockWidget:
            pass

        class MyWidget(MockWidget, WidgetBase):
            _value: Variable[int] = new(0)

            def __setup__(self) -> None:
                self._value.value = 42

        obj = MyWidget()
        assert_that(obj._value.value).is_equal_to(42)

    def test_non_variable_fields_instantiated(self) -> None:
        """Non-Variable new() fields are instantiated."""

        class Counter:
            def __init__(self, start: int = 0) -> None:
                self.value = start

        class MockWidget:
            pass

        class MyWidget(MockWidget, WidgetBase):
            _counter: Counter = new(start=10)

        obj = MyWidget()
        assert_that(obj._counter.value).is_equal_to(10)


class TestWidgetBaseWithRealQt:
    """Test WidgetBase with real Qt widgets."""

    def test_qwidget_subclass(self, qt: QtDriver) -> None:
        """WidgetBase works with QWidget subclass."""

        class MyWidget(QWidget, WidgetBase):
            _title: Variable[str] = new("default")

        widget = qt.track(MyWidget())
        widget._title.value = "Hello Qt!"
        assert_that(widget._title.value).is_equal_to("Hello Qt!")

    def test_qlistview_subclass(self, qt: QtDriver) -> None:
        """WidgetBase works with QListView (the intended use case)."""

        class MyListView(QListView, WidgetBase):
            _items: Variable[list[str]] = new([])

            def __setup__(self) -> None:
                self._items.value = ["one", "two", "three"]

        view = qt.track(MyListView())
        assert_that(view._items.value).is_equal_to(["one", "two", "three"])

    def test_setup_runs_after_qt_init(self, qt: QtDriver) -> None:
        """__setup__ runs after Qt widget is fully initialized."""
        was_initialized = False

        class MyWidget(QWidget, WidgetBase):
            def __setup__(self) -> None:
                nonlocal was_initialized
                # If Qt init ran, we should be able to set window title
                self.setWindowTitle("Test")
                was_initialized = True

        _ = qt.track(MyWidget())
        assert_that(was_initialized).is_true()

    def test_mixed_qt_and_variable_fields(self, qt: QtDriver) -> None:
        """Can mix Variable fields with instantiated Qt widgets."""

        class MyWidget(QWidget, WidgetBase):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click me")
            _clicked_count: Variable[int] = new(0)

            def __setup__(self) -> None:
                self._button.clicked.connect(self._on_click)

            def _on_click(self) -> None:
                self._clicked_count.value += 1

        w = qt.track(MyWidget())
        assert_that(w._label.text()).is_equal_to("Hello")
        assert_that(w._button.text()).is_equal_to("Click me")
        assert_that(w._clicked_count.value).is_equal_to(0)

        # Simulate click
        qt.click(w._button)
        assert_that(w._clicked_count.value).is_equal_to(1)
