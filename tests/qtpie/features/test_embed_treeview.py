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
# pyright: reportUnknownVariableType=false
"""Tests for QTreeView with embedded widgets using widget= and embed().

Tests that QTreeView can display custom Widget subclasses for each tree node
using Qt's openPersistentEditor() mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from assertpy import assert_that
from observant import ObservableList
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QTreeView

from qtpie import Variable, Widget, embed, new, widget
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class TreeNode:
    """Test dataclass for tree node."""

    name: str
    children: list[TreeNode] = field(default_factory=list)


@dataclass
class ObservableTreeNode:
    """Test dataclass for tree node with ObservableList children.

    Used for testing dynamic child insertion scenarios where the model
    needs to be notified of nested changes.
    """

    name: str
    children: ObservableList[ObservableTreeNode] = field(default_factory=ObservableList)


# Simple embedded widget for tree nodes
@widget
class NodeLabel(Widget[TreeNode]):
    """A simple widget that displays node info."""

    _label: QLabel = new(bind="{record.name}")


# Embedded widget for observable tree nodes
@widget
class ObservableNodeLabel(Widget[ObservableTreeNode]):
    """A simple widget that displays observable tree node info."""

    _label: QLabel = new(bind="{record.name}")


# Widget with index injection
@widget
class NodeLabelWithIndex(Widget[TreeNode]):
    """Widget with index injection."""

    row_index: Variable[int]  # Bare annotation - will be injected
    _label: QLabel = new(bind="[{row_index}] {record.name}")


# Widget with signal for parent connection
@widget
class NodeLabelWithDelete(Widget[TreeNode]):
    """Widget with delete signal."""

    delete_requested = Signal()

    _label: QLabel = new(bind="{record.name}")
    _delete: QPushButton = new("Delete", clicked="on_delete")

    def on_delete(self) -> None:
        self.delete_requested.emit()


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewEmbedBasic:
    """Basic QTreeView with widget= embedding."""

    def test_simple_widget_shows_for_root_nodes(self, base_class, decorator, qt: QtDriver) -> None:
        """widget=MyWidget shows widget for root tree nodes."""
        nodes = [
            TreeNode("Root 1"),
            TreeNode("Root 2"),
        ]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _tree: QTreeView = new(bind="_nodes", children="children", widget=NodeLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(2)

    def test_widget_shows_for_child_nodes(self, base_class, decorator, qt: QtDriver) -> None:
        """widget=MyWidget shows widget for child tree nodes."""
        nodes = [
            TreeNode(
                "Root",
                children=[
                    TreeNode("Child 1"),
                    TreeNode("Child 2"),
                ],
            ),
        ]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _tree: QTreeView = new(bind="_nodes", children="children", widget=NodeLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(1)

        # Check children exist
        root_index = model.index(0, 0)
        assert_that(model.rowCount(root_index)).is_equal_to(2)

    def test_widget_shows_for_deeply_nested_nodes(self, base_class, decorator, qt: QtDriver) -> None:
        """widget=MyWidget shows widget for deeply nested tree nodes."""
        nodes = [
            TreeNode(
                "Root",
                children=[
                    TreeNode(
                        "Child",
                        children=[
                            TreeNode("Grandchild"),
                        ],
                    ),
                ],
            ),
        ]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _tree: QTreeView = new(bind="_nodes", children="children", widget=NodeLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()

        root_index = model.index(0, 0)
        child_index = model.index(0, 0, root_index)
        assert_that(model.rowCount(child_index)).is_equal_to(1)

    def test_empty_tree_no_crash(self, base_class, decorator, qt: QtDriver) -> None:
        """No crash when tree starts empty."""

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new([])
            _tree: QTreeView = new(bind="_nodes", children="children", widget=NodeLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(0)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewEmbedWithIndex:
    """QTreeView with embed() and selectedIndex injection."""

    def test_embed_with_selected_index(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(MyWidget, selectedIndex='var') injects row index into bare Variable."""
        nodes = [
            TreeNode("Root 1"),
            TreeNode("Root 2"),
        ]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _tree: QTreeView = new(
                bind="_nodes",
                children="children",
                widget=embed(NodeLabelWithIndex, selectedIndex="row_index"),
            )

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewEmbedWithSignalConnection:
    """QTreeView with embed() and signal connections to parent."""

    def test_embed_signal_connection(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(MyWidget, delete_requested='handler') connects signal to parent method."""
        delete_called = {"count": 0}
        nodes = [TreeNode("Root")]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _tree: QTreeView = new(
                bind="_nodes",
                children="children",
                widget=embed(NodeLabelWithDelete, delete_requested="handle_delete"),
            )

            def handle_delete(self) -> None:
                delete_called["count"] += 1

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewLifecycle:
    """QTreeView widget lifecycle management."""

    def test_widget_created_on_node_append_root(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget created when node appended to root."""
        nodes = [TreeNode("Root 1")]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _tree: QTreeView = new(bind="_nodes", children="children", widget=NodeLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(1)

        instance._nodes.append(TreeNode("Root 2"))
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)

    def test_widget_created_on_nested_child_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget created when child node appended to existing parent.

        Regression test: Previously persistent editors were only opened for root-level
        insertions. This test ensures nested children also get their embedded widgets.

        Uses ObservableTreeNode with ObservableList children so the model gets notified
        of nested insertions via the rowsInserted signal.
        """
        # Start with a root node that has no children (using ObservableList for children)
        root_node = ObservableTreeNode("Root")
        nodes = [root_node]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[ObservableTreeNode]] = new(nodes)
            _tree: QTreeView = new(bind="_nodes", children="children", widget=ObservableNodeLabel, expand=True)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        root_index = model.index(0, 0)

        # Root should have embedded widget
        root_widget = instance._tree.indexWidget(root_index)
        assert_that(root_widget).is_not_none()
        assert_that(root_widget).is_instance_of(ObservableNodeLabel)

        # No children yet
        assert_that(model.rowCount(root_index)).is_equal_to(0)

        # Now add a child to the root node (ObservableList.append triggers model notification)
        root_node.children.append(ObservableTreeNode("Child 1"))
        qt.process_events()

        # Child should exist
        assert_that(model.rowCount(root_index)).is_equal_to(1)

        # Child should have embedded widget (this was the bug!)
        child_index = model.index(0, 0, root_index)
        child_widget = instance._tree.indexWidget(child_index)
        assert_that(child_widget).is_not_none()
        assert_that(child_widget).is_instance_of(ObservableNodeLabel)

    def test_widget_created_on_deeply_nested_child_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget created when deeply nested child is appended.

        Regression test: Ensures rowsInserted signal handles deeply nested insertions.

        Uses ObservableTreeNode with ObservableList children so the model gets notified
        of nested insertions via the rowsInserted signal.
        """
        # Start with root -> child structure (using ObservableList for children)
        child_node = ObservableTreeNode("Child")
        root_node = ObservableTreeNode("Root", children=ObservableList([child_node]))
        nodes = [root_node]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[ObservableTreeNode]] = new(nodes)
            _tree: QTreeView = new(bind="_nodes", children="children", widget=ObservableNodeLabel, expand=True)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        root_index = model.index(0, 0)
        child_index = model.index(0, 0, root_index)

        # Both root and child should have widgets
        assert_that(instance._tree.indexWidget(root_index)).is_not_none()
        assert_that(instance._tree.indexWidget(child_index)).is_not_none()

        # Now add a grandchild (ObservableList.append triggers model notification)
        child_node.children.append(ObservableTreeNode("Grandchild"))
        qt.process_events()

        # Grandchild should exist and have widget
        assert_that(model.rowCount(child_index)).is_equal_to(1)
        grandchild_index = model.index(0, 0, child_index)
        grandchild_widget = instance._tree.indexWidget(grandchild_index)
        assert_that(grandchild_widget).is_not_none()
        assert_that(grandchild_widget).is_instance_of(ObservableNodeLabel)

    def test_widget_removed_on_node_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget removed when node removed."""
        nodes = [TreeNode("A"), TreeNode("B")]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _tree: QTreeView = new(bind="_nodes", children="children", widget=NodeLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()
        assert_that(model.rowCount()).is_equal_to(2)

        instance._nodes.pop(0)
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTreeViewSelectedWidget:
    """QTreeView with selectedWidget binding to get embedded widget."""

    def test_selected_widget_is_none_initially(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedWidget is None when nothing is selected."""
        nodes = [TreeNode("Root 1"), TreeNode("Root 2")]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _selected_widget: Variable[Widget | None] = new(None)
            _tree: QTreeView = new(
                bind="_nodes",
                children="children",
                widget=NodeLabel,
                selectedWidget="_selected_widget",
            )

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        # Initially no selection, so widget should be None
        assert_that(instance._selected_widget.value).is_none()

    def test_selected_widget_updates_on_selection(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedWidget updates when a row is selected."""
        nodes = [TreeNode("Root 1"), TreeNode("Root 2")]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _selected_widget: Variable[Widget | None] = new(None)
            _tree: QTreeView = new(
                bind="_nodes",
                children="children",
                widget=NodeLabel,
                selectedWidget="_selected_widget",
            )

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        # Select the first row
        model = instance._tree.model()
        index = model.index(0, 0)
        instance._tree.setCurrentIndex(index)
        qt.process_events()

        # Now the widget should be set to the embedded widget at that index
        # indexWidget returns the persistent editor widget
        embedded = instance._tree.indexWidget(index)
        assert_that(instance._selected_widget.value).is_same_as(embedded)

    def test_selected_widget_updates_on_selection_change(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedWidget updates when selection changes."""
        nodes = [TreeNode("Root 1"), TreeNode("Root 2")]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _selected_widget: Variable[Widget | None] = new(None)
            _tree: QTreeView = new(
                bind="_nodes",
                children="children",
                widget=NodeLabel,
                selectedWidget="_selected_widget",
            )

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._tree.model()

        # Select first row
        index0 = model.index(0, 0)
        instance._tree.setCurrentIndex(index0)
        qt.process_events()
        widget0 = instance._selected_widget.value

        # Select second row
        index1 = model.index(1, 0)
        instance._tree.setCurrentIndex(index1)
        qt.process_events()
        widget1 = instance._selected_widget.value

        # Widgets should be different
        assert_that(widget0).is_not_same_as(widget1)
        assert_that(instance._selected_widget.value).is_same_as(instance._tree.indexWidget(index1))

    def test_selected_widget_is_node_label_instance(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedWidget is an instance of the embedded widget class."""
        nodes = [TreeNode("Root 1")]

        @decorator
        class TestClass(base_class):
            _nodes: Variable[list[TreeNode]] = new(nodes)
            _selected_widget: Variable[Widget | None] = new(None)
            _tree: QTreeView = new(
                bind="_nodes",
                children="children",
                widget=NodeLabel,
                selectedWidget="_selected_widget",
            )

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        # Select the row
        model = instance._tree.model()
        index = model.index(0, 0)
        instance._tree.setCurrentIndex(index)
        qt.process_events()

        # Check it's a NodeLabel instance
        assert_that(instance._selected_widget.value).is_instance_of(NodeLabel)
