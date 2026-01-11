# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
"""Tests for QComboBox model binding with bind=.

Tests that QComboBox bound to Variable[list] uses ReactiveListModel
and updates reactively when the list changes.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QComboBox

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for format= tests."""

    name: str
    age: int


@dataclass
class Product:
    """Test dataclass for format spec tests."""

    name: str
    price: float


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxModelBinding:
    """QComboBox with bind= to Variable[list]."""

    def test_combo_shows_list_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with bind= shows Variable[list] items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)
        assert_that(instance._combo.itemText(0)).is_equal_to("A")
        assert_that(instance._combo.itemText(1)).is_equal_to("B")
        assert_that(instance._combo.itemText(2)).is_equal_to("C")

    def test_combo_updates_on_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(1)

        instance._items.append("B")
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(1)).is_equal_to("B")

    def test_combo_updates_on_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)

        instance._items.remove("B")
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(0)).is_equal_to("A")
        assert_that(instance._combo.itemText(1)).is_equal_to("C")

    def test_combo_updates_on_replace(self, base_class, decorator, qt: QtDriver) -> None:
        """Replacing item in list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("A")

        instance._items[0] = "Z"
        assert_that(instance._combo.itemText(0)).is_equal_to("Z")

    def test_combo_updates_on_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)

        instance._items.clear()
        assert_that(instance._combo.count()).is_equal_to(0)

    def test_combo_with_integers(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox works with integer lists (str conversion)."""

        @decorator
        class TestClass(base_class):
            _numbers: Variable[list[int]] = new([1, 2, 3])
            _combo: QComboBox = new(bind="_numbers")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)
        assert_that(instance._combo.itemText(0)).is_equal_to("1")
        assert_that(instance._combo.itemText(1)).is_equal_to("2")
        assert_that(instance._combo.itemText(2)).is_equal_to("3")

    def test_combo_empty_initial_list(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox starts empty with empty list."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new([])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(0)

        # Adding items works
        instance._items.append("First")
        assert_that(instance._combo.count()).is_equal_to(1)
        assert_that(instance._combo.itemText(0)).is_equal_to("First")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxFormatBinding:
    """QComboBox with bind= and format= for complex objects."""

    def test_format_simple_property(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with simple property access."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido")
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex")

    def test_format_multiple_properties(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with multiple properties."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name} ({age} years)")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido (3 years)")
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex (5 years)")

    def test_format_method_call(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with method calls like .upper()."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("FIDO")
        assert_that(instance._combo.itemText(1)).is_equal_to("REX")

    def test_format_function_call(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with function calls like len()."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Buddy", 2)])
            _combo: QComboBox = new(bind="_dogs", format="{name} (len={len(name)})")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido (len=4)")
        assert_that(instance._combo.itemText(1)).is_equal_to("Buddy (len=5)")

    def test_format_complex_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with complex expressions combining method and function calls."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="Name: {name.upper()} - Length: {len(name)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Name: FIDO - Length: 4")
        assert_that(instance._combo.itemText(1)).is_equal_to("Name: REX - Length: 3")

    def test_format_math_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with math expressions."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name} - dog years: {age * 7}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido - dog years: 21")
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex - dog years: 35")

    def test_format_spec(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with Python format specs like :.2f."""

        @decorator
        class TestClass(base_class):
            _products: Variable[list[Product]] = new([Product("Apple", 1.5), Product("Banana", 0.75)])
            _combo: QComboBox = new(bind="_products", format="{name}: ${price:.2f}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Apple: $1.50")
        assert_that(instance._combo.itemText(1)).is_equal_to("Banana: $0.75")

    def test_format_self_reference(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with #self for the whole item."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["hello", "world"])
            _combo: QComboBox = new(bind="_items", format="Item: {#self.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Item: HELLO")
        assert_that(instance._combo.itemText(1)).is_equal_to("Item: WORLD")

    def test_format_updates_on_change(self, base_class, decorator, qt: QtDriver) -> None:
        """format= works correctly when list changes."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _combo: QComboBox = new(bind="_dogs", format="{name} ({age})")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido (3)")

        # Append new item
        instance._dogs.append(Dog("Rex", 5))
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex (5)")

        # Replace item
        instance._dogs[0] = Dog("Max", 7)
        assert_that(instance._combo.itemText(0)).is_equal_to("Max (7)")
