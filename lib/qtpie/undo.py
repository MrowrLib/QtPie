"""Undo/Redo infrastructure for QtPie."""

import time
from dataclasses import dataclass
from typing import Any, Protocol

from observant import Observable, ObservableDict, ObservableList
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QApplication

# Type for any observable type
AnyObservable = Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any]

# Default values for undo configuration
UNDO_DEFAULT_ENABLED = True
UNDO_DEFAULT_DEBOUNCE_MS = 1000
UNDO_DEFAULT_MAX = 1000


@dataclass
class UndoConfig:
    """Configuration for undo behavior."""

    enabled: bool = UNDO_DEFAULT_ENABLED
    debounce_ms: int = UNDO_DEFAULT_DEBOUNCE_MS
    max_size: int = UNDO_DEFAULT_MAX


class UndoableAction(Protocol):
    """Protocol for actions that can be undone/redone."""

    def undo(self) -> None:
        """Reverse this action."""
        ...

    def redo(self) -> None:
        """Re-apply this action."""
        ...


@dataclass
class SetValueAction:
    """Action that sets a value on an Observable, ObservableList, or ObservableDict."""

    observable: AnyObservable
    old_value: Any
    new_value: Any
    _skip_undo_push: bool = False  # Flag to prevent recursive pushes

    def _set_value(self, value: Any) -> None:
        """Set the value on the appropriate observable type."""
        if isinstance(self.observable, Observable):
            self.observable.set(value)
        elif isinstance(self.observable, ObservableList):
            self.observable.clear()
            self.observable.extend(value)
        else:  # ObservableDict
            self.observable.clear()
            self.observable.update(value)

    def undo(self) -> None:
        """Restore the old value."""
        self._set_value(self.old_value)

    def redo(self) -> None:
        """Re-apply the new value."""
        self._set_value(self.new_value)


class UndoStack:
    """
    App-level undo stack with per-field debouncing.

    Uses a single QTimer to manage debounce for all fields efficiently.
    """

    def __init__(self, max_size: int = UNDO_DEFAULT_MAX) -> None:
        self._stack: list[UndoableAction] = []
        self._redo_stack: list[UndoableAction] = []
        self._max_size = max_size

        # Per-field debouncing: field_id -> (action, due_time)
        self._pending: dict[str, tuple[UndoableAction, float]] = {}

        # Single timer for all debouncing
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timer)

        # Observable state for can_undo/can_redo
        self._can_undo: Observable[bool] = Observable(False, dirty_tracking=False, validation=False)
        self._can_redo: Observable[bool] = Observable(False, dirty_tracking=False, validation=False)

        # Flag to prevent recursive pushes during undo/redo
        self._in_undo_redo = False

    @property
    def can_undo(self) -> Observable[bool]:
        """Observable indicating if undo is available."""
        return self._can_undo

    @property
    def can_redo(self) -> Observable[bool]:
        """Observable indicating if redo is available."""
        return self._can_redo

    @property
    def in_undo_redo(self) -> bool:
        """True if currently executing an undo or redo operation."""
        return self._in_undo_redo

    def push_debounced(self, action: UndoableAction, field_id: str, debounce_ms: int) -> None:
        """
        Push an action with debouncing.

        If the same field_id has a pending action, update it instead of creating a new one.
        The action won't be committed to the stack until debounce_ms after the last update.
        """
        if self._in_undo_redo:
            return  # Don't push during undo/redo operations

        now = time.time()
        due_time = now + (debounce_ms / 1000.0)

        if field_id in self._pending:
            # Update existing pending action - keep old_value, update new_value
            existing_action, _ = self._pending[field_id]
            if isinstance(existing_action, SetValueAction) and isinstance(action, SetValueAction):
                # Merge: keep original old_value, use latest new_value
                merged = SetValueAction(
                    observable=action.observable,
                    old_value=existing_action.old_value,
                    new_value=action.new_value,
                )
                self._pending[field_id] = (merged, due_time)
            else:
                # Different action type, just replace
                self._pending[field_id] = (action, due_time)
        else:
            # New pending action
            self._pending[field_id] = (action, due_time)

        self._reschedule_timer()
        self._update_can_states()

    def push_immediate(self, action: UndoableAction) -> None:
        """Push an action immediately without debouncing."""
        if self._in_undo_redo:
            return

        self._stack.append(action)
        self._redo_stack.clear()  # Clear redo stack on new action

        # Enforce max size
        while len(self._stack) > self._max_size:
            self._stack.pop(0)

        self._update_can_states()

    def undo(self) -> bool:
        """
        Undo the last action.

        Returns True if an action was undone, False if stack was empty.
        """
        # First, flush any pending actions
        self.flush_pending()

        if not self._stack:
            return False

        self._in_undo_redo = True
        try:
            action = self._stack.pop()
            action.undo()
            self._redo_stack.append(action)
        finally:
            self._in_undo_redo = False

        self._update_can_states()
        return True

    def redo(self) -> bool:
        """
        Redo the last undone action.

        Returns True if an action was redone, False if redo stack was empty.
        """
        if not self._redo_stack:
            return False

        self._in_undo_redo = True
        try:
            action = self._redo_stack.pop()
            action.redo()
            self._stack.append(action)
        finally:
            self._in_undo_redo = False

        self._update_can_states()
        return True

    def clear(self) -> None:
        """Clear all undo/redo history."""
        self._stack.clear()
        self._redo_stack.clear()
        self._pending.clear()
        self._timer.stop()
        self._update_can_states()

    def _reschedule_timer(self) -> None:
        """Reschedule timer to fire at the earliest pending action's due time."""
        if not self._pending:
            self._timer.stop()
            return

        # Find earliest due time
        now = time.time()
        earliest_due = min(due for _, due in self._pending.values())
        delay_ms = max(0, int((earliest_due - now) * 1000))

        self._timer.start(delay_ms)

    def _on_timer(self) -> None:
        """Process pending actions that are due."""
        now = time.time()

        # Find all actions that are due
        ready_ids = [fid for fid, (_, due) in self._pending.items() if due <= now]

        # Process them
        for field_id in ready_ids:
            action, _ = self._pending.pop(field_id)
            self.push_immediate(action)

        # Reschedule for any remaining
        self._reschedule_timer()

    def flush_pending(self) -> None:
        """Immediately commit all pending actions (useful for testing)."""
        for action, _ in self._pending.values():
            self.push_immediate(action)
        self._pending.clear()
        self._timer.stop()

    def _update_can_states(self) -> None:
        """Update can_undo and can_redo observables."""
        can_undo = len(self._stack) > 0 or len(self._pending) > 0
        can_redo = len(self._redo_stack) > 0

        if self._can_undo.get() != can_undo:
            self._can_undo.set(can_undo)
        if self._can_redo.get() != can_redo:
            self._can_redo.set(can_redo)


def get_undo_stack() -> UndoStack | None:
    """
    Get the app's undo stack.

    Returns None if no App instance exists or if the application
    is not using QtPie's App class.
    """
    app = QApplication.instance()
    if app is None:
        return None

    # Import here to avoid circular imports
    from qtpie.app import App

    if isinstance(app, App):
        return app.undo_stack

    return None


def resolve_undo_config(
    *,
    field_undo: bool | None = None,
    field_debounce_ms: int | None = None,
    field_max: int | None = None,
    widget_undo: bool | None = None,
    widget_debounce_ms: int | None = None,
    widget_max: int | None = None,
    app_undo: bool | None = None,
    app_debounce_ms: int | None = None,
    app_max: int | None = None,
) -> UndoConfig:
    """
    Resolve undo configuration through the cascade.

    Priority: field -> widget -> app -> defaults
    """
    # Resolve enabled
    if field_undo is not None:
        enabled = field_undo
    elif widget_undo is not None:
        enabled = widget_undo
    elif app_undo is not None:
        enabled = app_undo
    else:
        enabled = UNDO_DEFAULT_ENABLED

    # Resolve debounce_ms
    if field_debounce_ms is not None:
        debounce_ms = field_debounce_ms
    elif widget_debounce_ms is not None:
        debounce_ms = widget_debounce_ms
    elif app_debounce_ms is not None:
        debounce_ms = app_debounce_ms
    else:
        debounce_ms = UNDO_DEFAULT_DEBOUNCE_MS

    # Resolve max_size
    if field_max is not None:
        max_size = field_max
    elif widget_max is not None:
        max_size = widget_max
    elif app_max is not None:
        max_size = app_max
    else:
        max_size = UNDO_DEFAULT_MAX

    return UndoConfig(enabled=enabled, debounce_ms=debounce_ms, max_size=max_size)
