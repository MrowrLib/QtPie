# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportUnknownMemberType=false
"""Tests for ViewModel dirty tracking."""

from assertpy import assert_that

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
        assert_that(w.view_model.is_dirty).is_false()

    def test_dirty_after_change(self, qt: QtDriver) -> None:
        """view_model becomes dirty after Variable change."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

        w = qt.track(MyWidget())
        w._name.value = "changed"
        assert_that(w.view_model.is_dirty).is_true()

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
        assert_that(w.view_model.is_dirty).is_true()

        w.view_model.reset_dirty()
        assert_that(w.view_model.is_dirty).is_false()
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
        assert_that(w.view_model.is_dirty).is_true()


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
        assert_that(w.view_model.is_dirty).is_true()
