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

from .conftest import WIDGET_CLASS_TYPES, create_and_track


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


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewRecordBindingWithLocalVariable:
    """Test QListView bound to record field with local Variable for selection.

    This tests the scenario where:
    - bind="dogs" should resolve to record.dogs (the list to display)
    - selectedItems="_dogs" should resolve to local _dogs Variable (selection state)

    These two should NOT conflict even though they share the same base name.
    """

    def test_record_dogs_with_local_dogs_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """bind='dogs' resolves to record.dogs, selectedItems='_dogs' resolves to local _dogs."""
        from dataclasses import dataclass

        from qtpie import Widget

        @dataclass
        class DogsContainer:
            dogs: list[Dog]

        if base_class.__name__ == "Widget":
            # Widget with record type - must use Widget[DogsContainer] for record type inference
            @decorator(record=DogsContainer(dogs=[Dog("Fido", 3), Dog("Rex", 5), Dog("Buddy", 2)]))
            class TestClass(Widget[DogsContainer]):
                # Local Variable for storing selected items - NOT the same as record.dogs
                _dogs: Variable[list[Dog]]
                # bind="dogs" should use record.dogs, selectedItems uses local _dogs
                _list: QListView = new(bind="dogs", format="{name}", selectedItems="_dogs")

            instance = create_and_track(qt, TestClass, base_class)
        else:
            # Skip non-Widget base classes for this test
            pytest.skip("Record binding only works with Widget")
            return

        model = instance._list.model()

        # Model should have 3 rows from record.dogs
        assert_that(model.rowCount()).is_equal_to(3)

        # Check the data comes from record.dogs
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Rex")
        assert_that(model.data(model.index(2, 0))).is_equal_to("Buddy")

        # _dogs Variable should be a list (for multi-selection)
        assert_that(instance._dogs.value).is_instance_of(list)
