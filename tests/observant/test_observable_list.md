# ObservableList Test Summary

## Standard List Operations

ObservableList supports all standard Python list operations: append, extend, insert, remove, pop, clear, indexing, slicing, iteration, contains, index, count.

```python
obs = ObservableList[int]([1, 2, 3])
obs.append(4)
obs.extend([5, 6])
obs.insert(1, 99)
obs.remove(2)
item = obs.pop(0)
del obs[1]
obs[0] = 100
assert_that(2 in obs).is_true()
assert_that(list(obs)).is_equal_to([1, 2, 3])
```

## Generic Change Callbacks

Register callbacks that fire on any mutation via `on_change()`. Multiple callbacks are supported, duplicates ignored.

```python
obs = ObservableList[int]()
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

obs.append(1)  # Fires callback
obs.remove(1)  # Fires callback
obs[0] = 99    # Fires callback
obs.clear()    # Fires callback
```

```python
obs.on_change(lambda: results.append(1))
obs.on_change(lambda: results.append(2))
obs.append(42)
assert_that(results).is_equal_to([1, 2])  # Both fire
```

## Granular Callbacks

Fine-grained callbacks for specific operations: `on_insert`, `on_remove`, `on_replace`, `on_clear`. Each provides detailed change information.

```python
obs = ObservableList[str](["a", "c"])
inserts: list[tuple[int, str]] = []
obs.on_insert(lambda idx, item: inserts.append((idx, item)))

obs.insert(1, "b")
assert_that(inserts).is_equal_to([(1, "b")])
```

```python
obs = ObservableList[str](["a", "b", "c"])
replaces: list[tuple[int, str, str]] = []
obs.on_replace(lambda idx, old, new: replaces.append((idx, old, new)))

obs[1] = "B"
assert_that(replaces).is_equal_to([(1, "b", "B")])
```

```python
obs = ObservableList[str](["a", "b", "c"])
clears: list[list[str]] = []
obs.on_clear(lambda items: clears.append(items))

obs.clear()
assert_that(clears).is_equal_to([["a", "b", "c"]])
```

## Dirty Tracking

Tracks whether the list has been modified since initialization or last reset. Returns to clean state if reverted to original contents.

```python
obs = ObservableList[int]([1, 2])
obs.reset_dirty()
assert_that(bool(obs.is_dirty)).is_false()

obs.append(3)
assert_that(bool(obs.is_dirty)).is_true()

obs.pop()  # back to [1, 2]
assert_that(bool(obs.is_dirty)).is_false()
```

```python
obs = ObservableList[int]()
dirty_states: list[bool] = []
obs.is_dirty.on_change(lambda d: dirty_states.append(d))

obs.append(1)  # clean -> dirty
obs.append(2)  # stays dirty (no callback)
obs.reset_dirty()  # dirty -> clean

assert_that(dirty_states).is_equal_to([True, False])
```
