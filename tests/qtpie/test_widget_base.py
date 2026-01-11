# pyright: reportPrivateUsage=false
"""Tests for WidgetBase mixin."""

from typing import cast

from assertpy import assert_that
from observant import Observable
from qtpy.QtWidgets import QLabel, QListView, QPushButton, QWidget

from qtpie import Variable, WidgetBase, new, widget
from qtpie.testing import QtDriver


class TestWidgetBaseWithQWidget:
    """Test WidgetBase with QWidget classes (requires @widget decorator)."""

    def test_setup_called_after_init(self, qt: QtDriver) -> None:
        """__setup__ is called after __init__ completes."""
        call_order: list[str] = []

        @widget
        class MyWidget(QWidget, WidgetBase):
            def __setup__(self) -> None:
                call_order.append("setup")

        qt.track(MyWidget())
        assert_that(call_order).is_equal_to(["setup"])

    def test_variable_works(self, qt: QtDriver) -> None:
        """Variable fields work with @widget decorator."""

        @widget
        class MyWidget(QWidget, WidgetBase):
            _name: Variable[str] = new("")

        obj = qt.track(MyWidget())
        obj._name.value = "hello"
        assert_that(obj._name.value).is_equal_to("hello")

    def test_variable_reactive(self, qt: QtDriver) -> None:
        """Variable fields are reactive."""

        @widget
        class MyWidget(QWidget, WidgetBase):
            _count: Variable[int] = new(0)

        obj = qt.track(MyWidget())
        received: list[int] = []
        observable = cast(Observable[int], obj._count.observable)
        observable.on_change(lambda v: received.append(v))

        obj._count.value = 1
        obj._count.value = 2

        assert_that(received).is_equal_to([1, 2])

    def test_setup_can_access_variables(self, qt: QtDriver) -> None:
        """__setup__ can read and write Variable fields."""

        @widget
        class MyWidget(QWidget, WidgetBase):
            _value: Variable[int] = new(0)

            def __setup__(self) -> None:
                self._value.value = 42

        obj = qt.track(MyWidget())
        assert_that(obj._value.value).is_equal_to(42)

    def test_non_variable_fields_instantiated(self, qt: QtDriver) -> None:
        """Non-Variable new() fields are instantiated."""

        class Counter:
            def __init__(self, start: int = 0) -> None:
                self.value = start

        @widget
        class MyWidget(QWidget, WidgetBase):
            _counter: Counter = new(start=10)

        obj = qt.track(MyWidget())
        assert_that(obj._counter.value).is_equal_to(10)


class TestWidgetBaseWithRealQt:
    """Test WidgetBase with real Qt widgets."""

    def test_qwidget_subclass(self, qt: QtDriver) -> None:
        """WidgetBase works with QWidget subclass."""

        @widget
        class MyWidget(QWidget, WidgetBase):
            _title: Variable[str] = new("default")

        w = qt.track(MyWidget())
        w._title.value = "Hello Qt!"
        assert_that(w._title.value).is_equal_to("Hello Qt!")

    def test_qlistview_subclass(self, qt: QtDriver) -> None:
        """WidgetBase works with QListView (the intended use case)."""

        @widget
        class MyListView(QListView, WidgetBase):
            _items: Variable[list[str]] = new([])

            def __setup__(self) -> None:
                self._items.value = ["one", "two", "three"]

        view = qt.track(MyListView())
        assert_that(view._items.value).is_equal_to(["one", "two", "three"])

    def test_setup_runs_after_qt_init(self, qt: QtDriver) -> None:
        """__setup__ runs after Qt widget is fully initialized."""
        was_initialized = False

        @widget
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

        @widget
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
