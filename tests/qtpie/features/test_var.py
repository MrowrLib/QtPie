# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Tests for self.var() method across Widget, Window, Menu, and App.

Tests variable resolution from self, parent hierarchy, and QApplication.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES, QWIDGET_CLASS_TYPES, create_and_track

# =============================================================================
# Basic var() resolution (self)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVarSelf:
    """var() resolves variables on self."""

    def test_var_resolves_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """var('name') resolves Variable on self."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(42)

        instance = create_and_track(qt, TestClass, base_class)
        result = instance.var("count", int)

        assert_that(result).is_equal_to(42)

    def test_var_resolves_with_underscore(self, base_class, decorator, qt: QtDriver) -> None:
        """var('_name') resolves Variable with underscore prefix."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(99)

        instance = create_and_track(qt, TestClass, base_class)
        result = instance.var("_count", int)

        assert_that(result).is_equal_to(99)

    def test_var_resolves_plain_attribute(self, base_class, decorator, qt: QtDriver) -> None:
        """var() resolves plain attributes (not just Variables)."""

        @decorator
        class TestClass(base_class):
            my_value: int = 123

        instance = create_and_track(qt, TestClass, base_class)
        result = instance.var("my_value", int)

        assert_that(result).is_equal_to(123)

    def test_var_raises_for_missing(self, base_class, decorator, qt: QtDriver) -> None:
        """var() raises AttributeError for missing variable."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)

        with pytest.raises(AttributeError, match="nonexistent"):
            instance.var("nonexistent", int)


# =============================================================================
# Parent hierarchy resolution
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestVarParentHierarchy:
    """var() resolves variables from parent widget hierarchy."""

    def test_var_resolves_from_parent(self, base_class, decorator, qt: QtDriver) -> None:
        """var() finds Variable on parent widget."""

        @widget
        class Child(Widget):
            label: QLabel = new("child")

            def get_parent_count(self) -> int:
                return self.var("count", int)

        @decorator
        class Parent(base_class):
            _count: Variable[int] = new(42)
            child: Child = new()

        parent = create_and_track(qt, Parent, base_class)
        result = parent.child.get_parent_count()

        assert_that(result).is_equal_to(42)

    def test_var_resolves_from_grandparent(self, base_class, decorator, qt: QtDriver) -> None:
        """var() walks up multiple levels to find Variable."""

        @widget
        class GrandChild(Widget):
            label: QLabel = new("grandchild")

            def get_root_value(self) -> str:
                return self.var("root_value", str)

        @widget
        class Child(Widget):
            grandchild: GrandChild = new()

        @decorator
        class Root(base_class):
            _root_value: Variable[str] = new("from_root")
            child: Child = new()

        root = create_and_track(qt, Root, base_class)
        result = root.child.grandchild.get_root_value()

        assert_that(result).is_equal_to("from_root")

    def test_var_prefers_closer_parent(self, base_class, decorator, qt: QtDriver) -> None:
        """var() returns value from closest parent when multiple have same name."""

        @widget
        class GrandChild(Widget):
            label: QLabel = new("grandchild")

            def get_count(self) -> int:
                return self.var("count", int)

        @widget
        class Child(Widget):
            _count: Variable[int] = new(100)  # Closer
            grandchild: GrandChild = new()

        @decorator
        class Root(base_class):
            _count: Variable[int] = new(1)  # Further
            child: Child = new()

        root = create_and_track(qt, Root, base_class)
        result = root.child.grandchild.get_count()

        assert_that(result).is_equal_to(100)

    def test_var_prefers_self_over_parent(self, base_class, decorator, qt: QtDriver) -> None:
        """var() returns value from self if present, not parent."""

        @widget
        class Child(Widget):
            _count: Variable[int] = new(999)

            def get_count(self) -> int:
                return self.var("count", int)

        @decorator
        class Parent(base_class):
            _count: Variable[int] = new(1)
            child: Child = new()

        parent = create_and_track(qt, Parent, base_class)
        result = parent.child.get_count()

        assert_that(result).is_equal_to(999)


# =============================================================================
# Reactivity
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestVarReactivity:
    """var() returns current value (reactive updates work)."""

    def test_var_returns_updated_value(self, base_class, decorator, qt: QtDriver) -> None:
        """var() returns the current value after Variable changes."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance.var("count", int)).is_equal_to(0)

        instance._count.value = 42

        assert_that(instance.var("count", int)).is_equal_to(42)


@pytest.mark.parametrize("base_class,decorator", QWIDGET_CLASS_TYPES)
class TestVarParentReactivity:
    """var() returns updated values from parent hierarchy."""

    def test_var_reflects_parent_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """var() returns updated value when parent Variable changes."""

        @widget
        class Child(Widget):
            label: QLabel = new("child")

            def get_parent_count(self) -> int:
                return self.var("count", int)

        @decorator
        class Parent(base_class):
            _count: Variable[int] = new(0)
            child: Child = new()

        parent = create_and_track(qt, Parent, base_class)

        assert_that(parent.child.get_parent_count()).is_equal_to(0)

        parent._count.value = 123

        assert_that(parent.child.get_parent_count()).is_equal_to(123)
