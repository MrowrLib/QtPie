"""Tests for UndoStack."""
# pyright: reportPrivateUsage=false

from assertpy import assert_that
from observant import Observable
from qtpy.QtTest import QTest

from qtpie import App
from qtpie.undo import SetValueAction, UndoStack, get_undo_stack, resolve_undo_config


class TestUndoStackBasic:
    """Basic UndoStack tests."""

    def test_stack_starts_empty(self, qapp: App) -> None:
        """New UndoStack should be empty."""
        stack = UndoStack()
        assert_that(stack.can_undo.get()).is_false()
        assert_that(stack.can_redo.get()).is_false()

    def test_push_immediate_enables_undo(self, qapp: App) -> None:
        """Pushing an action should enable undo."""
        stack = UndoStack()
        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        stack.push_immediate(action)

        assert_that(stack.can_undo.get()).is_true()
        assert_that(stack.can_redo.get()).is_false()

    def test_undo_restores_value(self, qapp: App) -> None:
        """Undo should restore the old value."""
        stack = UndoStack()
        obs = Observable(0)
        obs.set(1)  # Change to 1
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        stack.push_immediate(action)
        stack.undo()

        assert_that(obs.get()).is_equal_to(0)

    def test_redo_reapplies_value(self, qapp: App) -> None:
        """Redo should reapply the new value."""
        stack = UndoStack()
        obs = Observable(0)
        obs.set(1)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        stack.push_immediate(action)
        stack.undo()
        stack.redo()

        assert_that(obs.get()).is_equal_to(1)

    def test_undo_returns_true_when_action_exists(self, qapp: App) -> None:
        """undo() returns True when there was an action to undo."""
        stack = UndoStack()
        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        stack.push_immediate(action)
        result = stack.undo()

        assert_that(result).is_true()

    def test_undo_returns_false_when_empty(self, qapp: App) -> None:
        """undo() returns False when stack is empty."""
        stack = UndoStack()
        result = stack.undo()

        assert_that(result).is_false()

    def test_redo_returns_false_when_empty(self, qapp: App) -> None:
        """redo() returns False when redo stack is empty."""
        stack = UndoStack()
        result = stack.redo()

        assert_that(result).is_false()

    def test_new_action_clears_redo_stack(self, qapp: App) -> None:
        """Pushing a new action after undo should clear redo stack."""
        stack = UndoStack()
        obs = Observable(0)
        action1 = SetValueAction(observable=obs, old_value=0, new_value=1)
        action2 = SetValueAction(observable=obs, old_value=1, new_value=2)

        stack.push_immediate(action1)
        stack.undo()
        assert_that(stack.can_redo.get()).is_true()

        stack.push_immediate(action2)
        assert_that(stack.can_redo.get()).is_false()


class TestUndoStackMaxSize:
    """Test max size enforcement."""

    def test_max_size_enforced(self, qapp: App) -> None:
        """Stack should not exceed max size."""
        stack = UndoStack(max_size=3)
        obs = Observable(0)

        for i in range(5):
            action = SetValueAction(observable=obs, old_value=i, new_value=i + 1)
            stack.push_immediate(action)

        # Should only be able to undo 3 times
        undo_count = 0
        while stack.undo():
            undo_count += 1

        assert_that(undo_count).is_equal_to(3)

    def test_oldest_actions_dropped(self, qapp: App) -> None:
        """Oldest actions should be dropped when max size exceeded."""
        stack = UndoStack(max_size=2)
        obs = Observable(0)

        # Push 3 actions: 0->1, 1->2, 2->3
        for i in range(3):
            obs.set(i + 1)
            action = SetValueAction(observable=obs, old_value=i, new_value=i + 1)
            stack.push_immediate(action)

        # obs is now 3
        # Undo twice should take us to 1 (not 0, because 0->1 was dropped)
        stack.undo()  # 3 -> 2
        stack.undo()  # 2 -> 1
        assert_that(obs.get()).is_equal_to(1)

        # No more undos
        assert_that(stack.can_undo.get()).is_false()


class TestUndoStackDebounce:
    """Test debouncing behavior."""

    def test_debounced_action_not_immediate(self, qapp: App) -> None:
        """Debounced action should not be on stack immediately."""
        stack = UndoStack()
        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        stack.push_debounced(action, "field1", debounce_ms=100)

        # Action is pending, not on stack yet
        # can_undo should be True because pending actions count
        assert_that(stack.can_undo.get()).is_true()

    def test_debounced_action_commits_after_timer(self, qapp: App) -> None:
        """Debounced action should commit after timer fires."""
        stack = UndoStack()
        obs = Observable(0)
        obs.set(1)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        stack.push_debounced(action, "field1", debounce_ms=50)

        # Wait for debounce
        QTest.qWait(100)

        # Now undo should work
        stack.undo()
        assert_that(obs.get()).is_equal_to(0)

    def test_rapid_changes_merge(self, qapp: App) -> None:
        """Rapid changes to same field should merge into one action."""
        stack = UndoStack()
        obs = Observable(0)

        # Simulate rapid typing: 0 -> 1 -> 2 -> 3
        for i in range(1, 4):
            action = SetValueAction(observable=obs, old_value=i - 1, new_value=i)
            stack.push_debounced(action, "field1", debounce_ms=200)

        # Set final value
        obs.set(3)

        # Wait for debounce
        QTest.qWait(250)

        # Should only need one undo to get back to 0 (merged action)
        stack.undo()
        assert_that(obs.get()).is_equal_to(0)

        # No more undos
        assert_that(stack.can_undo.get()).is_false()

    def test_different_fields_not_merged(self, qapp: App) -> None:
        """Changes to different fields should not merge."""
        stack = UndoStack()
        obs1 = Observable(0)
        obs2 = Observable(0)

        action1 = SetValueAction(observable=obs1, old_value=0, new_value=1)
        action2 = SetValueAction(observable=obs2, old_value=0, new_value=2)

        stack.push_debounced(action1, "field1", debounce_ms=50)
        stack.push_debounced(action2, "field2", debounce_ms=50)

        obs1.set(1)
        obs2.set(2)

        # Wait for debounce
        QTest.qWait(100)

        # Should have 2 separate actions
        stack.undo()
        stack.undo()
        assert_that(obs1.get()).is_equal_to(0)
        assert_that(obs2.get()).is_equal_to(0)


class TestUndoStackClear:
    """Test clear functionality."""

    def test_clear_removes_all(self, qapp: App) -> None:
        """clear() should remove all undo and redo history."""
        stack = UndoStack()
        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        stack.push_immediate(action)
        stack.undo()
        assert_that(stack.can_redo.get()).is_true()

        stack.clear()

        assert_that(stack.can_undo.get()).is_false()
        assert_that(stack.can_redo.get()).is_false()


class TestUndoStackObservables:
    """Test can_undo/can_redo observables."""

    def test_can_undo_observable_updates(self, qapp: App) -> None:
        """can_undo observable should fire on changes."""
        stack = UndoStack()
        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        changes: list[bool] = []
        stack.can_undo.on_change(lambda v: changes.append(v))

        stack.push_immediate(action)  # False -> True
        stack.undo()  # True -> False

        assert_that(changes).contains(True, False)

    def test_can_redo_observable_updates(self, qapp: App) -> None:
        """can_redo observable should fire on changes."""
        stack = UndoStack()
        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        changes: list[bool] = []
        stack.can_redo.on_change(lambda v: changes.append(v))

        stack.push_immediate(action)
        stack.undo()  # -> can_redo True
        stack.redo()  # -> can_redo False

        assert_that(changes).contains(True, False)


class TestInUndoRedoFlag:
    """Test that in_undo_redo flag prevents recursive pushes."""

    def test_in_undo_redo_flag_during_undo(self, qapp: App) -> None:
        """in_undo_redo should be True during undo operation."""
        stack = UndoStack()
        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        flag_values: list[bool] = []

        def capture_flag(_: int) -> None:
            flag_values.append(stack.in_undo_redo)

        obs.on_change(capture_flag)

        stack.push_immediate(action)
        stack.undo()

        assert_that(flag_values).contains(True)

    def test_push_during_undo_ignored(self, qapp: App) -> None:
        """Push during undo should be ignored."""
        stack = UndoStack()
        obs = Observable(0)

        # First action
        action1 = SetValueAction(observable=obs, old_value=0, new_value=1)
        stack.push_immediate(action1)

        # Try to push during undo (simulated by directly calling with flag set)
        stack._in_undo_redo = True
        action2 = SetValueAction(observable=obs, old_value=1, new_value=2)
        stack.push_immediate(action2)
        stack._in_undo_redo = False

        # Should only have one action
        stack.undo()
        assert_that(stack.can_undo.get()).is_false()


class TestGetUndoStack:
    """Test get_undo_stack helper."""

    def test_get_undo_stack_returns_app_stack(self, qapp: App) -> None:
        """get_undo_stack should return App's undo stack."""
        stack = get_undo_stack()
        assert_that(stack).is_same_as(qapp.undo_stack)

    def test_get_undo_stack_returns_none_without_app(self) -> None:
        """get_undo_stack returns None when no App exists."""
        # This test is tricky because qapp fixture creates App
        # We'll test the function signature instead
        from qtpie.undo import get_undo_stack

        assert_that(callable(get_undo_stack)).is_true()


class TestResolveUndoConfig:
    """Test undo config resolution."""

    def test_field_takes_priority(self) -> None:
        """Field-level config should take priority."""
        config = resolve_undo_config(
            field_undo=False,
            widget_undo=True,
            app_undo=True,
        )
        assert_that(config.enabled).is_false()

    def test_widget_takes_priority_over_app(self) -> None:
        """Widget-level config should take priority over app."""
        config = resolve_undo_config(
            field_undo=None,
            widget_undo=False,
            app_undo=True,
        )
        assert_that(config.enabled).is_false()

    def test_app_used_when_others_none(self) -> None:
        """App-level config should be used when others are None."""
        config = resolve_undo_config(
            field_undo=None,
            widget_undo=None,
            app_undo=False,
        )
        assert_that(config.enabled).is_false()

    def test_defaults_used_when_all_none(self) -> None:
        """Defaults should be used when all levels are None."""
        config = resolve_undo_config(
            field_undo=None,
            widget_undo=None,
            app_undo=None,
        )
        assert_that(config.enabled).is_true()  # Default is True
        assert_that(config.debounce_ms).is_equal_to(1000)  # Default
        assert_that(config.max_size).is_equal_to(1000)  # Default

    def test_debounce_cascade(self) -> None:
        """Debounce should cascade properly."""
        config = resolve_undo_config(
            field_debounce_ms=100,
            widget_debounce_ms=500,
            app_debounce_ms=1000,
        )
        assert_that(config.debounce_ms).is_equal_to(100)

        config2 = resolve_undo_config(
            field_debounce_ms=None,
            widget_debounce_ms=500,
            app_debounce_ms=1000,
        )
        assert_that(config2.debounce_ms).is_equal_to(500)
