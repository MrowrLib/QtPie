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


# Simple embedded widget for tree nodes
@widget
class NodeLabel(Widget[TreeNode]):
    """A simple widget that displays node info."""

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
