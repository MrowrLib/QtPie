"""Tests for ObservableDict."""

from assertpy import assert_that
from observant import ObservableDict


class TestObservableDictBasics:
    """Test basic dict operations."""

    def test_empty_dict(self) -> None:
        """Empty dict has length 0."""
        obs = ObservableDict[str, int]()
        assert_that(len(obs)).is_equal_to(0)

    def test_init_with_items(self) -> None:
        """Can initialize with items."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        assert_that(len(obs)).is_equal_to(2)
        assert_that(obs["a"]).is_equal_to(1)

    def test_setitem(self) -> None:
        """Set item."""
        obs = ObservableDict[str, int]()
        obs["key"] = 42
        assert_that(obs["key"]).is_equal_to(42)

    def test_getitem(self) -> None:
        """Get item."""
        obs = ObservableDict[str, int]({"a": 1})
        assert_that(obs["a"]).is_equal_to(1)

    def test_delitem(self) -> None:
        """Delete item."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        del obs["a"]
        assert_that("a" in obs).is_false()
        assert_that(len(obs)).is_equal_to(1)

    def test_get_with_default(self) -> None:
        """Get with default."""
        obs = ObservableDict[str, int]({"a": 1})
        assert_that(obs.get("a")).is_equal_to(1)
        assert_that(obs.get("missing")).is_none()
        assert_that(obs.get("missing", 99)).is_equal_to(99)

    def test_pop(self) -> None:
        """Pop removes and returns."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        val = obs.pop("a")
        assert_that(val).is_equal_to(1)
        assert_that("a" in obs).is_false()

    def test_pop_with_default(self) -> None:
        """Pop with default for missing key."""
        obs = ObservableDict[str, int]()
        val = obs.pop("missing", 99)
        assert_that(val).is_equal_to(99)

    def test_popitem(self) -> None:
        """Popitem removes and returns pair."""
        obs = ObservableDict[str, int]({"a": 1})
        key, val = obs.popitem()
        assert_that(key).is_equal_to("a")
        assert_that(val).is_equal_to(1)
        assert_that(len(obs)).is_equal_to(0)

    def test_clear(self) -> None:
        """Clear removes all."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        obs.clear()
        assert_that(len(obs)).is_equal_to(0)

    def test_update(self) -> None:
        """Update from other dict."""
        obs = ObservableDict[str, int]({"a": 1})
        obs.update({"b": 2, "c": 3})
        assert_that(obs.to_dict()).is_equal_to({"a": 1, "b": 2, "c": 3})

    def test_setdefault(self) -> None:
        """Setdefault sets if missing."""
        obs = ObservableDict[str, int]({"a": 1})
        val1 = obs.setdefault("a", 99)
        val2 = obs.setdefault("b", 99)
        assert_that(val1).is_equal_to(1)
        assert_that(val2).is_equal_to(99)
        assert_that(obs["b"]).is_equal_to(99)

    def test_contains(self) -> None:
        """Check key in dict."""
        obs = ObservableDict[str, int]({"a": 1})
        assert_that("a" in obs).is_true()
        assert_that("missing" in obs).is_false()

    def test_iter(self) -> None:
        """Iterate over keys."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        assert_that(set(obs)).is_equal_to({"a", "b"})

    def test_keys(self) -> None:
        """Get keys."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        assert_that(set(obs.keys())).is_equal_to({"a", "b"})

    def test_values(self) -> None:
        """Get values."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        assert_that(set(obs.values())).is_equal_to({1, 2})

    def test_items(self) -> None:
        """Get items."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        assert_that(set(obs.items())).is_equal_to({("a", 1), ("b", 2)})


class TestObservableDictCallbacks:
    """Test change callbacks."""

    def test_on_change_fires_on_setitem(self) -> None:
        """Callback fires on setitem."""
        obs = ObservableDict[str, int]()
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs["a"] = 1
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_delitem(self) -> None:
        """Callback fires on delitem."""
        obs = ObservableDict[str, int]({"a": 1})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        del obs["a"]
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_pop(self) -> None:
        """Callback fires on pop."""
        obs = ObservableDict[str, int]({"a": 1})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.pop("a")
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_clear(self) -> None:
        """Callback fires on clear."""
        obs = ObservableDict[str, int]({"a": 1})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.clear()
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_update(self) -> None:
        """Callback fires on update."""
        obs = ObservableDict[str, int]()
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.update({"a": 1})
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_setdefault_new_key(self) -> None:
        """Callback fires on setdefault for new key."""
        obs = ObservableDict[str, int]()
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.setdefault("a", 1)
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_not_fired_on_setdefault_existing(self) -> None:
        """Callback not fired if setdefault key exists."""
        obs = ObservableDict[str, int]({"a": 1})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.setdefault("a", 99)
        assert_that(changes).is_equal_to([])

    def test_multiple_callbacks(self) -> None:
        """Multiple callbacks all fire."""
        obs = ObservableDict[str, int]()
        results: list[int] = []
        obs.on_change(lambda: results.append(1))
        obs.on_change(lambda: results.append(2))

        obs["a"] = 1
        assert_that(results).is_equal_to([1, 2])

    def test_duplicate_callback_ignored(self) -> None:
        """Same callback not added twice."""
        obs = ObservableDict[str, int]()
        results: list[int] = []

        def cb() -> None:
            results.append(1)

        obs.on_change(cb)
        obs.on_change(cb)

        obs["a"] = 1
        assert_that(results).is_equal_to([1])


class TestObservableDictDirty:
    """Test dirty tracking."""

    def test_initially_not_dirty(self) -> None:
        """New dict is not dirty."""
        obs = ObservableDict[str, int]({"a": 1})
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_setitem(self) -> None:
        """Dict becomes dirty after setitem."""
        obs = ObservableDict[str, int]()
        obs["a"] = 1
        assert_that(bool(obs.is_dirty)).is_true()

    def test_dirty_after_delitem(self) -> None:
        """Dict becomes dirty after delitem."""
        obs = ObservableDict[str, int]({"a": 1})
        del obs["a"]
        assert_that(bool(obs.is_dirty)).is_true()

    def test_dirty_after_update(self) -> None:
        """Dict becomes dirty after update."""
        obs = ObservableDict[str, int]()
        obs.update({"a": 1})
        assert_that(bool(obs.is_dirty)).is_true()

    def test_reset_dirty_clears(self) -> None:
        """reset_dirty marks as clean."""
        obs = ObservableDict[str, int]()
        obs["a"] = 1
        assert_that(bool(obs.is_dirty)).is_true()

        obs.reset_dirty()
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_reset_and_change(self) -> None:
        """After reset, new changes make dirty again."""
        obs = ObservableDict[str, int]()
        obs["a"] = 1
        obs.reset_dirty()

        obs["b"] = 2
        assert_that(bool(obs.is_dirty)).is_true()

    def test_clean_if_reverted_to_clean_state(self) -> None:
        """Reverting to clean state makes it clean."""
        obs = ObservableDict[str, int]({"a": 1})
        obs.reset_dirty()

        obs["b"] = 2
        assert_that(bool(obs.is_dirty)).is_true()

        del obs["b"]  # back to {"a": 1}
        assert_that(bool(obs.is_dirty)).is_false()

    def test_is_dirty_is_observable(self) -> None:
        """is_dirty can be subscribed to."""
        obs = ObservableDict[str, int]()
        dirty_states: list[bool] = []

        obs.is_dirty.on_change(lambda d: dirty_states.append(d))

        obs["a"] = 1  # clean -> dirty
        obs["b"] = 2  # stays dirty
        obs.reset_dirty()  # dirty -> clean

        assert_that(dirty_states).is_equal_to([True, False])
