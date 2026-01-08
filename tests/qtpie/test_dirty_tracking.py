# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportUnknownMemberType=false
"""Tests for ViewModel dirty tracking."""

from assertpy import assert_that
from observant import Observable
from qtpy.QtWidgets import QPushButton

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


class TestViewModelDirtyTracking:
    """Test dirty tracking on auto-generated view_model."""

    def test_initially_not_dirty(self, qt: QtDriver) -> None:
        """New widget's view_model is not dirty."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        assert_that(w.view_model.is_dirty.get()).is_false()

    def test_dirty_after_change(self, qt: QtDriver) -> None:
        """view_model becomes dirty after Variable change."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        w._name.value = "changed"
        assert_that(w.view_model.is_dirty.get()).is_true()

    def test_dirty_fields_tracks_which_changed(self, qt: QtDriver) -> None:
        """dirty_fields() returns only the changed fields."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        w = qt.track(MyWidget())
        w._name.value = "changed"

        assert_that(w.view_model.dirty_fields).is_equal_to({"_name"})

    def test_dirty_fields_multiple(self, qt: QtDriver) -> None:
        """dirty_fields() returns all changed fields."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        w = qt.track(MyWidget())
        w._name.value = "changed"
        w._count.value = 42

        assert_that(w.view_model.dirty_fields).is_equal_to({"_name", "_count"})

    def test_reset_dirty_clears_all(self, qt: QtDriver) -> None:
        """reset_dirty() marks all Variables as clean."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

        w = qt.track(MyWidget())
        w._name.value = "changed"
        w._count.value = 42
        assert_that(w.view_model.is_dirty.get()).is_true()

        w.view_model.reset_dirty()
        assert_that(w.view_model.is_dirty.get()).is_false()
        assert_that(w.view_model.dirty_fields).is_equal_to(set())

    def test_dirty_after_reset_and_change(self, qt: QtDriver) -> None:
        """After reset, changing a value makes it dirty again."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        w._name.value = "first"
        w.view_model.reset_dirty()

        w._name.value = "second"
        assert_that(w.view_model.is_dirty.get()).is_true()


class TestIsDirtyObservable:
    """Test that view_model.is_dirty is Observable[bool] for reactive bindings."""

    def test_is_dirty_is_observable(self, qt: QtDriver) -> None:
        """view_model.is_dirty should return Observable[bool]."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        assert_that(w.view_model.is_dirty).is_instance_of(Observable)
        assert_that(w.view_model.is_dirty.get()).is_false()

    def test_is_dirty_reactive_updates(self, qt: QtDriver) -> None:
        """view_model.is_dirty Observable should update when dirty state changes."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        dirty_changes: list[bool] = []
        w.view_model.is_dirty.on_change(lambda v: dirty_changes.append(v))

        # Initially clean
        assert_that(w.view_model.is_dirty.get()).is_false()

        # Become dirty
        w._name.value = "changed"
        assert_that(w.view_model.is_dirty.get()).is_true()
        assert_that(dirty_changes).contains(True)

        # Become clean again
        w.view_model.reset_dirty()
        assert_that(w.view_model.is_dirty.get()).is_false()
        assert_that(dirty_changes).contains(False)

    def test_is_dirty_in_binding(self, qt: QtDriver) -> None:
        """view_model.is_dirty can be used in enabled= bindings."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _save_btn: QPushButton = new("Save", enabled="{view_model.is_dirty.get()}")

        w = qt.track(MyWidget())

        # Initially clean - button should be disabled
        assert_that(w._save_btn.isEnabled()).is_false()

        # Become dirty - button should enable
        w._name.value = "changed"
        assert_that(w._save_btn.isEnabled()).is_true()

        # Become clean - button should disable
        w.view_model.reset_dirty()
        assert_that(w._save_btn.isEnabled()).is_false()


class TestOnDirtyChangedHook:
    """Test on_dirty_changed lifecycle hook."""

    def test_hook_fires_on_dirty(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when widget becomes dirty."""
        dirty_states: list[bool] = []

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(MyWidget())
        w._name.value = "changed"

        assert_that(dirty_states).is_equal_to([True])

    def test_hook_fires_on_clean(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when widget becomes clean."""
        dirty_states: list[bool] = []

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(MyWidget())
        w._name.value = "changed"
        w.view_model.reset_dirty()

        assert_that(dirty_states).is_equal_to([True, False])

    def test_hook_fires_on_transition_only(self, qt: QtDriver) -> None:
        """on_dirty_changed only fires on state transitions, not every change."""
        dirty_states: list[bool] = []

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)

            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        w = qt.track(MyWidget())
        w._name.value = "first"  # clean -> dirty
        w._name.value = "second"  # dirty -> dirty (no fire)
        w._count.value = 42  # dirty -> dirty (no fire)

        assert_that(dirty_states).is_equal_to([True])

    def test_hook_not_required(self, qt: QtDriver) -> None:
        """Widget without on_dirty_changed still works."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        w._name.value = "changed"
        # Should not raise
        assert_that(w.view_model.is_dirty.get()).is_true()


class TestWidgetIsDirty:
    """Test Widget.is_dirty property (aggregates Variables AND record)."""

    def test_widget_is_dirty_returns_observable(self, qt: QtDriver) -> None:
        """Widget.is_dirty should return Observable[bool]."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        assert_that(w.is_dirty).is_instance_of(Observable)
        assert_that(w.is_dirty.get()).is_false()

    def test_widget_is_dirty_from_variables(self, qt: QtDriver) -> None:
        """Widget.is_dirty becomes True when Variables change."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        assert_that(w.is_dirty.get()).is_false()

        w._name.value = "changed"
        assert_that(w.is_dirty.get()).is_true()

    def test_widget_is_dirty_from_record(self, qt: QtDriver) -> None:
        """Widget.is_dirty becomes True when record changes."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @widget(record=Person())
        class PersonEditor(Widget[Person]):
            pass

        w = qt.track(PersonEditor())
        assert_that(w.is_dirty.get()).is_false()

        w.record.name = "Alice"
        assert_that(w.is_dirty.get()).is_true()

    def test_widget_is_dirty_aggregates_both(self, qt: QtDriver) -> None:
        """Widget.is_dirty aggregates Variables AND record."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""

        @widget(record=Person())
        class PersonEditor(Widget[Person]):
            _extra: Variable[str] = new("")

        w = qt.track(PersonEditor())
        assert_that(w.is_dirty.get()).is_false()

        # Modify Variable
        w._extra.value = "extra"
        assert_that(w.is_dirty.get()).is_true()

        # Reset Variables, still dirty from record access (triggers lazily)
        w.view_model.reset_dirty()
        assert_that(w.is_dirty.get()).is_false()

        # Modify record
        w.record.name = "Bob"
        assert_that(w.is_dirty.get()).is_true()

    def test_widget_is_dirty_reactive_binding(self, qt: QtDriver) -> None:
        """Widget.is_dirty can be used in enabled= bindings."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _save_btn: QPushButton = new("Save", enabled="{is_dirty.get()}")

        w = qt.track(MyWidget())

        # Initially clean - button should be disabled
        assert_that(w._save_btn.isEnabled()).is_false()

        # Become dirty - button should enable
        w._name.value = "changed"
        assert_that(w._save_btn.isEnabled()).is_true()

    def test_widget_is_dirty_with_record_reactive(self, qt: QtDriver) -> None:
        """Widget.is_dirty updates reactively when record changes."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""

        @widget(record=Person())
        class PersonEditor(Widget[Person]):
            _save_btn: QPushButton = new("Save", enabled="{is_dirty.get()}")

        w = qt.track(PersonEditor())

        # Initially clean - button should be disabled
        assert_that(w._save_btn.isEnabled()).is_false()

        # Modify record - button should enable
        w.record.name = "Alice"
        assert_that(w._save_btn.isEnabled()).is_true()

    def test_widget_is_dirty_subscribable(self, qt: QtDriver) -> None:
        """Widget.is_dirty Observable can be subscribed to."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        dirty_changes: list[bool] = []
        w.is_dirty.on_change(lambda v: dirty_changes.append(v))

        w._name.value = "changed"
        assert_that(dirty_changes).contains(True)

        w.view_model.reset_dirty()
        assert_that(dirty_changes).contains(False)
