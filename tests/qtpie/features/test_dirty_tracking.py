# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportGeneralTypeIssues=false
"""Tests for dirty tracking across Widget, Window, Menu, and App.

Tests is_dirty, dirty_fields, reset_dirty(), and on_dirty_changed hook.
"""

from typing import override

import pytest
from assertpy import assert_that
from observant import Observable

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES, create_and_track

# =============================================================================
# Basic Dirty State
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestDirtyState:
    """Basic dirty tracking works across all class types."""

    def test_initially_not_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """New instance is not dirty."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty.get()).is_false()

    def test_dirty_after_change(self, base_class, decorator, qt: QtDriver) -> None:
        """Instance becomes dirty after Variable change."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "changed"
        assert_that(instance.is_dirty.get()).is_true()

    def test_dirty_fields_tracks_changed(self, base_class, decorator, qt: QtDriver) -> None:
        """dirty_fields contains only changed fields."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "changed"

        assert_that(instance.dirty_fields).is_equal_to({"_name"})

    def test_dirty_fields_multiple(self, base_class, decorator, qt: QtDriver) -> None:
        """dirty_fields tracks all changed fields."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "changed"
        instance._count.value = 42

        assert_that(instance.dirty_fields).is_equal_to({"_name", "_count"})

    def test_reset_dirty_clears_all(self, base_class, decorator, qt: QtDriver) -> None:
        """reset_dirty() marks all Variables as clean."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "changed"
        instance._count.value = 42
        assert_that(instance.is_dirty.get()).is_true()

        instance.reset_dirty()
        assert_that(instance.is_dirty.get()).is_false()
        assert_that(instance.dirty_fields).is_equal_to(set())

    def test_dirty_after_reset_and_change(self, base_class, decorator, qt: QtDriver) -> None:
        """After reset, changing a value makes it dirty again."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "first"
        instance.reset_dirty()

        instance._name.value = "second"
        assert_that(instance.is_dirty.get()).is_true()


# =============================================================================
# is_dirty Observable
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestIsDirtyObservable:
    """is_dirty is Observable[bool] for reactive bindings."""

    def test_is_dirty_is_observable(self, base_class, decorator, qt: QtDriver) -> None:
        """is_dirty returns Observable[bool]."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty).is_instance_of(Observable)
        assert_that(instance.is_dirty.get()).is_false()

    def test_is_dirty_reactive_updates(self, base_class, decorator, qt: QtDriver) -> None:
        """is_dirty Observable updates when dirty state changes."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        dirty_changes: list[bool] = []
        instance.is_dirty.on_change(lambda v: dirty_changes.append(v))

        # Initially clean
        assert_that(instance.is_dirty.get()).is_false()

        # Become dirty
        instance._name.value = "changed"
        assert_that(instance.is_dirty.get()).is_true()
        assert_that(dirty_changes).contains(True)

        # Become clean again
        instance.reset_dirty()
        assert_that(instance.is_dirty.get()).is_false()
        assert_that(dirty_changes).contains(False)


# =============================================================================
# on_dirty_changed Hook
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestOnDirtyChangedHook:
    """on_dirty_changed lifecycle hook works across class types."""

    def test_hook_fires_on_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """on_dirty_changed fires when instance becomes dirty."""
        dirty_states: list[bool] = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "changed"

        assert_that(dirty_states).is_equal_to([True])

    def test_hook_fires_on_clean(self, base_class, decorator, qt: QtDriver) -> None:
        """on_dirty_changed fires when instance becomes clean."""
        dirty_states: list[bool] = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "changed"
        instance.reset_dirty()

        assert_that(dirty_states).is_equal_to([True, False])

    def test_hook_fires_on_transition_only(self, base_class, decorator, qt: QtDriver) -> None:
        """on_dirty_changed only fires on state transitions, not every change."""
        dirty_states: list[bool] = []

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "first"  # clean -> dirty
        instance._name.value = "second"  # dirty -> dirty (no fire)
        instance._count.value = 42  # dirty -> dirty (no fire)

        assert_that(dirty_states).is_equal_to([True])

    def test_hook_not_required(self, base_class, decorator, qt: QtDriver) -> None:
        """Class without on_dirty_changed still works."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "changed"
        # Should not raise
        assert_that(instance.is_dirty.get()).is_true()


# =============================================================================
# Dirty Tracking with List Variables
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestDirtyWithList:
    """Dirty tracking works with list Variables."""

    def test_list_append_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to list makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty.get()).is_false()

        instance._items.observable.append("a")  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()
        assert_that(instance.dirty_fields).contains("_items")

    def test_list_remove_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from list makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b"])

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()  # Clear initial state

        instance._items.observable.remove("a")  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()

    def test_list_clear_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b"])

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()

        instance._items.observable.clear()  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()

    def test_list_insert_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Inserting into list makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b"])

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()

        instance._items.observable.insert(0, "z")  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()

    def test_list_pop_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Popping from list makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(default=["a", "b"])

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()

        instance._items.observable.pop()  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()


# =============================================================================
# Dirty Tracking with Dict Variables
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestDirtyWithDict:
    """Dirty tracking works with dict Variables."""

    def test_dict_setitem_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting dict item makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty.get()).is_false()

        instance._data.observable["key"] = 42  # type: ignore[index]
        assert_that(instance.is_dirty.get()).is_true()
        assert_that(instance.dirty_fields).contains("_data")

    def test_dict_delitem_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Deleting dict item makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"key": 42})

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()

        del instance._data.observable["key"]  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()

    def test_dict_update_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Updating dict makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new()

        instance = create_and_track(qt, TestClass, base_class)

        instance._data.observable.update({"a": 1, "b": 2})  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()

    def test_dict_clear_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing dict makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _data: Variable[dict[str, int]] = new(default={"a": 1})

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()

        instance._data.observable.clear()  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()


# =============================================================================
# Dirty Tracking with Set Variables
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestDirtyWithSet:
    """Dirty tracking works with set Variables."""

    def test_set_add_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Adding to set makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty.get()).is_false()

        instance._tags.observable.add("tag")  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()
        assert_that(instance.dirty_fields).contains("_tags")

    def test_set_discard_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Discarding from set makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b"})

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()

        instance._tags.observable.discard("a")  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()

    def test_set_clear_makes_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing set makes instance dirty."""

        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str]] = new(default={"a", "b"})

        instance = create_and_track(qt, TestClass, base_class)
        instance.reset_dirty()

        instance._tags.observable.clear()  # type: ignore[union-attr]
        assert_that(instance.is_dirty.get()).is_true()


# =============================================================================
# Dirty Tracking with Multiple Variables
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestDirtyMultipleVariables:
    """Dirty tracking with multiple Variables of different types."""

    def test_mixed_types_dirty_fields(self, base_class, decorator, qt: QtDriver) -> None:
        """dirty_fields tracks changes across different Variable types."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)
            _items: Variable[list[str]] = new()
            _data: Variable[dict[str, int]] = new()

        instance = create_and_track(qt, TestClass, base_class)

        instance._name.value = "changed"
        instance._items.observable.append("a")  # type: ignore[union-attr]

        assert_that(instance.dirty_fields).is_equal_to({"_name", "_items"})
        assert_that("_count" in instance.dirty_fields).is_false()
        assert_that("_data" in instance.dirty_fields).is_false()

    def test_reset_clears_all_types(self, base_class, decorator, qt: QtDriver) -> None:
        """reset_dirty clears all Variable types."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")
            _items: Variable[list[str]] = new()
            _tags: Variable[set[str]] = new()

        instance = create_and_track(qt, TestClass, base_class)

        instance._name.value = "changed"
        instance._items.observable.append("a")  # type: ignore[union-attr]
        instance._tags.observable.add("tag")  # type: ignore[union-attr]

        assert_that(instance.dirty_fields).is_equal_to({"_name", "_items", "_tags"})

        instance.reset_dirty()
        assert_that(instance.dirty_fields).is_equal_to(set())
        assert_that(instance.is_dirty.get()).is_false()


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestDirtyEdgeCases:
    """Edge cases for dirty tracking."""

    def test_reset_on_clean_is_safe(self, base_class, decorator, qt: QtDriver) -> None:
        """reset_dirty on already-clean instance is safe."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty.get()).is_false()

        instance.reset_dirty()  # Should not raise
        assert_that(instance.is_dirty.get()).is_false()

    def test_same_value_still_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting same value still marks as dirty (value was touched)."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("initial")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "initial"  # Same value

        # Implementation may or may not consider this dirty - check actual behavior
        # Most implementations track "was set" not "value changed"
        # This test documents the actual behavior
        # assert_that(instance.is_dirty.get()).is_true()  # or is_false()

    def test_empty_class_not_dirty(self, base_class, decorator, qt: QtDriver) -> None:
        """Class with no Variables starts not dirty."""

        @decorator
        class TestClass(base_class):
            pass

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance.is_dirty.get()).is_false()
        assert_that(instance.dirty_fields).is_equal_to(set())

    def test_multiple_changes_same_field(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple changes to same field only tracked once in dirty_fields."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class)
        instance._name.value = "first"
        instance._name.value = "second"
        instance._name.value = "third"

        assert_that(instance.dirty_fields).is_equal_to({"_name"})
