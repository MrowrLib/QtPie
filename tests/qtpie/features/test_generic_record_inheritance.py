# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
"""Tests for generic record type inheritance.

This feature allows intermediate generic classes to properly pass through
the record type T to the base Widget[T]/Window[T]/etc:

    class DeleteWidget[T](Widget[T]):
        delete: QPushButton = new("Delete")

    @widget
    class DeletePersonWidget(DeleteWidget[Person]): ...
    # Should correctly have record_type = Person
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QPushButton

from qtpie import new
from qtpie.testing import QtDriver

from .conftest import RECORD_CLASS_TYPES, create_and_track


@dataclass
class Person:
    name: str = "Alice"
    age: int = 30


@dataclass
class Animal:
    species: str = "Dog"
    legs: int = 4


# =============================================================================
# Generic Record Type Inheritance
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestGenericRecordInheritance:
    """Record type T is correctly extracted through intermediate generic classes."""

    def test_direct_generic_still_works(self, base_class, decorator, qt: QtDriver) -> None:
        """Direct Widget[Person] still works (baseline)."""

        @decorator(layout="vertical")
        class DirectWidget(base_class[Person]):
            button: QPushButton = new("Click")

        instance = create_and_track(qt, DirectWidget, base_class)
        assert_that(DirectWidget._qtpie_config.record_type).is_equal_to(Person)
        assert_that(instance.record.name).is_equal_to("Alice")

    def test_intermediate_generic_class(self, base_class, decorator, qt: QtDriver) -> None:
        """Intermediate generic class passes T through correctly."""

        @decorator(layout="vertical")
        class GenericBase[T](base_class[T]):
            button: QPushButton = new("Generic Button")

        @decorator(layout="vertical")
        class ConcreteWidget(GenericBase[Person]):
            pass

        instance = create_and_track(qt, ConcreteWidget, base_class)
        assert_that(ConcreteWidget._qtpie_config.record_type).is_equal_to(Person)
        assert_that(instance.record.name).is_equal_to("Alice")
        assert_that(instance.record.age).is_equal_to(30)

    def test_intermediate_with_different_types(self, base_class, decorator, qt: QtDriver) -> None:
        """Same intermediate class can be specialized with different types."""

        @decorator(layout="vertical")
        class GenericBase[T](base_class[T]):
            action: QPushButton = new("Action")

        @decorator(layout="vertical")
        class PersonWidget(GenericBase[Person]):
            pass

        @decorator(layout="vertical")
        class AnimalWidget(GenericBase[Animal]):
            pass

        person_instance = create_and_track(qt, PersonWidget, base_class)
        animal_instance = create_and_track(qt, AnimalWidget, base_class)

        assert_that(PersonWidget._qtpie_config.record_type).is_equal_to(Person)
        assert_that(AnimalWidget._qtpie_config.record_type).is_equal_to(Animal)

        assert_that(person_instance.record.name).is_equal_to("Alice")
        assert_that(animal_instance.record.species).is_equal_to("Dog")

    def test_intermediate_adds_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Intermediate generic class can add widgets that use record."""

        @decorator(layout="vertical")
        class DeleteBase[T](base_class[T]):
            delete_btn: QPushButton = new("Delete", clicked="{on_delete(record)}")

            def on_delete(self, record) -> None:
                self._deleted = True

        @decorator(layout="vertical")
        class DeletePersonWidget(DeleteBase[Person]):
            pass

        instance = create_and_track(qt, DeletePersonWidget, base_class)
        assert_that(instance.record.name).is_equal_to("Alice")
        assert_that(instance.delete_btn).is_instance_of(QPushButton)

    def test_multiple_levels_of_inheritance(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple levels of generic inheritance work."""

        @decorator(layout="vertical")
        class Level1[T](base_class[T]):
            btn1: QPushButton = new("Level 1")

        @decorator(layout="vertical")
        class Level2[T](Level1[T]):
            btn2: QPushButton = new("Level 2")

        @decorator(layout="vertical")
        class Level3(Level2[Person]):
            btn3: QPushButton = new("Level 3")

        instance = create_and_track(qt, Level3, base_class)
        assert_that(Level3._qtpie_config.record_type).is_equal_to(Person)
        assert_that(instance.record.name).is_equal_to("Alice")
