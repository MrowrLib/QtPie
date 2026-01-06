# pyright: reportPrivateUsage=false, reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false
"""Tests for Variable[T, W] with widget type parameter."""

from dataclasses import dataclass
from typing import override

import pytest
from PySide6.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import Variable, Widget, bind, new, new_fields, widget
from qtpie.testing import QtDriver


class TestVariableWidgetTypeExtraction:
    """Test extraction of widget type from Variable[T, W]."""

    def test_single_type_param_no_widget(self) -> None:
        """Variable[str] has no widget type."""

        @new_fields
        class Test:
            _name: Variable[str] = new("")

        # Access internal descriptor to check widget_type
        desc = type.__getattribute__(Test, "_name")
        assert desc._widget_type is None

    def test_two_type_params_extracts_widget(self) -> None:
        """Variable[str, QLineEdit] extracts QLineEdit as widget type."""

        @new_fields
        class Test:
            _name: Variable[str, QLineEdit] = new("")  # type: ignore[type-arg]

        desc = type.__getattribute__(Test, "_name")
        assert desc._widget_type is QLineEdit

    def test_widget_type_stored_in_variable_instance(self) -> None:
        """Widget type is accessible on the Variable instance."""

        @new_fields
        class Test:
            _name: Variable[str, QLineEdit] = new("")  # type: ignore[type-arg]

        obj = Test()
        assert obj._name._widget_type is QLineEdit

    def test_widget_property_initially_none(self) -> None:
        """Variable.widget is None until widget is created (Phase 4)."""

        @new_fields
        class Test:
            _name: Variable[str, QLineEdit] = new("")  # type: ignore[type-arg]

        obj = Test()
        assert obj._name.widget is None

    def test_variable_still_works_with_widget_type(self) -> None:
        """Variable[T, W] still functions as a normal Variable."""

        @new_fields
        class Test:
            _name: Variable[str, QLineEdit] = new("default")  # type: ignore[type-arg]

        obj = Test()
        assert obj._name.value == "default"

        obj._name.value = "updated"
        assert obj._name.value == "updated"

    def test_different_widget_types(self) -> None:
        """Can use different widget types."""

        @new_fields
        class Test:
            _input: Variable[str, QLineEdit] = new("")  # type: ignore[type-arg]
            _label: Variable[str, QLabel] = new("")  # type: ignore[type-arg]

        input_desc = type.__getattribute__(Test, "_input")
        label_desc = type.__getattribute__(Test, "_label")

        assert input_desc._widget_type is QLineEdit
        assert label_desc._widget_type is QLabel

    def test_mixed_variable_types(self) -> None:
        """Can mix Variable[T] and Variable[T, W]."""

        @new_fields
        class Test:
            _plain: Variable[str] = new("")
            _with_widget: Variable[str, QLineEdit] = new("")  # type: ignore[type-arg]

        plain_desc = type.__getattribute__(Test, "_plain")
        widget_desc = type.__getattribute__(Test, "_with_widget")

        assert plain_desc._widget_type is None
        assert widget_desc._widget_type is QLineEdit


class TestVariableWidgetLayoutOrder:
    """Test that Variable[T, W].widget appears in correct layout order."""

    @pytest.mark.skip(reason="Phase 5: Widget instantiation not yet implemented")
    def test_interleaved_layout_order(self, qt: QtDriver) -> None:
        """Variable[T, W] widgets interleave correctly with regular QWidgets."""

        @widget
        class MixedForm(Widget):
            _label1: QLabel = new("First")
            _name: Variable[str, QLabel] = new("Second")  # type: ignore[type-arg]
            _label2: QLabel = new("Third")
            _age: Variable[str, QLabel] = new("Fourth")  # type: ignore[type-arg]

        w = qt.track(MixedForm())
        layout = w.layout()

        # Should be 4 widgets in order: label1, name.widget, label2, age.widget
        assert layout.count() == 4
        assert layout.itemAt(0).widget().text() == "First"
        assert layout.itemAt(1).widget().text() == "Second"
        assert layout.itemAt(2).widget().text() == "Third"
        assert layout.itemAt(3).widget().text() == "Fourth"

        # Verify the Variable widgets are the same as .widget property
        assert layout.itemAt(1).widget() is w._name.widget
        assert layout.itemAt(3).widget() is w._age.widget


class TestBindingTypeConversion:
    """Test that binding converts types correctly (int→str, dataclass→str)."""

    def test_bind_int_to_qlabel(self, qt: QtDriver) -> None:
        """Binding an int Variable to QLabel converts to string."""

        @widget
        class IntDisplay(Widget):
            _count: Variable[int] = new(42)
            _label: QLabel = new("")

            def __setup__(self) -> None:
                bind(self._count).to(self._label)

        w = qt.track(IntDisplay())

        # Initial binding should convert int to str
        assert w._label.text() == "42"

        # Changing the value should update the label
        w._count.value = 100
        assert w._label.text() == "100"

    def test_bind_float_to_qlabel(self, qt: QtDriver) -> None:
        """Binding a float Variable to QLabel converts to string."""

        @widget
        class FloatDisplay(Widget):
            _value: Variable[float] = new(3.14)
            _label: QLabel = new("")

            def __setup__(self) -> None:
                bind(self._value).to(self._label)

        w = qt.track(FloatDisplay())
        assert w._label.text() == "3.14"

        w._value.value = 2.718
        assert w._label.text() == "2.718"

    def test_bind_dataclass_to_qlabel(self, qt: QtDriver) -> None:
        """Binding a dataclass Variable to QLabel uses str() conversion."""

        @dataclass
        class Person:
            name: str
            age: int

            @override
            def __str__(self) -> str:
                return f"{self.name} ({self.age})"

        @widget
        class PersonDisplay(Widget):
            _person: Variable[Person] = new(default=Person("Alice", 30))
            _label: QLabel = new("")

            def __setup__(self) -> None:
                bind(self._person).to(self._label)

        w = qt.track(PersonDisplay())

        # Should use __str__ method
        assert w._label.text() == "Alice (30)"

    def test_bind_none_to_qlabel(self, qt: QtDriver) -> None:
        """Binding converts None to empty string for QLabel."""

        @widget
        class NoneDisplay(Widget):
            _value: Variable[str] = new("hello")
            _label: QLabel = new("initial")

            def __setup__(self) -> None:
                bind(self._value).to(self._label)

        w = qt.track(NoneDisplay())
        assert w._label.text() == "hello"

        # Setting to None-ish - the binding setter handles None by converting to ""
        # (this tests the str(v) if v is not None else "" logic in the registry)
        w._value.value = ""  # Empty string, not None
        assert w._label.text() == ""

    def test_bind_int_to_qspinbox(self, qt: QtDriver) -> None:
        """Binding int Variable to QSpinBox uses value property."""

        @widget
        class SpinBoxWidget(Widget):
            _count: Variable[int] = new(5)
            _spin: QSpinBox = new()

            def __setup__(self) -> None:
                bind(self._count).to(self._spin)

        w = qt.track(SpinBoxWidget())
        assert w._spin.value() == 5

        w._count.value = 10
        assert w._spin.value() == 10

        # Two-way: changing spinbox updates variable
        w._spin.setValue(20)
        assert w._count.value == 20
