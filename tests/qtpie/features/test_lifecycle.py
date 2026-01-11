# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportCallIssue=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportArgumentType=false
# pyright: reportIndexIssue=false
"""Tests for lifecycle hooks across Widget, Window, Menu, and App.

Tests __setup__(), on_close(), etc.
"""

import pytest
from assertpy import assert_that

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES, create_and_track

# =============================================================================
# __setup__ Hook
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestSetupHook:
    """__setup__ lifecycle hook works across all class types."""

    def test_setup_is_called(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ is invoked during initialization."""
        setup_called = [False]

        @decorator
        class TestClass(base_class):
            def __setup__(self) -> None:
                setup_called[0] = True

        create_and_track(qt, TestClass, base_class)
        assert_that(setup_called[0]).is_true()

    def test_setup_called_once(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ is called exactly once."""
        call_count = [0]

        @decorator
        class TestClass(base_class):
            def __setup__(self) -> None:
                call_count[0] += 1

        create_and_track(qt, TestClass, base_class)
        assert_that(call_count[0]).is_equal_to(1)

    def test_setup_has_access_to_fields(self, base_class, decorator, qt: QtDriver) -> None:
        """Fields are accessible in __setup__."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

            def __setup__(self) -> None:
                # Field should be accessible and have initial value
                self._count.value = 42

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._count.value).is_equal_to(42)

    def test_setup_can_add_validators(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ can add validators."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        instance = create_and_track(qt, TestClass, base_class)
        # Validator was added, so empty name is invalid
        assert_that(instance.is_valid.get()).is_false()

        instance._name.value = "hello"
        assert_that(instance.is_valid.get()).is_true()

    def test_setup_can_set_record(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ can set the record for Widget[T]."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""

        @decorator
        class TestClass(base_class[Person]):  # type: ignore[misc]
            def __setup__(self) -> None:
                self.record = Person("Alice")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.record.name).is_equal_to("Alice")


# =============================================================================
# Field Initialization Order
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestInitializationOrder:
    """Fields are initialized before __setup__ runs."""

    def test_fields_exist_before_setup(self, base_class, decorator, qt: QtDriver) -> None:
        """All fields exist when __setup__ is called."""
        fields_exist = [False]

        @decorator
        class TestClass(base_class):
            _a: Variable[int] = new(1)
            _b: Variable[str] = new("hello")

            def __setup__(self) -> None:
                # Both fields should exist
                fields_exist[0] = hasattr(self, "_a") and hasattr(self, "_b")

        create_and_track(qt, TestClass, base_class)
        assert_that(fields_exist[0]).is_true()

    def test_field_values_accessible_in_setup(self, base_class, decorator, qt: QtDriver) -> None:
        """Field values are accessible in __setup__."""
        values_correct = [False]

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(42)
            _name: Variable[str] = new("test")

            def __setup__(self) -> None:
                values_correct[0] = self._count.value == 42 and self._name.value == "test"

        create_and_track(qt, TestClass, base_class)
        assert_that(values_correct[0]).is_true()


# =============================================================================
# Setup with Different Field Types
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestSetupWithFieldTypes:
    """__setup__ works with various field types."""

    def test_setup_with_scalar_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ can modify scalar Variable."""

        @decorator
        class TestClass(base_class):
            _value: Variable[int] = new(0)

            def __setup__(self) -> None:
                self._value.value = 100

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._value.value).is_equal_to(100)

    def test_setup_with_list_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ can modify list Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new([])

            def __setup__(self) -> None:
                self._items.observable.append("first")
                self._items.observable.append("second")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._items.value).is_equal_to(["first", "second"])

    def test_setup_with_dict_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ can modify dict Variable."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new({})

            def __setup__(self) -> None:
                self._data.observable["key"] = 42

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._data.value).is_equal_to({"key": 42})


# =============================================================================
# Multiple Setup Scenarios
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestMultipleSetupScenarios:
    """Various __setup__ scenarios."""

    def test_setup_without_explicit_hook(self, base_class, decorator, qt: QtDriver) -> None:
        """Class without __setup__ works fine."""

        @decorator
        class TestClass(base_class):
            _value: Variable[int] = new(42)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._value.value).is_equal_to(42)

    def test_setup_modifying_multiple_fields(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ can modify multiple fields."""

        @decorator
        class TestClass(base_class):
            _a: Variable[int] = new(0)
            _b: Variable[int] = new(0)
            _c: Variable[int] = new(0)

            def __setup__(self) -> None:
                self._a.value = 1
                self._b.value = 2
                self._c.value = 3

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._a.value).is_equal_to(1)
        assert_that(instance._b.value).is_equal_to(2)
        assert_that(instance._c.value).is_equal_to(3)

    def test_setup_calling_methods(self, base_class, decorator, qt: QtDriver) -> None:
        """__setup__ can call other instance methods."""

        @decorator
        class TestClass(base_class):
            _value: Variable[int] = new(0)

            def __setup__(self) -> None:
                self._initialize()

            def _initialize(self) -> None:
                self._value.value = 99

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._value.value).is_equal_to(99)
