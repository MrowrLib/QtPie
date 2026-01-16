# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for Widget[T] record types across Widget, Window, Menu, and App.

Tests record creation, access, auto-binding, and dirty tracking with records.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLineEdit

from qtpie import Variable, Widget, Window, new, widget, window
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES, create_and_track

# Widget/Window types that support record auto-binding to widget fields
# App doesn't currently support record auto-binding (fields don't auto-bind to record properties)
RECORD_AUTO_BIND_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
]


@dataclass
class Person:
    """Test record type."""

    name: str = ""
    age: int = 0
    active: bool = True


@dataclass
class Address:
    """Another test record type."""

    street: str = ""
    city: str = ""
    zip_code: str = ""


# =============================================================================
# Basic Record Creation
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestRecordCreation:
    """Record creation with Class[T] pattern."""

    def test_widget_with_record_type(self, base_class, decorator, qt: QtDriver) -> None:
        """Class[T] creates a class with record type T."""

        @decorator
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record).is_not_none()

    def test_record_via_decorator(self, base_class, decorator, qt: QtDriver) -> None:
        """record= in decorator sets initial record value."""

        @decorator(record=Person("Alice", 30))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.name).is_equal_to("Alice")
        assert_that(instance.record.age).is_equal_to(30)

    def test_record_via_setup(self, base_class, decorator, qt: QtDriver) -> None:
        """Record can be set in __setup__."""

        @decorator
        class TestClass(base_class[Person]):  # type: ignore[misc]
            def __setup__(self) -> None:
                self.record = Person("Bob", 25)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.name).is_equal_to("Bob")
        assert_that(instance.record.age).is_equal_to(25)

    def test_record_with_defaults(self, base_class, decorator, qt: QtDriver) -> None:
        """Record uses dataclass defaults when not specified."""

        @decorator(record=Person())
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.name).is_equal_to("")
        assert_that(instance.record.age).is_equal_to(0)
        assert_that(instance.record.active).is_true()


# =============================================================================
# Record Property Access
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestRecordAccess:
    """Record property access and modification."""

    def test_record_property_access(self, base_class, decorator, qt: QtDriver) -> None:
        """Can access record properties via self.record.field."""

        @decorator(record=Person("Charlie", 40))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            def get_name(self) -> str:
                return self.record.name  # type: ignore[return-value]

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.get_name()).is_equal_to("Charlie")

    def test_record_property_set(self, base_class, decorator, qt: QtDriver) -> None:
        """Can set record properties via self.record.field = value."""

        @decorator(record=Person("Dave", 50))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            def set_name(self, name: str) -> None:
                self.record.name = name

        instance = create_and_track(qt, TestClass, base_class)
        instance.set_name("David")
        assert_that(instance.record.name).is_equal_to("David")

    def test_multiple_property_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """Can change multiple record properties."""

        @decorator(record=Person("Eve", 25))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        instance.record.name = "Eva"
        instance.record.age = 26
        instance.record.active = False

        assert_that(instance.record.name).is_equal_to("Eva")
        assert_that(instance.record.age).is_equal_to(26)
        assert_that(instance.record.active).is_false()


# =============================================================================
# Record Auto-Binding (Widget/Window/App only - they support QWidget fields)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", RECORD_AUTO_BIND_TYPES)
class TestRecordAutoBinding:
    """Fields auto-bind to record properties by name.

    Note: App doesn't currently support record auto-binding.
    """

    def test_field_binds_to_record_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Field named same as record property auto-binds."""

        @decorator(record=Person("Ivy", 28))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            name: QLineEdit = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.name.text()).is_equal_to("Ivy")

    def test_record_change_updates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing record property updates bound widget."""

        @decorator(record=Person("Jack", 32))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            name: QLineEdit = new()

        instance = create_and_track(qt, TestClass, base_class)
        instance.record.name = "Jackie"
        assert_that(instance.name.text()).is_equal_to("Jackie")

    def test_widget_change_updates_record(self, base_class, decorator, qt: QtDriver) -> None:
        """Editing widget updates record property (two-way binding)."""

        @decorator(record=Person("Kate", 38))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            name: QLineEdit = new()

        instance = create_and_track(qt, TestClass, base_class)
        instance.name.setText("Katherine")
        assert_that(instance.record.name).is_equal_to("Katherine")

    def test_multiple_fields_bind_to_record(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple fields can bind to different record properties."""

        @decorator(record=Address("123 Main", "Springfield", "12345"))
        class TestClass(base_class[Address]):  # type: ignore[misc]
            street: QLineEdit = new()
            city: QLineEdit = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.street.text()).is_equal_to("123 Main")
        assert_that(instance.city.text()).is_equal_to("Springfield")


# =============================================================================
# Record Dirty Tracking Integration
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestRecordDirtyTracking:
    """Record changes integrate with widget-level dirty tracking."""

    def test_record_change_makes_widget_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing record property makes widget dirty."""

        @decorator(record=Person("Mike", 55))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty.get()).is_false()

        instance.record.name = "Michael"
        assert_that(instance.is_dirty.get()).is_true()

    def test_record_reset_clears_widget_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """reset_dirty() on widget clears record dirty state."""

        @decorator(record=Person("Nancy", 48))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        instance.record.name = "Nan"
        assert_that(instance.is_dirty.get()).is_true()

        instance.reset_dirty()
        assert_that(instance.is_dirty.get()).is_false()

    def test_record_and_variable_dirty_combined(self, base_class, decorator, qt: QtDriver) -> None:
        """Both record and Variable changes contribute to dirty state."""

        @decorator(record=Person("Oscar", 65))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)

        # Change variable
        instance._count.value = 5
        assert_that(instance.is_dirty.get()).is_true()

        instance.reset_dirty()
        assert_that(instance.is_dirty.get()).is_false()

        # Change record
        instance.record.name = "Ozzy"
        assert_that(instance.is_dirty.get()).is_true()


# =============================================================================
# Record Edge Cases
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestRecordEdgeCases:
    """Edge cases and complex scenarios with records."""

    def test_replace_entire_record(self, base_class, decorator, qt: QtDriver) -> None:
        """Can replace the entire record."""

        @decorator(record=Person("Pat", 70))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        instance.record = Person("Patricia", 72)  # type: ignore[assignment]

        assert_that(instance.record.name).is_equal_to("Patricia")
        assert_that(instance.record.age).is_equal_to(72)

    def test_record_with_complex_dataclass(self, base_class, decorator, qt: QtDriver) -> None:
        """Works with complex nested dataclasses."""

        @decorator(record=Address("123 Main St", "Springfield", "12345"))
        class TestClass(base_class[Address]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.street).is_equal_to("123 Main St")
        assert_that(instance.record.city).is_equal_to("Springfield")
        assert_that(instance.record.zip_code).is_equal_to("12345")

    def test_record_initial_none_with_setup(self, base_class, decorator, qt: QtDriver) -> None:
        """Record can start None and be set in __setup__."""

        @decorator
        class TestClass(base_class[Person]):  # type: ignore[misc]
            def __setup__(self) -> None:
                self.record = Person("Quinn", 33)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.name).is_equal_to("Quinn")

    def test_record_bool_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Can access and modify boolean record properties."""

        @decorator(record=Person("Ross", 40, True))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.active).is_true()

        instance.record.active = False
        assert_that(instance.record.active).is_false()

    def test_record_int_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Can access and modify int record properties."""

        @decorator(record=Person("Sam", 30))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.age).is_equal_to(30)

        instance.record.age = 31
        assert_that(instance.record.age).is_equal_to(31)


# =============================================================================
# Record Value (Unwrapped Access)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestRecordValue:
    """Test record_value property for unwrapped access."""

    def test_record_value_returns_raw_object(self, base_class, decorator, qt: QtDriver) -> None:
        """record_value returns the actual dataclass, not ObservableProxy."""

        @decorator(record=Person("Alice", 30))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        raw = instance.record_value

        # Should be the actual Person instance
        assert_that(raw).is_instance_of(Person)
        assert_that(raw.name).is_equal_to("Alice")
        assert_that(raw.age).is_equal_to(30)

    def test_record_value_enables_isinstance(self, base_class, decorator, qt: QtDriver) -> None:
        """record_value enables isinstance checks."""

        @decorator(record=Person("Bob", 25))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)

        # isinstance works on record_value
        assert_that(isinstance(instance.record_value, Person)).is_true()

    def test_record_value_reflects_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """record_value reflects changes made via record proxy."""

        @decorator(record=Person("Charlie", 40))
        class TestClass(base_class[Person]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record_value.name).is_equal_to("Charlie")

        # Change via proxy
        instance.record.name = "Chuck"

        # record_value should reflect the change
        assert_that(instance.record_value.name).is_equal_to("Chuck")

    def test_record_value_with_nested_objects(self, base_class, decorator, qt: QtDriver) -> None:
        """record_value works with nested dataclasses."""

        @decorator(record=Address("123 Main", "Springfield", "12345"))
        class TestClass(base_class[Address]):  # type: ignore[misc]
            pass

        instance = create_and_track(qt, TestClass, base_class)
        raw = instance.record_value

        assert_that(isinstance(raw, Address)).is_true()
        assert_that(raw.street).is_equal_to("123 Main")
        assert_that(raw.city).is_equal_to("Springfield")
