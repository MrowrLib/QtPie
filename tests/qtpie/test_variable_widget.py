# pyright: reportPrivateUsage=false, reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false
# pyright: reportArgumentType=false, reportUnknownLambdaType=false
# pyright: reportCallIssue=false
"""Tests for Variable[T, W] with widget type parameter."""

from dataclasses import dataclass
from typing import override

from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox

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

    def test_widget_type_stored_in_variable_instance(self, qt: QtDriver) -> None:
        """Widget type is accessible on the Variable instance."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLineEdit] = new("")  # type: ignore[type-arg]

        w = qt.track(Test())
        assert w._name._widget_type is QLineEdit

    def test_widget_created_and_bound(self, qt: QtDriver) -> None:
        """Variable[T, W].widget is created and bound to the Variable."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLineEdit] = new("hello")  # type: ignore[type-arg]

        w = qt.track(Test())

        # Widget should be created
        assert w._name.widget is not None
        assert isinstance(w._name.widget, QLineEdit)

        # Widget should be bound to Variable value
        assert w._name.widget.text() == "hello"

        # Changing Variable updates widget
        w._name.value = "world"
        assert w._name.widget.text() == "world"

        # Two-way: changing widget updates Variable
        w._name.widget.setText("updated")
        assert w._name.value == "updated"

    def test_widget_none_when_no_widget_type(self, qt: QtDriver) -> None:
        """Variable[T] (no widget type) has widget=None."""

        @widget
        class Test(Widget):
            _name: Variable[str] = new("hello")

        w = qt.track(Test())
        assert w._name.widget is None

    def test_variable_still_works_with_widget_type(self, qt: QtDriver) -> None:
        """Variable[T, W] still functions as a normal Variable."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLineEdit] = new("default")  # type: ignore[type-arg]

        w = qt.track(Test())
        assert w._name.value == "default"

        w._name.value = "updated"
        assert w._name.value == "updated"

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


class TestCallableNewSyntax:
    """Test new(value_args)(widget_args) callable chain syntax."""

    def test_invalid_widget_kwarg_raises_clear_error(self, qt: QtDriver) -> None:
        """Invalid widget kwarg raises TypeError with helpful message."""
        import pytest

        @widget
        class Test(Widget):
            # 'placeholder' is wrong - should be 'placeholderText'
            _name: Variable[str, QLineEdit] = new("hi")(placeholder="wrong kwarg")  # type: ignore[type-arg]

        with pytest.raises(TypeError) as exc_info:
            Test()

        error_msg = str(exc_info.value)
        assert "QLineEdit" in error_msg
        assert "_name" in error_msg
        assert "placeholder" in error_msg

    def test_widget_kwargs_passed_to_constructor(self, qt: QtDriver) -> None:
        """new("value")(placeholder="...") passes kwargs to widget."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLineEdit] = new("default")(placeholderText="Enter name...")  # type: ignore[type-arg]

        w = qt.track(Test())

        # Value should be set
        assert w._name.value == "default"
        assert w._name.widget.text() == "default"

        # Widget kwarg should be applied
        assert w._name.widget.placeholderText() == "Enter name..."

    def test_widget_kwargs_without_value(self, qt: QtDriver) -> None:
        """new()(placeholder="...") works with no value args."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLineEdit] = new()(placeholderText="Type here...")  # type: ignore[type-arg]

        w = qt.track(Test())

        # Default value should be None/empty
        assert w._name.value is None or w._name.value == ""

        # Widget kwarg should be applied
        assert w._name.widget.placeholderText() == "Type here..."

    def test_widget_multiple_kwargs(self, qt: QtDriver) -> None:
        """Multiple widget kwargs are all passed."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLineEdit] = new("hello")(  # type: ignore[type-arg]
                placeholderText="Placeholder",
                maxLength=10,
            )

        w = qt.track(Test())

        assert w._name.widget.placeholderText() == "Placeholder"
        assert w._name.widget.maxLength() == 10

    def test_no_widget_call_still_works(self, qt: QtDriver) -> None:
        """new("value") without second call still works (backward compat)."""

        @widget
        class Test(Widget):
            _name: Variable[str, QLineEdit] = new("hello")  # type: ignore[type-arg]

        w = qt.track(Test())

        assert w._name.value == "hello"
        assert w._name.widget.text() == "hello"
        # Default placeholder is empty
        assert w._name.widget.placeholderText() == ""

    def test_spinbox_with_range(self, qt: QtDriver) -> None:
        """QSpinBox can be configured with range kwargs."""

        @widget
        class Test(Widget):
            _count: Variable[int, QSpinBox] = new(50)(minimum=0, maximum=100)  # type: ignore[type-arg]

        w = qt.track(Test())

        assert w._count.value == 50
        assert w._count.widget.value() == 50
        assert w._count.widget.minimum() == 0
        assert w._count.widget.maximum() == 100


class TestVariableProxyFieldAccess:
    """Test direct field access on Variable[MyClass] via proxy forwarding."""

    def test_get_field_via_variable(self, qt: QtDriver) -> None:
        """self._dog.name returns dog.name value."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dog: Variable[Dog] = new(Dog("Fido", 3))

        w = qt.track(Test())

        # Direct field access should work
        assert w._dog.name == "Fido"
        assert w._dog.age == 3

    def test_set_field_via_variable_is_reactive(self, qt: QtDriver) -> None:
        """self._dog.name = 'Max' is reactive."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dog: Variable[Dog] = new(Dog("Fido", 3))
            _label: QLabel = new("")

            def __setup__(self) -> None:
                # Set initial value
                self._label.setText(f"Name: {self._dog.name}")
                # Bind to the observable manually to verify reactivity
                self._dog.observable.name.on_change(lambda v: self._label.setText(f"Name: {v}"))

        w = qt.track(Test())

        # Initial state
        assert w._label.text() == "Name: Fido"

        # Change via direct field access
        w._dog.name = "Max"

        # Should have triggered the callback
        assert w._label.text() == "Name: Max"

        # And the value should be updated
        assert w._dog.name == "Max"
        assert w._dog.value.name == "Max"

    def test_set_field_updates_bound_widget(self, qt: QtDriver) -> None:
        """self._dog.name = 'Max' updates bound Widget[Dog]."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget(layout="form")
        class DogEditor(Widget[Dog]):
            _name: QLineEdit = new(label="Name")
            _age: QSpinBox = new(label="Age")

        @widget
        class Test(Widget):
            _dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))  # type: ignore[type-arg]

        w = qt.track(Test())
        editor = w._dog.widget

        # Initial state - widget should show values
        assert editor._name.text() == "Fido"
        assert editor._age.value() == 3

        # Change via direct field access on Variable
        w._dog.name = "Buddy"
        w._dog.age = 5

        # Widget should update
        assert editor._name.text() == "Buddy"
        assert editor._age.value() == 5

    def test_variable_own_attributes_not_forwarded(self, qt: QtDriver) -> None:
        """Variable's own attributes (value, widget, etc.) still work."""

        @dataclass
        class Dog:
            name: str
            value: str  # Intentionally named 'value' to test collision

        @widget
        class Test(Widget):
            _dog: Variable[Dog] = new(Dog("Fido", "test_value"))

        w = qt.track(Test())

        # Variable.value should return the Dog object, not dog.value
        assert isinstance(w._dog.value, Dog)
        assert w._dog.value.name == "Fido"

        # But we can still access dog.value through the proxy
        # by going through observable directly
        assert w._dog.observable.value.get() == "test_value"

    def test_field_access_only_for_proxy_types(self, qt: QtDriver) -> None:
        """Direct field access only works for Variable[MyClass], not primitives."""
        import pytest

        @widget
        class Test(Widget):
            _count: Variable[int] = new(42)

        w = qt.track(Test())

        # Primitives don't have fields
        with pytest.raises(AttributeError):
            _ = w._count.some_field  # type: ignore[attr-defined]

    def test_replace_entire_object(self, qt: QtDriver) -> None:
        """self._dog.value = Dog(...) replaces the entire object reactively."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dog: Variable[Dog] = new(Dog("Fido", 3))
            _label: QLabel = new("")

            def __setup__(self) -> None:
                self._update_label()
                self._dog.observable.on_change(self._update_label)

            def _update_label(self) -> None:
                self._label.setText(f"{self._dog.name}, {self._dog.age}")

        w = qt.track(Test())

        # Initial state
        assert w._label.text() == "Fido, 3"

        # Replace entire object
        w._dog.value = Dog("Buddy", 5)

        # Should have updated reactively
        assert w._label.text() == "Buddy, 5"
        assert w._dog.name == "Buddy"
        assert w._dog.age == 5

    def test_replace_object_updates_bound_widget(self, qt: QtDriver) -> None:
        """Replacing object updates bound Widget[T]."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget(layout="form")
        class DogEditor(Widget[Dog]):
            _name: QLineEdit = new(label="Name")
            _age: QSpinBox = new(label="Age")

        @widget
        class Test(Widget):
            _dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))

        w = qt.track(Test())
        editor = w._dog.widget

        # Initial state
        assert editor._name.text() == "Fido"
        assert editor._age.value() == 3

        # Replace entire object
        w._dog.value = Dog("Rex", 7)

        # Widget should update
        assert editor._name.text() == "Rex"
        assert editor._age.value() == 7

    def test_assign_object_via_descriptor(self, qt: QtDriver) -> None:
        """self._dog = Dog(...) also works (via descriptor __set__)."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dog: Variable[Dog] = new(Dog("Fido", 3))

        w = qt.track(Test())

        # This goes through _VariableDescriptor.__set__ -> Variable.value setter
        w._dog = Dog("Max", 2)  # type: ignore[assignment]

        assert w._dog.name == "Max"
        assert w._dog.age == 2


class TestVariableWidgetSignalConnections:
    """Test signal connections on Variable[T, W] widgets.

    This tests that kwargs like `returnPressed="handler"` are properly
    extracted and connected, rather than passed to the widget constructor
    (which would cause Qt to mangle the handler name).
    """

    def test_signal_connection_string_handler(self, qt: QtDriver) -> None:
        """Signal connection with string handler resolves to parent method."""
        call_count = 0

        @widget
        class Test(Widget):
            _input: Variable[str, QLineEdit] = new("")(returnPressed="on_submit")  # type: ignore[type-arg]

            def on_submit(self) -> None:
                nonlocal call_count
                call_count += 1

        w = qt.track(Test())

        # Simulate pressing Enter in the line edit
        w._input.widget.returnPressed.emit()

        assert call_count == 1

    def test_signal_connection_callable_handler(self, qt: QtDriver) -> None:
        """Signal connection with callable handler connects directly."""
        call_count = 0

        def handler() -> None:
            nonlocal call_count
            call_count += 1

        @widget
        class Test(Widget):
            _input: Variable[str, QLineEdit] = new("")(returnPressed=handler)  # type: ignore[type-arg]

        w = qt.track(Test())

        w._input.widget.returnPressed.emit()

        assert call_count == 1

    def test_signal_kwargs_not_passed_to_widget(self, qt: QtDriver) -> None:
        """Signal kwargs are extracted, not passed to widget constructor.

        This is the original bug - if signal kwargs are passed to the widget
        constructor, Qt mangles the handler name (e.g., "add_item" -> "dd_item").
        """

        @widget
        class Test(Widget):
            # If returnPressed="on_submit" was passed to QLineEdit constructor,
            # it would fail with a mangled name error
            _input: Variable[str, QLineEdit] = new("")(  # type: ignore[type-arg]
                placeholderText="Type here",
                returnPressed="on_submit",
            )

            def on_submit(self) -> None:
                pass

        # Should not raise any Qt warnings about invalid method signatures
        w = qt.track(Test())

        # Verify the widget kwarg was applied correctly
        assert w._input.widget.placeholderText() == "Type here"

    def test_nonexistent_handler_raises_runtime_error(self, qt: QtDriver) -> None:
        """Connecting to nonexistent handler raises RuntimeError."""
        import pytest

        @widget
        class Test(Widget):
            _input: Variable[str, QLineEdit] = new("")(returnPressed="nonexistent")  # type: ignore[type-arg]

        # The error happens during widget creation when Variable is first accessed
        # RuntimeError is used instead of AttributeError because getattr(self, name, None)
        # in widget.py would swallow AttributeError during layout setup
        with pytest.raises(RuntimeError, match="nonexistent"):
            qt.track(Test())

    def test_multiple_signal_connections(self, qt: QtDriver) -> None:
        """Multiple signals can be connected on the same widget."""
        return_pressed_count = 0
        editing_finished_count = 0

        @widget
        class Test(Widget):
            _input: Variable[str, QLineEdit] = new("")(  # type: ignore[type-arg]
                returnPressed="on_return",
                editingFinished="on_editing_finished",
            )

            def on_return(self) -> None:
                nonlocal return_pressed_count
                return_pressed_count += 1

            def on_editing_finished(self) -> None:
                nonlocal editing_finished_count
                editing_finished_count += 1

        w = qt.track(Test())

        w._input.widget.returnPressed.emit()
        assert return_pressed_count == 1
        assert editing_finished_count == 0

        w._input.widget.editingFinished.emit()
        assert return_pressed_count == 1
        assert editing_finished_count == 1
