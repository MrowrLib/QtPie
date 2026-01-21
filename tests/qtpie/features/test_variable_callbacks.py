# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownLambdaType=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
"""Tests for Variable callbacks (onChange, onInsert, etc.) across all QtPie class types.

These callbacks were originally implemented for State, but should work on all
QtPie classes that host Variables: Widget, Window, Dialog, Menu, App, WidgetBase, State.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES_WITH_STATE, WIDGET_CLASS_TYPES, create_and_track


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES_WITH_STATE)
class TestOnChangeCallback:
    """onChange callback works across all class types."""

    def test_on_change_called_on_value_change(self, base_class, decorator, qt: QtDriver) -> None:
        """onChange is called when value changes."""
        calls: list[int] = []

        @decorator
        class TestClass(base_class):
            count: Variable[int] = new(0, onChange="_on_changed")

            def _on_changed(self) -> None:
                calls.append(self.count.value)

        instance = create_and_track(qt, TestClass, base_class)
        instance.count.value = 5

        assert_that(calls).is_equal_to([5])

    def test_on_change_with_value_parameter(self, base_class, decorator, qt: QtDriver) -> None:
        """onChange can receive the new value as parameter."""
        calls: list[str] = []

        @decorator
        class TestClass(base_class):
            name: Variable[str] = new("", onChange="_on_changed")

            def _on_changed(self, value: str) -> None:
                calls.append(value)

        instance = create_and_track(qt, TestClass, base_class)
        instance.name.value = "hello"

        assert_that(calls).is_equal_to(["hello"])

    def test_on_change_multiple_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """onChange is called for each value change."""
        calls: list[int] = []

        @decorator
        class TestClass(base_class):
            count: Variable[int] = new(0, onChange="_on_changed")

            def _on_changed(self, value: int) -> None:
                calls.append(value)

        instance = create_and_track(qt, TestClass, base_class)
        instance.count.value = 1
        instance.count.value = 2
        instance.count.value = 3

        assert_that(calls).is_equal_to([1, 2, 3])

    def test_on_change_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onChange can be a lambda."""
        calls: list[int] = []

        @decorator
        class TestClass(base_class):
            count: Variable[int] = new(0, onChange=lambda v: calls.append(v))

        instance = create_and_track(qt, TestClass, base_class)
        instance.count.value = 42

        assert_that(calls).is_equal_to([42])


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES_WITH_STATE)
class TestListCallbacks:
    """List Variable callbacks (onInsert, onRemove) work across all class types."""

    def test_on_insert_called(self, base_class, decorator, qt: QtDriver) -> None:
        """onInsert is called when items are appended."""
        inserts: list[str] = []

        @decorator
        class TestClass(base_class):
            items: Variable[list[str]] = new([], onInsert="_on_insert")

            def _on_insert(self, item: str, index: int) -> None:
                inserts.append(item)

        instance = create_and_track(qt, TestClass, base_class)
        instance.items.append("a")
        instance.items.append("b")

        assert_that(inserts).is_equal_to(["a", "b"])

    def test_on_remove_called(self, base_class, decorator, qt: QtDriver) -> None:
        """onRemove is called when items are removed."""
        removes: list[str] = []

        @decorator
        class TestClass(base_class):
            items: Variable[list[str]] = new(["a", "b", "c"], onRemove="_on_remove")

            def _on_remove(self, item: str, index: int) -> None:
                removes.append(item)

        instance = create_and_track(qt, TestClass, base_class)
        instance.items.remove("b")

        assert_that(removes).is_equal_to(["b"])

    def test_list_insert_and_remove_together(self, base_class, decorator, qt: QtDriver) -> None:
        """onInsert and onRemove work together."""
        inserts: list[str] = []
        removes: list[str] = []

        @decorator
        class TestClass(base_class):
            items: Variable[list[str]] = new([], onInsert="_on_insert", onRemove="_on_remove")

            def _on_insert(self, item: str, index: int) -> None:
                inserts.append(item)

            def _on_remove(self, item: str, index: int) -> None:
                removes.append(item)

        instance = create_and_track(qt, TestClass, base_class)
        instance.items.append("a")
        instance.items.append("b")
        instance.items.remove("a")

        assert_that(inserts).is_equal_to(["a", "b"])
        assert_that(removes).is_equal_to(["a"])

    def test_on_insert_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """onInsert can be a lambda."""
        inserts: list[str] = []

        @decorator
        class TestClass(base_class):
            items: Variable[list[str]] = new([], onInsert=lambda item, i: inserts.append(item))

        instance = create_and_track(qt, TestClass, base_class)
        instance.items.append("x")

        assert_that(inserts).is_equal_to(["x"])


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES_WITH_STATE)
class TestSetCallbacks:
    """Set Variable callbacks (onAdd, onRemove) work across all class types."""

    def test_on_add_called(self, base_class, decorator, qt: QtDriver) -> None:
        """onAdd is called when items are added to set."""
        adds: list[str] = []

        @decorator
        class TestClass(base_class):
            tags: Variable[set[str]] = new(set(), onAdd="_on_add")

            def _on_add(self, item: str) -> None:
                adds.append(item)

        instance = create_and_track(qt, TestClass, base_class)
        instance.tags.add("python")
        instance.tags.add("rust")

        assert_that(adds).is_equal_to(["python", "rust"])

    def test_on_remove_called_for_set(self, base_class, decorator, qt: QtDriver) -> None:
        """onRemove is called when items are removed from set."""
        removes: list[str] = []

        @decorator
        class TestClass(base_class):
            tags: Variable[set[str]] = new({"a", "b", "c"}, onRemove="_on_remove")

            def _on_remove(self, item: str) -> None:
                removes.append(item)

        instance = create_and_track(qt, TestClass, base_class)
        instance.tags.discard("b")

        assert_that(removes).is_equal_to(["b"])

    def test_set_add_and_remove_together(self, base_class, decorator, qt: QtDriver) -> None:
        """onAdd and onRemove work together for sets."""
        adds: list[str] = []
        removes: list[str] = []

        @decorator
        class TestClass(base_class):
            tags: Variable[set[str]] = new(set(), onAdd="_on_add", onRemove="_on_remove")

            def _on_add(self, item: str) -> None:
                adds.append(item)

            def _on_remove(self, item: str) -> None:
                removes.append(item)

        instance = create_and_track(qt, TestClass, base_class)
        instance.tags.add("x")
        instance.tags.add("y")
        instance.tags.discard("x")

        assert_that(adds).is_equal_to(["x", "y"])
        assert_that(removes).is_equal_to(["x"])


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES_WITH_STATE)
class TestDictCallbacks:
    """Dict Variable callbacks (onSet, onRemove) work across all class types."""

    def test_on_set_called(self, base_class, decorator, qt: QtDriver) -> None:
        """onSet is called when items are set in dict."""
        sets: list[str] = []

        @decorator
        class TestClass(base_class):
            config: Variable[dict[str, int]] = new({}, onSet="_on_set")

            def _on_set(self, key: str, value: int) -> None:
                sets.append(f"{key}={value}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.config["x"] = 10
        instance.config["y"] = 20

        assert_that(sets).is_equal_to(["x=10", "y=20"])

    def test_on_remove_called_for_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """onRemove is called when items are deleted from dict."""
        removes: list[str] = []

        @decorator
        class TestClass(base_class):
            config: Variable[dict[str, int]] = new({"a": 1, "b": 2}, onRemove="_on_remove")

            def _on_remove(self, key: str, value: int) -> None:
                removes.append(f"{key}={value}")

        instance = create_and_track(qt, TestClass, base_class)
        del instance.config["a"]

        assert_that(removes).is_equal_to(["a=1"])

    def test_dict_set_and_remove_together(self, base_class, decorator, qt: QtDriver) -> None:
        """onSet and onRemove work together for dicts."""
        sets: list[str] = []
        removes: list[str] = []

        @decorator
        class TestClass(base_class):
            config: Variable[dict[str, int]] = new({}, onSet="_on_set", onRemove="_on_remove")

            def _on_set(self, key: str, value: int) -> None:
                sets.append(f"{key}={value}")

            def _on_remove(self, key: str, value: int) -> None:
                removes.append(f"{key}={value}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.config["x"] = 10
        instance.config["y"] = 20
        del instance.config["x"]

        assert_that(sets).is_equal_to(["x=10", "y=20"])
        assert_that(removes).is_equal_to(["x=10"])


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestCallbackIntegration:
    """Integration tests for callbacks with UI binding scenarios (widget classes only)."""

    def test_callback_updates_ui(self, base_class, decorator, qt: QtDriver) -> None:
        """Callback can update UI in response to Variable change."""

        @decorator
        class TestClass(base_class):
            count: Variable[int] = new(0, onChange="_update_label")
            label: QLabel = new("Count: 0")

            def _update_label(self) -> None:
                self.label.setText(f"Count: {self.count.value}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.count.value = 42

        assert_that(instance.label.text()).is_equal_to("Count: 42")

    def test_callback_chain(self, base_class, decorator, qt: QtDriver) -> None:
        """Callbacks can trigger other Variable changes."""
        history: list[str] = []

        @decorator
        class TestClass(base_class):
            input_value: Variable[str] = new("", onChange="_on_input")
            output_value: Variable[str] = new("", onChange="_on_output")

            def _on_input(self, value: str) -> None:
                history.append(f"input:{value}")
                self.output_value.value = value.upper()

            def _on_output(self, value: str) -> None:
                history.append(f"output:{value}")

        instance = create_and_track(qt, TestClass, base_class)
        instance.input_value.value = "hello"

        assert_that(history).is_equal_to(["input:hello", "output:HELLO"])
        assert_that(instance.output_value.value).is_equal_to("HELLO")
