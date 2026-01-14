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
