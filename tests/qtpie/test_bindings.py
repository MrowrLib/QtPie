# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportUnknownMemberType=false
"""Tests for bind() - connecting Variables to widget properties."""

from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import Variable, Widget, bind, new, widget
from qtpie.testing import QtDriver


class TestOneWayBinding:
    """Test one-way binding: Variable → widget."""

    def test_bind_sets_initial_value(self, qt: QtDriver) -> None:
        """bind() sets the widget's initial value from the Variable."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Hello")
            _label: QLabel = new("")

            def __setup__(self) -> None:
                bind(self._name).to(self._label)

        w = qt.track(MyWidget())
        assert_that(w._label.text()).is_equal_to("Hello")

    def test_variable_change_updates_widget(self, qt: QtDriver) -> None:
        """Changing the Variable updates the widget."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Initial")
            _label: QLabel = new("")

            def __setup__(self) -> None:
                bind(self._name).to(self._label)

        w = qt.track(MyWidget())
        assert_that(w._label.text()).is_equal_to("Initial")

        w._name.value = "Updated"
        assert_that(w._label.text()).is_equal_to("Updated")

    def test_bind_with_explicit_property(self, qt: QtDriver) -> None:
        """bind() can specify an explicit property name."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Hello")
            _label: QLabel = new("")

            def __setup__(self) -> None:
                bind(self._name).to(self._label, "text")

        w = qt.track(MyWidget())
        assert_that(w._label.text()).is_equal_to("Hello")


class TestTwoWayBinding:
    """Test two-way binding: Variable ↔ widget."""

    def test_widget_change_updates_variable(self, qt: QtDriver) -> None:
        """Changing the widget updates the Variable."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _input: QLineEdit = new("")

            def __setup__(self) -> None:
                bind(self._name).to(self._input)

        w = qt.track(MyWidget())

        # Simulate user typing
        w._input.setText("User typed")
        assert_that(w._name.value).is_equal_to("User typed")

    def test_two_way_binding_sync(self, qt: QtDriver) -> None:
        """Two-way binding keeps Variable and widget in sync."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)
            _spinbox: QSpinBox = new()

            def __setup__(self) -> None:
                self._spinbox.setMaximum(1000)  # Extend default range
                bind(self._count).to(self._spinbox)

        w = qt.track(MyWidget())

        # Variable → widget
        w._count.value = 42
        assert_that(w._spinbox.value()).is_equal_to(42)

        # Widget → Variable
        w._spinbox.setValue(100)
        assert_that(w._count.value).is_equal_to(100)

    def test_one_way_binding_option(self, qt: QtDriver) -> None:
        """two_way=False disables widget → Variable updates."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Initial")
            _input: QLineEdit = new("")

            def __setup__(self) -> None:
                bind(self._name).to(self._input, two_way=False)

        w = qt.track(MyWidget())

        # Variable → widget works
        w._name.value = "From Variable"
        assert_that(w._input.text()).is_equal_to("From Variable")

        # Widget → Variable does NOT update
        w._input.setText("From Widget")
        assert_that(w._name.value).is_equal_to("From Variable")  # Unchanged


class TestBindingWithDefaultProperties:
    """Test that default properties are used when not specified."""

    def test_qlabel_default_text(self, qt: QtDriver) -> None:
        """QLabel defaults to 'text' property."""

        @widget
        class MyWidget(Widget):
            _msg: Variable[str] = new("Hello")
            _label: QLabel = new("")

            def __setup__(self) -> None:
                bind(self._msg).to(self._label)  # No property specified

        w = qt.track(MyWidget())
        assert_that(w._label.text()).is_equal_to("Hello")

    def test_qlineedit_default_text(self, qt: QtDriver) -> None:
        """QLineEdit defaults to 'text' property."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Default")
            _input: QLineEdit = new("")

            def __setup__(self) -> None:
                bind(self._name).to(self._input)

        w = qt.track(MyWidget())
        assert_that(w._input.text()).is_equal_to("Default")

    def test_qspinbox_default_value(self, qt: QtDriver) -> None:
        """QSpinBox defaults to 'value' property."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(42)
            _spinbox: QSpinBox = new()

            def __setup__(self) -> None:
                bind(self._count).to(self._spinbox)

        w = qt.track(MyWidget())
        assert_that(w._spinbox.value()).is_equal_to(42)
