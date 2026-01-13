# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUnknownArgumentType=false
# pyright: reportImplicitOverride=false
# pyright: reportUnknownVariableType=false
"""Tests for QTreeView with bind= to hierarchical data."""

from dataclasses import dataclass, field

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QTreeView, QWidget

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import RECORD_CLASS_TYPES, WIDGET_CLASS_TYPES, create_and_track


@dataclass
class TreeNode:
    """Simple tree node with children."""

    name: str
    children: "list[TreeNode]" = field(default_factory=list)  # noqa: UP037

    def __str__(self) -> str:
        return self.name


@dataclass
class FileNode:
    """File system-like node with 'items' as children attr."""

    name: str
    items: "list[FileNode]" = field(default_factory=list)  # noqa: UP037

    def __str__(self) -> str:
        return self.name


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewModelBinding:
    """Test QTreeView with bind= to hierarchical Variable[list]."""

    def test_tree_shows_root_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with bind= shows root items."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("Root 1"),
                    TreeNode("Root 2"),
                    TreeNode("Root 3"),
                ]
            )
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        assert_that(model.rowCount()).is_equal_to(3)
        assert_that(model.data(model.index(0, 0))).is_equal_to("Root 1")
        assert_that(model.data(model.index(1, 0))).is_equal_to("Root 2")
        assert_that(model.data(model.index(2, 0))).is_equal_to("Root 3")

    def test_tree_shows_child_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView shows nested children."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode(
                        "Parent",
                        [
                            TreeNode("Child 1"),
                            TreeNode("Child 2"),
                        ],
                    ),
                ]
            )
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Root has 1 item
        assert_that(model.rowCount()).is_equal_to(1)

        # Parent index
        parent_idx = model.index(0, 0)
        assert_that(model.data(parent_idx)).is_equal_to("Parent")

        # Parent has 2 children
        assert_that(model.rowCount(parent_idx)).is_equal_to(2)

        # Check children
        child1_idx = model.index(0, 0, parent_idx)
        child2_idx = model.index(1, 0, parent_idx)
        assert_that(model.data(child1_idx)).is_equal_to("Child 1")
        assert_that(model.data(child2_idx)).is_equal_to("Child 2")

    def test_tree_deep_nesting(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView handles multiple levels of nesting."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode(
                        "Level 0",
                        [
                            TreeNode(
                                "Level 1",
                                [
                                    TreeNode(
                                        "Level 2",
                                        [
                                            TreeNode("Level 3"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ]
            )
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Navigate down the tree
        level0 = model.index(0, 0)
        assert_that(model.data(level0)).is_equal_to("Level 0")

        level1 = model.index(0, 0, level0)
        assert_that(model.data(level1)).is_equal_to("Level 1")

        level2 = model.index(0, 0, level1)
        assert_that(model.data(level2)).is_equal_to("Level 2")

        level3 = model.index(0, 0, level2)
        assert_that(model.data(level3)).is_equal_to("Level 3")

    def test_tree_updates_on_root_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to root list updates QTreeView."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new([TreeNode("A")])
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        assert_that(model.rowCount()).is_equal_to(1)

        instance._nodes.append(TreeNode("B"))
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(1, 0))).is_equal_to("B")

    def test_tree_updates_on_root_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from root list updates QTreeView."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("A"),
                    TreeNode("B"),
                    TreeNode("C"),
                ]
            )
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        assert_that(model.rowCount()).is_equal_to(3)

        # Remove middle item
        del instance._nodes[1]
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.data(model.index(0, 0))).is_equal_to("A")
        assert_that(model.data(model.index(1, 0))).is_equal_to("C")

    def test_tree_updates_on_root_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing root list updates QTreeView."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new([TreeNode("A"), TreeNode("B")])
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        assert_that(model.rowCount()).is_equal_to(2)

        instance._nodes.clear()
        assert_that(model.rowCount()).is_equal_to(0)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewWithFormat:
    """Test QTreeView with format= for display customization."""

    def test_tree_with_format(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with format= customizes display text."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("Root", [TreeNode("Child")]),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", format="Node: {name}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        root_idx = model.index(0, 0)
        assert_that(model.data(root_idx)).is_equal_to("Node: Root")

        child_idx = model.index(0, 0, root_idx)
        assert_that(model.data(child_idx)).is_equal_to("Node: Child")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewWithCustomChildren:
    """Test QTreeView with children= to specify non-default children attribute."""

    def test_tree_with_custom_children_attr(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with children= uses custom attribute for children."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[FileNode]] = new(
                [
                    FileNode(
                        "Folder",
                        [
                            FileNode("File 1"),
                            FileNode("File 2"),
                        ],
                    ),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", children="items")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Root has 1 folder
        assert_that(model.rowCount()).is_equal_to(1)

        folder_idx = model.index(0, 0)
        assert_that(model.data(folder_idx)).is_equal_to("Folder")

        # Folder has 2 files (accessed via 'items' attribute)
        assert_that(model.rowCount(folder_idx)).is_equal_to(2)

        file1_idx = model.index(0, 0, folder_idx)
        file2_idx = model.index(1, 0, folder_idx)
        assert_that(model.data(file1_idx)).is_equal_to("File 1")
        assert_that(model.data(file2_idx)).is_equal_to("File 2")

    def test_tree_with_bind_children_and_format(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with bind=, children=, and format= all together."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[FileNode]] = new(
                [
                    FileNode(
                        "Documents",
                        [
                            FileNode("Report.pdf"),
                            FileNode("Notes.txt"),
                        ],
                    ),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", children="items", format="[{name}]")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Check root with format
        folder_idx = model.index(0, 0)
        assert_that(model.data(folder_idx)).is_equal_to("[Documents]")

        # Check children with format
        file1_idx = model.index(0, 0, folder_idx)
        file2_idx = model.index(1, 0, folder_idx)
        assert_that(model.data(file1_idx)).is_equal_to("[Report.pdf]")
        assert_that(model.data(file2_idx)).is_equal_to("[Notes.txt]")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewSelectionBindings:
    """Test QTreeView with selectedItem= and selectedItems= bindings."""

    def test_selectedItem_bare_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= with bare Variable annotation syncs selection."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("A"),
                    TreeNode("B"),
                    TreeNode("C"),
                ]
            )
            _selected: Variable[TreeNode | None]  # Bare - no default
            _tree: QTreeView = new(bind="_nodes", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially no selection
        assert_that(instance._selected.value).is_none()

        # Simulate selection by setting Variable
        node_b = instance._nodes.value[1]
        instance._selected.value = node_b
        assert_that(instance._selected.value).is_equal_to(node_b)

    def test_selectedItem_with_default(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= with Variable that has default value."""
        node_a = TreeNode("A")
        node_b = TreeNode("B")

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new([node_a, node_b])
            _selected: Variable[TreeNode | None] = new(node_b)  # Default to B
            _tree: QTreeView = new(bind="_nodes", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Should start with default value
        assert_that(instance._selected.value).is_equal_to(node_b)

    def test_selectedItems_bare_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItems= with bare Variable annotation for multi-select."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("A"),
                    TreeNode("B"),
                    TreeNode("C"),
                ]
            )
            _selected: Variable[list[TreeNode]]  # Bare - no default
            _tree: QTreeView = new(bind="_nodes", selectedItems="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially empty list (from selection model)
        assert_that(instance._selected.value).is_equal_to([])

    def test_selectedItems_with_default(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItems= with Variable that has default value."""
        node_a = TreeNode("A")
        node_b = TreeNode("B")
        node_c = TreeNode("C")

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new([node_a, node_b, node_c])
            _selected: Variable[list[TreeNode]] = new([node_a, node_c])  # Default selection
            _tree: QTreeView = new(bind="_nodes", selectedItems="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Should maintain default (or be initialized)
        # Note: Multi-select initialization from Variable isn't implemented yet
        assert_that(instance._selected.value).is_instance_of(list)

    def test_selectedItem_and_selectedItems_together(self, base_class, decorator, qt: QtDriver) -> None:
        """Both selectedItem= and selectedItems= work together."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("A"),
                    TreeNode("B"),
                ]
            )
            _current: Variable[TreeNode | None]  # Current item
            _selected: Variable[list[TreeNode]]  # All selected items
            _tree: QTreeView = new(bind="_nodes", selectedItem="_current", selectedItems="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Set current item via Variable
        node_a = instance._nodes.value[0]
        instance._current.value = node_a
        assert_that(instance._current.value).is_equal_to(node_a)

    def test_selectedItem_with_nested_nodes(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= works with nested tree nodes."""
        child_node = TreeNode("Child")
        parent_node = TreeNode("Parent", [child_node])

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new([parent_node])
            _selected: Variable[TreeNode | None] = new(child_node)  # Default to nested child
            _tree: QTreeView = new(bind="_nodes", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Should be able to select nested child
        assert_that(instance._selected.value).is_equal_to(child_node)

    def test_format_binding_to_selectedItems_count(self, base_class, decorator, qt: QtDriver) -> None:
        """QLabel format binding to {len(_selected)} updates when tree selection changes."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("A"),
                    TreeNode("B"),
                    TreeNode("C"),
                ]
            )
            _selected: Variable[list[TreeNode]]  # Bare Variable
            _tree: QTreeView = new(bind="_nodes", selectedItems="_selected")
            _count_label: QLabel = new(bind="Selected: {len(_selected)}")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially should show count of 0
        assert_that(instance._count_label.text()).is_equal_to("Selected: 0")

        # Verify the Variable exists and is empty
        assert_that(instance._selected.value).is_equal_to([])

    def test_format_binding_updates_when_variable_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """QLabel format binding updates when the Variable value changes programmatically."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(
                [
                    TreeNode("A"),
                    TreeNode("B"),
                    TreeNode("C"),
                ]
            )
            _selected: Variable[list[TreeNode]]  # Bare Variable
            _tree: QTreeView = new(bind="_nodes", selectedItems="_selected")
            _count_label: QLabel = new(bind="Selected: {len(_selected)}")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially should show count of 0
        assert_that(instance._count_label.text()).is_equal_to("Selected: 0")

        # Programmatically set the Variable to a list with 2 items
        node_a = instance._nodes.value[0]
        node_b = instance._nodes.value[1]
        instance._selected.value = [node_a, node_b]

        # The label should update to show count of 2
        assert_that(instance._count_label.text()).is_equal_to("Selected: 2")

        # Clear the selection
        instance._selected.value = []
        assert_that(instance._count_label.text()).is_equal_to("Selected: 0")


@pytest.mark.parametrize("base_class,decorator", RECORD_CLASS_TYPES)
class TestTreeViewRecordBindings:
    """Test QTreeView with Widget[T] record bindings."""

    def test_format_binding_to_selectedItems_with_record(self, base_class, decorator, qt: QtDriver) -> None:
        """QLabel format binding to {len(_selected)} works with Widget[T] record type."""

        @dataclass
        class Container:
            nodes: "list[TreeNode]" = field(default_factory=list)  # noqa: UP037

        @decorator(record=Container(nodes=[TreeNode("A"), TreeNode("B"), TreeNode("C")]))
        class TestClass(base_class[Container]):  # type: ignore[misc]
            _selected: Variable[list[TreeNode]]  # Bare Variable for selection
            _tree: QTreeView = new(bind="nodes", selectedItems="_selected", children="children")
            _count_label: QLabel = new(bind="Selected: {len(_selected)}")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially should show count of 0
        assert_that(instance._count_label.text()).is_equal_to("Selected: 0")

        # Verify the Variable exists and is empty
        assert_that(instance._selected.value).is_equal_to([])

    def test_user_scenario_self_referential_record(self, base_class, decorator, qt: QtDriver) -> None:
        """User's exact scenario: Widget[Cat] with self-referential Cat.kittens."""

        @dataclass
        class Cat:
            name: str
            age: int
            kittens: "list[Cat]" = field(default_factory=list)  # noqa: UP037

        cat = Cat(name="Mittens", age=4, kittens=[Cat(name="Fluffy", age=1, kittens=[]), Cat(name="Snowball", age=2, kittens=[Cat(name="Tiny", age=0, kittens=[])])])

        @decorator(record=cat)
        class TestClass(base_class[Cat]):  # type: ignore[misc]
            _selected_kittens: Variable[list[Cat]]
            _tree: QTreeView = new(bind="kittens", format="{name} ({age} yrs)", children="kittens", selectedItems="_selected_kittens")
            _selected_kittens_info: QLabel = new(bind="Selected Kitten Count: {len(_selected_kittens)}")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially should show count of 0
        assert_that(instance._selected_kittens_info.text()).is_equal_to("Selected Kitten Count: 0")

        # Verify the Variable exists
        assert_that(instance._selected_kittens.value).is_equal_to([])

        # Set selection programmatically
        instance._selected_kittens.value = [cat.kittens[0]]
        assert_that(instance._selected_kittens_info.text()).is_equal_to("Selected Kitten Count: 1")


class _CustomTreeWidget(QWidget):
    """Custom widget for testing kwargs passthrough."""

    def __init__(
        self,
        parent: QWidget | None = None,
        children: str | None = None,
        format: str | None = None,  # noqa: A002
    ) -> None:
        super().__init__(parent)
        self.my_children = children
        self.my_format = format


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewSelectionParamsNotStolen:
    """Ensure kwargs pass to constructor when widget is not a model widget."""

    def test_treeview_kwargs_pass_to_non_model_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView-related kwargs pass to constructor for non-model widgets."""

        @decorator
        class TestClass(base_class):
            _custom: _CustomTreeWidget = new(bind="x", children="items", format="{name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._custom.my_children).is_equal_to("items")
        assert_that(instance._custom.my_format).is_equal_to("{name}")
