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
"""Tests for QTableView model binding with bind=.

Tests that QTableView bound to Variable[list] uses ReactiveTableModel
and updates reactively when the list changes.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableView

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for table tests."""

    name: str
    age: int


@dataclass
class Product:
    """Test dataclass for table tests."""

    name: str
    price: float
    quantity: int


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewModelBinding:
    """QTableView with bind= to Variable[list]."""

    def test_table_shows_list_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind= shows Variable[list] items with auto-detected columns."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have 2 rows
        assert_that(model.rowCount()).is_equal_to(2)
        # Should auto-detect columns from dataclass (name, age)
        assert_that(model.columnCount()).is_equal_to(2)

        # Check data
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")
        assert_that(model.data(model.index(0, 1))).is_equal_to("3")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Rex")
        assert_that(model.data(model.index(1, 1))).is_equal_to("5")

    def test_table_with_explicit_columns(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with explicit columns= shows only specified columns."""

        @decorator
        class TestClass(base_class):
            _products: Variable[list[Product]] = new([Product("Widget", 19.99, 10)])
            _table: QTableView = new(bind="_products", columns=["name", "price"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have 2 columns (not 3)
        assert_that(model.columnCount()).is_equal_to(2)
        # Check data - only name and price, not quantity
        assert_that(model.data(model.index(0, 0))).is_equal_to("Widget")
        assert_that(model.data(model.index(0, 1))).is_equal_to("19.99")

    def test_table_with_custom_headers(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with headers= shows custom column headers."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(
                bind="_dogs",
                columns=["name", "age"],
                headers={"name": "Dog Name", "age": "Age (Years)"},
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Check headers
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Dog Name")
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Age (Years)")

    def test_table_updates_on_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to list updates QTableView."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(1)

        instance._dogs.append(Dog("Rex", 5))
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(1, 0))).is_equal_to("Rex")
        assert_that(model.data(model.index(1, 1))).is_equal_to("5")

    def test_table_updates_on_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from list updates QTableView."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Spot", 2)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(3)

        # Remove middle item
        del instance._dogs[1]
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Spot")

    def test_table_updates_on_replace(self, base_class, decorator, qt: QtDriver) -> None:
        """Replacing item in list updates QTableView."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        instance._dogs[0] = Dog("Buddy", 7)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Buddy")
        assert_that(model.data(model.index(0, 1))).is_equal_to("7")

    def test_table_updates_on_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list updates QTableView."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(2)

        instance._dogs.clear()
        assert_that(model.rowCount()).is_equal_to(0)

    def test_table_item_at_via_user_role(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView model returns actual item via UserRole."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Get the actual item via UserRole
        item = model.data(model.index(0, 0), Qt.ItemDataRole.UserRole)
        assert_that(item).is_instance_of(Dog)
        assert_that(item.name).is_equal_to("Fido")
        assert_that(item.age).is_equal_to(3)

    def test_table_default_headers_from_field_names(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView shows title-cased field names as default headers."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Default headers should be title-cased field names
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Name")
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Age")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewSelectionBinding:
    """QTableView selection bindings with selectedIndex= and selectedItem=."""

    def test_table_selected_index_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with selectedIndex= binds to row index Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _idx: Variable[int] = new(0)
            _table: QTableView = new(bind="_dogs", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - index 0 selected
        assert_that(instance._idx.value).is_equal_to(0)

        # Change selection via Variable
        instance._idx.value = 1
        current_idx = instance._table.selectionModel().currentIndex()
        assert_that(current_idx.row()).is_equal_to(1)

    def test_table_selected_item_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with selectedItem= binds to actual item Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _dog: Variable[Dog]  # Bare annotation - syncs from widget
            _table: QTableView = new(bind="_dogs", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - first item selected (synced from widget)
        assert_that(instance._dog.value).is_not_none()
        assert_that(instance._dog.value.name).is_equal_to("Fido")

    def test_table_both_bindings(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with both selectedIndex= and selectedItem= keeps them in sync."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _idx: Variable[int]  # Bare annotation
            _dog: Variable[Dog]  # Bare annotation
            _table: QTableView = new(bind="_dogs", selectedIndex="_idx", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Both should sync on init
        assert_that(instance._idx.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("Fido")

        # Change index - item should update
        instance._idx.value = 1
        assert_that(instance._dog.value.name).is_equal_to("Rex")

    def test_table_bare_variable_selection(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bare Variable[T] (no new()) works for selection bindings."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _idx: Variable[int]  # Bare annotation - no new()
            _dog: Variable[Dog]  # Bare annotation - no new()
            _table: QTableView = new(bind="_dogs", selectedIndex="_idx", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Both should sync from widget
        assert_that(instance._idx.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("Fido")

        # Change index - item should update
        instance._idx.value = 1
        assert_that(instance._dog.value.name).is_equal_to("Rex")
