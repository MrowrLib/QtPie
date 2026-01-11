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
    """QTableView selection bindings.

    Single: selectedRow, selectedColumn, selectedCell, selectedItem
    Multi: selectedRows, selectedColumns, selectedCells, selectedItems
    """

    def test_table_selected_row_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with selectedRow= binds to row index Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _row: Variable[int]  # Bare annotation
            _table: QTableView = new(bind="_dogs", selectedRow="_row")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - row 0 selected
        assert_that(instance._row.value).is_equal_to(0)

        # Change selection via Variable
        instance._row.value = 1
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
        """QTableView with both selectedRow= and selectedItem= keeps them in sync."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _row: Variable[int]  # Bare annotation
            _dog: Variable[Dog]  # Bare annotation
            _table: QTableView = new(bind="_dogs", selectedRow="_row", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Both should sync on init
        assert_that(instance._row.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("Fido")

        # Change row - item should update
        instance._row.value = 1
        assert_that(instance._dog.value.name).is_equal_to("Rex")

    def test_table_bare_variable_selection(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bare Variable[T] (no new()) works for selection bindings."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _row: Variable[int]  # Bare annotation - no new()
            _dog: Variable[Dog]  # Bare annotation - no new()
            _table: QTableView = new(bind="_dogs", selectedRow="_row", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Both should sync from widget
        assert_that(instance._row.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("Fido")

        # Change row - item should update
        instance._row.value = 1
        assert_that(instance._dog.value.name).is_equal_to("Rex")

    def test_table_selected_column_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with selectedColumn= binds to column index Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _col: Variable[int]  # Bare annotation
            _table: QTableView = new(bind="_dogs", selectedColumn="_col")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - column 0 selected
        assert_that(instance._col.value).is_equal_to(0)

        # Change column via Variable
        instance._col.value = 1
        current_idx = instance._table.selectionModel().currentIndex()
        assert_that(current_idx.column()).is_equal_to(1)

    def test_table_selected_cell_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with selectedCell= binds to (row, col) tuple Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _cell: Variable[tuple[int, int]]  # Bare annotation
            _table: QTableView = new(bind="_dogs", selectedCell="_cell")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - cell (0, 0) selected
        assert_that(instance._cell.value).is_equal_to((0, 0))

        # Change cell via Variable
        instance._cell.value = (1, 1)
        current_idx = instance._table.selectionModel().currentIndex()
        assert_that(current_idx.row()).is_equal_to(1)
        assert_that(current_idx.column()).is_equal_to(1)

    def test_table_all_single_selection_bindings(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with all single selection bindings keeps them in sync."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _row: Variable[int]
            _col: Variable[int]
            _cell: Variable[tuple[int, int]]
            _dog: Variable[Dog]
            _table: QTableView = new(
                bind="_dogs",
                selectedRow="_row",
                selectedColumn="_col",
                selectedCell="_cell",
                selectedItem="_dog",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # All should sync on init
        assert_that(instance._row.value).is_equal_to(0)
        assert_that(instance._col.value).is_equal_to(0)
        assert_that(instance._cell.value).is_equal_to((0, 0))
        assert_that(instance._dog.value.name).is_equal_to("Fido")

        # Change row - all should update
        instance._row.value = 1
        assert_that(instance._cell.value).is_equal_to((1, 0))
        assert_that(instance._dog.value.name).is_equal_to("Rex")

        # Change column - cell should update
        instance._col.value = 1
        assert_that(instance._cell.value).is_equal_to((1, 1))

        # Change cell - row, col, item should update
        instance._cell.value = (0, 0)
        assert_that(instance._row.value).is_equal_to(0)
        assert_that(instance._col.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("Fido")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewSelectionParamsNotStolen:
    """Ensure selection kwargs pass to constructor when widget is not a model widget."""

    def test_tableview_kwargs_pass_to_non_model_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView-related kwargs pass to constructor for non-model widgets."""
        from PySide6.QtWidgets import QWidget

        class CustomWidget(QWidget):
            def __init__(
                self,
                parent: QWidget | None = None,
                selectedRow: int = -1,
                selectedColumn: int = -1,
                selectedCell: tuple[int, int] | None = None,
                selectedItem: str | None = None,
                selectedRows: list[int] | None = None,
                selectedColumns: list[int] | None = None,
                selectedCells: list[tuple[int, int]] | None = None,
                selectedItems: list[str] | None = None,
                format: str | None = None,  # noqa: A002
            ) -> None:
                super().__init__(parent)
                self.my_row = selectedRow
                self.my_column = selectedColumn
                self.my_cell = selectedCell
                self.my_item = selectedItem
                self.my_rows = selectedRows
                self.my_columns = selectedColumns
                self.my_cells = selectedCells
                self.my_items = selectedItems
                self.my_format = format

        @decorator
        class TestClass(base_class):
            _custom: CustomWidget = new(
                bind="x",
                selectedRow=2,
                selectedColumn=3,
                selectedCell=(1, 1),
                selectedItem="test_item",
                selectedRows=[0, 2],
                selectedColumns=[1, 3],
                selectedCells=[(0, 0), (1, 1)],
                selectedItems=["a", "b"],
                format="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._custom.my_row).is_equal_to(2)
        assert_that(instance._custom.my_column).is_equal_to(3)
        assert_that(instance._custom.my_cell).is_equal_to((1, 1))
        assert_that(instance._custom.my_item).is_equal_to("test_item")
        assert_that(instance._custom.my_rows).is_equal_to([0, 2])
        assert_that(instance._custom.my_columns).is_equal_to([1, 3])
        assert_that(instance._custom.my_cells).is_equal_to([(0, 0), (1, 1)])
        assert_that(instance._custom.my_items).is_equal_to(["a", "b"])
        assert_that(instance._custom.my_format).is_equal_to("{name}")
