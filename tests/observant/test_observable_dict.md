# ObservableDict Test Summary

## Basic Dictionary Operations

ObservableDict implements standard dict interface with all common operations.

```python
obs = ObservableDict[str, int]({"a": 1, "b": 2})
obs["key"] = 42
assert_that(obs["key"]).is_equal_to(42)
del obs["a"]
assert_that("a" in obs).is_false()
```

```python
obs = ObservableDict[str, int]({"a": 1})
obs.update({"b": 2, "c": 3})
val = obs.pop("a")
obs.clear()
assert_that(obs.to_dict()).is_equal_to({"a": 1, "b": 2, "c": 3})
```

## Generic Change Callbacks

`on_change()` fires on any modification (setitem, delitem, pop, clear, update, setdefault for new keys).

```python
obs = ObservableDict[str, int]()
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

obs["a"] = 1
assert_that(changes).is_equal_to(["changed"])
```

```python
obs = ObservableDict[str, int]({"a": 1})
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

obs.setdefault("a", 99)
assert_that(changes).is_equal_to([])  # No change for existing key
```

## Dirty Tracking

Tracks whether dict has changed since last reset. Returns to clean if reverted to original state.

```python
obs = ObservableDict[str, int]({"a": 1})
obs.reset_dirty()

obs["b"] = 2
assert_that(bool(obs.is_dirty)).is_true()

del obs["b"]  # back to {"a": 1}
assert_that(bool(obs.is_dirty)).is_false()
```

```python
obs = ObservableDict[str, int]()
dirty_states: list[bool] = []

obs.is_dirty.on_change(lambda d: dirty_states.append(d))

obs["a"] = 1  # clean -> dirty
obs["b"] = 2  # stays dirty
obs.reset_dirty()  # dirty -> clean

assert_that(dirty_states).is_equal_to([True, False])
```

## Granular Callbacks

Separate callbacks for insert (new key), replace (existing key), remove, and clear operations.

```python
obs = ObservableDict[str, int]({"a": 1})
inserts: list[tuple[str, int]] = []
obs.on_insert(lambda k, v: inserts.append((k, v)))

obs["b"] = 2
assert_that(inserts).is_equal_to([("b", 2)])

obs["a"] = 99  # update, not insert
assert_that(inserts).is_equal_to([("b", 2)])  # unchanged
```

```python
obs = ObservableDict[str, int]({"a": 1})
replaces: list[tuple[str, int, int]] = []
obs.on_replace(lambda k, old, new: replaces.append((k, old, new)))

obs["a"] = 99
assert_that(replaces).is_equal_to([("a", 1, 99)])
```

```python
obs = ObservableDict[str, int]({"a": 1, "b": 2})
removes: list[tuple[str, int]] = []
obs.on_remove(lambda k, v: removes.append((k, v)))

del obs["a"]
assert_that(removes).is_equal_to([("a", 1)])
```

```python
obs = ObservableDict[str, int]({"a": 1, "b": 2})
clears: list[dict[str, int]] = []
obs.on_clear(lambda items: clears.append(items))

obs.clear()
assert_that(clears).is_equal_to([{"a": 1, "b": 2}])
```

## Callback Management

Multiple callbacks can be registered. Duplicate callbacks are ignored. Both granular and generic callbacks fire together.

```python
obs = ObservableDict[str, int]()
results: list[int] = []

def cb() -> None:
    results.append(1)

obs.on_change(cb)
obs.on_change(cb)

obs["a"] = 1
assert_that(results).is_equal_to([1])  # Only fires once
```

```python
obs = ObservableDict[str, int]()
events: list[str] = []
obs.on_insert(lambda k, v: events.append(f"insert:{k}={v}"))
obs.on_change(lambda: events.append("change"))

obs["a"] = 1
assert_that(events).is_equal_to(["insert:a=1", "change"])
```
