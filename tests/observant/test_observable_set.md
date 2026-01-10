# ObservableSet Test Summary

## Basic Set Operations

Standard Python set operations (add, remove, discard, pop, clear, contains, iteration) work as expected. Includes initialization with items and conversion to regular sets.

```python
obs = ObservableSet[int]({1, 2, 3})
obs.add(42)
obs.remove(2)
assert_that(obs.to_set()).is_equal_to({1, 3, 42})
```

## Set Theory Operations

In-place mutations (update, intersection_update, difference_update, symmetric_difference_update) and immutable operations (union, intersection, difference, symmetric_difference). Includes relationship tests (issubset, issuperset, isdisjoint).

```python
obs = ObservableSet[int]({1, 2, 3})
obs.symmetric_difference_update({2, 3, 4})
assert_that(obs.to_set()).is_equal_to({1, 4})
```

```python
obs = ObservableSet[int]({1, 2})
result = obs.union({3, 4})
assert_that(result).is_equal_to({1, 2, 3, 4})
assert_that(obs.to_set()).is_equal_to({1, 2})  # Original unchanged
```

## Change Callbacks

Generic `on_change()` callback fires on any mutation, but only when the set actually changes (not for duplicate adds or missing discards). Multiple callbacks can be registered, and duplicate callback references are ignored.

```python
obs = ObservableSet[int]({1})
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

obs.add(1)  # Duplicate - no callback
assert_that(changes).is_equal_to([])

obs.add(2)  # Actual change - fires callback
assert_that(changes).is_equal_to(["changed"])
```

## Granular Callbacks

Specific callbacks (`on_add`, `on_remove`, `on_clear`) fire for targeted operations with relevant data. Granular and generic callbacks both fire when applicable.

```python
obs = ObservableSet[str]({"a", "b"})
adds: list[str] = []
removes: list[str] = []
obs.on_add(lambda item: adds.append(item))
obs.on_remove(lambda item: removes.append(item))

obs.symmetric_difference_update({"b", "c"})
assert_that(set(adds)).is_equal_to({"c"})
assert_that(set(removes)).is_equal_to({"b"})
```

```python
obs = ObservableSet[str]({"a", "b", "c"})
clears: list[set[str]] = []
obs.on_clear(lambda items: clears.append(items))

obs.clear()
assert_that(clears).is_equal_to([{"a", "b", "c"}])
```

## Dirty Tracking

Observable `is_dirty` property tracks whether the set has changed from its clean state. Set becomes dirty on mutations, can be reset to clean, and automatically becomes clean when reverted to the clean state.

```python
obs = ObservableSet[int]({1, 2})
obs.reset_dirty()

obs.add(3)
assert_that(bool(obs.is_dirty)).is_true()

obs.remove(3)  # back to {1, 2}
assert_that(bool(obs.is_dirty)).is_false()
```

```python
obs = ObservableSet[int]()
dirty_states: list[bool] = []
obs.is_dirty.on_change(lambda d: dirty_states.append(d))

obs.add(1)  # clean -> dirty
obs.reset_dirty()  # dirty -> clean

assert_that(dirty_states).is_equal_to([True, False])
```

## Validation

Named validators can be added to make the set invalid based on custom rules. Observable `is_valid` property and `validation_errors` dict track validation state. Validators return None for valid, error message string for invalid.

```python
obs = ObservableSet[int]()
obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")
assert_that(bool(obs.is_valid)).is_false()

obs.add(1)
assert_that(bool(obs.is_valid)).is_true()
```

```python
obs = ObservableSet[int]()
obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")

errors = obs.validation_errors.get()
assert_that(errors["not_empty"]).is_equal_to(["Set must not be empty"])

messages = obs.validation_error_messages.get()
assert_that(messages).is_equal_to(["Set must not be empty"])
```

## Equality and Representation

ObservableSet supports equality comparison with other ObservableSets and regular Python sets. Provides useful repr output.

```python
obs = ObservableSet[int]({1, 2, 3})
assert_that(obs == {1, 2, 3}).is_true()

assert_that(repr(obs)).contains("ObservableSet")
```
