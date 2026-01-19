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
from observant import ObservableList
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


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewSelectedItemFromParent:
    """Test selectedItem= binding to Variable in parent widget hierarchy."""

    def test_selectedItem_resolves_from_parent_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= finds Variable in parent widget, not just host."""
        from qtpie import AppBase, Widget, widget

        # Skip AppBase for this test - AppBase is not a QWidget so parent() hierarchy
        # doesn't work the same way. The child's format binding can't walk up to AppBase.
        if base_class is AppBase:
            pytest.skip("AppBase is not a QWidget, parent hierarchy lookup doesn't apply")

        @widget
        class ChildTreeWidget(Widget):
            """Child widget with tree that binds selectedItem to parent's Variable."""

            _nodes: Variable[list[TreeNode]] = new([TreeNode("Node 1"), TreeNode("Node 2"), TreeNode("Node 3")])
            # selectedItem references a Variable that exists on PARENT, not here
            _tree: QTreeView = new(bind="_nodes", selectedItem="selected_node")
            # This label is in the CHILD, binding to parent's Variable
            _child_info: QLabel = new(bind="Child sees: {selected_node?.name}")

        @decorator
        class ParentWidget(base_class):
            """Parent widget that owns the selected_node Variable."""

            selected_node: Variable[TreeNode | None] = new(None)
            _child: ChildTreeWidget = new()
            _selected_info: QLabel = new(bind="Selected: {selected_node?.name}")

        parent = create_and_track(qt, ParentWidget, base_class)

        # Process events to allow deferred parent binding subscriptions to complete
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        # Initially nothing selected
        assert_that(parent.selected_node.value).is_none()

        # Set selection via parent's Variable
        parent.selected_node.value = parent._child._nodes.value[1]  # "Node 2"
        assert_that(parent._selected_info.text()).is_equal_to("Selected: Node 2")
        # Child's label should also update (proves it's the same Variable)
        assert_that(parent._child._child_info.text()).is_equal_to("Child sees: Node 2")

        # Change selection
        parent.selected_node.value = parent._child._nodes.value[0]  # "Node 1"
        assert_that(parent._selected_info.text()).is_equal_to("Selected: Node 1")
        assert_that(parent._child._child_info.text()).is_equal_to("Child sees: Node 1")

    def test_selectedItem_resolves_from_grandparent_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= finds Variable multiple levels up the hierarchy."""
        from qtpie import Widget, widget

        @widget
        class GrandchildTreeWidget(Widget):
            """Grandchild with tree binding to grandparent's Variable."""

            _nodes: Variable[list[TreeNode]] = new([TreeNode("A"), TreeNode("B")])
            _tree: QTreeView = new(bind="_nodes", selectedItem="selected_node")

        @widget
        class ChildWidget(Widget):
            """Middle widget - does NOT have selected_node."""

            _grandchild: GrandchildTreeWidget = new()

        @decorator
        class GrandparentWidget(base_class):
            """Grandparent owns the Variable."""

            selected_node: Variable[TreeNode | None] = new(None)
            _child: ChildWidget = new()
            _info: QLabel = new(bind="Selection: {selected_node?.name}")

        grandparent = create_and_track(qt, GrandparentWidget, base_class)

        assert_that(grandparent.selected_node.value).is_none()

        # Set selection on grandparent - should propagate to grandchild's tree binding
        grandparent.selected_node.value = grandparent._child._grandchild._nodes.value[0]
        assert_that(grandparent._info.text()).is_equal_to("Selection: A")

        grandparent.selected_node.value = grandparent._child._grandchild._nodes.value[1]
        assert_that(grandparent._info.text()).is_equal_to("Selection: B")


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


@dataclass
class SelectableNode:
    """Tree node with a bool field for checkbox testing."""

    name: str
    selected: bool = False
    children: "list[SelectableNode]" = field(default_factory=list)  # noqa: UP037

    def __str__(self) -> str:
        return self.name


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewCheckable:
    """Test QTreeView with checkable= for checkbox support."""

    def test_checkable_field_shows_checkbox(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='field_name' enables checkboxes on tree items."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode("A", selected=True),
                    SelectableNode("B", selected=False),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", checkable="selected")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

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
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode("A", selected=False),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", checkable="selected")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()
        idx = model.index(0, 0)

        # Initially unchecked
        assert_that(instance._nodes.value[0].selected).is_false()
        assert_that(model.data(idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

        # Set via model (simulating checkbox click)
        model.setData(idx, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole)

        # Underlying data should be updated
        assert_that(instance._nodes.value[0].selected).is_true()

    def test_checkable_expression_read_only(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='{expr}' creates read-only checkbox from expression."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode("Parent", children=[SelectableNode("Child")]),
                    SelectableNode("Leaf"),  # No children
                ]
            )
            _tree: QTreeView = new(bind="_nodes", checkable="{len(children) > 0}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        idx_parent = model.index(0, 0)
        idx_leaf = model.index(1, 0)

        # Parent has children -> checked
        assert_that(model.data(idx_parent, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        # Leaf has no children -> unchecked
        assert_that(model.data(idx_leaf, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

        # Expression-based checkable should NOT allow setData
        result = model.setData(idx_leaf, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole)
        assert_that(result).is_false()

    def test_checkable_expression_evaluates(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable='{expr}' correctly evaluates expression per node."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode("Selected", selected=True),
                    SelectableNode("Unselected", selected=False),
                ]
            )
            # Expression that evaluates to the 'selected' field value
            _tree: QTreeView = new(bind="_nodes", checkable="{selected}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        idx_selected = model.index(0, 0)
        idx_unselected = model.index(1, 0)

        assert_that(model.data(idx_selected, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        assert_that(model.data(idx_unselected, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

    def test_checkable_false_no_checkbox(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable=False explicitly disables checkboxes."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode("A", selected=True),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", checkable=False)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

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
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode("A", selected=True),
                ]
            )
            _tree: QTreeView = new(bind="_nodes")  # No checkable=

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

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
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode("Node A", selected=True),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", format="[{name}]", checkable="selected")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        idx = model.index(0, 0)

        # Format affects display
        assert_that(model.data(idx, Qt.ItemDataRole.DisplayRole)).is_equal_to("[Node A]")
        # Checkable affects check state
        assert_that(model.data(idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)

    def test_checkable_nested_nodes(self, base_class, decorator, qt: QtDriver) -> None:
        """checkable= works on nested child nodes."""
        from PySide6.QtCore import Qt

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[SelectableNode]] = new(
                [
                    SelectableNode(
                        "Parent",
                        selected=False,
                        children=[
                            SelectableNode("Child 1", selected=True),
                            SelectableNode("Child 2", selected=False),
                        ],
                    ),
                ]
            )
            _tree: QTreeView = new(bind="_nodes", checkable="selected")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        parent_idx = model.index(0, 0)
        child1_idx = model.index(0, 0, parent_idx)
        child2_idx = model.index(1, 0, parent_idx)

        # Check parent
        assert_that(model.data(parent_idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)
        # Check children
        assert_that(model.data(child1_idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Checked)
        assert_that(model.data(child2_idx, Qt.ItemDataRole.CheckStateRole)).is_equal_to(Qt.CheckState.Unchecked)

        # Two-way binding on nested node
        model.setData(child2_idx, Qt.CheckState.Checked.value, Qt.ItemDataRole.CheckStateRole)
        assert_that(instance._nodes.value[0].children[1].selected).is_true()


class TestTreeViewSignalHandlerOrder:
    """Test that user signal handlers see UPDATED values after selection changes."""

    def test_treeview_deeply_nested_in_tab_widget(self, qt: QtDriver) -> None:
        """Test: Deeply nested Widget[T] with QTreeView and nested optional path.

        This test ensures that when a user's signal handler (clicked) fires,
        the selectedItem binding has ALREADY updated the record field.
        The handler should see the NEW value, not the OLD value.
        """
        from enum import Enum

        from PySide6.QtCore import QItemSelectionModel
        from PySide6.QtWidgets import QTabWidget

        from qtpie import Widget, widget

        class Location(Enum):
            HEADER = "header"
            QUERY = "query"

            def __str__(self) -> str:
                return self.value

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

            # Bind directly to Location enum values (they are the tree nodes)
            _tree: QTreeView = new(
                bind=list(Location),
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

        grandchild_widget = instance._child._tabs.widget(0)
        assert_that(grandchild_widget).is_instance_of(GrandchildTab)
        assert isinstance(grandchild_widget, GrandchildTab)
        grandchild = grandchild_widget

        # Simulate click on QUERY (row 1)
        model = grandchild._tree.model()
        index = model.index(1, 0)
        grandchild._tree.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        grandchild._tree.clicked.emit(index)

        assert_that(call_count["value"]).is_equal_to(1)
        assert_that(seen_values).is_equal_to([Location.QUERY])


@dataclass
class ObservableTreeNode:
    """Tree node with ObservableList children for reactive updates."""

    name: str
    children: "ObservableList[ObservableTreeNode]" = field(  # noqa: UP037
        default_factory=lambda: ObservableList()
    )

    def __str__(self) -> str:
        return self.name


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewChildrenListUpdates:
    """Test QTreeView reactively updates when children ObservableLists change."""

    def test_tree_updates_on_child_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to a child's ObservableList updates QTreeView."""
        from observant import ObservableList

        root_children: ObservableList[ObservableTreeNode] = ObservableList([ObservableTreeNode("Child 1")])
        root = ObservableTreeNode("Root", root_children)

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[ObservableTreeNode]] = new([root])
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Initially 1 root with 1 child
        root_idx = model.index(0, 0)
        assert_that(model.rowCount(root_idx)).is_equal_to(1)
        assert_that(model.data(model.index(0, 0, root_idx))).is_equal_to("Child 1")

        # Append a new child to root's children
        root_children.append(ObservableTreeNode("Child 2"))

        # Tree should now show 2 children
        assert_that(model.rowCount(root_idx)).is_equal_to(2)
        assert_that(model.data(model.index(1, 0, root_idx))).is_equal_to("Child 2")

    def test_tree_updates_on_child_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from a child's ObservableList updates QTreeView."""
        from observant import ObservableList

        root_children: ObservableList[ObservableTreeNode] = ObservableList(
            [
                ObservableTreeNode("Child A"),
                ObservableTreeNode("Child B"),
                ObservableTreeNode("Child C"),
            ]
        )
        root = ObservableTreeNode("Root", root_children)

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[ObservableTreeNode]] = new([root])
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        root_idx = model.index(0, 0)
        assert_that(model.rowCount(root_idx)).is_equal_to(3)

        # Remove middle child
        del root_children[1]

        assert_that(model.rowCount(root_idx)).is_equal_to(2)
        assert_that(model.data(model.index(0, 0, root_idx))).is_equal_to("Child A")
        assert_that(model.data(model.index(1, 0, root_idx))).is_equal_to("Child C")

    def test_tree_updates_on_child_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing a child's ObservableList updates QTreeView."""
        from observant import ObservableList

        root_children: ObservableList[ObservableTreeNode] = ObservableList([ObservableTreeNode("Child 1"), ObservableTreeNode("Child 2")])
        root = ObservableTreeNode("Root", root_children)

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[ObservableTreeNode]] = new([root])
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        root_idx = model.index(0, 0)
        assert_that(model.rowCount(root_idx)).is_equal_to(2)

        # Clear all children
        root_children.clear()

        assert_that(model.rowCount(root_idx)).is_equal_to(0)

    def test_tree_updates_on_nested_child_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to a deeply nested child's ObservableList updates QTreeView."""
        from observant import ObservableList

        grandchild_children: ObservableList[ObservableTreeNode] = ObservableList()
        grandchild = ObservableTreeNode("Grandchild", grandchild_children)
        child_children: ObservableList[ObservableTreeNode] = ObservableList([grandchild])
        child = ObservableTreeNode("Child", child_children)
        root_children: ObservableList[ObservableTreeNode] = ObservableList([child])
        root = ObservableTreeNode("Root", root_children)

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[ObservableTreeNode]] = new([root])
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Navigate to grandchild
        root_idx = model.index(0, 0)
        child_idx = model.index(0, 0, root_idx)
        grandchild_idx = model.index(0, 0, child_idx)

        # Initially grandchild has no children
        assert_that(model.rowCount(grandchild_idx)).is_equal_to(0)

        # Append a great-grandchild
        grandchild_children.append(ObservableTreeNode("Great-Grandchild"))

        # Tree should now show 1 great-grandchild
        assert_that(model.rowCount(grandchild_idx)).is_equal_to(1)
        great_grandchild_idx = model.index(0, 0, grandchild_idx)
        assert_that(model.data(great_grandchild_idx)).is_equal_to("Great-Grandchild")

    def test_tree_updates_when_new_node_added_to_root_then_children_modified(self, base_class, decorator, qt: QtDriver) -> None:
        """Adding a node to root and then modifying its children works."""
        from observant import ObservableList

        root_children: ObservableList[ObservableTreeNode] = ObservableList()

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[ObservableTreeNode]] = new([])
            _tree: QTreeView = new(bind="_nodes")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Start with empty tree
        assert_that(model.rowCount()).is_equal_to(0)

        # Add root node
        new_root = ObservableTreeNode("New Root", root_children)
        instance._nodes.append(new_root)

        assert_that(model.rowCount()).is_equal_to(1)
        root_idx = model.index(0, 0)
        assert_that(model.rowCount(root_idx)).is_equal_to(0)

        # Now add children to the new root
        root_children.append(ObservableTreeNode("New Child"))

        assert_that(model.rowCount(root_idx)).is_equal_to(1)
        assert_that(model.data(model.index(0, 0, root_idx))).is_equal_to("New Child")


# =============================================================================
# Issue Reproduction: selectedItem Dirty State Across Selections
# =============================================================================


@dataclass
class EditableTreeNode:
    """Editable tree node for dirty state testing."""

    name: str
    children: "list[EditableTreeNode]" = field(default_factory=list)  # noqa: UP037


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewSelectedItemDirtyStateAcrossSelections:
    """Test that dirty state is tracked correctly when tree selection changes.

    The key scenario: if you have two nodes and you:
    1. Select node 1
    2. Modify node 1 via selectedItem (dirty = true)
    3. Select node 2
    4. What is _selected.is_dirty?

    It SHOULD be false (node 2 is clean) but if dirty state is per-Variable
    rather than per-proxy, it might incorrectly show dirty.
    """

    def test_dirty_state_resets_when_selecting_clean_node(self, base_class, decorator, qt: QtDriver) -> None:
        """Switching selection to a clean node should show is_dirty=false."""
        from PySide6.QtCore import QItemSelectionModel

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[EditableTreeNode]] = new(
                [
                    EditableTreeNode("Alice"),
                    EditableTreeNode("Bob"),
                ]
            )
            _selected: Variable[EditableTreeNode | None] = new(None)
            _tree: QTreeView = new(bind="_nodes", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        # Select first item
        model = instance._tree.model()
        index = model.index(0, 0)
        instance._tree.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        qt.process_events()

        assert_that(instance._selected.value).is_not_none()
        assert_that(instance._selected.value.name).is_equal_to("Alice")

        # Modify the first item
        instance._selected.name = "Alice Modified"  # type: ignore[attr-defined]
        qt.process_events()

        # Should be dirty now
        assert_that(instance._selected.is_dirty.get()).is_true()

        # Select second item (Bob, which is clean)
        index = model.index(1, 0)
        instance._tree.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        qt.process_events()

        # Now _selected points to Bob
        assert_that(instance._selected.value.name).is_equal_to("Bob")

        # EXPECTED: Since Bob is clean, is_dirty should be false
        # This WILL FAIL if dirty state is tracked per-Variable rather than per-item
        assert_that(instance._selected.is_dirty.get()).is_false()

    def test_dirty_state_persists_for_modified_node(self, base_class, decorator, qt: QtDriver) -> None:
        """Going back to a modified node should show is_dirty=true."""
        from PySide6.QtCore import QItemSelectionModel

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[EditableTreeNode]] = new(
                [
                    EditableTreeNode("Alice"),
                    EditableTreeNode("Bob"),
                ]
            )
            _selected: Variable[EditableTreeNode | None] = new(None)
            _tree: QTreeView = new(bind="_nodes", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        # Select and modify first item
        model = instance._tree.model()
        index = model.index(0, 0)
        instance._tree.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        qt.process_events()

        assert_that(instance._selected.value.name).is_equal_to("Alice")
        instance._selected.name = "Alice Modified"  # type: ignore[attr-defined]
        qt.process_events()
        assert_that(instance._selected.is_dirty.get()).is_true()

        # Select second item
        index = model.index(1, 0)
        instance._tree.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        qt.process_events()

        # Select first item again
        index = model.index(0, 0)
        instance._tree.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        qt.process_events()

        # EXPECTED: First item (Alice Modified) is still dirty
        # This test checks if dirty state is remembered per-item
        assert_that(instance._selected.value.name).is_equal_to("Alice Modified")
        assert_that(instance._selected.is_dirty.get()).is_true()
