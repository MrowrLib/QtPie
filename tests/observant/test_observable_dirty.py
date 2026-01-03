"""Tests for Observable dirty tracking."""

from assertpy import assert_that
from observant import Observable


class TestObservableDirtyTracking:
    """Test dirty tracking on Observable."""

    def test_initially_not_dirty(self) -> None:
        """New Observable is not dirty."""
        obs = Observable[str]("hello")
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_change(self) -> None:
        """Observable becomes dirty after value change."""
        obs = Observable[str]("hello")
        obs.set("world")
        assert_that(bool(obs.is_dirty)).is_true()

    def test_not_dirty_if_set_to_same_value(self) -> None:
        """Setting same value doesn't make it dirty."""
        obs = Observable[str]("hello")
        obs.set("hello")
        assert_that(bool(obs.is_dirty)).is_false()

    def test_reset_dirty_clears(self) -> None:
        """reset_dirty() marks current value as clean."""
        obs = Observable[str]("hello")
        obs.set("world")
        assert_that(bool(obs.is_dirty)).is_true()

        obs.reset_dirty()
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_reset_and_change(self) -> None:
        """After reset, changing value makes it dirty again."""
        obs = Observable[str]("hello")
        obs.set("world")
        obs.reset_dirty()

        obs.set("foo")
        assert_that(bool(obs.is_dirty)).is_true()

    def test_clean_after_reset_to_new_value(self) -> None:
        """After reset, setting to reset value is clean."""
        obs = Observable[str]("hello")
        obs.set("world")
        obs.reset_dirty()  # "world" is now clean

        obs.set("foo")
        assert_that(bool(obs.is_dirty)).is_true()

        obs.set("world")  # back to clean value
        assert_that(bool(obs.is_dirty)).is_false()

    def test_is_dirty_is_observable(self) -> None:
        """is_dirty returns an Observable that can be subscribed to."""
        obs = Observable[str]("hello")
        dirty_changes: list[bool] = []

        obs.is_dirty.on_change(lambda d: dirty_changes.append(d))

        obs.set("world")  # becomes dirty
        obs.set("foo")  # stays dirty, no transition
        obs.reset_dirty()  # becomes clean

        assert_that(dirty_changes).is_equal_to([True, False])

    def test_is_dirty_observable_fires_on_transition_only(self) -> None:
        """is_dirty Observable only fires when state actually changes."""
        obs = Observable[str]("hello")
        dirty_changes: list[bool] = []

        obs.is_dirty.on_change(lambda d: dirty_changes.append(d))

        obs.set("world")  # clean -> dirty
        obs.set("another")  # dirty -> dirty (no fire)
        obs.set("hello")  # dirty -> clean (back to original)

        assert_that(dirty_changes).is_equal_to([True, False])


class TestObservableBool:
    """Test Observable __bool__ behavior."""

    def test_bool_true(self) -> None:
        """Observable with truthy value is truthy."""
        obs = Observable[int](42)
        assert_that(bool(obs)).is_true()

    def test_bool_false(self) -> None:
        """Observable with falsy value is falsy."""
        obs = Observable[int](0)
        assert_that(bool(obs)).is_false()

    def test_bool_with_string(self) -> None:
        """Observable with non-empty string is truthy."""
        obs = Observable[str]("hello")
        assert_that(bool(obs)).is_true()

        obs.set("")
        assert_that(bool(obs)).is_false()
