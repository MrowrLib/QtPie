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

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QComboBox

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


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
