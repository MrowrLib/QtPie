"""Tests for RecordVariable undo/redo integration."""
# pyright: reportAttributeAccessIssue=false

from dataclasses import dataclass

from assertpy import assert_that

from qtpie import App, Widget, widget


@dataclass
class Person:
    name: str = ""
    age: int = 0


@dataclass
class Address:
    street: str = ""
    city: str = ""


class TestRecordUndoBasic:
    """Test RecordVariable pushes to undo stack."""

    def test_record_field_change_pushes_undo(self, qapp: App) -> None:
        """Changing a record field should push to undo stack."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

    def test_record_field_undo_restores_value(self, qapp: App) -> None:
        """Undoing a record field change should restore old value."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()

        qapp.undo()

        assert_that(w.record.name).is_equal_to("Alice")

    def test_record_field_redo_reapplies_value(self, qapp: App) -> None:
        """Redoing a record field change should reapply new value."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()

        qapp.undo()
        qapp.redo()

        assert_that(w.record.name).is_equal_to("Bob")


class TestRecordUndoMultipleFields:
    """Test undo with multiple record fields."""

    def test_multiple_fields_create_separate_undo_actions(self, qapp: App) -> None:
        """Changes to different record fields should create separate undo actions."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.name = "Bob"
        w.record.age = 25
        qapp.undo_stack.flush_pending()

        # Should have two separate undo actions
        assert_that(qapp.can_undo.get()).is_true()
        qapp.undo()  # Undo age
        qapp.undo()  # Undo name

        assert_that(w.record.name).is_equal_to("Alice")
        assert_that(w.record.age).is_equal_to(30)

    def test_rapid_changes_to_same_field_merge(self, qapp: App) -> None:
        """Rapid changes to the same record field should merge."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        # Rapid changes before debounce fires
        w.record.name = "B"
        w.record.name = "Bo"
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()

        # Should only have one undo action (merged)
        qapp.undo()
        assert_that(w.record.name).is_equal_to("Alice")
        assert_that(qapp.can_undo.get()).is_false()


class TestRecordUndoDisabled:
    """Test undo can be disabled for records."""

    def test_widget_undo_false_disables_record_undo(self, qapp: App) -> None:
        """@widget(undo=False) should disable record undo."""
        qapp.undo_stack.clear()

        @widget(undo=False, record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_false()


class TestRecordUndoDebounce:
    """Test record field debouncing."""

    def test_custom_debounce_ms(self, qapp: App) -> None:
        """Custom undo_debounce_ms on widget should apply to record."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30), undo_debounce_ms=100)
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()


class TestRecordUndoWithSetRecord:
    """Test undo when setting record value in __setup__."""

    def test_record_set_in_setup_has_undo(self, qapp: App) -> None:
        """Setting record in __setup__ should support undo for field changes."""
        qapp.undo_stack.clear()

        @widget
        class TestWidget(Widget[Person]):
            def __setup__(self) -> None:
                self.record = Person("Alice", 30)

        w = TestWidget()
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()

        assert_that(qapp.can_undo.get()).is_true()

        qapp.undo()
        assert_that(w.record.name).is_equal_to("Alice")


class TestRecordUndoMultipleUndoRedo:
    """Test multiple undo/redo operations with records."""

    def test_multiple_undo_redo_sequence(self, qapp: App) -> None:
        """Multiple undo/redo operations should work correctly."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()

        # Make changes with flush between to create separate actions
        w.record.name = "Bob"
        qapp.undo_stack.flush_pending()
        w.record.name = "Charlie"
        qapp.undo_stack.flush_pending()
        w.record.name = "Dave"
        qapp.undo_stack.flush_pending()

        # Undo all
        assert_that(w.record.name).is_equal_to("Dave")
        qapp.undo()
        assert_that(w.record.name).is_equal_to("Charlie")
        qapp.undo()
        assert_that(w.record.name).is_equal_to("Bob")
        qapp.undo()
        assert_that(w.record.name).is_equal_to("Alice")

        # Redo all
        qapp.redo()
        assert_that(w.record.name).is_equal_to("Bob")
        qapp.redo()
        assert_that(w.record.name).is_equal_to("Charlie")
        qapp.redo()
        assert_that(w.record.name).is_equal_to("Dave")


class TestRecordUndoIntField:
    """Test undo with int record fields."""

    def test_int_field_undo(self, qapp: App) -> None:
        """Int field undo should work correctly."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.age = 25
        qapp.undo_stack.flush_pending()

        qapp.undo()
        assert_that(w.record.age).is_equal_to(30)

    def test_int_field_redo(self, qapp: App) -> None:
        """Int field redo should work correctly."""
        qapp.undo_stack.clear()

        @widget(record=Person("Alice", 30))
        class TestWidget(Widget[Person]):
            pass

        w = TestWidget()
        w.record.age = 25
        qapp.undo_stack.flush_pending()

        qapp.undo()
        qapp.redo()
        assert_that(w.record.age).is_equal_to(25)
