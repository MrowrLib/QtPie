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

    def test_replace(self) -> None:
        """Replace all items atomically."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        obs.replace({"c": 3, "d": 4})
        assert_that(obs.to_dict()).is_equal_to({"c": 3, "d": 4})

    def test_replace_empty(self) -> None:
        """Replace with empty dict."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        obs.replace({})
        assert_that(len(obs)).is_equal_to(0)

    def test_replace_from_empty(self) -> None:
        """Replace empty dict with items."""
        obs = ObservableDict[str, int]()
        obs.replace({"a": 1, "b": 2})
        assert_that(obs.to_dict()).is_equal_to({"a": 1, "b": 2})

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

    def test_on_change_fires_on_replace(self) -> None:
        """Callback fires on replace."""
        obs = ObservableDict[str, int]({"a": 1})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.replace({"b": 2, "c": 3})
        assert_that(changes).is_equal_to(["changed"])

    def test_on_clear_fires_on_replace(self) -> None:
        """Clear callback fires on replace (with old items)."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        cleared: list[dict[str, int]] = []
        obs.on_clear(lambda items: cleared.append(dict(items)))

        obs.replace({"c": 3})
        assert_that(cleared).is_equal_to([{"a": 1, "b": 2}])

    def test_replace_no_insert_callbacks(self) -> None:
        """Replace does NOT fire individual insert callbacks."""
        obs = ObservableDict[str, int]({"a": 1})
        inserts: list[str] = []
        obs.on_insert(lambda k, v: inserts.append(k))

        obs.replace({"b": 2, "c": 3})
        # Should NOT have any insert callbacks - that's the point of replace
        assert_that(inserts).is_empty()

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


class TestObservableDictGranularCallbacks:
    """Test granular insert/remove/replace/clear callbacks."""

    def test_on_insert_fires_on_new_key(self) -> None:
        """on_insert fires when adding a new key."""
        obs = ObservableDict[str, int]({"a": 1})
        inserts: list[tuple[str, int]] = []
        obs.on_insert(lambda k, v: inserts.append((k, v)))

        obs["b"] = 2
        assert_that(inserts).is_equal_to([("b", 2)])

    def test_on_insert_not_fired_on_existing_key(self) -> None:
        """on_insert does NOT fire when updating existing key."""
        obs = ObservableDict[str, int]({"a": 1})
        inserts: list[tuple[str, int]] = []
        obs.on_insert(lambda k, v: inserts.append((k, v)))

        obs["a"] = 99  # update, not insert
        assert_that(inserts).is_equal_to([])

    def test_on_insert_fires_on_setdefault_new_key(self) -> None:
        """on_insert fires on setdefault for new key."""
        obs = ObservableDict[str, int]()
        inserts: list[tuple[str, int]] = []
        obs.on_insert(lambda k, v: inserts.append((k, v)))

        obs.setdefault("a", 1)
        assert_that(inserts).is_equal_to([("a", 1)])

    def test_on_insert_not_fired_on_setdefault_existing(self) -> None:
        """on_insert not fired on setdefault for existing key."""
        obs = ObservableDict[str, int]({"a": 1})
        inserts: list[tuple[str, int]] = []
        obs.on_insert(lambda k, v: inserts.append((k, v)))

        obs.setdefault("a", 99)
        assert_that(inserts).is_equal_to([])

    def test_on_insert_fires_on_update_new_keys(self) -> None:
        """on_insert fires for each new key in update."""
        obs = ObservableDict[str, int]({"a": 1})
        inserts: list[tuple[str, int]] = []
        obs.on_insert(lambda k, v: inserts.append((k, v)))

        obs.update({"b": 2, "c": 3})
        assert_that(inserts).is_equal_to([("b", 2), ("c", 3)])

    def test_on_replace_fires_on_existing_key(self) -> None:
        """on_replace fires when updating existing key."""
        obs = ObservableDict[str, int]({"a": 1})
        replaces: list[tuple[str, int, int]] = []
        obs.on_replace(lambda k, old, new: replaces.append((k, old, new)))

        obs["a"] = 99
        assert_that(replaces).is_equal_to([("a", 1, 99)])

    def test_on_replace_not_fired_on_new_key(self) -> None:
        """on_replace does NOT fire when adding new key."""
        obs = ObservableDict[str, int]({"a": 1})
        replaces: list[tuple[str, int, int]] = []
        obs.on_replace(lambda k, old, new: replaces.append((k, old, new)))

        obs["b"] = 2  # new key, not replace
        assert_that(replaces).is_equal_to([])

    def test_on_replace_fires_on_update_existing_keys(self) -> None:
        """on_replace fires for each existing key in update."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        replaces: list[tuple[str, int, int]] = []
        obs.on_replace(lambda k, old, new: replaces.append((k, old, new)))

        obs.update({"a": 10, "c": 3})  # a is replace, c is insert
        assert_that(replaces).is_equal_to([("a", 1, 10)])

    def test_on_remove_fires_on_delitem(self) -> None:
        """on_remove fires on del dict[key]."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        removes: list[tuple[str, int]] = []
        obs.on_remove(lambda k, v: removes.append((k, v)))

        del obs["a"]
        assert_that(removes).is_equal_to([("a", 1)])

    def test_on_remove_fires_on_pop(self) -> None:
        """on_remove fires on pop."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        removes: list[tuple[str, int]] = []
        obs.on_remove(lambda k, v: removes.append((k, v)))

        obs.pop("a")
        assert_that(removes).is_equal_to([("a", 1)])

    def test_on_remove_not_fired_on_pop_missing_with_default(self) -> None:
        """on_remove not fired on pop with default for missing key."""
        obs = ObservableDict[str, int]({"a": 1})
        removes: list[tuple[str, int]] = []
        obs.on_remove(lambda k, v: removes.append((k, v)))

        obs.pop("missing", 99)
        assert_that(removes).is_equal_to([])

    def test_on_remove_fires_on_popitem(self) -> None:
        """on_remove fires on popitem."""
        obs = ObservableDict[str, int]({"a": 1})
        removes: list[tuple[str, int]] = []
        obs.on_remove(lambda k, v: removes.append((k, v)))

        obs.popitem()
        assert_that(removes).is_equal_to([("a", 1)])

    def test_on_clear_fires_with_removed_items(self) -> None:
        """on_clear fires with dict of all removed items."""
        obs = ObservableDict[str, int]({"a": 1, "b": 2})
        clears: list[dict[str, int]] = []
        obs.on_clear(lambda items: clears.append(items))

        obs.clear()
        assert_that(clears).is_equal_to([{"a": 1, "b": 2}])

    def test_on_clear_fires_with_empty_dict_if_already_empty(self) -> None:
        """on_clear fires with empty dict if dict was already empty."""
        obs = ObservableDict[str, int]()
        clears: list[dict[str, int]] = []
        obs.on_clear(lambda items: clears.append(items))

        obs.clear()
        assert_that(clears).is_equal_to([{}])

    def test_multiple_granular_callbacks(self) -> None:
        """Multiple callbacks of same type all fire."""
        obs = ObservableDict[str, int]()
        results: list[int] = []
        obs.on_insert(lambda k, v: results.append(1))
        obs.on_insert(lambda k, v: results.append(2))

        obs["a"] = 1
        assert_that(results).is_equal_to([1, 2])

    def test_duplicate_granular_callback_ignored(self) -> None:
        """Same callback not added twice."""
        obs = ObservableDict[str, int]()
        results: list[int] = []

        def cb(k: str, v: int) -> None:
            results.append(1)

        obs.on_insert(cb)
        obs.on_insert(cb)

        obs["a"] = 1
        assert_that(results).is_equal_to([1])

    def test_granular_and_generic_both_fire(self) -> None:
        """Both granular and generic on_change fire."""
        obs = ObservableDict[str, int]()
        events: list[str] = []
        obs.on_insert(lambda k, v: events.append(f"insert:{k}={v}"))
        obs.on_change(lambda: events.append("change"))

        obs["a"] = 1
        assert_that(events).is_equal_to(["insert:a=1", "change"])
