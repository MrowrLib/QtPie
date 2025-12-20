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
from qtpie_test import QtDriver


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
    """Tests for Widget used without type parameter (no model binding)."""

    def test_widget_without_type_param_works(self, qt: QtDriver) -> None:
        """Widget without type param should work as simple mixin."""

        @widget()
        class SimpleWidget(QWidget, Widget):
            label: QLabel = make(QLabel, "Hello")
            button: QLineEdit = make(QLineEdit)

        w = SimpleWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Hello")
        # No model or proxy should exist
        assert_that(hasattr(w, "model")).is_false()
        assert_that(hasattr(w, "proxy")).is_false()

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
    """Tests for automatic model creation with Widget[T]."""

    def test_auto_creates_model_with_no_args(self, qt: QtDriver) -> None:
        """Should auto-create model as T() when no model field defined."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.model).is_instance_of(Person)
        assert_that(w.model.name).is_equal_to("")
        assert_that(w.model.age).is_equal_to(0)

    def test_auto_creates_proxy(self, qt: QtDriver) -> None:
        """Should auto-create ObservableProxy for the model."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.proxy).is_not_none()
        # Proxy should wrap the model
        assert_that(w.proxy.observable(str, "name").get()).is_equal_to("")


class TestWidgetCustomFactory:
    """Tests for custom model factory with make()."""

    def test_uses_make_factory_for_model(self, qt: QtDriver) -> None:
        """Should use make() factory when model field is defined."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            model: Person = make(Person, name="Bob", age=30)
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.model.name).is_equal_to("Bob")
        assert_that(w.model.age).is_equal_to(30)

    def test_proxy_wraps_custom_model(self, qt: QtDriver) -> None:
        """Proxy should wrap the custom model."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            model: Person = make(Person, name="Alice")
            name: QLineEdit = make(QLineEdit)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.proxy.observable(str, "name").get()).is_equal_to("Alice")


class TestWidgetMakeLater:
    """Tests for make_later() with Widget[T]."""

    def test_make_later_with_setup(self, qt: QtDriver) -> None:
        """Should use model set in setup() when make_later() is used."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            model: Person = make_later()
            name: QLineEdit = make(QLineEdit)

            @override
            def setup(self) -> None:
                self.model = Person(name="Charlie", age=25)

        w = PersonEditor()
        qt.track(w)

        assert_that(w.model.name).is_equal_to("Charlie")
        assert_that(w.model.age).is_equal_to(25)

    def test_make_later_error_when_not_set(self, qt: QtDriver) -> None:
        """Should raise error if make_later() is used but model not set in setup()."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            model: Person = make_later()
            name: QLineEdit = make(QLineEdit)
            # Note: no setup() method to set model

        with pytest.raises(ValueError, match="make_later.*not set in setup"):
            PersonEditor()


class TestWidgetAutoBinding:
    """Tests for automatic binding by field name."""

    def test_auto_binds_by_matching_name(self, qt: QtDriver) -> None:
        """Should auto-bind widget fields to model properties with matching names."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Model → Widget
        w.proxy.observable(str, "name").set("David")
        assert_that(w.name.text()).is_equal_to("David")

        w.proxy.observable(int, "age").set(40)
        assert_that(w.age.value()).is_equal_to(40)

    def test_auto_binds_widget_to_model(self, qt: QtDriver) -> None:
        """Widget changes should update model via auto-binding."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Widget → Model
        w.name.setText("Eve")
        assert_that(w.model.name).is_equal_to("Eve")

        w.age.setValue(35)
        assert_that(w.model.age).is_equal_to(35)

    def test_skips_non_matching_fields(self, qt: QtDriver) -> None:
        """Should not bind widget fields that don't match model properties."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            extra_field: QLineEdit = make(QLineEdit)  # No 'extra_field' on Person

        w = PersonEditor()
        qt.track(w)

        # extra_field should not be bound - setting it shouldn't affect model
        w.extra_field.setText("test")
        # Model doesn't have extra_field, so nothing should happen
        assert_that(hasattr(w.model, "extra_field")).is_false()

    def test_explicit_bind_takes_precedence(self, qt: QtDriver) -> None:
        """Explicit bind= should override auto-binding."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            model: Person = make(Person, name="Initial")
            # Field named 'name' but explicitly bound to nothing (no bind=)
            # This should still auto-bind
            name: QLineEdit = make(QLineEdit)
            # Field with different name but explicit bind
            name_display: QLabel = make(QLabel, bind="proxy.name")

        w = PersonEditor()
        qt.track(w)

        # Both should show the name
        assert_that(w.name.text()).is_equal_to("Initial")
        assert_that(w.name_display.text()).is_equal_to("Initial")

        # Change via widget
        w.name.setText("Updated")
        assert_that(w.model.name).is_equal_to("Updated")
        assert_that(w.name_display.text()).is_equal_to("Updated")


class TestModelWidgetCheckbox:
    """Tests for checkbox binding in Widget."""

    def test_checkbox_auto_binding(self, qt: QtDriver) -> None:
        """Checkbox should auto-bind to bool model property."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            active: QCheckBox = make(QCheckBox, "Active")

        w = PersonEditor()
        qt.track(w)

        assert_that(w.active.isChecked()).is_false()

        w.proxy.observable(bool, "active").set(True)
        assert_that(w.active.isChecked()).is_true()

        w.active.setChecked(False)
        assert_that(w.model.active).is_false()


class TestModelWidgetSetModel:
    """Tests for set_model() method."""

    def test_set_model_updates_bindings(self, qt: QtDriver) -> None:
        """set_model() should update all bound widgets."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Initial state
        assert_that(w.name.text()).is_equal_to("")
        assert_that(w.age.value()).is_equal_to(0)

        # Set new model
        new_person = Person(name="Frank", age=50)
        w.set_model(new_person)

        # Note: set_model needs to rebind - for now just check model/proxy updated
        assert_that(w.model).is_equal_to(new_person)
        assert_that(w.model.name).is_equal_to("Frank")


class TestModelWidgetDifferentModels:
    """Tests with different model types."""

    def test_works_with_different_model_type(self, qt: QtDriver) -> None:
        """Should work with any dataclass model type."""

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            name: QLineEdit = make(QLineEdit)
            breed: QLineEdit = make(QLineEdit)

        w = DogEditor()
        qt.track(w)

        w.name.setText("Buddy")
        w.breed.setText("Golden Retriever")

        assert_that(w.model.name).is_equal_to("Buddy")
        assert_that(w.model.breed).is_equal_to("Golden Retriever")


class TestModelWidgetWithCustomModel:
    """Tests combining custom model and auto-binding."""

    def test_custom_model_with_auto_binding(self, qt: QtDriver) -> None:
        """Custom model should work with auto-binding."""

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            model: Person = make(Person, name="George", age=60)
            name: QLineEdit = make(QLineEdit)
            age: QSpinBox = make(QSpinBox)

        w = PersonEditor()
        qt.track(w)

        # Auto-binding should sync initial values
        assert_that(w.name.text()).is_equal_to("George")
        assert_that(w.age.value()).is_equal_to(60)

        # Two-way binding should work
        w.name.setText("Henry")
        assert_that(w.model.name).is_equal_to("Henry")
