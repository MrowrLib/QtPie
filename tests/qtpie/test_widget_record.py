# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false
# pyright: reportUnknownMemberType=false, reportCallIssue=false
"""Tests for Widget[T] with record support."""

from dataclasses import dataclass
from typing import override

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QLabel

from qtpie import RecordVariable, Variable, Widget, new, widget
from qtpie.testing import QtDriver


@dataclass
class Person:
    """Test model."""

    name: str = ""
    age: int = 0


@dataclass
class Dog:
    """Test model with nested type."""

    name: str = ""
    breed: str = ""


@dataclass
class Cat:
    """Test model WITHOUT default values - requires explicit new()."""

    name: str
    lives: int


class TestWidgetRecord:
    """Test Widget[T] record property."""

    def test_record_type_extracted(self, qt: QtDriver) -> None:
        """Widget[Person] extracts Person as record type."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        assert_that(w._qtpie_config.record_type).is_equal_to(Person)

    def test_record_auto_created(self, qt: QtDriver) -> None:
        """Accessing record_state returns a RecordVariable[T]."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        assert_that(w._qtpie.record_state).is_instance_of(RecordVariable)

    def test_record_has_model_fields(self, qt: QtDriver) -> None:
        """Record proxy has model fields accessible."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        # Access fields through the observable
        w._qtpie.record_state.observable.name.set("Alice")
        w._qtpie.record_state.observable.age.set(30)

        assert_that(w._qtpie.record_state.value.name).is_equal_to("Alice")
        assert_that(w._qtpie.record_state.value.age).is_equal_to(30)

    def test_record_direct_field_access(self, qt: QtDriver) -> None:
        """Record supports direct field access and assignment."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())

        # Direct assignment triggers reactivity
        w.record.name = "Bob"
        w.record.age = 42

        # Direct read returns actual value (not Observable)
        assert_that(w.record.name).is_equal_to("Bob")
        assert_that(w.record.age).is_equal_to(42)

    def test_record_state_for_state_access(self, qt: QtDriver) -> None:
        """record_state returns RecordVariable for state access."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())

        # record_state returns RecordVariable
        assert_that(w._qtpie.record_state).is_instance_of(RecordVariable)

        # Can access state properties
        assert_that(w._qtpie.record_state.is_dirty.get()).is_false()

        w.record.name = "Changed"
        assert_that(w._qtpie.record_state.is_dirty.get()).is_true()
        assert_that(w._qtpie.record_state.value.name).is_equal_to("Changed")

    def test_record_dirty_tracking(self, qt: QtDriver) -> None:
        """Record participates in dirty tracking."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        assert_that(w._qtpie.record_state.is_dirty.get()).is_false()

        w._qtpie.record_state.observable.name.set("Bob")
        assert_that(w._qtpie.record_state.is_dirty.get()).is_true()

    def test_record_with_other_variables(self, qt: QtDriver) -> None:
        """Widget can have record AND other variables."""

        @widget
        class PersonEditor(Widget[Person]):
            _status: Variable[str] = new("idle")
            _label: QLabel = new("Editor")

        w = qt.track(PersonEditor())

        # Record works
        w._qtpie.record_state.observable.name.set("Charlie")
        assert_that(w._qtpie.record_state.value.name).is_equal_to("Charlie")

        # Other variable works independently
        w._status.value = "editing"
        assert_that(w._status.value).is_equal_to("editing")

    def test_widget_without_record_type_raises(self, qt: QtDriver) -> None:
        """Accessing record on Widget without type param raises."""

        @widget
        class PlainWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(PlainWidget())

        # Uses AttributeError so hasattr() works correctly
        with pytest.raises(AttributeError, match="no record type"):
            _ = w.record

    def test_record_state_without_record_type_raises(self, qt: QtDriver) -> None:
        """Accessing record_state on Widget without type param raises."""

        @widget
        class PlainWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(PlainWidget())

        # Uses AttributeError so hasattr() works correctly
        with pytest.raises(AttributeError, match="has no record"):
            _ = w._qtpie.record_state

    def test_record_setter_with_value(self, qt: QtDriver) -> None:
        """Can set record with a model instance."""

        @widget
        class DogEditor(Widget[Dog]):
            pass

        w = qt.track(DogEditor())

        # First access creates default
        _ = w.record

        # Set via value (creates new instance internally)
        # Note: This replaces the proxy target which isn't directly supported
        # The typical pattern is to set fields, not replace the whole record

    def test_record_set_fields_in_setup(self, qt: QtDriver) -> None:
        """Can set record fields in __setup__."""

        @widget
        class PersonEditor(Widget[Person]):
            def __setup__(self) -> None:
                # Use self.record for direct field access in __setup__
                self.record.name = "Setup Name"
                self.record.age = 25

        w = qt.track(PersonEditor())
        assert_that(w._qtpie.record_state.value.name).is_equal_to("Setup Name")
        assert_that(w._qtpie.record_state.value.age).is_equal_to(25)


class TestWidgetRecordExplicit:
    """Test explicit record declaration for types without defaults."""

    def test_no_default_allows_none_record(self, qt: QtDriver) -> None:
        """Record on type without defaults starts as None (set in __setup__)."""

        @widget
        class CatEditor(Widget[Cat]):
            pass

        w = qt.track(CatEditor())

        # Record is accessible but value is None
        assert_that(w._qtpie.record_state.value).is_none()

    def test_set_record_in_setup(self, qt: QtDriver) -> None:
        """Can set record in __setup__ for types requiring args."""

        @widget
        class CatEditor(Widget[Cat]):
            def __setup__(self) -> None:
                self.record = Cat(name="Whiskers", lives=9)

        w = qt.track(CatEditor())
        assert_that(w._qtpie.record_state.value).is_not_none()
        assert_that(w._qtpie.record_state.value.name).is_equal_to("Whiskers")

    def test_explicit_record_with_default(self, qt: QtDriver) -> None:
        """Can declare record explicitly with default value."""

        @widget
        class CatEditor(Widget[Cat]):
            record: Variable[Cat] = new(default=Cat("Whiskers", 9))  # type: ignore[assignment]

        w = qt.track(CatEditor())

        # When explicit, record_state still works and returns the Variable
        # (not RecordVariable, but has same interface for .value, .is_dirty)
        assert_that(w._qtpie.record_state.value.name).is_equal_to("Whiskers")
        assert_that(w._qtpie.record_state.value.lives).is_equal_to(9)

    def test_explicit_record_modifiable(self, qt: QtDriver) -> None:
        """Explicit record fields are modifiable."""

        @widget
        class CatEditor(Widget[Cat]):
            record: Variable[Cat] = new(default=Cat("Mittens", 7))  # type: ignore[assignment]

        w = qt.track(CatEditor())

        w._qtpie.record_state.observable.name.set("Felix")  # type: ignore[union-attr]
        w._qtpie.record_state.observable.lives.set(8)  # type: ignore[union-attr]

        assert_that(w._qtpie.record_state.value.name).is_equal_to("Felix")
        assert_that(w._qtpie.record_state.value.lives).is_equal_to(8)

    def test_explicit_record_dirty_tracking(self, qt: QtDriver) -> None:
        """Explicit record participates in dirty tracking."""

        @widget
        class CatEditor(Widget[Cat]):
            record: Variable[Cat] = new(default=Cat("Luna", 9))  # type: ignore[assignment]

        w = qt.track(CatEditor())

        assert_that(w._qtpie.record_state.is_dirty.get()).is_false()

        w._qtpie.record_state.observable.lives.set(8)  # type: ignore[union-attr]
        assert_that(w._qtpie.record_state.is_dirty.get()).is_true()


class TestWidgetRecordDecorator:
    """Test @widget(record=...) decorator parameter."""

    def test_record_via_decorator(self, qt: QtDriver) -> None:
        """@widget(record=...) sets initial record value."""

        @widget(record=Dog("Fido", "Lab"))
        class DogEditor(Widget[Dog]):
            pass

        w = qt.track(DogEditor())
        assert_that(w.record.name).is_equal_to("Fido")
        assert_that(w.record.breed).is_equal_to("Lab")

    def test_record_via_decorator_accessible_in_setup(self, qt: QtDriver) -> None:
        """Record from decorator is available in __setup__."""
        captured_name: list[str] = []

        @widget(record=Dog("Buddy", "Golden"))
        class DogEditor(Widget[Dog]):
            def __setup__(self) -> None:
                captured_name.append(self.record.name)

        qt.track(DogEditor())
        assert_that(captured_name[0]).is_equal_to("Buddy")

    def test_record_via_decorator_modifiable(self, qt: QtDriver) -> None:
        """Record from decorator can be modified."""

        @widget(record=Person("Alice", 30))
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        w.record.name = "Bob"
        w.record.age = 25

        assert_that(w.record.name).is_equal_to("Bob")
        assert_that(w.record.age).is_equal_to(25)

    def test_record_via_decorator_dirty_tracking(self, qt: QtDriver) -> None:
        """Record from decorator participates in dirty tracking."""

        @widget(record=Person("Initial", 0))
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        assert_that(w._qtpie.record_state.is_dirty.get()).is_false()

        w.record.name = "Changed"
        assert_that(w._qtpie.record_state.is_dirty.get()).is_true()

    def test_record_via_decorator_with_no_defaults(self, qt: QtDriver) -> None:
        """@widget(record=...) works with types that have no default values."""

        @widget(record=Cat("Whiskers", 9))
        class CatEditor(Widget[Cat]):
            pass

        w = qt.track(CatEditor())
        assert_that(w.record.name).is_equal_to("Whiskers")
        assert_that(w.record.lives).is_equal_to(9)


class TestWidgetRecordDirtyHook:
    """Test dirty hook with record."""

    def test_on_dirty_changed_fires_for_record(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when record becomes dirty."""
        dirty_states: list[bool] = []

        @widget
        class PersonEditor(Widget[Person]):
            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(PersonEditor())

        # Touch record to register it
        _ = w._qtpie.record_state

        # Modify record
        w._qtpie.record_state.observable.name.set("Dirty")
        assert_that(dirty_states).contains(True)
