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
"""Tests for expression-based model binding.

Tests that model widgets (QListView, QComboBox, QTableView, QTreeView) can
bind to expression results like `bind="{items[0]}"` for one-way reactive binding.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from assertpy import assert_that
from PySide6.QtWidgets import QComboBox, QListView, QTableView, QTreeView

from qtpie import State, Variable, Widget, new, state, widget
from qtpie.testing import QtDriver


@dataclass
class Item:
    """Test item with a name."""

    name: str


@dataclass
class Category:
    """Category containing items."""

    title: str
    items: list[Item] = field(default_factory=list)


@dataclass
class TreeNode:
    """Node with children for tree testing."""

    name: str
    children: list[TreeNode] = field(default_factory=list)


@dataclass
class Workspace:
    """Workspace with nested data for optional chaining tests."""

    name: str
    categories: list[Category] = field(default_factory=list)


# State classes for real-world Forc2 scenario tests
@state
class StateItem(State):
    """State item with name - simulates Request/Collection items."""

    name: Variable[str] = new("")


@state
class StateCollection(State):
    """State collection - simulates Collection with nested items."""

    name: Variable[str] = new("")
    # Use Any to avoid forward reference issues in test file
    items: Variable[list[StateItem]] = new([])


class TestExpressionModelBindingQListView:
    """Test expression-based binding for QListView."""

    def test_bind_to_nested_collection_via_index(self, qt: QtDriver) -> None:
        """QListView can bind to a nested collection via index expression."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new(
                [
                    Category("Animals", [Item("Dog"), Item("Cat"), Item("Bird")]),
                    Category("Fruits", [Item("Apple"), Item("Banana")]),
                ]
            )
            # Bind to the first category's items
            _list: QListView = new(bind="{_categories[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(3)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Dog")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Cat")
        assert_that(model.data(model.index(2, 0))).is_equal_to("Bird")

    def test_bind_with_optional_chain(self, qt: QtDriver) -> None:
        """QListView can bind using optional chaining in expression."""

        @widget
        class TestWidget(Widget):
            _workspace: Variable[Workspace | None] = new(Workspace("Test", [Category("Items", [Item("A"), Item("B")])]))
            _list: QListView = new(bind="{_workspace?.categories[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("A")
        assert_that(model.data(model.index(1, 0))).is_equal_to("B")

    def test_bind_updates_when_source_changes(self, qt: QtDriver) -> None:
        """QListView updates when source collection changes."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new(
                [
                    Category("Initial", [Item("One"), Item("Two")]),
                ]
            )
            _list: QListView = new(bind="{_categories[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)

        # Replace the entire categories list
        instance._categories.value = [Category("New", [Item("X"), Item("Y"), Item("Z")])]
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(3)
        assert_that(model.data(model.index(0, 0))).is_equal_to("X")

    def test_bind_handles_none_gracefully(self, qt: QtDriver) -> None:
        """QListView handles None result from optional chain gracefully."""

        @widget
        class TestWidget(Widget):
            _workspace: Variable[Workspace | None] = new(None)
            _list: QListView = new(bind="{_workspace?.categories}", format="{title}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(0)

        # Now set a value
        instance._workspace.value = Workspace("Test", [Category("Cat1"), Category("Cat2")])
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Cat1")


class TestExpressionModelBindingQComboBox:
    """Test expression-based binding for QComboBox."""

    def test_bind_to_nested_collection(self, qt: QtDriver) -> None:
        """QComboBox can bind to nested collection via expression."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new(
                [
                    Category("Colors", [Item("Red"), Item("Green"), Item("Blue")]),
                ]
            )
            _combo: QComboBox = new(bind="{_categories[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        combo = instance._combo
        assert_that(combo.count()).is_equal_to(3)
        assert_that(combo.itemText(0)).is_equal_to("Red")
        assert_that(combo.itemText(1)).is_equal_to("Green")
        assert_that(combo.itemText(2)).is_equal_to("Blue")

    def test_bind_updates_reactively(self, qt: QtDriver) -> None:
        """QComboBox updates when source changes."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new([Category("A", [Item("X"), Item("Y")])])
            _combo: QComboBox = new(bind="{_categories[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        combo = instance._combo
        assert_that(combo.count()).is_equal_to(2)

        # Replace data
        instance._categories.value = [Category("B", [Item("P"), Item("Q"), Item("R")])]
        qt.process_events()

        assert_that(combo.count()).is_equal_to(3)
        assert_that(combo.itemText(0)).is_equal_to("P")


class TestExpressionModelBindingQTableView:
    """Test expression-based binding for QTableView."""

    def test_bind_to_nested_collection(self, qt: QtDriver) -> None:
        """QTableView can bind to nested collection via expression."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new(
                [
                    Category("Data", [Item("Row1"), Item("Row2")]),
                ]
            )
            _table: QTableView = new(
                bind="{_categories[0].items}",
                columns=["name"],
            )

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Row1")

    def test_bind_updates_when_source_changes(self, qt: QtDriver) -> None:
        """QTableView updates reactively."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new([Category("Init", [Item("A")])])
            _table: QTableView = new(
                bind="{_categories[0].items}",
                columns=["name"],
            )

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(1)

        instance._categories.value = [Category("New", [Item("B"), Item("C"), Item("D")])]
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(3)


class TestExpressionModelBindingQTreeView:
    """Test expression-based binding for QTreeView."""

    def test_bind_to_nested_collection_with_children(self, qt: QtDriver) -> None:
        """QTreeView can bind to nested collection with children=."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new(
                [
                    Category("Root", [Item("Child1"), Item("Child2")]),
                ]
            )
            _tree: QTreeView = new(bind="{_categories[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(2)

    def test_bind_single_object_as_root_with_children(self, qt: QtDriver) -> None:
        """QTreeView can bind to single object when children= is specified."""
        root = TreeNode(
            "Root",
            [
                TreeNode("Child1", [TreeNode("Grandchild")]),
                TreeNode("Child2"),
            ],
        )

        @widget
        class TestWidget(Widget):
            _nodes: Variable[list[TreeNode]] = new([root])
            # Bind to the first node directly - it becomes the tree data
            _tree: QTreeView = new(
                bind="{_nodes[0].children}",
                children="children",
                format="{name}",
            )

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._tree.model()
        # Should show the children of root (Child1, Child2)
        assert_that(model.rowCount()).is_equal_to(2)


class TestExpressionModelBindingWithRecord:
    """Test expression-based binding for Widget[T] record types.

    This tests the case where the expression accesses fields on the record,
    not on widget Variables. E.g., Widget[Collection] with bind="{items[0].items}".

    These tests simulate the REAL Forc2 scenario using @state classes with Var fields.
    """

    def test_listview_bind_to_state_record_nested_collection(self, qt: QtDriver) -> None:
        """QListView binds to nested collection on State record - REAL Forc2 scenario.

        Simulates CollectionsTreeWidget(Widget[Collection | None]) where Collection
        is a @state with items: Var[list[...]] = new([])
        """

        @widget
        class TestWidget(Widget[StateCollection | None]):
            _list: QListView = new(bind="{items[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        # Initially empty (record is None)
        assert_that(model.rowCount()).is_equal_to(0)

        # Create state objects
        item_a = StateItem()
        item_a.name.value = "A"
        item_b = StateItem()
        item_b.name.value = "B"
        item_c = StateItem()
        item_c.name.value = "C"

        child_collection = StateCollection()
        child_collection.name.value = "Child"
        child_collection.items.value = [item_a, item_b, item_c]

        root_collection = StateCollection()
        root_collection.name.value = "Root"
        root_collection.items.value = [child_collection]

        # Set the record
        instance.record = root_collection
        qt.process_events()

        # Should now show items from items[0].items (the 3 StateItems)
        assert_that(model.rowCount()).is_equal_to(3)
        assert_that(model.data(model.index(0, 0))).is_equal_to("A")

    def test_combobox_bind_to_state_record_nested_collection(self, qt: QtDriver) -> None:
        """QComboBox binds to nested collection on State record."""

        @widget
        class TestWidget(Widget[StateCollection | None]):
            _combo: QComboBox = new(bind="{items[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        assert_that(instance._combo.count()).is_equal_to(0)

        # Create nested structure
        item_x = StateItem()
        item_x.name.value = "X"
        item_y = StateItem()
        item_y.name.value = "Y"

        child = StateCollection()
        child.items.value = [item_x, item_y]

        root = StateCollection()
        root.items.value = [child]

        instance.record = root
        qt.process_events()

        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(0)).is_equal_to("X")

    def test_tableview_bind_to_state_record_nested_collection(self, qt: QtDriver) -> None:
        """QTableView binds to nested collection on State record."""

        @widget
        class TestWidget(Widget[StateCollection | None]):
            _table: QTableView = new(bind="{items[0].items}", columns=["name"])

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(0)

        row1 = StateItem()
        row1.name.value = "Row1"
        row2 = StateItem()
        row2.name.value = "Row2"

        child = StateCollection()
        child.items.value = [row1, row2]

        root = StateCollection()
        root.items.value = [child]

        instance.record = root
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Row1")

    def test_treeview_bind_to_state_record_single_object(self, qt: QtDriver) -> None:
        """QTreeView binds to single State object with children=."""

        @widget
        class TestWidget(Widget[StateCollection | None]):
            _tree: QTreeView = new(bind="{items[0]}", children="items", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(0)

        child1 = StateItem()
        child1.name.value = "Child1"
        child2 = StateItem()
        child2.name.value = "Child2"

        first_item = StateCollection()
        first_item.name.value = "Root"
        first_item.items.value = [child1, child2]

        root = StateCollection()
        root.items.value = [first_item]

        instance.record = root
        qt.process_events()

        # Tree should show 1 root item (items[0])
        assert_that(model.rowCount()).is_equal_to(1)


class TestExpressionModelBindingEdgeCases:
    """Test edge cases for expression-based model binding."""

    def test_empty_collection(self, qt: QtDriver) -> None:
        """Binding to empty collection shows empty list."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new([Category("Empty", [])])
            _list: QListView = new(bind="{_categories[0].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(0)

    def test_index_out_of_bounds_shows_empty(self, qt: QtDriver) -> None:
        """Index out of bounds in expression shows empty list (no crash)."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new([Category("One", [Item("A")])])
            # Index 5 doesn't exist - should show empty
            _list: QListView = new(bind="{_categories[5].items if len(_categories) > 5 else []}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(0)

    def test_complex_expression_with_method_call(self, qt: QtDriver) -> None:
        """Binding can use method calls in expression."""

        @widget
        class TestWidget(Widget):
            _categories: Variable[list[Category]] = new(
                [
                    Category("First", [Item("A")]),
                    Category("Second", [Item("B"), Item("C")]),
                    Category("Third", [Item("D"), Item("E"), Item("F")]),
                ]
            )
            # Get items from the last category using negative index
            _list: QListView = new(bind="{_categories[-1].items}", format="{name}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(3)
        assert_that(model.data(model.index(0, 0))).is_equal_to("D")
        assert_that(model.data(model.index(2, 0))).is_equal_to("F")
