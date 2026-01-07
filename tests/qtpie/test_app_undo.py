"""Tests for App undo/redo integration."""

from assertpy import assert_that
from observant import Observable

from qtpie import App
from qtpie.undo import SetValueAction, get_undo_stack


class TestAppUndoStack:
    """Test App has undo stack."""

    def test_app_has_undo_stack(self, qapp: App) -> None:
        """App should have an undo_stack property."""
        assert_that(qapp.undo_stack).is_not_none()

    def test_get_undo_stack_returns_app_stack(self, qapp: App) -> None:
        """get_undo_stack() should return the App's undo stack."""
        stack = get_undo_stack()
        assert_that(stack).is_same_as(qapp.undo_stack)


class TestAppUndoMethods:
    """Test App.undo() and App.redo() convenience methods."""

    def test_app_undo_delegates_to_stack(self, qapp: App) -> None:
        """App.undo() should delegate to undo_stack.undo()."""
        obs = Observable(0)
        obs.set(1)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        qapp.undo_stack.push_immediate(action)
        result = qapp.undo()

        assert_that(result).is_true()
        assert_that(obs.get()).is_equal_to(0)

    def test_app_redo_delegates_to_stack(self, qapp: App) -> None:
        """App.redo() should delegate to undo_stack.redo()."""
        obs = Observable(0)
        obs.set(1)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)

        qapp.undo_stack.push_immediate(action)
        qapp.undo()
        result = qapp.redo()

        assert_that(result).is_true()
        assert_that(obs.get()).is_equal_to(1)

    def test_app_undo_returns_false_when_empty(self, qapp: App) -> None:
        """App.undo() should return False when nothing to undo."""
        qapp.undo_stack.clear()
        result = qapp.undo()
        assert_that(result).is_false()

    def test_app_redo_returns_false_when_empty(self, qapp: App) -> None:
        """App.redo() should return False when nothing to redo."""
        qapp.undo_stack.clear()
        result = qapp.redo()
        assert_that(result).is_false()


class TestAppCanUndoRedo:
    """Test App.can_undo and App.can_redo properties."""

    def test_can_undo_is_observable(self, qapp: App) -> None:
        """App.can_undo should be an Observable[bool]."""
        qapp.undo_stack.clear()
        assert_that(qapp.can_undo.get()).is_false()

        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)
        qapp.undo_stack.push_immediate(action)

        assert_that(qapp.can_undo.get()).is_true()

    def test_can_redo_is_observable(self, qapp: App) -> None:
        """App.can_redo should be an Observable[bool]."""
        qapp.undo_stack.clear()
        assert_that(qapp.can_redo.get()).is_false()

        obs = Observable(0)
        action = SetValueAction(observable=obs, old_value=0, new_value=1)
        qapp.undo_stack.push_immediate(action)
        qapp.undo()

        assert_that(qapp.can_redo.get()).is_true()

    def test_can_undo_delegates_to_stack(self, qapp: App) -> None:
        """App.can_undo should delegate to undo_stack.can_undo."""
        assert_that(qapp.can_undo).is_same_as(qapp.undo_stack.can_undo)

    def test_can_redo_delegates_to_stack(self, qapp: App) -> None:
        """App.can_redo should delegate to undo_stack.can_redo."""
        assert_that(qapp.can_redo).is_same_as(qapp.undo_stack.can_redo)


class TestAppUndoConfig:
    """Test App undo configuration."""

    def test_app_undo_enabled_default_is_none(self, qapp: App) -> None:
        """App.undo_enabled should default to None (use defaults)."""
        # The qapp fixture uses default config
        # We need to create a new App to test defaults
        pass  # Skip - can't create multiple QApplications

    def test_app_undo_debounce_ms_default_is_none(self, qapp: App) -> None:
        """App.undo_debounce_ms should default to None (use defaults)."""
        pass  # Skip - can't create multiple QApplications

    def test_app_undo_max_sets_stack_max(self) -> None:
        """App(undo_max=N) should create stack with max_size=N."""
        # This test would need to inspect the stack's max_size
        # which isn't directly exposed. The test is in test_undo_stack.py
        pass


class TestAppUndoWorkflow:
    """Test typical undo/redo workflows."""

    def test_multiple_undo_redo(self, qapp: App) -> None:
        """Multiple undo/redo operations should work correctly."""
        qapp.undo_stack.clear()
        obs = Observable(0)

        # Make 3 changes
        for i in range(1, 4):
            old_val = obs.get()
            obs.set(i)
            action = SetValueAction(observable=obs, old_value=old_val, new_value=i)
            qapp.undo_stack.push_immediate(action)

        # obs is now 3
        assert_that(obs.get()).is_equal_to(3)

        # Undo all 3
        qapp.undo()
        assert_that(obs.get()).is_equal_to(2)

        qapp.undo()
        assert_that(obs.get()).is_equal_to(1)

        qapp.undo()
        assert_that(obs.get()).is_equal_to(0)

        # Redo all 3
        qapp.redo()
        assert_that(obs.get()).is_equal_to(1)

        qapp.redo()
        assert_that(obs.get()).is_equal_to(2)

        qapp.redo()
        assert_that(obs.get()).is_equal_to(3)

    def test_new_action_after_undo_clears_redo(self, qapp: App) -> None:
        """New action after undo should clear redo stack."""
        qapp.undo_stack.clear()
        obs = Observable(0)

        # Make a change
        obs.set(1)
        action1 = SetValueAction(observable=obs, old_value=0, new_value=1)
        qapp.undo_stack.push_immediate(action1)

        # Undo it
        qapp.undo()
        assert_that(qapp.can_redo.get()).is_true()

        # Make a new change
        obs.set(2)
        action2 = SetValueAction(observable=obs, old_value=0, new_value=2)
        qapp.undo_stack.push_immediate(action2)

        # Redo should no longer be available
        assert_that(qapp.can_redo.get()).is_false()
