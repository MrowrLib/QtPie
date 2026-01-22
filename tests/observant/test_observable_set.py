"""Tests for ObservableSet."""

from assertpy import assert_that
from observant import ObservableSet


class TestObservableSetBasics:
    """Test basic set operations."""

    def test_empty_set(self) -> None:
        """Empty set has length 0."""
        obs = ObservableSet[int]()
        assert_that(len(obs)).is_equal_to(0)

    def test_init_with_items(self) -> None:
        """Can initialize with items."""
        obs = ObservableSet[int]({1, 2, 3})
        assert_that(len(obs)).is_equal_to(3)
        assert_that(1 in obs).is_true()

    def test_add(self) -> None:
        """Add adds item."""
        obs = ObservableSet[int]()
        obs.add(42)
        assert_that(len(obs)).is_equal_to(1)
        assert_that(42 in obs).is_true()

    def test_add_duplicate(self) -> None:
        """Adding duplicate does not increase size."""
        obs = ObservableSet[int]({1, 2})
        obs.add(1)
        assert_that(len(obs)).is_equal_to(2)

    def test_remove(self) -> None:
        """Remove removes item."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.remove(2)
        assert_that(obs.to_set()).is_equal_to({1, 3})

    def test_discard(self) -> None:
        """Discard removes item if present."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.discard(2)
        assert_that(obs.to_set()).is_equal_to({1, 3})

    def test_discard_missing(self) -> None:
        """Discard does nothing if item not present."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.discard(99)
        assert_that(obs.to_set()).is_equal_to({1, 2, 3})

    def test_pop(self) -> None:
        """Pop removes and returns an item."""
        obs = ObservableSet[int]({42})
        item = obs.pop()
        assert_that(item).is_equal_to(42)
        assert_that(len(obs)).is_equal_to(0)

    def test_clear(self) -> None:
        """Clear removes all items."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.clear()
        assert_that(len(obs)).is_equal_to(0)

    def test_update(self) -> None:
        """Update adds items from another set."""
        obs = ObservableSet[int]({1})
        obs.update({2, 3})
        assert_that(obs.to_set()).is_equal_to({1, 2, 3})

    def test_replace(self) -> None:
        """Replace all items atomically."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.replace({4, 5})
        assert_that(obs.to_set()).is_equal_to({4, 5})

    def test_replace_empty(self) -> None:
        """Replace with empty set."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.replace(set())
        assert_that(len(obs)).is_equal_to(0)

    def test_replace_from_empty(self) -> None:
        """Replace empty set with items."""
        obs = ObservableSet[int]()
        obs.replace({1, 2, 3})
        assert_that(obs.to_set()).is_equal_to({1, 2, 3})

    def test_intersection_update(self) -> None:
        """Intersection update keeps only common items."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.intersection_update({2, 3, 4})
        assert_that(obs.to_set()).is_equal_to({2, 3})

    def test_difference_update(self) -> None:
        """Difference update removes items in other."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.difference_update({2, 4})
        assert_that(obs.to_set()).is_equal_to({1, 3})

    def test_symmetric_difference_update(self) -> None:
        """Symmetric difference update keeps items in either but not both."""
        obs = ObservableSet[int]({1, 2, 3})
        obs.symmetric_difference_update({2, 3, 4})
        assert_that(obs.to_set()).is_equal_to({1, 4})

    def test_contains(self) -> None:
        """Check item in set."""
        obs = ObservableSet[int]({1, 2, 3})
        assert_that(2 in obs).is_true()
        assert_that(99 in obs).is_false()

    def test_iter(self) -> None:
        """Iterate over set."""
        obs = ObservableSet[int]({1, 2, 3})
        assert_that(set(obs)).is_equal_to({1, 2, 3})

    def test_issubset(self) -> None:
        """Test subset relationship."""
        obs = ObservableSet[int]({1, 2})
        assert_that(obs.issubset({1, 2, 3})).is_true()
        assert_that(obs.issubset({1})).is_false()

    def test_issuperset(self) -> None:
        """Test superset relationship."""
        obs = ObservableSet[int]({1, 2, 3})
        assert_that(obs.issuperset({1, 2})).is_true()
        assert_that(obs.issuperset({1, 4})).is_false()

    def test_isdisjoint(self) -> None:
        """Test disjoint relationship."""
        obs = ObservableSet[int]({1, 2})
        assert_that(obs.isdisjoint({3, 4})).is_true()
        assert_that(obs.isdisjoint({2, 3})).is_false()

    def test_union(self) -> None:
        """Union returns new set."""
        obs = ObservableSet[int]({1, 2})
        result = obs.union({3, 4})
        assert_that(result).is_equal_to({1, 2, 3, 4})
        assert_that(obs.to_set()).is_equal_to({1, 2})  # Original unchanged

    def test_intersection(self) -> None:
        """Intersection returns new set."""
        obs = ObservableSet[int]({1, 2, 3})
        result = obs.intersection({2, 3, 4})
        assert_that(result).is_equal_to({2, 3})

    def test_difference(self) -> None:
        """Difference returns new set."""
        obs = ObservableSet[int]({1, 2, 3})
        result = obs.difference({2, 4})
        assert_that(result).is_equal_to({1, 3})

    def test_symmetric_difference(self) -> None:
        """Symmetric difference returns new set."""
        obs = ObservableSet[int]({1, 2, 3})
        result = obs.symmetric_difference({2, 3, 4})
        assert_that(result).is_equal_to({1, 4})


class TestObservableSetCallbacks:
    """Test change callbacks."""

    def test_on_change_fires_on_add(self) -> None:
        """Callback fires on add."""
        obs = ObservableSet[int]()
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.add(1)
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_not_fired_on_duplicate_add(self) -> None:
        """Callback does not fire when adding duplicate."""
        obs = ObservableSet[int]({1})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.add(1)
        assert_that(changes).is_equal_to([])

    def test_on_change_fires_on_remove(self) -> None:
        """Callback fires on remove."""
        obs = ObservableSet[int]({1, 2})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.remove(1)
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_discard(self) -> None:
        """Callback fires on discard if item was present."""
        obs = ObservableSet[int]({1, 2})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.discard(1)
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_not_fired_on_discard_missing(self) -> None:
        """Callback does not fire when discarding missing item."""
        obs = ObservableSet[int]({1})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.discard(99)
        assert_that(changes).is_equal_to([])

    def test_on_change_fires_on_clear(self) -> None:
        """Callback fires on clear."""
        obs = ObservableSet[int]({1, 2})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.clear()
        assert_that(changes).is_equal_to(["changed"])

    def test_on_change_fires_on_replace(self) -> None:
        """Callback fires on replace."""
        obs = ObservableSet[int]({1, 2})
        changes: list[str] = []
        obs.on_change(lambda: changes.append("changed"))

        obs.replace({3, 4, 5})
        assert_that(changes).is_equal_to(["changed"])

    def test_on_clear_fires_on_replace(self) -> None:
        """Clear callback fires on replace (with old items)."""
        obs = ObservableSet[int]({1, 2})
        cleared: list[set[int]] = []
        obs.on_clear(lambda items: cleared.append(set(items)))

        obs.replace({3, 4, 5})
        assert_that(cleared).is_equal_to([{1, 2}])

    def test_replace_no_add_callbacks(self) -> None:
        """Replace does NOT fire individual add callbacks."""
        obs = ObservableSet[int]({1, 2})
        adds: list[int] = []
        obs.on_add(lambda item: adds.append(item))

        obs.replace({3, 4, 5})
        # Should NOT have any add callbacks - that's the point of replace
        assert_that(adds).is_empty()

    def test_multiple_callbacks(self) -> None:
        """Multiple callbacks all fire."""
        obs = ObservableSet[int]()
        results: list[int] = []
        obs.on_change(lambda: results.append(1))
        obs.on_change(lambda: results.append(2))

        obs.add(42)
        assert_that(results).is_equal_to([1, 2])

    def test_duplicate_callback_ignored(self) -> None:
        """Same callback not added twice."""
        obs = ObservableSet[int]()
        results: list[int] = []

        def cb() -> None:
            results.append(1)

        obs.on_change(cb)
        obs.on_change(cb)

        obs.add(42)
        assert_that(results).is_equal_to([1])


class TestObservableSetDirty:
    """Test dirty tracking."""

    def test_initially_not_dirty(self) -> None:
        """New set is not dirty."""
        obs = ObservableSet[int]({1, 2, 3})
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_add(self) -> None:
        """Set becomes dirty after add."""
        obs = ObservableSet[int]()
        obs.add(1)
        assert_that(bool(obs.is_dirty)).is_true()

    def test_dirty_after_remove(self) -> None:
        """Set becomes dirty after remove."""
        obs = ObservableSet[int]({1, 2})
        obs.remove(1)
        assert_that(bool(obs.is_dirty)).is_true()

    def test_not_dirty_after_duplicate_add(self) -> None:
        """Set stays clean after adding duplicate."""
        obs = ObservableSet[int]({1, 2})
        obs.add(1)
        assert_that(bool(obs.is_dirty)).is_false()

    def test_reset_dirty_clears(self) -> None:
        """reset_dirty marks as clean."""
        obs = ObservableSet[int]()
        obs.add(1)
        assert_that(bool(obs.is_dirty)).is_true()

        obs.reset_dirty()
        assert_that(bool(obs.is_dirty)).is_false()

    def test_dirty_after_reset_and_change(self) -> None:
        """After reset, new changes make dirty again."""
        obs = ObservableSet[int]()
        obs.add(1)
        obs.reset_dirty()

        obs.add(2)
        assert_that(bool(obs.is_dirty)).is_true()

    def test_clean_if_reverted_to_clean_state(self) -> None:
        """Reverting to clean state makes it clean."""
        obs = ObservableSet[int]({1, 2})
        obs.reset_dirty()

        obs.add(3)
        assert_that(bool(obs.is_dirty)).is_true()

        obs.remove(3)  # back to {1, 2}
        assert_that(bool(obs.is_dirty)).is_false()

    def test_is_dirty_is_observable(self) -> None:
        """is_dirty can be subscribed to."""
        obs = ObservableSet[int]()
        dirty_states: list[bool] = []

        obs.is_dirty.on_change(lambda d: dirty_states.append(d))

        obs.add(1)  # clean -> dirty
        obs.add(2)  # stays dirty
        obs.reset_dirty()  # dirty -> clean

        assert_that(dirty_states).is_equal_to([True, False])


class TestObservableSetGranularCallbacks:
    """Test granular add/remove/clear callbacks."""

    def test_on_add_fires_on_add(self) -> None:
        """on_add fires with correct item on add."""
        obs = ObservableSet[str]({"a", "b"})
        adds: list[str] = []
        obs.on_add(lambda item: adds.append(item))

        obs.add("c")
        assert_that(adds).is_equal_to(["c"])

    def test_on_add_not_fired_on_duplicate(self) -> None:
        """on_add does not fire for duplicate add."""
        obs = ObservableSet[str]({"a"})
        adds: list[str] = []
        obs.on_add(lambda item: adds.append(item))

        obs.add("a")
        assert_that(adds).is_equal_to([])

    def test_on_add_fires_on_update(self) -> None:
        """on_add fires for each new item on update."""
        obs = ObservableSet[str]({"a"})
        adds: list[str] = []
        obs.on_add(lambda item: adds.append(item))

        obs.update({"a", "b", "c"})
        assert_that(set(adds)).is_equal_to({"b", "c"})

    def test_on_remove_fires_on_remove(self) -> None:
        """on_remove fires with correct item."""
        obs = ObservableSet[str]({"a", "b", "c"})
        removes: list[str] = []
        obs.on_remove(lambda item: removes.append(item))

        obs.remove("b")
        assert_that(removes).is_equal_to(["b"])

    def test_on_remove_fires_on_discard(self) -> None:
        """on_remove fires on discard if item was present."""
        obs = ObservableSet[str]({"a", "b", "c"})
        removes: list[str] = []
        obs.on_remove(lambda item: removes.append(item))

        obs.discard("b")
        assert_that(removes).is_equal_to(["b"])

    def test_on_remove_not_fired_on_discard_missing(self) -> None:
        """on_remove does not fire when discarding missing item."""
        obs = ObservableSet[str]({"a"})
        removes: list[str] = []
        obs.on_remove(lambda item: removes.append(item))

        obs.discard("z")
        assert_that(removes).is_equal_to([])

    def test_on_remove_fires_on_pop(self) -> None:
        """on_remove fires on pop."""
        obs = ObservableSet[str]({"a"})
        removes: list[str] = []
        obs.on_remove(lambda item: removes.append(item))

        obs.pop()
        assert_that(removes).is_equal_to(["a"])

    def test_on_remove_fires_on_difference_update(self) -> None:
        """on_remove fires for each removed item on difference_update."""
        obs = ObservableSet[str]({"a", "b", "c"})
        removes: list[str] = []
        obs.on_remove(lambda item: removes.append(item))

        obs.difference_update({"b", "c", "d"})
        assert_that(set(removes)).is_equal_to({"b", "c"})

    def test_on_clear_fires_with_removed_items(self) -> None:
        """on_clear fires with set of all removed items."""
        obs = ObservableSet[str]({"a", "b", "c"})
        clears: list[set[str]] = []
        obs.on_clear(lambda items: clears.append(items))

        obs.clear()
        assert_that(clears).is_equal_to([{"a", "b", "c"}])

    def test_on_clear_fires_with_empty_set_if_already_empty(self) -> None:
        """on_clear fires with empty set if set was already empty."""
        obs = ObservableSet[str]()
        clears: list[set[str]] = []
        obs.on_clear(lambda items: clears.append(items))

        obs.clear()
        assert_that(clears).is_equal_to([set()])

    def test_multiple_granular_callbacks(self) -> None:
        """Multiple callbacks of same type all fire."""
        obs = ObservableSet[str]()
        results: list[int] = []
        obs.on_add(lambda item: results.append(1))
        obs.on_add(lambda item: results.append(2))

        obs.add("a")
        assert_that(results).is_equal_to([1, 2])

    def test_duplicate_granular_callback_ignored(self) -> None:
        """Same callback not added twice."""
        obs = ObservableSet[str]()
        results: list[int] = []

        def cb(item: str) -> None:
            results.append(1)

        obs.on_add(cb)
        obs.on_add(cb)

        obs.add("a")
        assert_that(results).is_equal_to([1])

    def test_granular_and_generic_both_fire(self) -> None:
        """Both granular and generic on_change fire."""
        obs = ObservableSet[str]()
        events: list[str] = []
        obs.on_add(lambda item: events.append(f"add:{item}"))
        obs.on_change(lambda: events.append("change"))

        obs.add("a")
        assert_that(events).is_equal_to(["add:a", "change"])

    def test_symmetric_difference_update_callbacks(self) -> None:
        """symmetric_difference_update fires both add and remove callbacks."""
        obs = ObservableSet[str]({"a", "b"})
        adds: list[str] = []
        removes: list[str] = []
        obs.on_add(lambda item: adds.append(item))
        obs.on_remove(lambda item: removes.append(item))

        obs.symmetric_difference_update({"b", "c"})
        assert_that(set(adds)).is_equal_to({"c"})
        assert_that(set(removes)).is_equal_to({"b"})


class TestObservableSetEquality:
    """Test equality comparisons."""

    def test_equal_to_observable_set(self) -> None:
        """Two ObservableSets with same items are equal."""
        obs1 = ObservableSet[int]({1, 2, 3})
        obs2 = ObservableSet[int]({1, 2, 3})
        assert_that(obs1 == obs2).is_true()

    def test_equal_to_regular_set(self) -> None:
        """ObservableSet equals regular set with same items."""
        obs = ObservableSet[int]({1, 2, 3})
        assert_that(obs == {1, 2, 3}).is_true()

    def test_not_equal_different_items(self) -> None:
        """ObservableSets with different items are not equal."""
        obs1 = ObservableSet[int]({1, 2, 3})
        obs2 = ObservableSet[int]({1, 2, 4})
        assert_that(obs1 == obs2).is_false()

    def test_repr(self) -> None:
        """repr shows items."""
        obs = ObservableSet[int]({1})
        assert_that(repr(obs)).is_equal_to("ObservableSet({1})")


class TestObservableSetValidation:
    """Test validation functionality."""

    def test_initially_valid(self) -> None:
        """New set is valid."""
        obs = ObservableSet[int]()
        assert_that(bool(obs.is_valid)).is_true()

    def test_validator_makes_invalid(self) -> None:
        """Validator can make set invalid."""
        obs = ObservableSet[int]()
        obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")
        assert_that(bool(obs.is_valid)).is_false()

    def test_becomes_valid_after_add(self) -> None:
        """Set becomes valid after satisfying validator."""
        obs = ObservableSet[int]()
        obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")
        assert_that(bool(obs.is_valid)).is_false()

        obs.add(1)
        assert_that(bool(obs.is_valid)).is_true()

    def test_validation_errors_dict(self) -> None:
        """Validation errors are accessible by name."""
        obs = ObservableSet[int]()
        obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")

        errors = obs.validation_errors.get()
        assert_that(errors["not_empty"]).is_equal_to(["Set must not be empty"])

    def test_validation_error_messages(self) -> None:
        """Flat list of error messages available."""
        obs = ObservableSet[int]()
        obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")
        obs.add_validator("size", lambda s: None if len(s) <= 5 else "Too many items")

        messages = obs.validation_error_messages.get()
        assert_that(messages).is_equal_to(["Set must not be empty"])

    def test_is_valid_is_observable(self) -> None:
        """is_valid can be subscribed to."""
        obs = ObservableSet[int]()
        obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Empty")

        valid_states: list[bool] = []
        obs.is_valid.on_change(lambda v: valid_states.append(v))

        obs.add(1)  # invalid -> valid
        obs.clear()  # valid -> invalid

        assert_that(valid_states).is_equal_to([True, False])
