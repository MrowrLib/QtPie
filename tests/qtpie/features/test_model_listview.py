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
"""Tests for QListView model binding with bind=.

Tests that QListView bound to Variable[list] uses ReactiveListModel
and updates reactively when the list changes, with proper selection bindings.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QListView

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import RECORD_CLASS_TYPES, WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for format= tests."""

    name: str
    age: int


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewModelBinding:
    """QListView with bind= to Variable[list]."""

    def test_list_shows_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with bind= shows Variable[list] items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _list: QListView = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        assert_that(model.rowCount()).is_equal_to(3)
        assert_that(model.data(model.index(0, 0))).is_equal_to("A")
        assert_that(model.data(model.index(1, 0))).is_equal_to("B")
        assert_that(model.data(model.index(2, 0))).is_equal_to("C")

    def test_list_updates_on_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to list updates QListView."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A"])
            _list: QListView = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(1)

        instance._items.append("B")
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(1, 0))).is_equal_to("B")

    def test_list_updates_on_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from list updates QListView."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _list: QListView = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(3)

        instance._items.remove("B")
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("A")
        assert_that(model.data(model.index(1, 0))).is_equal_to("C")

    def test_list_updates_on_replace(self, base_class, decorator, qt: QtDriver) -> None:
        """Replacing item in list updates QListView."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B"])
            _list: QListView = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        instance._items[0] = "Z"
        assert_that(model.data(model.index(0, 0))).is_equal_to("Z")

    def test_list_updates_on_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list updates QListView."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _list: QListView = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(3)

        instance._items.clear()
        assert_that(model.rowCount()).is_equal_to(0)

    def test_list_with_format(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with format= customizes item display."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _list: QListView = new(bind="_dogs", format="{name} ({age})")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido (3)")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Rex (5)")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewSelectionBinding:
    """QListView selection bindings with selectedIndex= and selectedItem=."""

    def test_list_selected_index_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with selectedIndex= binds to row index Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int]  # Bare annotation
            _list: QListView = new(bind="_items", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - syncs from widget (may be 0 or -1 depending on selection)
        # After sync, should be 0 (first row)
        assert_that(instance._idx.value).is_equal_to(0)

        # Change selection via Variable
        instance._idx.value = 2
        current_idx = instance._list.selectionModel().currentIndex()
        assert_that(current_idx.row()).is_equal_to(2)

    def test_list_selected_item_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with selectedItem= binds to actual item Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _dog: Variable[Dog]  # Bare annotation
            _list: QListView = new(bind="_dogs", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - first item selected (synced from widget)
        assert_that(instance._dog.value).is_not_none()
        assert_that(instance._dog.value.name).is_equal_to("Fido")

    def test_list_both_bindings(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with both selectedIndex= and selectedItem= keeps them in sync."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _idx: Variable[int]  # Bare annotation
            _dog: Variable[Dog]  # Bare annotation
            _list: QListView = new(bind="_dogs", selectedIndex="_idx", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Both should sync on init
        assert_that(instance._idx.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("Fido")

        # Change index - item should update
        instance._idx.value = 1
        assert_that(instance._dog.value.name).is_equal_to("Rex")

    def test_list_with_format_and_selection(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with format= and selection bindings work together."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _idx: Variable[int]  # Bare annotation
            _dog: Variable[Dog]  # Bare annotation
            _list: QListView = new(bind="_dogs", format="{name} ({age})", selectedIndex="_idx", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Format works
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido (3)")

        # Selection bindings work
        instance._idx.value = 1
        assert_that(instance._dog.value.name).is_equal_to("Rex")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewMultiSelectionBinding:
    """QListView multi-selection bindings with selectedIndexes= and selectedItems=."""

    def test_list_selected_indexes_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with selectedIndexes= binds to list of row indices Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _indexes: Variable[list[int]]  # Bare annotation
            _list: QListView = new(bind="_items", selectedIndexes="_indexes")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - empty or current selection
        assert_that(instance._indexes.value).is_instance_of(list)

    def test_list_selected_items_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with selectedItems= binds to list of actual items Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Spot", 2)])
            _selected: Variable[list[Dog]]  # Bare annotation
            _list: QListView = new(bind="_dogs", selectedItems="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - empty or current selection
        assert_that(instance._selected.value).is_instance_of(list)

    def test_list_both_multi_bindings(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with both selectedIndexes= and selectedItems= keeps them in sync."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Spot", 2)])
            _indexes: Variable[list[int]]  # Bare annotation
            _selected: Variable[list[Dog]]  # Bare annotation
            _list: QListView = new(bind="_dogs", selectedIndexes="_indexes", selectedItems="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Both should be lists
        assert_that(instance._indexes.value).is_instance_of(list)
        assert_that(instance._selected.value).is_instance_of(list)

    def test_list_single_and_multi_bindings_together(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with both single and multi selection bindings work together."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Spot", 2)])
            _idx: Variable[int]  # Single current index
            _dog: Variable[Dog]  # Single current item
            _indexes: Variable[list[int]]  # Multi selected indexes
            _selected: Variable[list[Dog]]  # Multi selected items
            _list: QListView = new(
                bind="_dogs",
                selectedIndex="_idx",
                selectedItem="_dog",
                selectedIndexes="_indexes",
                selectedItems="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Single selection bindings work
        assert_that(instance._idx.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("Fido")

        # Multi selection bindings are lists
        assert_that(instance._indexes.value).is_instance_of(list)
        assert_that(instance._selected.value).is_instance_of(list)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewSelectionParamsNotStolen:
    """Ensure selection kwargs pass to constructor when widget is not a model widget."""

    def test_listview_kwargs_pass_to_non_model_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView-related kwargs pass to constructor for non-model widgets."""
        from PySide6.QtWidgets import QWidget

        class CustomWidget(QWidget):
            def __init__(
                self,
                parent: QWidget | None = None,
                selectedIndex: int = -1,
                selectedItem: str | None = None,
                selectedIndexes: list[int] | None = None,
                selectedItems: list[str] | None = None,
                selectedRow: int = -1,
                selectedRows: list[int] | None = None,
                format: str | None = None,  # noqa: A002
            ) -> None:
                super().__init__(parent)
                self.my_index = selectedIndex
                self.my_item = selectedItem
                self.my_indexes = selectedIndexes
                self.my_items = selectedItems
                self.my_row = selectedRow
                self.my_rows = selectedRows
                self.my_format = format

        @decorator
        class TestClass(base_class):
            _custom: CustomWidget = new(
                bind="x",
                selectedIndex=5,
                selectedItem="test_item",
                selectedIndexes=[0, 2, 4],
                selectedItems=["a", "b"],
                selectedRow=3,
                selectedRows=[1, 3, 5],
                format="{name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._custom.my_index).is_equal_to(5)
        assert_that(instance._custom.my_item).is_equal_to("test_item")
        assert_that(instance._custom.my_indexes).is_equal_to([0, 2, 4])
        assert_that(instance._custom.my_items).is_equal_to(["a", "b"])
        assert_that(instance._custom.my_row).is_equal_to(3)
        assert_that(instance._custom.my_rows).is_equal_to([1, 3, 5])
        assert_that(instance._custom.my_format).is_equal_to("{name}")


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestListViewRecordBindingWithLocalVariable:
    """Test QListView bound to record field with local Variable for selection.

    This tests the scenario where:
    - bind="dogs" should resolve to record.dogs (the list to display)
    - selectedItems="_dogs" should resolve to local _dogs Variable (selection state)

    These two should NOT conflict even though they share the same base name.
    """

    def test_record_dogs_with_local_dogs_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='dogs' resolves to record.dogs, selectedItems='_dogs' resolves to local _dogs."""

        @dataclass
        class DogsContainer:
            dogs: list[Dog]

        record = DogsContainer(dogs=[Dog("Fido", 3), Dog("Rex", 5), Dog("Buddy", 2)])

        @decorator(record=record)
        class TestClass(base_class[DogsContainer]):  # type: ignore[misc]
            _dogs: Variable[list[Dog]]
            _list: QListView = new(bind="dogs", format="{name}", selectedItems="_dogs")

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()

        # Model should have 3 rows from record.dogs
        assert_that(model.rowCount()).is_equal_to(3)

        # Check the data comes from record.dogs
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Rex")
        assert_that(model.data(model.index(2, 0))).is_equal_to("Buddy")

        # _dogs Variable should be a list (for multi-selection)
        assert_that(instance._dogs.value).is_instance_of(list)


@dataclass
class Task:
    """Task dataclass for checkbox testing."""

    title: str
    done: bool = False


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewCheckable:
    """Test QListView with checkable= for checkbox support."""

    def test_checkable_field_shows_checkbox(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='field_name' enables checkboxes on list items."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new(
                [
                    Task("Task A", done=True),
                    Task("Task B", done=False),
                ]
            )
            _list: QListView = new(bind="_tasks", checkable="done")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Check that ItemIsUserCheckable flag is set
        idx_a = model.index(0, 0)
        idx_b = model.index(1, 0)
        assert_that(model.flags(idx_a) & Qt.ItemFlag.ItemIsUserCheckable).is_true()
        assert_that(model.flags(idx_b) & Qt.ItemFlag.ItemIsUserCheckable).is_true()

        # Check states match the bool field
        assert_that(model.data(idx_a, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        assert_that(model.data(idx_b, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

    def test_checkable_field_two_way_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='field_name' provides two-way binding to bool field."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new(
                [
                    Task("Task A", done=False),
                ]
            )
            _list: QListView = new(bind="_tasks", checkable="done")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()
        idx = model.index(0, 0)

        # Initially unchecked
        assert_that(instance._tasks.value[0].done).is_false()
        assert_that(model.data(idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

        # Set via model (simulating checkbox click)
        model.setData(idx, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole)

        # Underlying data should be updated
        assert_that(instance._tasks.value[0].done).is_true()

    def test_checkable_expression_read_only(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='{expr}' creates read-only checkbox from expression."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new(
                [
                    Task("A long task title here", done=False),
                    Task("Short", done=False),
                ]
            )
            _list: QListView = new(bind="_tasks", checkable="{len(title) > 10}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        idx_long = model.index(0, 0)
        idx_short = model.index(1, 0)

        # Long title -> checked
        assert_that(model.data(idx_long, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        # Short title -> unchecked
        assert_that(model.data(idx_short, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

        # Expression-based checkable should NOT allow setData
        result = model.setData(idx_short, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole)
        assert_that(result).is_false()

    def test_checkable_expression_evaluates(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='{expr}' correctly evaluates expression per item."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new(
                [
                    Task("Done task", done=True),
                    Task("Not done", done=False),
                ]
            )
            # Expression that evaluates to the 'done' field value
            _list: QListView = new(bind="_tasks", checkable="{done}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        idx_done = model.index(0, 0)
        idx_not_done = model.index(1, 0)

        assert_that(model.data(idx_done, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        assert_that(model.data(idx_not_done, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

    def test_checkable_false_no_checkbox(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable=False explicitly disables checkboxes."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new(
                [
                    Task("Task A", done=True),
                ]
            )
            _list: QListView = new(bind="_tasks", checkable=False)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        idx = model.index(0, 0)

        # No checkbox flag
        assert_that(model.flags(idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()
        # No check state
        assert_that(model.data(idx, Qt.ItemDataRole.CheckStateRole)).is_none()

    def test_checkable_default_no_checkbox(self, base_class, decorator, qt: QtDriver) -> None:
        """No checkable= parameter means no checkboxes (default)."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new(
                [
                    Task("Task A", done=True),
                ]
            )
            _list: QListView = new(bind="_tasks")  # No checkable=

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        idx = model.index(0, 0)

        # No checkbox flag
        assert_that(model.flags(idx) & Qt.ItemFlag.ItemIsUserCheckable).is_false()
        # No check state
        assert_that(model.data(idx, Qt.ItemDataRole.CheckStateRole)).is_none()

    def test_checkable_with_format(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable= and format= work together independently."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[Task]] = new(
                [
                    Task("Task A", done=True),
                ]
            )
            _list: QListView = new(bind="_tasks", format="[{title}]", checkable="done")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        idx = model.index(0, 0)

        # Format affects display
        assert_that(model.data(idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("[Task A]")
        # Checkable affects check state
        assert_that(model.data(idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)


@dataclass
class Response:
    """Test dataclass with dict property for dict binding tests."""

    status_code: int
    headers: dict[str, str]


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewDictBinding:
    """QListView with bind= to Variable[dict]."""

    def test_list_binds_to_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with bind=Variable[dict] shows dict items."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json", "Accept": "text/html"})
            _list: QListView = new(bind="_headers")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Should have 2 rows (one per dict entry)
        assert_that(model.rowCount()).is_equal_to(2)

    def test_list_dict_with_format(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with bind=dict and format='{#key}: {#value}' formats properly."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _list: QListView = new(bind="_headers", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Should show formatted key: value
        assert_that(model.data(model.index(0, 0))).is_equal_to("Content-Type: application/json")

    def test_list_dict_optional_chaining(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with bind='response?.headers' where response is Variable[Response | None]."""

        @decorator
        class TestClass(base_class):
            _response: Variable[Response | None] = new(None)
            _list: QListView = new(bind="_response?.headers", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Initially response is None, list should be empty
        assert_that(model.rowCount()).is_equal_to(0)

        # Set response - list should update
        instance._response.value = Response(200, {"X-Custom": "test-value"})

        assert_that(model.rowCount()).is_equal_to(1)
        assert_that(model.data(model.index(0, 0))).is_equal_to("X-Custom: test-value")
