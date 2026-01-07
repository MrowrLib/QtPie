"""Tests for Variable undo/redo integration."""
# pyright: reportAttributeAccessIssue=false

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLineEdit

from qtpie import App, Widget, new, widget
from qtpie.variable import Variable


@dataclass
class Dog:
    name: str = ""
    age: int = 0


class TestVariableUndoBasic:
    """Test Variable pushes to undo stack."""

    def test_variable_str_pushes_undo(self, qapp: App) -> None:
        """Changing Variable[str] should push to undo stack."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("")

        w = TestWidget()
        w.name = "hello"

        # Wait for debounce (default 1000ms, but we can flush)
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

    def test_variable_str_undo_restores_value(self, qapp: App) -> None:
        """Undoing Variable[str] change should restore old value."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("")

        w = TestWidget()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        qapp.undo()

        assert_that(w.name.value).is_equal_to("")

    def test_variable_str_redo_reapplies_value(self, qapp: App) -> None:
        """Redoing Variable[str] change should reapply new value."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("")

        w = TestWidget()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        qapp.undo()
        qapp.redo()

        assert_that(w.name.value).is_equal_to("hello")


class TestVariableUndoList:
    """Test Variable[list[T]] undo."""

    def test_variable_list_pushes_undo(self, qapp: App) -> None:
        """Changing Variable[list[str]] should push to undo stack."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            items: Variable[list[str]] = new([])

        w = TestWidget()
        w.items = ["a", "b", "c"]
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

    def test_variable_list_undo_restores_value(self, qapp: App) -> None:
        """Undoing Variable[list[str]] should restore empty list."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            items: Variable[list[str]] = new([])

        w = TestWidget()
        w.items = ["a", "b", "c"]
        qapp.undo_stack.flush_pending()

        qapp.undo()

        assert_that(w.items.value).is_equal_to([])

    def test_variable_list_redo_reapplies_value(self, qapp: App) -> None:
        """Redoing Variable[list[str]] should reapply list."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            items: Variable[list[str]] = new([])

        w = TestWidget()
        w.items = ["a", "b", "c"]
        qapp.undo_stack.flush_pending()

        qapp.undo()
        qapp.redo()

        assert_that(w.items.value).is_equal_to(["a", "b", "c"])


class TestVariableUndoDict:
    """Test Variable[dict[K, V]] undo."""

    def test_variable_dict_pushes_undo(self, qapp: App) -> None:
        """Changing Variable[dict[str, int]] should push to undo stack."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            scores: Variable[dict[str, int]] = new({})

        w = TestWidget()
        w.scores = {"alice": 100, "bob": 85}
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

    def test_variable_dict_undo_restores_value(self, qapp: App) -> None:
        """Undoing Variable[dict[str, int]] should restore empty dict."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            scores: Variable[dict[str, int]] = new({})

        w = TestWidget()
        w.scores = {"alice": 100, "bob": 85}
        qapp.undo_stack.flush_pending()

        qapp.undo()

        assert_that(w.scores.value).is_equal_to({})

    def test_variable_dict_redo_reapplies_value(self, qapp: App) -> None:
        """Redoing Variable[dict[str, int]] should reapply dict."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            scores: Variable[dict[str, int]] = new({})

        w = TestWidget()
        w.scores = {"alice": 100, "bob": 85}
        qapp.undo_stack.flush_pending()

        qapp.undo()
        qapp.redo()

        assert_that(w.scores.value).is_equal_to({"alice": 100, "bob": 85})


class TestVariableUndoWithWidget:
    """Test Variable[T, QWidget] undo."""

    def test_variable_with_widget_pushes_undo(self, qapp: App) -> None:
        """Variable[str, QLineEdit] should push to undo stack."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str, QLineEdit] = new("")

        w = TestWidget()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

    def test_variable_with_widget_undo_restores_value(self, qapp: App) -> None:
        """Undoing Variable[str, QLineEdit] should restore value."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str, QLineEdit] = new("")

        w = TestWidget()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        qapp.undo()

        assert_that(w.name.value).is_equal_to("")


class TestVariableUndoDisabled:
    """Test undo can be disabled."""

    def test_variable_undo_false_disables_undo(self, qapp: App) -> None:
        """Variable with undo=False should not push to undo stack."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("", undo=False)

        w = TestWidget()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_false()

    def test_widget_undo_false_disables_all_variables(self, qapp: App) -> None:
        """@widget(undo=False) should disable undo for all variables."""
        qapp.undo_stack.clear()

        @widget(undo=False)
        class TestWidget(Widget):
            name: Variable[str] = new("")
            age: Variable[int] = new(0)

        w = TestWidget()
        w.name = "hello"
        w.age = 25
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_false()

    def test_field_undo_override_widget_undo(self, qapp: App) -> None:
        """Field-level undo=True should override widget-level undo=False."""
        qapp.undo_stack.clear()

        @widget(undo=False)
        class TestWidget(Widget):
            name: Variable[str] = new("", undo=True)  # Override
            age: Variable[int] = new(0)  # Inherits undo=False

        w = TestWidget()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

        # Clear and test age - should not push
        qapp.undo_stack.clear()
        w.age = 25
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_false()


class TestVariableUndoDebounce:
    """Test Variable debouncing."""

    def test_rapid_changes_merge(self, qapp: App) -> None:
        """Multiple rapid changes should merge into one undo action."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("")

        w = TestWidget()

        # Rapid changes before debounce timer fires
        w.name = "a"
        w.name = "ab"
        w.name = "abc"
        qapp.undo_stack.flush_pending()

        # Should only have one undo action
        assert_that(qapp.can_undo.get()).is_true()
        qapp.undo()
        assert_that(w.name.value).is_equal_to("")
        assert_that(qapp.can_undo.get()).is_false()

    def test_different_fields_not_merged(self, qapp: App) -> None:
        """Changes to different fields should not merge."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("")
            age: Variable[int] = new(0)

        w = TestWidget()

        w.name = "hello"
        w.age = 25
        qapp.undo_stack.flush_pending()

        # Should have two undo actions
        assert_that(qapp.can_undo.get()).is_true()
        qapp.undo()  # Undo age
        qapp.undo()  # Undo name
        assert_that(w.name.value).is_equal_to("")
        assert_that(w.age.value).is_equal_to(0)

    def test_custom_debounce_ms(self, qapp: App) -> None:
        """Custom undo_debounce_ms should be respected."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("", undo_debounce_ms=100)

        w = TestWidget()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()


class TestVariableUndoMultiple:
    """Test multiple undo/redo operations."""

    def test_multiple_undo_redo(self, qapp: App) -> None:
        """Multiple undo/redo operations should work correctly."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            name: Variable[str] = new("")

        w = TestWidget()

        # Make changes with flush between to create separate actions
        w.name = "a"
        qapp.undo_stack.flush_pending()
        w.name = "ab"
        qapp.undo_stack.flush_pending()
        w.name = "abc"
        qapp.undo_stack.flush_pending()

        assert_that(w.name.value).is_equal_to("abc")

        # Undo all
        qapp.undo()
        assert_that(w.name.value).is_equal_to("ab")
        qapp.undo()
        assert_that(w.name.value).is_equal_to("a")
        qapp.undo()
        assert_that(w.name.value).is_equal_to("")

        # Redo all
        qapp.redo()
        assert_that(w.name.value).is_equal_to("a")
        qapp.redo()
        assert_that(w.name.value).is_equal_to("ab")
        qapp.redo()
        assert_that(w.name.value).is_equal_to("abc")


class TestVariableUndoComplexObject:
    """Test Variable[ComplexObject] undo behavior."""

    def test_variable_complex_object_uses_observable_proxy(self, qapp: App) -> None:
        """Variable[Dog] uses ObservableProxy and skips undo (handled by RecordVariable)."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget):
            dog: Variable[Dog] = new(Dog("Fido", 3))

        w = TestWidget()
        # Setting the whole value for a complex object - this uses ObservableProxy
        # and undo is intentionally skipped (RecordVariable handles field-level undo)
        w.dog = Dog("Rex", 5)
        qapp.undo_stack.flush_pending()

        # ObservableProxy changes don't push to undo stack
        # (Individual field changes via RecordVariable will be tested separately)
        assert_that(qapp.can_undo.get()).is_false()
