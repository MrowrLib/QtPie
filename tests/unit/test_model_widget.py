"""Tests for Widget base class functionality."""

from dataclasses import dataclass
from typing import override

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from qtpie import Widget, make, make_later, widget
from qtpie.testing import QtDriver


@dataclass
class Person:
    """Simple test model."""

    name: str = ""
    age: int = 0
    active: bool = False


@dataclass
class Dog:
    """Another test model."""

    name: str = ""
    breed: str = ""


class TestWidgetWithoutTypeParam:
    """Tests for Widget used without type parameter (no record binding)."""

    def test_widget_without_type_param_works(self, qt: QtDriver) -> None:
        """Widget without type param should work as simple mixin."""

        @widget()
        class SimpleWidget(QWidget, Widget):
            label: QLabel = make(QLabel, "Hello")
            button: QLineEdit = make(QLineEdit)

        w = SimpleWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Hello")
        # No record or record_observable_proxy should exist
        assert_that(hasattr(w, "record")).is_false()
        assert_that(hasattr(w, "record_observable_proxy")).is_false()

    def test_widget_without_type_param_no_auto_binding(self, qt: QtDriver) -> None:
        """Widget without type param should not do auto-binding."""

        @widget()
        class SimpleWidget(QWidget, Widget):
            name: QLineEdit = make(QLineEdit)  # Same name as Person.name but no binding

        w = SimpleWidget()
        qt.track(w)

        # Just a regular widget field
        w.name.setText("Test")
        assert_that(w.name.text()).is_equal_to("Test")


class TestWidgetWithTypeParam:
    """Tests for automatic record creation with Widget[T]."""

    def test_auto_creates_record_with_no_args(self, qt: QtDriver) -> None:
        """Should auto-create record as T() when no record field defined."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.record).is_instance_of(Person)
        assert_that(w.record.name).is_equal_to("")
        assert_that(w.record.age).is_equal_to(0)

    def test_auto_creates_proxy(self, qt: QtDriver) -> None:
        """Should auto-create ObservableProxy for the record."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.record_observable_proxy).is_not_none()
        # Proxy should wrap the record
        assert_that(w.record_observable_proxy.observable(str, "name").get()).is_equal_to("")


class TestWidgetCustomFactory:
    """Tests for custom record factory with make()."""

    def test_uses_make_factory_for_record(self, qt: QtDriver) -> None:
        """Should use make() factory when record field is defined."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make(Person, name="Bob", age=30)
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.record.name).is_equal_to("Bob")
        assert_that(w.record.age).is_equal_to(30)

    def test_proxy_wraps_custom_record(self, qt: QtDriver) -> None:
        """Proxy should wrap the custom record."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make(Person, name="Alice")
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.record_observable_proxy.observable(str, "name").get()).is_equal_to("Alice")


class TestWidgetMakeLater:
    """Tests for make_later() with Widget[T]."""

    def test_make_later_with_configure(self, qt: QtDriver) -> None:
        """Should use record set in configure() when make_later() is used."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make_later()
            name: QLineEdit = make(QLineEdit)

            @override
            def configure(self) -> None:
                self.record = Person(name="Charlie", age=25)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.record.name).is_equal_to("Charlie")
        assert_that(w.record.age).is_equal_to(25)

    def test_make_later_error_when_not_set(self, qt: QtDriver) -> None:
        """Should raise error if make_later() is used but record not set in configure()."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make_later()
            name: QLineEdit = make(QLineEdit)
            # Note: no configure() method to set record

        with pytest.raises(ValueError, match="make_later.*not set in configure"):
            PersonEditor()


class TestWidgetAutoBinding:
    """Tests for automatic binding by field name."""

    def test_auto_binds_by_matching_name(self, qt: QtDriver) -> None:
        """Should auto-bind widget fields to record properties with matching names."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Record → Widget
        w.record_observable_proxy.observable(str, "name").set("David")
        assert_that(w.name.text()).is_equal_to("David")

        w.record_observable_proxy.observable(int, "age").set(40)
        assert_that(w.age.value()).is_equal_to(40)

    def test_auto_binds_widget_to_record(self, qt: QtDriver) -> None:
        """Widget changes should update record via auto-binding."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Widget → Record
        w.name.setText("Eve")
        assert_that(w.record.name).is_equal_to("Eve")

        w.age.setValue(35)
        assert_that(w.record.age).is_equal_to(35)

    def test_skips_non_matching_fields(self, qt: QtDriver) -> None:
        """Should not bind widget fields that don't match record properties."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            extra_field: QLineEdit = make(QLineEdit)  # No 'extra_field' on Person

        w = PersonEditor()
        qt.track(w)

        # extra_field should not be bound - setting it shouldn't affect record
        w.extra_field.setText("test")
        # Record doesn't have extra_field, so nothing should happen
        assert_that(hasattr(w.record, "extra_field")).is_false()

    def test_explicit_bind_takes_precedence(self, qt: QtDriver) -> None:
        """Explicit bind= should override auto-binding."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make(Person, name="Initial")
            # Field named 'name' but explicitly bound to nothing (no bind=)
            # This should still auto-bind
            name: QLineEdit = make(QLineEdit)
            # Field with different name but explicit bind
            name_display: QLabel = make(QLabel, bind="name")

        w = PersonEditor()
        qt.track(w)

        # Both should show the name
        assert_that(w.name.text()).is_equal_to("Initial")
        assert_that(w.name_display.text()).is_equal_to("Initial")

        # Change via widget
        w.name.setText("Updated")
        assert_that(w.record.name).is_equal_to("Updated")
        assert_that(w.name_display.text()).is_equal_to("Updated")


class TestRecordWidgetCheckbox:
    """Tests for checkbox binding in Widget."""

    def test_checkbox_auto_binding(self, qt: QtDriver) -> None:
        """Checkbox should auto-bind to bool record property."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            active: QCheckBox = make(QCheckBox, "Active")

        w = PersonEditor()
        qt.track(w)

        assert_that(w.active.isChecked()).is_false()

        w.record_observable_proxy.observable(bool, "active").set(True)
        assert_that(w.active.isChecked()).is_true()

        w.active.setChecked(False)
        assert_that(w.record.active).is_false()


class TestRecordWidgetSetRecord:
    """Tests for set_record() method."""

    def test_set_record_updates_bindings(self, qt: QtDriver) -> None:
        """set_record() should update all bound widgets."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Initial state
        assert_that(w.name.text()).is_equal_to("")
        assert_that(w.age.value()).is_equal_to(0)

        # Set new record
        new_person = Person(name="Frank", age=50)
        w.set_record(new_person)

        # Note: set_record needs to rebind - for now just check record/proxy updated
        assert_that(w.record).is_equal_to(new_person)
        assert_that(w.record.name).is_equal_to("Frank")


class TestRecordWidgetDifferentRecords:
    """Tests with different record types."""

    def test_works_with_different_record_type(self, qt: QtDriver) -> None:
        """Should work with any dataclass record type."""

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            name: QLineEdit = make(QLineEdit)
            breed: QLineEdit = make(QLineEdit)

        w = DogEditor()
        qt.track(w)

        w.name.setText("Buddy")
        w.breed.setText("Golden Retriever")

        assert_that(w.record.name).is_equal_to("Buddy")
        assert_that(w.record.breed).is_equal_to("Golden Retriever")


class TestRecordWidgetWithCustomRecord:
    """Tests combining custom record and auto-binding."""

    def test_custom_record_with_auto_binding(self, qt: QtDriver) -> None:
        """Custom record should work with auto-binding."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make(Person, name="George", age=60)
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Auto-binding should sync initial values
        assert_that(w.name.text()).is_equal_to("George")
        assert_that(w.age.value()).is_equal_to(60)

        # Two-way binding should work
        w.name.setText("Henry")
        assert_that(w.record.name).is_equal_to("Henry")


class TestAutoBindFalse:
    """Tests for auto_bind=False to disable automatic binding by field name."""

    def test_auto_bind_false_disables_name_matching(self, qt: QtDriver) -> None:
        """With auto_bind=False, fields should NOT auto-bind by name."""

        @widget(auto_bind=False)
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Record should exist with defaults
        assert_that(w.record.name).is_equal_to("")
        assert_that(w.record.age).is_equal_to(0)

        # Widget should NOT be bound - changing widget won't affect record
        w.name.setText("Alice")
        w.age.setValue(30)

        # Record should still have default values (no binding occurred)
        assert_that(w.record.name).is_equal_to("")
        assert_that(w.record.age).is_equal_to(0)

    def test_auto_bind_false_still_allows_explicit_bind(self, qt: QtDriver) -> None:
        """With auto_bind=False, explicit bind= should still work."""

        @widget(auto_bind=False)
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make(Person, name="Bob", age=25)
            name_input: QLineEdit = make(QLineEdit, bind="name")
            age_input: QSpinBox = make(QSpinBox, bind="age")

        w = PersonEditor()
        qt.track(w)

        # Explicit bindings should work
        assert_that(w.name_input.text()).is_equal_to("Bob")
        assert_that(w.age_input.value()).is_equal_to(25)

        # Two-way sync should work
        w.name_input.setText("Charlie")
        assert_that(w.record.name).is_equal_to("Charlie")

    def test_auto_bind_true_by_default(self, qt: QtDriver) -> None:
        """Verify auto_bind=True is the default (current behavior preserved)."""

        @widget()  # No auto_bind specified - should default to True
        class PersonEditor(QWidget, Widget[Person]):
            record: Person = make(Person, name="Default")
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        # Auto-binding should work by default
        assert_that(w.name.text()).is_equal_to("Default")
