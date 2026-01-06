"""Tests for ObservableList."""

from assertpy import assert_that
from observant import ObservableList


class TestObservableListBasics:
    """Test basic list operations."""

    def test_empty_list(self) -> None:
        """Empty list has length 0."""
        obs = ObservableList[int]()
        assert_that(len(obs)).is_equal_to(0)

    def test_init_with_items(self) -> None:
        """Can initialize with items."""
        obs = ObservableList[int]([1, 2, 3])
        assert_that(len(obs)).is_equal_to(3)
        assert_that(obs[0]).is_equal_to(1)

    def test_append(self) -> None:
        """Append adds item."""
        obs = ObservableList[int]()
        obs.append(42)
        assert_that(len(obs)).is_equal_to(1)
        assert_that(obs[0]).is_equal_to(42)

    def test_extend(self) -> None:
        """Extend adds multiple items."""
        obs = ObservableList[int]([1])
        obs.extend([2, 3])
        assert_that(obs.to_list()).is_equal_to([1, 2, 3])

    def test_insert(self) -> None:
        """Insert at index."""
        obs = ObservableList[int]([1, 3])
        obs.insert(1, 2)
        assert_that(obs.to_list()).is_equal_to([1, 2, 3])

    def test_remove(self) -> None:
        """Remove item."""
        obs = ObservableList[int]([1, 2, 3])
        obs.remove(2)
        assert_that(obs.to_list()).is_equal_to([1, 3])

    def test_pop(self) -> None:
        """Pop removes and returns."""
        obs = ObservableList[int]([1, 2, 3])
        item = obs.pop()
        assert_that(item).is_equal_to(3)
        assert_that(obs.to_list()).is_equal_to([1, 2])

    def test_pop_at_index(self) -> None:
        """Pop at specific index."""
        obs = ObservableList[int]([1, 2, 3])
        item = obs.pop(0)
        assert_that(item).is_equal_to(1)
        assert_that(obs.to_list()).is_equal_to([2, 3])

    def test_clear(self) -> None:
        """Clear removes all."""
        obs = ObservableList[int]([1, 2, 3])
        obs.clear()
        assert_that(len(obs)).is_equal_to(0)

    def test_setitem(self) -> None:
        """Set item at index."""
        obs = ObservableList[int]([1, 2, 3])
        obs[1] = 99
        assert_that(obs.to_list()).is_equal_to([1, 99, 3])

    def test_delitem(self) -> None:
        """Delete item at index."""
        obs = ObservableList[int]([1, 2, 3])
        del obs[1]
        assert_that(obs.to_list()).is_equal_to([1, 3])

    def test_contains(self) -> None:
        """Check item in list."""
        obs = ObservableList[int]([1, 2, 3])
        assert_that(2 in obs).is_true()
        assert_that(99 in obs).is_false()

    def test_iter(self) -> None:
        """Iterate over list."""
        obs = ObservableList[int]([1, 2, 3])
        assert_that(list(obs)).is_equal_to([1, 2, 3])

    def test_index(self) -> None:
        """Find index of item."""
        obs = ObservableList[int]([1, 2, 3])
        assert_that(obs.index(2)).is_equal_to(1)

    def test_count(self) -> None:
        """Count occurrences."""
        obs = ObservableList[int]([1, 2, 2, 3])
        assert_that(obs.count(2)).is_equal_to(2)


class TestObservableListCallbacks:
    """Test change callbacks."""

    def test_on_change_fires_on_append(self) -> None:
        """Callback fires on append."""
        obs = ObservableList[int]()
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.append(1)
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_remove(self) -> None:
        """Callback fires on remove."""
        obs = ObservableList[int]([1, 2])
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.remove(1)
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_setitem(self) -> None:
        """Callback fires on setitem."""
        obs = ObservableList[int]([1, 2])
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs[0] = 99
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_clear(self) -> None:
        """Callback fires on clear."""
        obs = ObservableList[int]([1, 2])
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.clear()
        assert_that(changes).is_equal_to(["changed"])

    def test_multiple_callbacks(self) -> None:
        """Multiple callbacks all fire."""
        obs = ObservableList[int]()
        results: list[int] = []
        obs.on_change(lambda: results.append(1))
        obs.on_change(lambda: results.append(2))

        obs.append(42)
        assert_that(results).is_equal_to([1, 2])

    def test_duplicate_callback_ignored(self) -> None:
        """Same callback not added twice."""
        obs = ObservableList[int]()
        results: list[int] = []

        def cb() -> None:
            results.append(1)

        obs.on_change(cb)
        obs.on_change(cb)

        obs.append(42)
        assert_that(results).is_equal_to([1])


class TestObservableListDirty:
    """Test dirty tracking."""

    def test_initially_not_dirty(self) -> None:
        """New list is not dirty."""
        obs = ObservableList[int]([1, 2, 3])
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_append(self) -> None:
        """List becomes dirty after append."""
        obs = ObservableList[int]()
        obs.append(1)
        assert_that(bool(obs.is_dirty)).is_true()

    def test_dirty_after_remove(self) -> None:
        """List becomes dirty after remove."""
        obs = ObservableList[int]([1, 2])
        obs.remove(1)
        assert_that(bool(obs.is_dirty)).is_true()

    def test_dirty_after_setitem(self) -> None:
        """List becomes dirty after setitem."""
        obs = ObservableList[int]([1, 2])
        obs[0] = 99
        assert_that(bool(obs.is_dirty)).is_true()

    def test_reset_dirty_clears(self) -> None:
        """reset_dirty marks as clean."""
        obs = ObservableList[int]()
        obs.append(1)
        assert_that(bool(obs.is_dirty)).is_true()

        obs.reset_dirty()
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_reset_and_change(self) -> None:
        """After reset, new changes make dirty again."""
        obs = ObservableList[int]()
        obs.append(1)
        obs.reset_dirty()

        obs.append(2)
        assert_that(bool(obs.is_dirty)).is_true()

    def test_clean_if_reverted_to_clean_state(self) -> None:
        """Reverting to clean state makes it clean."""
        obs = ObservableList[int]([1, 2])
        obs.reset_dirty()

        obs.append(3)
        assert_that(bool(obs.is_dirty)).is_true()

        obs.pop()  # back to [1, 2]
        assert_that(bool(obs.is_dirty)).is_false()

    def test_is_dirty_is_observable(self) -> None:
        """is_dirty can be subscribed to."""
        obs = ObservableList[int]()
        dirty_states: list[bool] = []

        obs.is_dirty.on_change(lambda d: dirty_states.append(d))

        obs.append(1)  # clean -> dirty
        obs.append(2)  # stays dirty
        obs.reset_dirty()  # dirty -> clean

        assert_that(dirty_states).is_equal_to([True, False])


class TestObservableListGranularCallbacks:
    """Test granular insert/remove/replace/clear callbacks."""

    def test_on_insert_fires_on_append(self) -> None:
        """on_insert fires with correct index and item on append."""
        obs = ObservableList[str](["a", "b"])
        inserts: list[tuple[int, str]] = []
        obs.on_insert(lambda idx, item: inserts.append((idx, item)))

        obs.append("c")
        assert_that(inserts).is_equal_to([(2, "c")])

    def test_on_insert_fires_on_insert(self) -> None:
        """on_insert fires with correct index on insert."""
        obs = ObservableList[str](["a", "c"])
        inserts: list[tuple[int, str]] = []
        obs.on_insert(lambda idx, item: inserts.append((idx, item)))

        obs.insert(1, "b")
        assert_that(inserts).is_equal_to([(1, "b")])

    def test_on_insert_fires_on_extend(self) -> None:
        """on_insert fires for each item on extend."""
        obs = ObservableList[str](["a"])
        inserts: list[tuple[int, str]] = []
        obs.on_insert(lambda idx, item: inserts.append((idx, item)))

        obs.extend(["b", "c", "d"])
        assert_that(inserts).is_equal_to([(1, "b"), (2, "c"), (3, "d")])

    def test_on_remove_fires_on_remove(self) -> None:
        """on_remove fires with correct index and item."""
        obs = ObservableList[str](["a", "b", "c"])
        removes: list[tuple[int, str]] = []
        obs.on_remove(lambda idx, item: removes.append((idx, item)))

        obs.remove("b")
        assert_that(removes).is_equal_to([(1, "b")])

    def test_on_remove_fires_on_pop(self) -> None:
        """on_remove fires on pop with correct index."""
        obs = ObservableList[str](["a", "b", "c"])
        removes: list[tuple[int, str]] = []
        obs.on_remove(lambda idx, item: removes.append((idx, item)))

        obs.pop()  # removes "c" at index 2
        assert_that(removes).is_equal_to([(2, "c")])

    def test_on_remove_fires_on_pop_at_index(self) -> None:
        """on_remove fires on pop(index) with correct index."""
        obs = ObservableList[str](["a", "b", "c"])
        removes: list[tuple[int, str]] = []
        obs.on_remove(lambda idx, item: removes.append((idx, item)))

        obs.pop(0)  # removes "a" at index 0
        assert_that(removes).is_equal_to([(0, "a")])

    def test_on_remove_fires_on_pop_negative_index(self) -> None:
        """on_remove normalizes negative index."""
        obs = ObservableList[str](["a", "b", "c"])
        removes: list[tuple[int, str]] = []
        obs.on_remove(lambda idx, item: removes.append((idx, item)))

        obs.pop(-2)  # removes "b" at index 1
        assert_that(removes).is_equal_to([(1, "b")])

    def test_on_remove_fires_on_delitem(self) -> None:
        """on_remove fires on del list[index]."""
        obs = ObservableList[str](["a", "b", "c"])
        removes: list[tuple[int, str]] = []
        obs.on_remove(lambda idx, item: removes.append((idx, item)))

        del obs[1]
        assert_that(removes).is_equal_to([(1, "b")])

    def test_on_replace_fires_on_setitem(self) -> None:
        """on_replace fires with index, old, and new item."""
        obs = ObservableList[str](["a", "b", "c"])
        replaces: list[tuple[int, str, str]] = []
        obs.on_replace(lambda idx, old, new: replaces.append((idx, old, new)))

        obs[1] = "B"
        assert_that(replaces).is_equal_to([(1, "b", "B")])

    def test_on_clear_fires_with_removed_items(self) -> None:
        """on_clear fires with list of all removed items."""
        obs = ObservableList[str](["a", "b", "c"])
        clears: list[list[str]] = []
        obs.on_clear(lambda items: clears.append(items))

        obs.clear()
        assert_that(clears).is_equal_to([["a", "b", "c"]])

    def test_on_clear_fires_with_empty_list_if_already_empty(self) -> None:
        """on_clear fires with empty list if list was already empty."""
        obs = ObservableList[str]()
        clears: list[list[str]] = []
        obs.on_clear(lambda items: clears.append(items))

        obs.clear()
        assert_that(clears).is_equal_to([[]])

    def test_multiple_granular_callbacks(self) -> None:
        """Multiple callbacks of same type all fire."""
        obs = ObservableList[str]()
        results: list[int] = []
        obs.on_insert(lambda idx, item: results.append(1))
        obs.on_insert(lambda idx, item: results.append(2))

        obs.append("a")
        assert_that(results).is_equal_to([1, 2])

    def test_duplicate_granular_callback_ignored(self) -> None:
        """Same callback not added twice."""
        obs = ObservableList[str]()
        results: list[int] = []

        def cb(idx: int, item: str) -> None:
            results.append(1)

        obs.on_insert(cb)
        obs.on_insert(cb)

        obs.append("a")
        assert_that(results).is_equal_to([1])

    def test_granular_and_generic_both_fire(self) -> None:
        """Both granular and generic on_change fire."""
        obs = ObservableList[str]()
        events: list[str] = []
        obs.on_insert(lambda idx, item: events.append(f"insert:{item}"))
        obs.on_change(lambda: events.append("change"))

        obs.append("a")
        assert_that(events).is_equal_to(["insert:a", "change"])
