# Observable Dirty Tracking

## Dirty State Tracking

`Observable` tracks whether its value has changed from the initial (or last reset) value. Setting to the same value doesn't mark it dirty.

```python
obs = Observable[str]("hello")
obs.set("world")
assert_that(bool(obs.is_dirty)).is_true()

obs.set("hello")  # back to original
assert_that(bool(obs.is_dirty)).is_false()
```

## Reset Dirty

`reset_dirty()` marks the current value as the new "clean" baseline. After reset, the Observable is not dirty until the value changes again.

```python
obs = Observable[str]("hello")
obs.set("world")
obs.reset_dirty()  # "world" is now clean

obs.set("foo")
assert_that(bool(obs.is_dirty)).is_true()

obs.set("world")  # back to clean value
assert_that(bool(obs.is_dirty)).is_false()
```

## Dirty as Observable

`is_dirty` returns an `Observable[bool]` that fires callbacks only on state transitions (clean ↔ dirty), not on every change.

```python
obs = Observable[str]("hello")
dirty_changes: list[bool] = []

obs.is_dirty.on_change(lambda d: dirty_changes.append(d))

obs.set("world")  # clean -> dirty
obs.set("another")  # dirty -> dirty (no fire)
obs.set("hello")  # dirty -> clean (back to original)

assert_that(dirty_changes).is_equal_to([True, False])
```

## Boolean Conversion

`Observable` supports `bool()` conversion based on the truthiness of its wrapped value.

```python
obs = Observable[int](42)
assert_that(bool(obs)).is_true()

obs = Observable[int](0)
assert_that(bool(obs)).is_false()

obs = Observable[str]("hello")
assert_that(bool(obs)).is_true()

obs.set("")
assert_that(bool(obs)).is_false()
```
