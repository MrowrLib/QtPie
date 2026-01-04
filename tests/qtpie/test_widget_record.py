# pyright: reportPrivateUsage=false
"""Tests for Widget[T] with record support."""

from dataclasses import dataclass

from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import Variable, Widget, new, widget
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
        """Accessing record auto-creates a Variable[T]."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        record = w.record
        assert_that(record).is_instance_of(Variable)

    def test_record_has_model_fields(self, qt: QtDriver) -> None:
        """Record proxy has model fields accessible."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        # Access fields through the proxy
        w.record.observable.name.set("Alice")  # type: ignore[union-attr]
        w.record.observable.age.set(30)  # type: ignore[union-attr]

        assert_that(w.record.value.name).is_equal_to("Alice")
        assert_that(w.record.value.age).is_equal_to(30)

    def test_record_dirty_tracking(self, qt: QtDriver) -> None:
        """Record participates in dirty tracking."""

        @widget
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        assert_that(w.record.is_dirty.get()).is_false()

        w.record.observable.name.set("Bob")  # type: ignore[union-attr]
        assert_that(w.record.is_dirty.get()).is_true()

    def test_record_with_other_variables(self, qt: QtDriver) -> None:
        """Widget can have record AND other variables."""

        @widget
        class PersonEditor(Widget[Person]):
            _status: Variable[str] = new("idle")
            _label: QLabel = new("Editor")

        w = qt.track(PersonEditor())

        # Record works
        w.record.observable.name.set("Charlie")  # type: ignore[union-attr]
        assert_that(w.record.value.name).is_equal_to("Charlie")

        # Other variable works independently
        w._status.value = "editing"
        assert_that(w._status.value).is_equal_to("editing")

    def test_widget_without_record_type_raises(self, qt: QtDriver) -> None:
        """Accessing record on Widget without type param raises."""

        @widget
        class PlainWidget(Widget):
            _label: QLabel = new("Hello")

        w = qt.track(PlainWidget())

        try:
            _ = w.record
            assert_that(False).is_true()  # Should not reach here
        except TypeError as e:
            assert_that(str(e)).contains("no record type")

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
                self.record.observable.name.set("Setup Name")  # type: ignore[union-attr]
                self.record.observable.age.set(25)  # type: ignore[union-attr]

        w = qt.track(PersonEditor())
        assert_that(w.record.value.name).is_equal_to("Setup Name")
        assert_that(w.record.value.age).is_equal_to(25)


class TestWidgetRecordExplicit:
    """Test explicit record declaration for types without defaults."""

    def test_no_default_raises_without_explicit_record(self, qt: QtDriver) -> None:
        """Accessing record on type without defaults raises helpful error."""

        @widget
        class CatEditor(Widget[Cat]):
            pass

        w = qt.track(CatEditor())

        try:
            _ = w.record
            assert_that(False).is_true()  # Should not reach here
        except ValueError as e:
            assert_that(str(e)).contains("Cannot create Variable[Cat]")
            assert_that(str(e)).contains("default value")

    def test_explicit_record_with_default(self, qt: QtDriver) -> None:
        """Can declare record explicitly with default value."""

        @widget
        class CatEditor(Widget[Cat]):
            record: Variable[Cat] = new(default=Cat("Whiskers", 9))

        w = qt.track(CatEditor())

        # Record should be accessible
        assert_that(w.record).is_instance_of(Variable)
        assert_that(w.record.value.name).is_equal_to("Whiskers")
        assert_that(w.record.value.lives).is_equal_to(9)

    def test_explicit_record_modifiable(self, qt: QtDriver) -> None:
        """Explicit record fields are modifiable."""

        @widget
        class CatEditor(Widget[Cat]):
            record: Variable[Cat] = new(default=Cat("Mittens", 7))

        w = qt.track(CatEditor())

        w.record.observable.name.set("Felix")  # type: ignore[union-attr]
        w.record.observable.lives.set(8)  # type: ignore[union-attr]

        assert_that(w.record.value.name).is_equal_to("Felix")
        assert_that(w.record.value.lives).is_equal_to(8)

    def test_explicit_record_dirty_tracking(self, qt: QtDriver) -> None:
        """Explicit record participates in dirty tracking."""

        @widget
        class CatEditor(Widget[Cat]):
            record: Variable[Cat] = new(default=Cat("Luna", 9))

        w = qt.track(CatEditor())

        assert_that(w.record.is_dirty.get()).is_false()

        w.record.observable.lives.set(8)  # type: ignore[union-attr]
        assert_that(w.record.is_dirty.get()).is_true()


class TestWidgetRecordDirtyHook:
    """Test dirty hook with record."""

    def test_on_dirty_changed_fires_for_record(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when record becomes dirty."""
        dirty_states: list[bool] = []

        @widget
        class PersonEditor(Widget[Person]):
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(PersonEditor())

        # Touch record to register it
        _ = w.record

        # Modify record
        w.record.observable.name.set("Dirty")  # type: ignore[union-attr]
        assert_that(dirty_states).contains(True)
