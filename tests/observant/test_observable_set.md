# ObservableSet Tests

## Basic Set Operations

Standard Python set operations on an observable wrapper. Initialize empty or with items, add/remove items, check containment, iterate, convert to regular set.

```python
obs = ObservableSet[int]({1, 2, 3})
obs.add(42)
assert_that(42 in obs).is_true()
obs.remove(2)
assert_that(obs.to_set()).is_equal_to({1, 3, 42})
```

```python
obs = ObservableSet[int]({1, 2})
obs.update({2, 3})
assert_that(obs.to_set()).is_equal_to({1, 2, 3})
```

## Set Algebra Operations

In-place and immutable set operations: union, intersection, difference, symmetric difference. Also subset/superset/disjoint checks.

```python
obs = ObservableSet[int]({1, 2, 3})
obs.intersection_update({2, 3, 4})
assert_that(obs.to_set()).is_equal_to({2, 3})
```

```python
obs = ObservableSet[int]({1, 2, 3})
result = obs.union({3, 4})
assert_that(result).is_equal_to({1, 2, 3, 4})
assert_that(obs.to_set()).is_equal_to({1, 2, 3})  # Original unchanged
```

## Change Callbacks

Generic `on_change()` callback fires on any mutation that actually changes the set. No callback on duplicate adds or discarding missing items. Multiple callbacks supported, duplicates ignored.

```python
obs = ObservableSet[int]()
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

obs.add(1)
assert_that(changes).is_equal_to(["changed"])
```

```python
obs = ObservableSet[int]({1})
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

obs.add(1)  # duplicate
assert_that(changes).is_equal_to([])
```

## Granular Callbacks

Specific callbacks for `on_add`, `on_remove`, and `on_clear` with item details. Fire alongside generic `on_change`. Only fire on actual mutations.

```python
obs = ObservableSet[str]({"a", "b"})
adds: list[str] = []
obs.on_add(lambda item: adds.append(item))

obs.add("c")
assert_that(adds).is_equal_to(["c"])
```

```python
obs = ObservableSet[str]({"a", "b", "c"})
clears: list[set[str]] = []
obs.on_clear(lambda items: clears.append(items))

obs.clear()
assert_that(clears).is_equal_to([{"a", "b", "c"}])
```

```python
obs = ObservableSet[str]()
events: list[str] = []
obs.on_add(lambda item: events.append(f"add:{item}"))
obs.on_change(lambda: events.append("change"))

obs.add("a")
assert_that(events).is_equal_to(["add:a", "change"])
```

## Dirty Tracking

Tracks whether the set has changed since creation or last `reset_dirty()`. Returns to clean state if reverted to original contents. `is_dirty` is an Observable.

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
obs.add(2)  # stays dirty
obs.reset_dirty()  # dirty -> clean

assert_that(dirty_states).is_equal_to([True, False])
```

## Validation

Named validators return error messages or None. `is_valid` and `validation_errors` are observables that update reactively.

```python
obs = ObservableSet[int]()
obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")
assert_that(bool(obs.is_valid)).is_false()

obs.add(1)
assert_that(bool(obs.is_valid)).is_true()
```

```python
obs = ObservableSet[int]()
obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Empty")

valid_states: list[bool] = []
obs.is_valid.on_change(lambda v: valid_states.append(v))

obs.add(1)  # invalid -> valid
obs.clear()  # valid -> invalid

assert_that(valid_states).is_equal_to([True, False])
```

## Equality

ObservableSet compares equal to other ObservableSets or regular sets with the same items.

```python
obs = ObservableSet[int]({1, 2, 3})
assert_that(obs == {1, 2, 3}).is_true()
```
