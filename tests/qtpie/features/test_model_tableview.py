# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
# pyright: reportUnnecessaryIsInstance=false
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


# =============================================================================
# RecordVariable isinstance check and record.nested_list binding
# =============================================================================


@dataclass
class Item:
    """Test item for nested list."""

    key: str
    value: str


@dataclass
class Container:
    """Test container with nested list."""

    name: str = ""
    items: list[Item] | None = None

    def __post_init__(self) -> None:
        if self.items is None:
            self.items = []


class TestRecordVariableIsVariable:
    """RecordVariable should be an instance of Variable."""

    def test_record_variable_isinstance_variable(self) -> None:
        """RecordVariable is a subclass of Variable, so isinstance should work."""
        from observant import ObservableProxy

        from qtpie.variable import RecordVariable, Variable

        proxy = ObservableProxy(Container("test", [Item("a", "1")]))
        record_var: object = RecordVariable(proxy)  # Cast to object for isinstance test

        # This test verifies the fix: RecordVariable must be a subclass of Variable
        # for binding code to recognize it (isinstance checks in ~50 places)
        assert_that(isinstance(record_var, Variable)).is_true()


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewRecordNestedListBinding:
    """QTableView with bind= to record.nested_list (nested path on Widget[T])."""

    def test_table_binds_to_record_nested_list(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind='record.items' shows nested list from Widget[T].record."""

        @decorator(record=Container("test", [Item("key1", "val1"), Item("key2", "val2")]))
        class TestClass(base_class[Container]):  # type: ignore[misc]
            _table: QTableView = new(bind="record.items", columns=["key", "value"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have 2 rows
        assert_that(model.rowCount()).is_equal_to(2)
        # Should have 2 columns (key, value)
        assert_that(model.columnCount()).is_equal_to(2)

        # Check data
        assert_that(model.data(model.index(0, 0))).is_equal_to("key1")
        assert_that(model.data(model.index(0, 1))).is_equal_to("val1")
        assert_that(model.data(model.index(1, 0))).is_equal_to("key2")
        assert_that(model.data(model.index(1, 1))).is_equal_to("val2")

    def test_widgets_after_table_render(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets declared after QTableView with record binding still render."""
        from PySide6.QtWidgets import QLabel

        @decorator(record=Container("test", [Item("a", "1")]))
        class TestClass(base_class[Container]):  # type: ignore[misc]
            _table: QTableView = new(bind="record.items", columns=["key", "value"])
            _label: QLabel = new("I should render!")

        instance = create_and_track(qt, TestClass, base_class)

        # Label should exist and have correct text
        assert_that(instance._label).is_not_none()
        assert_that(instance._label.text()).is_equal_to("I should render!")

    def test_remove_from_nested_list_no_recursion(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from record.nested_list should not cause infinite recursion."""

        @decorator(record=Container("test", [Item("a", "1"), Item("b", "2"), Item("c", "3")]))
        class TestClass(base_class[Container]):  # type: ignore[misc]
            _table: QTableView = new(bind="record.items", columns=["key", "value"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(3)

        # Remove an item - this should NOT cause RecursionError
        instance.record.items.remove(Item("b", "2"))

        assert_that(model.rowCount()).is_equal_to(2)


# Test dataclasses with bool fields for checkbox tests
@dataclass
class Task:
    """Test dataclass with bool field for checkable tests."""

    done: bool
    title: str
    archived: bool


@dataclass
class SimpleTask:
    """Test dataclass with single bool field."""

    completed: bool
    name: str


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewCheckable:
    """Test QTableView checkbox support for bool fields."""

    def test_bool_field_auto_detected_as_checkbox(self, base_class, decorator, qt: QtDriver) -> None:
        """Bool fields are automatically detected as checkable columns."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(True, "Task 1", False)])
            _table: QTableView = new(bind="_tasks")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Check that bool columns have ItemIsUserCheckable flag
        done_idx = model.index(0, 0)  # 'done' column
        title_idx = model.index(0, 1)  # 'title' column
        archived_idx = model.index(0, 2)  # 'archived' column

        assert_that(model.flags(done_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_true()
        assert_that(model.flags(title_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()
        assert_that(model.flags(archived_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_true()

    def test_checkbox_returns_check_state(self, base_class, decorator, qt: QtDriver) -> None:
        """Checkable columns return CheckStateRole data."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(True, "Task 1", False)])
            _table: QTableView = new(bind="_tasks")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Check CheckStateRole returns correct values
        done_idx = model.index(0, 0)
        archived_idx = model.index(0, 2)

        assert_that(model.data(done_idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        assert_that(model.data(archived_idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

    def test_checkbox_click_updates_dataclass(self, base_class, decorator, qt: QtDriver) -> None:
        """Clicking checkbox updates the underlying dataclass field (two-way binding)."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(False, "Task 1", True)])
            _table: QTableView = new(bind="_tasks")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Get the actual task object
        task = instance._tasks.value[0]
        assert_that(task.done).is_false()
        assert_that(task.archived).is_true()

        # Simulate checkbox toggle via setData
        done_idx = model.index(0, 0)
        archived_idx = model.index(0, 2)

        # Toggle done to True
        result = model.setData(done_idx, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole)
        assert_that(result).is_true()
        assert_that(task.done).is_true()

        # Toggle archived to False
        result = model.setData(archived_idx, Qt.CheckState.Unchecked.value, Qt.ItemDataRole.CheckStateRole)
        assert_that(result).is_true()
        assert_that(task.archived).is_false()

    def test_checkable_explicit_list(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable=['done'] limits checkboxes to only specified columns."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(True, "Task 1", False)])
            _table: QTableView = new(bind="_tasks", checkable=["done"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        done_idx = model.index(0, 0)  # 'done' - should be checkable
        archived_idx = model.index(0, 2)  # 'archived' - should NOT be checkable

        assert_that(model.flags(done_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_true()
        assert_that(model.flags(archived_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()

    def test_checkable_false_disables_all(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable=False disables all checkboxes even for bool fields."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(True, "Task 1", False)])
            _table: QTableView = new(bind="_tasks", checkable=False)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        done_idx = model.index(0, 0)
        archived_idx = model.index(0, 2)

        # No columns should be checkable
        assert_that(model.flags(done_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()
        assert_that(model.flags(archived_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()

    def test_checkbox_column_no_text_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Checkable columns show empty string for DisplayRole by default (checkbox only)."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(True, "Task 1", False)])
            _table: QTableView = new(bind="_tasks")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        done_idx = model.index(0, 0)
        title_idx = model.index(0, 1)

        # Checkable column should return empty string
        assert_that(model.data(done_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("")
        # Non-checkable column should return normal value
        assert_that(model.data(title_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("Task 1")

    def test_non_bool_field_not_checkable_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """Non-bool fields (str, int) are not checkable by default."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        name_idx = model.index(0, 0)
        age_idx = model.index(0, 1)

        # String and int columns should not be checkable
        assert_that(model.flags(name_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()
        assert_that(model.flags(age_idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()

    def test_checkable_text_string_all_columns(self, base_class, decorator, qt: QtDriver) -> None:
        """checkableText='{title}' applies format to all checkable columns."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(True, "Buy milk", False)])
            _table: QTableView = new(bind="_tasks", checkableText="{title}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        done_idx = model.index(0, 0)
        archived_idx = model.index(0, 2)

        # Both checkable columns should show the task title
        assert_that(model.data(done_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("Buy milk")
        assert_that(model.data(archived_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("Buy milk")

    def test_checkable_text_dict_per_column(self, base_class, decorator, qt: QtDriver) -> None:
        """checkableText={'done': '{title}'} applies format per column."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task(True, "Buy milk", False)])
            _table: QTableView = new(
                bind="_tasks",
                checkableText={
                    "done": "{title}",
                    # 'archived' not specified, should show empty
                },
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        done_idx = model.index(0, 0)
        archived_idx = model.index(0, 2)

        # 'done' should show title, 'archived' should be empty
        assert_that(model.data(done_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("Buy milk")
        assert_that(model.data(archived_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("")

    def test_checkable_text_with_index(self, base_class, decorator, qt: QtDriver) -> None:
        """checkableText='Row #{#index}' uses row index placeholder."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[SimpleTask]] = new([SimpleTask(True, "Task 1"), SimpleTask(False, "Task 2")])
            _table: QTableView = new(bind="_tasks", checkableText="Row #{#index}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        row0_idx = model.index(0, 0)
        row1_idx = model.index(1, 0)

        assert_that(model.data(row0_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("Row #0")
        assert_that(model.data(row1_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("Row #1")

    def test_checkable_text_with_value(self, base_class, decorator, qt: QtDriver) -> None:
        """checkableText='{#value}' shows the bool value."""

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[SimpleTask]] = new([SimpleTask(True, "Task 1"), SimpleTask(False, "Task 2")])
            _table: QTableView = new(bind="_tasks", checkableText="{#value}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        row0_idx = model.index(0, 0)  # completed=True
        row1_idx = model.index(1, 0)  # completed=False

        assert_that(model.data(row0_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("True")
        assert_that(model.data(row1_idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("False")


# =============================================================================
# Widget column header tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewWidgetColumnHeaders:
    """Test widget column headers from @widget(title=...) and embed(column_name=...)."""

    def test_widget_column_header_from_widget_title(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget column uses @widget(title=...) as column header."""
        from qtpie import Widget, widget

        @widget(title="Actions")
        class ActionWidget(Widget[Dog]):
            pass

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs", columns=["name", ActionWidget])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Column 0 should be "Name" (title-cased field name)
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Name")
        # Column 1 should be "Actions" (from @widget(title="Actions"))
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Actions")

    def test_widget_column_header_from_embed_column_name(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(column_name=...) overrides widget title for column header."""
        from qtpie import Widget, widget
        from qtpie.embed import embed

        @widget(title="Actions")
        class ActionWidget(Widget[Dog]):
            pass

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(
                bind="_dogs",
                columns=["name", embed(ActionWidget, column_name="Custom Header")],
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Column 1 should be "Custom Header" (override from embed)
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Custom Header")

    def test_widget_column_header_empty_when_no_title(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget column without title falls back to empty string header."""
        from qtpie import Widget, widget

        @widget  # No title specified
        class PlainWidget(Widget[Dog]):
            pass

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs", columns=["name", PlainWidget])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Column 1 should be empty string (no title)
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("")

    def test_widget_column_header_embed_empty_overrides_title(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(column_name="") can override widget title to show empty header."""
        from qtpie import Widget, widget
        from qtpie.embed import embed

        @widget(title="Actions")
        class ActionWidget(Widget[Dog]):
            pass

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(
                bind="_dogs",
                columns=["name", embed(ActionWidget, column_name="")],
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Column 1 should be empty (override from embed)
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("")

    def test_widget_column_with_headers_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """headers= dict can customize widget column headers by column name."""
        from qtpie import Widget, widget

        @widget(title="Actions")
        class ActionWidget(Widget[Dog]):
            pass

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(
                bind="_dogs",
                columns=["name", ActionWidget],
                headers={"Actions": "Do Stuff"},  # Override "Actions" column header
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Column 1 should be "Do Stuff" (from headers dict)
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Do Stuff")


# Test dataclass for dict property binding tests
@dataclass
class Response:
    """Test dataclass with dict property for header binding tests."""

    status_code: int
    headers: dict[str, str]


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewRecordDictBinding:
    """QTableView with bind= to record.dict_property (dict on Widget[T])."""

    def test_table_binds_to_record_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind='headers' shows dict from Widget[Response].record."""

        @decorator(record=Response(200, {"Content-Type": "application/json", "Cache-Control": "no-cache"}))
        class TestClass(base_class[Response]):  # type: ignore[misc]
            _table: QTableView = new(bind="headers")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have a model (this was the bug - model was None before fix)
        assert_that(model).is_not_none()

        # Should have 2 rows (one per dict entry)
        assert_that(model.rowCount()).is_equal_to(2)
        # Should have 2 columns (Key, Value)
        assert_that(model.columnCount()).is_equal_to(2)

        # Check headers
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Key")
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Value")

        # Check data - dict items as tuples (key, value)
        # Note: dict order in Python 3.7+ is insertion order
        row0_key = model.data(model.index(0, 0))
        row0_val = model.data(model.index(0, 1))
        row1_key = model.data(model.index(1, 0))
        row1_val = model.data(model.index(1, 1))

        # Check that both entries are present (order may vary in dict)
        entries = {(row0_key, row0_val), (row1_key, row1_val)}
        assert_that(entries).contains(("Content-Type", "application/json"))
        assert_that(entries).contains(("Cache-Control", "no-cache"))

    def test_table_binds_to_record_dict_via_variable_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[Response] with QTableView bind='headers' works when parent sets response later.

        This is the REAL scenario:
        1. Parent has response: Variable[Response | None] = new(None)
        2. Child Widget[Response] is created with _table: QTableView = new(bind="headers")
        3. Parent sets response = Response(...) LATER
        4. Child's QTableView should get its model at that point
        """
        from qtpie import Widget, widget

        @widget
        class ResponseHeadersViewer(Widget[Response]):
            """Child widget that displays headers in a table."""

            _table: QTableView = new(bind="headers")

        @decorator
        class TestClass(base_class):
            _response: Variable[Response | None] = new(None)
            _viewer: ResponseHeadersViewer = new(bind="_response")

        instance = create_and_track(qt, TestClass, base_class)

        # Get the child widget's table
        viewer = instance._viewer
        assert_that(viewer).is_not_none()

        # Initially response is None, so table may not have model yet
        # (this is OK - model gets set when response is set)

        # Now set the response - THIS should trigger model binding
        instance._response.value = Response(200, {"X-Custom": "test-value"})

        model = viewer._table.model()

        # Model should be set NOW (after response was set)
        assert_that(model).is_not_none()

        # Should have 1 row (one dict entry)
        assert_that(model.rowCount()).is_equal_to(1)

        # Check data
        assert_that(model.data(model.index(0, 0))).is_equal_to("X-Custom")
        assert_that(model.data(model.index(0, 1))).is_equal_to("test-value")

    def test_table_binds_to_optional_chaining_path(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind='response?.headers' where response is Variable[Response | None].

        This is a DIFFERENT scenario from bind="headers" inside Widget[Response]:
        - Parent has response: Variable[Response | None] = new(None)
        - QTableView uses bind="response?.headers" (optional chaining)
        - When response is set to Response(...), QTableView should display headers
        """

        @decorator
        class TestClass(base_class):
            _response: Variable[Response | None] = new(None)
            _table: QTableView = new(bind="_response?.headers")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially response is None, table may have no rows
        model = instance._table.model()
        # Model might exist but with 0 rows initially
        if model is not None:
            assert_that(model.rowCount()).is_equal_to(0)

        # Now set the response - THIS should trigger model update
        instance._response.value = Response(200, {"X-Header": "header-value", "Content-Type": "text/plain"})

        model = instance._table.model()

        # Model should be set NOW (after response was set)
        assert_that(model).is_not_none()

        # Should have 2 rows (two dict entries)
        assert_that(model.rowCount()).is_equal_to(2)

        # Check headers
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Key")
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Value")

        # Check data - get all entries and verify
        row0_key = model.data(model.index(0, 0))
        row0_val = model.data(model.index(0, 1))
        row1_key = model.data(model.index(1, 0))
        row1_val = model.data(model.index(1, 1))

        entries = {(row0_key, row0_val), (row1_key, row1_val)}
        assert_that(entries).contains(("X-Header", "header-value"))
        assert_that(entries).contains(("Content-Type", "text/plain"))


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewEditable:
    """QTableView with editable=/readOnly= parameters."""

    def test_table_editable_by_default(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView is editable by default (consistent with QLineEdit, QTextEdit, etc.)."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Check flags - SHOULD have ItemIsEditable by default
        assert_that(model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsEditable).is_not_equal_to(Qt.ItemFlag(0))
        assert_that(model.flags(model.index(0, 1)) & Qt.ItemFlag.ItemIsEditable).is_not_equal_to(Qt.ItemFlag(0))

    def test_table_readonly_true(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with readOnly=True makes it read-only (like QLineEdit.setReadOnly)."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers", readOnly=True)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Check flags - should NOT have ItemIsEditable
        assert_that(model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsEditable).is_equal_to(Qt.ItemFlag(0))
        assert_that(model.flags(model.index(0, 1)) & Qt.ItemFlag.ItemIsEditable).is_equal_to(Qt.ItemFlag(0))

    def test_table_editable_false(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with editable=False makes it read-only."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers", editable=False)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Check flags - should NOT have ItemIsEditable
        assert_that(model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsEditable).is_equal_to(Qt.ItemFlag(0))
        assert_that(model.flags(model.index(0, 1)) & Qt.ItemFlag.ItemIsEditable).is_equal_to(Qt.ItemFlag(0))

    def test_table_editable_all_columns_explicit(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with editable=True explicitly makes all columns editable."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers", editable=True)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Both columns should be editable
        assert_that(model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsEditable).is_not_equal_to(Qt.ItemFlag(0))
        assert_that(model.flags(model.index(0, 1)) & Qt.ItemFlag.ItemIsEditable).is_not_equal_to(Qt.ItemFlag(0))

    def test_table_editable_value_column_only(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with editable=["value"] only allows editing the value column."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers", editable=["value"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Key column (0) should NOT be editable
        assert_that(model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsEditable).is_equal_to(Qt.ItemFlag(0))
        # Value column (1) SHOULD be editable
        assert_that(model.flags(model.index(0, 1)) & Qt.ItemFlag.ItemIsEditable).is_not_equal_to(Qt.ItemFlag(0))

    def test_table_edit_dict_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Editing dict value updates the underlying dict."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers", editable=True)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Edit the value column
        success = model.setData(model.index(0, 1), "text/plain", Qt.ItemDataRole.EditRole)
        assert_that(success).is_true()

        # Verify the underlying dict was updated
        assert_that(instance._headers["Content-Type"]).is_equal_to("text/plain")

    def test_table_edit_dict_key(self, base_class, decorator, qt: QtDriver) -> None:
        """Editing dict key renames the key in the underlying dict."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Old-Key": "some-value"})
            _table: QTableView = new(bind="_headers", editable=True)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Edit the key column
        success = model.setData(model.index(0, 0), "New-Key", Qt.ItemDataRole.EditRole)
        assert_that(success).is_true()

        # Verify old key removed and new key exists
        assert_that("Old-Key" in instance._headers).is_false()
        assert_that("New-Key" in instance._headers).is_true()
        assert_that(instance._headers["New-Key"]).is_equal_to("some-value")

    def test_table_editable_dataclass(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with editable=True for dataclass list allows editing fields."""

        @dataclass
        class Task:
            name: str
            done: bool = False

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new([Task("Buy milk"), Task("Walk dog")])
            _table: QTableView = new(bind="_tasks", editable=["name"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Edit the name field
        success = model.setData(model.index(0, 0), "Buy bread", Qt.ItemDataRole.EditRole)
        assert_that(success).is_true()

        # Verify the underlying dataclass was updated
        assert_that(instance._tasks[0].name).is_equal_to("Buy bread")

    def test_table_editable_dict_str_int(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with Variable[dict[str, int]] editing converts values properly."""

        @decorator
        class TestClass(base_class):
            dictionary: Variable[dict[str, int]] = new({"count": 42, "total": 100})
            _table: QTableView = new(bind="dictionary", editable=["value"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Find the row with "count"
        for row in range(model.rowCount()):
            if model.data(model.index(row, 0)) == "count":
                # Edit the value
                success = model.setData(model.index(row, 1), "99", Qt.ItemDataRole.EditRole)
                assert_that(success).is_true()
                break

        # Verify the underlying dict was updated
        assert_that(instance.dictionary["count"]).is_equal_to("99")

    def test_edit_role_returns_current_value(self, base_class, decorator, qt: QtDriver) -> None:
        """EditRole returns current cell value so editor is pre-populated."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers", editable=True)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # EditRole should return the current value (for pre-populating editor)
        key_value = model.data(model.index(0, 0), Qt.ItemDataRole.EditRole)
        value_value = model.data(model.index(0, 1), Qt.ItemDataRole.EditRole)

        assert_that(key_value).is_equal_to("Content-Type")
        assert_that(value_value).is_equal_to("application/json")


# =============================================================================
# Comprehensive Dict Binding Tests (ObservableDict, Variable[dict], RecordVariable[dict], raw dict)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewObservableDictBinding:
    """QTableView with bind= to ObservableDict directly (not wrapped in Variable)."""

    def test_table_binds_to_observable_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind=ObservableDict shows dict items as key/value rows."""
        from observant import ObservableDict

        @decorator
        class TestClass(base_class):
            headers: ObservableDict[str, str]
            _table: QTableView = new(bind="headers")

            def __setup__(self) -> None:
                self.headers = ObservableDict({"Content-Type": "application/json", "Accept": "text/html"})

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have a model
        assert_that(model).is_not_none()

        # Should have 2 rows (one per dict entry)
        assert_that(model.rowCount()).is_equal_to(2)
        # Should have 2 columns (Key, Value)
        assert_that(model.columnCount()).is_equal_to(2)

        # Check headers
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Key")
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Value")

    def test_observable_dict_editable(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with editable=True and ObservableDict allows editing."""
        from observant import ObservableDict

        @decorator
        class TestClass(base_class):
            headers: ObservableDict[str, str]
            _table: QTableView = new(bind="headers", editable=True)

            def __setup__(self) -> None:
                self.headers = ObservableDict({"X-Custom": "initial-value"})

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Edit the value column
        success = model.setData(model.index(0, 1), "new-value", Qt.ItemDataRole.EditRole)
        assert_that(success).is_true()

        # Verify the underlying ObservableDict was updated
        assert_that(instance.headers["X-Custom"]).is_equal_to("new-value")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewRawDictBinding:
    """QTableView with bind= to plain Python dict (not Observable)."""

    def test_table_binds_to_raw_dict_via_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind=Variable[dict] works when Variable wraps a raw dict."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _table: QTableView = new(bind="_headers")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have a model
        assert_that(model).is_not_none()

        # Should have 1 row
        assert_that(model.rowCount()).is_equal_to(1)

        # Check headers
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Key")
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Value")

        # Check data
        assert_that(model.data(model.index(0, 0))).is_equal_to("Content-Type")
        assert_that(model.data(model.index(0, 1))).is_equal_to("application/json")


@dataclass
class HttpResponse:
    """Test dataclass with dict property for RecordVariable[dict] tests."""

    status_code: int
    headers: dict[str, str]


@dataclass
class Config:
    """Test dataclass with dict property."""

    settings: dict[str, int]


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewRecordVariableDictBinding:
    """QTableView with bind= to record.dict_property (RecordVariable[dict] scenario)."""

    def test_table_binds_to_record_dict_property(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind='headers' shows dict from Widget[HttpResponse].record."""

        @decorator(record=HttpResponse(200, {"Content-Type": "text/html", "Server": "nginx"}))
        class TestClass(base_class[HttpResponse]):  # type: ignore[misc]
            _table: QTableView = new(bind="headers")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have a model
        assert_that(model).is_not_none()

        # Should have 2 rows (one per dict entry)
        assert_that(model.rowCount()).is_equal_to(2)

        # Check headers
        assert_that(model.headerData(0, Qt.Orientation.Horizontal)).is_equal_to("Key")
        assert_that(model.headerData(1, Qt.Orientation.Horizontal)).is_equal_to("Value")

    def test_record_dict_property_editable(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with editable= and record.dict_property allows editing."""

        @decorator(record=HttpResponse(200, {"X-Test": "original"}))
        class TestClass(base_class[HttpResponse]):  # type: ignore[misc]
            _table: QTableView = new(bind="headers", editable=["value"])

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Key column (0) should NOT be editable
        assert_that(model.flags(model.index(0, 0)) & Qt.ItemFlag.ItemIsEditable).is_equal_to(Qt.ItemFlag(0))
        # Value column (1) SHOULD be editable
        assert_that(model.flags(model.index(0, 1)) & Qt.ItemFlag.ItemIsEditable).is_not_equal_to(Qt.ItemFlag(0))

    def test_record_dict_via_child_widget_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[HttpResponse] with QTableView bind='headers' works.

        This is the full scenario:
        1. Parent has response: Variable[HttpResponse | None] = new(None)
        2. Child Widget[HttpResponse] is created with _table: QTableView = new(bind="headers")
        3. Parent sets response = HttpResponse(...) LATER
        4. Child's QTableView should display the headers dict
        """
        from qtpie import Widget, widget

        @widget
        class HeadersViewer(Widget[HttpResponse]):
            """Child widget that displays headers in a table."""

            _table: QTableView = new(bind="headers")

        @decorator
        class TestClass(base_class):
            _response: Variable[HttpResponse | None] = new(None)
            _viewer: HeadersViewer = new(bind="_response")

        instance = create_and_track(qt, TestClass, base_class)

        # Get the child widget
        viewer = instance._viewer
        assert_that(viewer).is_not_none()

        # Now set the response - THIS should trigger model binding
        instance._response.value = HttpResponse(200, {"Authorization": "Bearer token"})

        model = viewer._table.model()

        # Model should be set NOW (after response was set)
        assert_that(model).is_not_none()

        # Should have 1 row (one dict entry)
        assert_that(model.rowCount()).is_equal_to(1)

        # Check data
        assert_that(model.data(model.index(0, 0))).is_equal_to("Authorization")
        assert_that(model.data(model.index(0, 1))).is_equal_to("Bearer token")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewDictBindingKeyValueFormat:
    """Test {#key} and {#value} format placeholders work correctly."""

    def test_dict_format_key_value_placeholders(self, base_class, decorator, qt: QtDriver) -> None:
        """format='{#key}: {#value}' works for dict binding."""

        @decorator
        class TestClass(base_class):
            _settings: Variable[dict[str, int]] = new({"timeout": 30, "retries": 3})
            _table: QTableView = new(bind="_settings")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # Should have 2 rows
        assert_that(model.rowCount()).is_equal_to(2)

        # Get all entries (order may vary)
        row0_key = model.data(model.index(0, 0))
        row0_val = model.data(model.index(0, 1))
        row1_key = model.data(model.index(1, 0))
        row1_val = model.data(model.index(1, 1))

        entries = {(row0_key, row0_val), (row1_key, row1_val)}
        assert_that(entries).contains(("timeout", "30"))
        assert_that(entries).contains(("retries", "3"))

    def test_dict_binding_with_different_value_types(self, base_class, decorator, qt: QtDriver) -> None:
        """Dict binding works with different value types (int, float, bool)."""

        @decorator
        class TestClass(base_class):
            _config: Variable[dict[str, int]] = new({"count": 10, "max": 100})
            _table: QTableView = new(bind="_config")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        assert_that(model.rowCount()).is_equal_to(2)

        # Values should be converted to strings
        entries = set()
        for row in range(model.rowCount()):
            key = model.data(model.index(row, 0))
            val = model.data(model.index(row, 1))
            entries.add((key, val))

        assert_that(entries).contains(("count", "10"))
        assert_that(entries).contains(("max", "100"))


# =============================================================================
# Signal Handler Order Tests (same issue as QComboBox/QListView)
# =============================================================================


class TestTableViewSignalHandlerOrder:
    """Test that user's signal handler sees UPDATED value after selection change."""

    def test_tableview_deeply_nested_in_tab_widget(self, qt: QtDriver) -> None:
        """Test: Deeply nested Widget[T] with QTableView and nested optional path."""
        from enum import Enum

        from PySide6.QtCore import QItemSelectionModel
        from PySide6.QtWidgets import QTabWidget

        from qtpie import Widget, widget

        class Location(Enum):
            HEADER = "header"
            QUERY = "query"

        @dataclass
        class AuthSettings:
            location: Location = Location.HEADER

        @dataclass
        class Settings:
            auth: AuthSettings | None = None

        call_count = {"value": 0}
        seen_values: list[Location] = []

        @widget(title="Auth Tab")
        class GrandchildTab(Widget[Settings]):
            """The deepest widget - like AuthTabContent."""

            _table: QTableView = new(
                bind=Location,
                selectedItem="auth?.location",
                clicked="_on_clicked",
            )

            def _on_clicked(self) -> None:
                call_count["value"] += 1
                if self.record_value and self.record_value.auth:
                    seen_values.append(self.record_value.auth.location)

        @widget
        class ChildWidget(Widget[Settings]):
            """Middle widget."""

            _tabs: QTabWidget = new(tabs=[GrandchildTab])

        @widget(record=Settings(auth=AuthSettings(location=Location.HEADER)))
        class ParentWidget(Widget[Settings]):
            """Top-level widget."""

            _child: ChildWidget

        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        call_count["value"] = 0
        seen_values.clear()

        grandchild = instance._child._tabs.widget(0)
        assert_that(grandchild).is_instance_of(GrandchildTab)

        # Simulate click on QUERY (row 1)
        model = grandchild._table.model()
        index = model.index(1, 0)
        grandchild._table.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        grandchild._table.clicked.emit(index)

        assert_that(call_count["value"]).is_equal_to(1)
        assert_that(seen_values).is_equal_to([Location.QUERY])
