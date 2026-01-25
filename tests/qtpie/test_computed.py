# pyright: reportPrivateUsage=false
"""Tests for Computed[T] - read-only derived variables."""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


class TestComputedBasic:
    """Basic Computed[T] functionality."""

    def test_computed_from_single_variable(self, qt: QtDriver) -> None:
        """Computed value derived from a single Variable."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("hello")
            _upper: Computed[str] = new("{_name.upper()}")

        instance = qt.track(TestWidget())

        # Computed value should be derived from _name
        assert_that(instance._upper.value).is_equal_to("HELLO")

    def test_computed_updates_when_source_changes(self, qt: QtDriver) -> None:
        """Computed value updates when source Variable changes."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_count * 2}")

        instance = qt.track(TestWidget())

        assert_that(instance._doubled.value).is_equal_to(10)

        # Change source
        instance._count.value = 10

        # Computed should update
        assert_that(instance._doubled.value).is_equal_to(20)

    def test_computed_from_multiple_variables(self, qt: QtDriver) -> None:
        """Computed value derived from multiple Variables."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _first: Variable[str] = new("Hello")
            _last: Variable[str] = new("World")
            _full: Computed[str] = new("{_first} {_last}")

        instance = qt.track(TestWidget())

        assert_that(instance._full.value).is_equal_to("Hello World")

        # Change first
        instance._first.value = "Goodbye"
        assert_that(instance._full.value).is_equal_to("Goodbye World")

        # Change second
        instance._last.value = "Everyone"
        assert_that(instance._full.value).is_equal_to("Goodbye Everyone")

    def test_computed_is_read_only(self, qt: QtDriver) -> None:
        """Cannot set value on Computed."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_count * 2}")

        instance = qt.track(TestWidget())

        with pytest.raises(AttributeError):
            instance._doubled.value = 100


class TestComputedWithRecord:
    """Computed[T] with Widget[T] record types."""

    def test_computed_from_record_field(self, qt: QtDriver) -> None:
        """Computed value derived from record field."""
        from qtpie import Computed

        @dataclass
        class Person:
            first_name: str = ""
            last_name: str = ""

        @widget(record=Person("John", "Doe"))
        class TestWidget(Widget[Person]):
            _full_name: Computed[str] = new("{first_name} {last_name}")

        instance = qt.track(TestWidget())

        assert_that(instance._full_name.value).is_equal_to("John Doe")

    def test_computed_updates_when_record_field_changes(self, qt: QtDriver) -> None:
        """Computed value updates when record field changes."""
        from qtpie import Computed

        @dataclass
        class Person:
            first_name: str = ""
            last_name: str = ""

        @widget(record=Person("John", "Doe"))
        class TestWidget(Widget[Person]):
            _full_name: Computed[str] = new("{first_name} {last_name}")

        instance = qt.track(TestWidget())

        assert_that(instance._full_name.value).is_equal_to("John Doe")

        # Change record field
        instance.record.first_name = "Jane"
        assert_that(instance._full_name.value).is_equal_to("Jane Doe")


class TestComputedInBindings:
    """Computed[T] can be used in widget bindings."""

    def test_computed_used_in_label_bind(self, qt: QtDriver) -> None:
        """Computed can be referenced in widget bind= expressions."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_count * 2}")
            _label: QLabel = new(bind="Doubled: {_doubled}")

        instance = qt.track(TestWidget())

        assert_that(instance._label.text()).is_equal_to("Doubled: 10")

        # Change source, label should update through the Computed
        instance._count.value = 7
        assert_that(instance._doubled.value).is_equal_to(14)  # Computed updated
        assert_that(instance._label.text()).is_equal_to("Doubled: 14")  # Label updated reactively

    def test_label_updates_through_computed_chain(self, qt: QtDriver) -> None:
        """Changing root Variable propagates through Computed to bound widget."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _base: Variable[int] = new(10)
            _doubled: Computed[int] = new("{_base * 2}")
            _quadrupled: Computed[int] = new("{_doubled * 2}")
            _label: QLabel = new(bind="Result: {_quadrupled}")

        instance = qt.track(TestWidget())

        # Initial: 10 * 2 * 2 = 40
        assert_that(instance._label.text()).is_equal_to("Result: 40")

        # Change base to 5: 5 * 2 * 2 = 20
        instance._base.value = 5
        assert_that(instance._doubled.value).is_equal_to(10)
        assert_that(instance._quadrupled.value).is_equal_to(20)
        assert_that(instance._label.text()).is_equal_to("Result: 20")

    def test_computed_chain(self, qt: QtDriver) -> None:
        """Computed can depend on other Computed values."""
        from qtpie import Computed

        @widget
        class TestWidget(Widget):
            _base: Variable[int] = new(5)
            _doubled: Computed[int] = new("{_base * 2}")
            _quadrupled: Computed[int] = new("{_doubled * 2}")

        instance = qt.track(TestWidget())

        assert_that(instance._doubled.value).is_equal_to(10)
        assert_that(instance._quadrupled.value).is_equal_to(20)

        # Change base
        instance._base.value = 3
        assert_that(instance._doubled.value).is_equal_to(6)
        assert_that(instance._quadrupled.value).is_equal_to(12)
