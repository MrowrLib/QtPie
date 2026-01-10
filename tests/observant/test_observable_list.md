# ObservableList Tests

## Standard List Operations

`ObservableList[T]` implements standard Python list operations: append, extend, insert, remove, pop, clear, indexing, slicing, iteration, contains, count, and index.

```python
obs = ObservableList[int]([1, 2, 3])
obs.append(4)
obs.insert(1, 99)
obs.remove(2)
item = obs.pop()
obs[0] = 100
del obs[1]
assert_that(2 in obs).is_true()
assert_that(list(obs)).is_equal_to([1, 2, 3])
```

## Generic Change Callbacks

`on_change()` fires on any modification to the list.

```python
obs = ObservableList[int]()
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

obs.append(1)
obs.remove(1)
obs[0] = 99
obs.clear()
# Callback fires after each operation
```

Multiple callbacks can be registered. Duplicate callbacks are ignored.

```python
obs.on_change(lambda: results.append(1))
obs.on_change(lambda: results.append(2))
obs.append(42)
assert_that(results).is_equal_to([1, 2])
```

## Granular Callbacks

Specific callbacks provide detailed information about each operation type.

### on_insert

Fires with `(index, item)` when items are added.

```python
obs = ObservableList[str](["a", "b"])
inserts: list[tuple[int, str]] = []
obs.on_insert(lambda idx, item: inserts.append((idx, item)))

obs.append("c")          # [(2, "c")]
obs.insert(1, "x")       # [(1, "x")]
obs.extend(["d", "e"])   # [(3, "d"), (4, "e")]
```

### on_remove

Fires with `(index, item)` when items are removed.

```python
obs = ObservableList[str](["a", "b", "c"])
removes: list[tuple[int, str]] = []
obs.on_remove(lambda idx, item: removes.append((idx, item)))

obs.remove("b")  # [(1, "b")]
obs.pop()        # [(2, "c")]
obs.pop(0)       # [(0, "a")]
del obs[1]       # [(1, item)]
```

### on_replace

Fires with `(index, old_item, new_item)` when items are replaced.

```python
obs = ObservableList[str](["a", "b", "c"])
replaces: list[tuple[int, str, str]] = []
obs.on_replace(lambda idx, old, new: replaces.append((idx, old, new)))

obs[1] = "B"
assert_that(replaces).is_equal_to([(1, "b", "B")])
```

### on_clear

Fires with `list[items]` containing all removed items.

```python
obs = ObservableList[str](["a", "b", "c"])
clears: list[list[str]] = []
obs.on_clear(lambda items: clears.append(items))

obs.clear()
assert_that(clears).is_equal_to([["a", "b", "c"]])
```

## Dirty Tracking

`is_dirty` tracks whether the list has been modified since creation or last reset. Automatically becomes clean if reverted to the clean state.

```python
obs = ObservableList[int]([1, 2])
assert_that(bool(obs.is_dirty)).is_false()

obs.append(3)
assert_that(bool(obs.is_dirty)).is_true()

obs.pop()  # back to [1, 2]
assert_that(bool(obs.is_dirty)).is_false()

obs.append(3)
obs.reset_dirty()
assert_that(bool(obs.is_dirty)).is_false()
```

`is_dirty` is itself an Observable that fires only on state transitions (clean↔dirty).

```python
obs = ObservableList[int]()
dirty_states: list[bool] = []
obs.is_dirty.on_change(lambda d: dirty_states.append(d))

obs.append(1)  # clean -> dirty, fires
obs.append(2)  # stays dirty, doesn't fire
obs.reset_dirty()  # dirty -> clean, fires

assert_that(dirty_states).is_equal_to([True, False])
```
