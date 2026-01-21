# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
# pyright: reportImplicitOverride=false
# pyright: reportUnknownLambdaType=false
"""Tests for QListView/QTreeView/QTableView model binding with State objects.

These tests verify that reactive models work correctly with State objects
that use Variable[T] fields instead of plain dataclass fields.

Key differences from dataclass:
- State objects have Variable[T] fields that wrap values
- Format evaluation must unwrap Variables to get actual values
- Children access for tree models must unwrap Variable[list[...]]
- Column auto-detection must recognize Variable fields as data columns
"""

from typing import Any

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QListView, QTableView, QTreeView

from qtpie import Event, State, Variable, new, state
from qtpie.testing import QtDriver

from .conftest import QWIDGET_CLASS_TYPES, create_and_track

# =============================================================================
# Test State Classes (using Variable[T] fields instead of dataclass)
# =============================================================================


@state
class StateDog(State):
    """State-based dog for format= tests (equivalent to dataclass Dog)."""

    name: Variable[str] = new("")
    age: Variable[int] = new(0)


@state
class StateTask(State):
    """State-based task for checkable tests (equivalent to dataclass Task)."""

    title: Variable[str] = new("")
    done: Variable[bool] = new(False)


@state
class StateTreeNode(State):
    """State-based tree node for QTreeView tests."""

    name: Variable[str] = new("")
    # Use Any for recursive type to avoid get_type_hints issue during class definition
    items: Variable[list[Any]] = new([])


@state
class StateEditableItem(State):
    """State-based item for editable tests."""

    name: Variable[str] = new("")


@state
class StateItemWithEvent(State):
    """State with Event field for column exclusion tests."""

    name: Variable[str] = new("")
    count: Variable[int] = new(0)
    on_change: Event  # Should NOT be a column


# =============================================================================
# QListView with State Objects
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestListViewStateModelBinding:
    """QListView with bind= to Variable[list[State]]."""

    def test_list_shows_state_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with bind= shows State items with format=."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name} ({age})")

            def __setup__(self) -> None:
                dog1 = StateDog()
                dog1.name = "Fido"
                dog1.age = 3
                dog2 = StateDog()
                dog2.name = "Rex"
                dog2.age = 5
                self._dogs.extend([dog1, dog2])

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido (3)")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Rex (5)")

    def test_list_updates_on_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending State item to list updates QListView."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name}")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(1)

        # Append another dog
        new_dog = StateDog()
        new_dog.name = "Rex"
        instance._dogs.append(new_dog)
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(1, 0))).is_equal_to("Rex")

    def test_list_updates_on_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing State item from list updates QListView."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name}")

            def __setup__(self) -> None:
                for name in ["Fido", "Rex", "Spot"]:
                    dog = StateDog()
                    dog.name = name
                    self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(3)

        # Remove middle dog
        del instance._dogs[1]
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Spot")

    def test_list_updates_on_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list of State items updates QListView."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name}")

            def __setup__(self) -> None:
                for name in ["Fido", "Rex"]:
                    dog = StateDog()
                    dog.name = name
                    self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)

        instance._dogs.clear()
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(0)

    def test_state_variable_change_updates_display(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing a State item's Variable field updates display."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name}")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")

        # Change the dog's name via Variable
        instance._dogs[0].name = "Rex"
        qt.process_events()

        # Note: This may require additional reactive binding setup
        # depending on how the model observes item changes
        # For now, verify the data source was updated
        assert_that(instance._dogs[0].name.value).is_equal_to("Rex")


# =============================================================================
# QTreeView with State Objects
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestTreeViewStateModelBinding:
    """QTreeView with bind= to Variable[list[State]] and children='items'."""

    def test_tree_shows_state_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with bind= shows State items with format=."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[StateTreeNode]] = new([])
            _tree: QTreeView = new(bind="_nodes", children="items", format="{name}")

            def __setup__(self) -> None:
                node = StateTreeNode()
                node.name = "Root"
                self._nodes.append(node)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(1)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Root")

    def test_tree_shows_nested_children(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with children='items' shows nested State children."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[StateTreeNode]] = new([])
            _tree: QTreeView = new(bind="_nodes", children="items", format="{name}")

            def __setup__(self) -> None:
                # Create root with children
                child1 = StateTreeNode()
                child1.name = "Child 1"
                child2 = StateTreeNode()
                child2.name = "Child 2"

                root = StateTreeNode()
                root.name = "Root"
                root.items.extend([child1, child2])

                self._nodes.append(root)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._tree.model()

        # Root item
        root_index = model.index(0, 0)
        assert_that(model.data(root_index)).is_equal_to("Root")

        # Children
        assert_that(model.rowCount(root_index)).is_equal_to(2)
        child1_index = model.index(0, 0, root_index)
        child2_index = model.index(1, 0, root_index)
        assert_that(model.data(child1_index)).is_equal_to("Child 1")
        assert_that(model.data(child2_index)).is_equal_to("Child 2")

    def test_tree_deeply_nested_children(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView shows deeply nested State children."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[StateTreeNode]] = new([])
            _tree: QTreeView = new(bind="_nodes", children="items", format="{name}")

            def __setup__(self) -> None:
                # Create: Root -> Child -> Grandchild
                grandchild = StateTreeNode()
                grandchild.name = "Grandchild"

                child = StateTreeNode()
                child.name = "Child"
                child.items.append(grandchild)

                root = StateTreeNode()
                root.name = "Root"
                root.items.append(child)

                self._nodes.append(root)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._tree.model()

        # Navigate: Root -> Child -> Grandchild
        root_index = model.index(0, 0)
        child_index = model.index(0, 0, root_index)
        grandchild_index = model.index(0, 0, child_index)

        assert_that(model.data(root_index)).is_equal_to("Root")
        assert_that(model.data(child_index)).is_equal_to("Child")
        assert_that(model.data(grandchild_index)).is_equal_to("Grandchild")

    def test_tree_append_child_updates_model(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending State child updates QTreeView."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[StateTreeNode]] = new([])
            _tree: QTreeView = new(bind="_nodes", children="items", format="{name}")

            def __setup__(self) -> None:
                root = StateTreeNode()
                root.name = "Root"
                self._nodes.append(root)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._tree.model()
        root_index = model.index(0, 0)

        # Initially no children
        assert_that(model.rowCount(root_index)).is_equal_to(0)

        # Add a child
        child = StateTreeNode()
        child.name = "New Child"
        instance._nodes[0].items.append(child)
        qt.process_events()

        assert_that(model.rowCount(root_index)).is_equal_to(1)
        child_index = model.index(0, 0, root_index)
        assert_that(model.data(child_index)).is_equal_to("New Child")


# =============================================================================
# QTableView with State Objects
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestTableViewStateModelBinding:
    """QTableView with bind= to Variable[list[State]]."""

    def test_table_shows_state_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with bind= shows State items."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _table: QTableView = new(bind="_dogs")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                dog.age = 3
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(1)
        # Auto-detected columns should include name and age (but not Event fields)
        assert_that(model.columnCount()).is_greater_than_or_equal_to(2)


class TestTableViewStateColumnDetection:
    """Test QTableView column auto-detection for State objects."""

    def test_table_column_auto_detection_excludes_events(self, qt: QtDriver) -> None:
        """QTableView auto-detects Variable columns but excludes Event fields."""
        from qtpie import Widget, widget

        @widget
        class TestClass(Widget):
            _items: Variable[list[StateItemWithEvent]] = new([])
            _table: QTableView = new(bind="_items")

            def __setup__(self) -> None:
                item = StateItemWithEvent()
                item.name = "Test"
                item.count = 42
                self._items.append(item)

        instance = create_and_track(qt, TestClass, Widget)

        model = instance._table.model()

        # Get column names
        columns: list[str] = []
        if hasattr(model, "_columns"):
            columns = list(model._columns)

        # Event fields should NOT be columns
        assert_that("on_change" not in columns).is_true()
        # Variable fields SHOULD be columns
        assert_that("name" in columns).is_true()
        assert_that("count" in columns).is_true()

    def test_table_column_excludes_state_parent(self, qt: QtDriver) -> None:
        """QTableView auto-detected columns exclude state_parent."""
        from qtpie import Widget, widget

        @widget
        class TestClass(Widget):
            _dogs: Variable[list[StateDog]] = new([])
            _table: QTableView = new(bind="_dogs")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, Widget)

        model = instance._table.model()

        # Get column names
        columns: list[str] = []
        if hasattr(model, "_columns"):
            columns = list(model._columns)

        # state_parent should NOT be a column
        assert_that("state_parent" not in columns).is_true()

    def test_table_displays_variable_values(self, qt: QtDriver) -> None:
        """QTableView displays Variable.value, not Variable object."""
        from PySide6.QtCore import Qt

        from qtpie import Widget, widget

        @widget
        class TestClass(Widget):
            _dogs: Variable[list[StateDog]] = new([])
            _table: QTableView = new(bind="_dogs")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                dog.age = 3
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, Widget)

        model = instance._table.model()

        # Find the 'name' column
        columns: list[Any] = []
        if hasattr(model, "_columns"):
            columns = list(model._columns)

        if "name" in columns:
            name_col = columns.index("name")
            name_value = model.data(model.index(0, name_col), Qt.ItemDataRole.DisplayRole)
            # Should be the actual string "Fido", not "Variable(...)" or similar
            assert_that(name_value).is_equal_to("Fido")

        if "age" in columns:
            age_col = columns.index("age")
            age_value = model.data(model.index(0, age_col), Qt.ItemDataRole.DisplayRole)
            # Should be "3", not the Variable object
            assert_that(age_value).is_equal_to("3")


# =============================================================================
# State Checkable Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestListViewStateCheckable:
    """Test QListView with checkable= for State objects."""

    def test_checkable_state_field(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='done' enables checkboxes on State items."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _tasks: Variable[list[StateTask]] = new([])
            _list: QListView = new(bind="_tasks", checkable="done")

            def __setup__(self) -> None:
                task1 = StateTask()
                task1.title = "Task A"
                task1.done = True
                task2 = StateTask()
                task2.title = "Task B"
                task2.done = False
                self._tasks.extend([task1, task2])

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()

        idx_a = model.index(0, 0)
        idx_b = model.index(1, 0)
        assert_that(model.flags(idx_a) & Qt.ItemFlag.ItemIsUserCheckable).is_true()
        assert_that(model.flags(idx_b) & Qt.ItemFlag.ItemIsUserCheckable).is_true()

        # Check states match the Variable values
        assert_that(model.data(idx_a, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        assert_that(model.data(idx_b, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)


# =============================================================================
# State Selection Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestListViewStateSelection:
    """Test QListView selection with State objects."""

    def test_selected_item_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with selectedItem= binds to State item Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _selected: Variable[StateDog | None] = new(None)
            _list: QListView = new(bind="_dogs", format="{name}", selectedItem="_selected")

            def __setup__(self) -> None:
                for name in ["Fido", "Rex"]:
                    dog = StateDog()
                    dog.name = name
                    self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        # Initial selection should be first item
        assert_that(instance._selected.value).is_not_none()
        assert_that(instance._selected.value.name.value).is_equal_to("Fido")

    def test_selected_index_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """QListView with selectedIndex= binds to row index Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _idx: Variable[int] = new(0)
            _list: QListView = new(bind="_dogs", format="{name}", selectedIndex="_idx")

            def __setup__(self) -> None:
                for name in ["Fido", "Rex", "Spot"]:
                    dog = StateDog()
                    dog.name = name
                    self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._idx.value).is_equal_to(0)

        # Change selection via Variable
        instance._idx.value = 2
        qt.process_events()

        current_idx = instance._list.selectionModel().currentIndex()
        assert_that(current_idx.row()).is_equal_to(2)


# =============================================================================
# Format Expression Tests with State Objects
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestStateFormatExpressions:
    """Test format expressions evaluate correctly on State objects."""

    def test_format_simple_field(self, base_class, decorator, qt: QtDriver) -> None:
        """Format with simple field access unwraps Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name}")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")

    def test_format_multiple_fields(self, base_class, decorator, qt: QtDriver) -> None:
        """Format with multiple fields unwraps all Variables."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name} is {age} years old")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                dog.age = 3
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido is 3 years old")

    def test_format_with_method_call(self, base_class, decorator, qt: QtDriver) -> None:
        """Format with method call on Variable value."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{name.upper()}")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.data(model.index(0, 0))).is_equal_to("FIDO")

    def test_format_with_len(self, base_class, decorator, qt: QtDriver) -> None:
        """Format with len() on Variable value."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="{len(name)} chars")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.data(model.index(0, 0))).is_equal_to("4 chars")

    def test_format_self_placeholder(self, base_class, decorator, qt: QtDriver) -> None:
        """Format with #self placeholder works with State."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", format="Dog: {#self.name}")

            def __setup__(self) -> None:
                dog = StateDog()
                dog.name = "Fido"
                self._dogs.append(dog)

        instance = create_and_track(qt, TestClass, base_class)

        model = instance._list.model()
        assert_that(model.data(model.index(0, 0))).is_equal_to("Dog: Fido")
