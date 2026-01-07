"""Tests for Window undo/redo integration."""
# pyright: reportAttributeAccessIssue=false
# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false

from dataclasses import dataclass

from assertpy import assert_that

from qtpie import App, Variable, Window, new, window


@dataclass
class Document:
    title: str = ""
    content: str = ""


class TestWindowVariableUndo:
    """Test Window with Variable undo support."""

    def test_window_variable_pushes_undo(self, qapp: App) -> None:
        """Changing a Window Variable should push to undo stack."""
        qapp.undo_stack.clear()

        @window(title="Test")
        class TestWindow(Window):
            name: Variable[str] = new("")

        w = TestWindow()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

    def test_window_variable_undo_restores_value(self, qapp: App) -> None:
        """Undoing Window Variable change should restore old value."""
        qapp.undo_stack.clear()

        @window(title="Test")
        class TestWindow(Window):
            name: Variable[str] = new("")

        w = TestWindow()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        qapp.undo()

        assert_that(w.name.value).is_equal_to("")

    def test_window_variable_redo_reapplies_value(self, qapp: App) -> None:
        """Redoing Window Variable change should reapply new value."""
        qapp.undo_stack.clear()

        @window(title="Test")
        class TestWindow(Window):
            name: Variable[str] = new("")

        w = TestWindow()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        qapp.undo()
        qapp.redo()

        assert_that(w.name.value).is_equal_to("hello")


class TestWindowRecordUndo:
    """Test Window[T] record undo support."""

    def test_window_record_field_pushes_undo(self, qapp: App) -> None:
        """Changing a Window record field should push to undo stack."""
        qapp.undo_stack.clear()

        @window(title="Editor", record=Document("Untitled", ""))
        class EditorWindow(Window[Document]):
            pass

        w = EditorWindow()
        w.record.title = "My Document"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

    def test_window_record_field_undo_restores_value(self, qapp: App) -> None:
        """Undoing Window record field change should restore old value."""
        qapp.undo_stack.clear()

        @window(title="Editor", record=Document("Untitled", ""))
        class EditorWindow(Window[Document]):
            pass

        w = EditorWindow()
        w.record.title = "My Document"
        qapp.undo_stack.flush_pending()

        qapp.undo()

        assert_that(w.record.title).is_equal_to("Untitled")

    def test_window_record_field_redo_reapplies_value(self, qapp: App) -> None:
        """Redoing Window record field change should reapply new value."""
        qapp.undo_stack.clear()

        @window(title="Editor", record=Document("Untitled", ""))
        class EditorWindow(Window[Document]):
            pass

        w = EditorWindow()
        w.record.title = "My Document"
        qapp.undo_stack.flush_pending()

        qapp.undo()
        qapp.redo()

        assert_that(w.record.title).is_equal_to("My Document")


class TestWindowUndoDisabled:
    """Test Window undo can be disabled."""

    def test_window_undo_false_disables_variable_undo(self, qapp: App) -> None:
        """@window(undo=False) should disable Variable undo."""
        qapp.undo_stack.clear()

        @window(title="Test", undo=False)
        class TestWindow(Window):
            name: Variable[str] = new("")

        w = TestWindow()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_false()

    def test_window_undo_false_disables_record_undo(self, qapp: App) -> None:
        """@window(undo=False) should disable record undo."""
        qapp.undo_stack.clear()

        @window(title="Test", undo=False, record=Document("Untitled", ""))
        class TestWindow(Window[Document]):
            pass

        w = TestWindow()
        w.record.title = "My Document"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_false()


class TestWindowUndoDebounce:
    """Test Window undo debouncing."""

    def test_window_custom_debounce_ms(self, qapp: App) -> None:
        """@window(undo_debounce_ms=...) should apply to Variables."""
        qapp.undo_stack.clear()

        @window(title="Test", undo_debounce_ms=100)
        class TestWindow(Window):
            name: Variable[str] = new("")

        w = TestWindow()
        w.name = "hello"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()


class TestWindowFieldUndoOverride:
    """Test field-level undo override on Window."""

    def test_field_undo_false_override(self, qapp: App) -> None:
        """Field-level undo=False should override window-level."""
        qapp.undo_stack.clear()

        @window(title="Test")
        class TestWindow(Window):
            tracked: Variable[str] = new("")
            untracked: Variable[str] = new("", undo=False)

        w = TestWindow()

        # Change tracked field - should push undo
        w.tracked = "hello"
        qapp.undo_stack.flush_pending()
        assert_that(qapp.can_undo.get()).is_true()

        # Clear and change untracked - should NOT push undo
        qapp.undo_stack.clear()
        w.untracked = "world"
        qapp.undo_stack.flush_pending()
        assert_that(qapp.can_undo.get()).is_false()

    def test_field_undo_true_override(self, qapp: App) -> None:
        """Field-level undo=True should override window-level undo=False."""
        qapp.undo_stack.clear()

        @window(title="Test", undo=False)
        class TestWindow(Window):
            tracked: Variable[str] = new("", undo=True)  # Override
            untracked: Variable[str] = new("")  # Inherits undo=False

        w = TestWindow()

        # Change tracked field - should push undo (override)
        w.tracked = "hello"
        qapp.undo_stack.flush_pending()
        assert_that(qapp.can_undo.get()).is_true()

        # Clear and change untracked - should NOT push undo
        qapp.undo_stack.clear()
        w.untracked = "world"
        qapp.undo_stack.flush_pending()
        assert_that(qapp.can_undo.get()).is_false()


class TestWindowUndoMultiple:
    """Test multiple undo/redo with Window."""

    def test_multiple_undo_redo_sequence(self, qapp: App) -> None:
        """Multiple undo/redo operations should work correctly."""
        qapp.undo_stack.clear()

        @window(title="Test")
        class TestWindow(Window):
            name: Variable[str] = new("")

        w = TestWindow()

        # Make changes with flush between
        w.name = "a"
        qapp.undo_stack.flush_pending()
        w.name = "ab"
        qapp.undo_stack.flush_pending()
        w.name = "abc"
        qapp.undo_stack.flush_pending()

        # Undo all
        assert_that(w.name.value).is_equal_to("abc")
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
