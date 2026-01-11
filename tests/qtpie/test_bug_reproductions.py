# pyright: reportPrivateUsage=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false
# pyright: reportArgumentType=false
# pyright: reportIndexIssue=false
# pyright: reportImplicitOverride=false
"""Tests that reproduce known bugs before fixing them.

These tests are expected to FAIL initially, then PASS after fixes.

Bugs:
1. SetWidgetRepeater missing two-way sync for primitives
2. Menu[T].record changes don't update is_dirty/is_valid
"""

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import Menu, Variable, Widget, WidgetRepeater, menu, new, widget
from qtpie.set_widget_repeater import SetWidgetRepeater
from qtpie.testing import QtDriver

# =============================================================================
# BUG 1: SetWidgetRepeater missing two-way sync for primitives
# =============================================================================


class TestSetWidgetRepeaterTwoWaySyncBug:
    """Bug: SetWidgetRepeater is missing _setup_primitive_sync.

    WidgetRepeater has this method which syncs widget changes back to the list.
    SetWidgetRepeater was copy-pasted but this method was not included.

    Expected behavior:
    - For set[int] with QSpinBox: editing spinbox should update the set
    - For set[str] with QLineEdit: editing line edit should update the set

    Actual behavior (BUG):
    - Widget changes are NOT synced back to the set
    """

    def test_set_widget_two_way_binding_spinbox(self, qt: QtDriver) -> None:
        """BUG REPRO: Editing spinbox in set[int] should update the set.

        This test reproduces the bug where SetWidgetRepeater doesn't have
        _setup_primitive_sync, so widget changes don't sync back to set.
        """

        @widget
        class Test(Widget):
            _numbers: Variable[set[int], QSpinBox] = new({1, 2, 3})  # type: ignore[type-arg]

        w = qt.track(Test())

        # Get the repeater and find the spinbox for value 1
        repeater: SetWidgetRepeater[int] = w._numbers.widget
        assert repeater.widget_count() == 3

        # Find the spinbox that has value 1
        spin_for_1 = repeater.widget_for_item(1)
        assert spin_for_1 is not None
        assert isinstance(spin_for_1, QSpinBox)
        assert spin_for_1.value() == 1

        # Change the spinbox value - THIS SHOULD update the set
        # With the bug, the set won't update
        spin_for_1.setValue(99)

        # The set should now contain {99, 2, 3} (1 replaced with 99)
        # BUG: With the bug, set still contains {1, 2, 3}
        current_values = set(w._numbers.observable)
        assert_that(current_values).contains(99)
        assert_that(current_values).does_not_contain(1)

    def test_set_widget_two_way_binding_lineedit(self, qt: QtDriver) -> None:
        """BUG REPRO: Editing QLineEdit in set[str] should update the set."""

        @widget
        class Test(Widget):
            _names: Variable[set[str], QLineEdit] = new({"alice", "bob"})  # type: ignore[type-arg]

        w = qt.track(Test())

        repeater: SetWidgetRepeater[str] = w._names.widget
        assert repeater.widget_count() == 2

        # Find the widget for "alice"
        edit_for_alice = repeater.widget_for_item("alice")
        assert edit_for_alice is not None
        assert isinstance(edit_for_alice, QLineEdit)
        assert edit_for_alice.text() == "alice"

        # Change the text - THIS SHOULD update the set
        edit_for_alice.setText("charlie")

        # BUG: With the bug, set still contains {"alice", "bob"}
        current_values = set(w._names.observable)
        assert_that(current_values).contains("charlie")
        assert_that(current_values).does_not_contain("alice")

    def test_list_widget_two_way_binding_works(self, qt: QtDriver) -> None:
        """CONTROL: Verify list[int] two-way binding works (for comparison)."""

        @widget
        class Test(Widget):
            _numbers: Variable[list[int], QSpinBox] = new([1, 2, 3])  # type: ignore[type-arg]

        w = qt.track(Test())

        repeater: WidgetRepeater[int] = w._numbers.widget
        spin = repeater.widget_at(1)
        assert isinstance(spin, QSpinBox)
        assert spin.value() == 2

        # Change spinbox value
        spin.setValue(99)

        # List SHOULD be updated (this works because WidgetRepeater has _setup_primitive_sync)
        assert w._numbers.observable[1] == 99


# =============================================================================
# BUG 2: Menu[T].record changes don't update is_dirty/is_valid
# =============================================================================


class TestMenuRecordDirtyTrackingBug:
    """Bug: Menu[T].record changes don't reactively update is_dirty Observable.

    Widget and Window properly subscribe record changes to dirty tracking.
    Menu's _MenuRecordDescriptor doesn't call:
    - state._subscribe_record_to_widget_dirty()
    - state._subscribe_record_to_widget_valid()

    Expected behavior:
    - Menu[T] with record: changing record.field should trigger is_dirty Observable
    - Widget[T] with record: changing record.field triggers is_dirty Observable (works)

    Actual behavior (BUG):
    - Menu's is_dirty Observable doesn't get notified of record changes
    - The value is computed correctly if you call .get(), but listeners aren't notified
    """

    def test_menu_record_change_triggers_is_dirty_subscription(self, qt: QtDriver) -> None:
        """BUG REPRO: is_dirty Observable should notify subscribers when record changes.

        The bug is that _MenuRecordDescriptor doesn't call _subscribe_record_to_widget_dirty().
        This means the is_dirty Observable won't be updated when record fields change.

        Note: Calling is_dirty.get() might still return True because _compute_widget_is_dirty
        checks the record, but the Observable value itself isn't updated.
        """
        dirty_notifications: list[bool] = []

        @dataclass
        class EditState:
            can_undo: bool = False

        @menu(text="&Edit", record=EditState())
        class EditMenu(Menu[EditState]):
            pass

        m = qt.track(EditMenu())

        # Subscribe to is_dirty Observable BEFORE changing record
        m.is_dirty.on_change(lambda v: dirty_notifications.append(v))

        # Initially not dirty
        assert_that(m.is_dirty.get()).is_false()

        # Change record field - this SHOULD trigger a notification to is_dirty subscribers
        m.record.can_undo = True

        # BUG: With the bug, no notification is sent to subscribers
        # The is_dirty Observable value isn't updated, even though record is dirty
        assert_that(dirty_notifications).contains(True)

    def test_widget_record_change_triggers_is_dirty_subscription(self, qt: QtDriver) -> None:
        """CONTROL: Widget[T].record changes DO trigger is_dirty notifications."""
        dirty_notifications: list[bool] = []

        @dataclass
        class Person:
            name: str = ""

        @widget(record=Person())
        class PersonWidget(Widget[Person]):
            _label: QLabel = new("test")

        w = qt.track(PersonWidget())

        # Subscribe to is_dirty BEFORE changing record
        w.is_dirty.on_change(lambda v: dirty_notifications.append(v))

        # Change record field
        w.record.name = "Alice"

        # Widget's is_dirty SHOULD have notified subscribers (this works)
        assert_that(dirty_notifications).contains(True)

    def test_menu_on_dirty_changed_fires_for_record(self, qt: QtDriver) -> None:
        """BUG REPRO: on_dirty_changed lifecycle hook should fire when record changes."""
        dirty_states: list[bool] = []

        @dataclass
        class EditState:
            can_undo: bool = False

        @menu(text="&Edit", record=EditState())
        class EditMenu(Menu[EditState]):
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        m = qt.track(EditMenu())

        # Change record
        m.record.can_undo = True

        # BUG: With the bug, on_dirty_changed never fires for record changes
        assert_that(dirty_states).contains(True)

    def test_widget_on_dirty_changed_fires_for_record(self, qt: QtDriver) -> None:
        """CONTROL: Widget's on_dirty_changed DOES fire for record changes."""
        dirty_states: list[bool] = []

        @dataclass
        class Person:
            name: str = ""

        @widget(record=Person())
        class PersonWidget(Widget[Person]):
            _label: QLabel = new("test")

            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(PersonWidget())

        # Change record
        w.record.name = "Alice"

        # Widget's on_dirty_changed SHOULD fire (this works)
        assert_that(dirty_states).contains(True)
