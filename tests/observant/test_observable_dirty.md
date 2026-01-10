# Observable Dirty Tracking Tests

## Dirty Tracking

Observable tracks whether its value has changed from its original (or last reset) value.

```python
obs = Observable[str]("hello")
assert_that(bool(obs.is_dirty)).is_false()

obs.set("world")
assert_that(bool(obs.is_dirty)).is_true()
```

## Smart Dirty Detection

Setting the same value doesn't mark it dirty. Setting back to the clean value marks it clean again.

```python
obs = Observable[str]("hello")
obs.set("hello")
assert_that(bool(obs.is_dirty)).is_false()
```

```python
obs = Observable[str]("hello")
obs.set("world")
obs.reset_dirty()  # "world" is now clean

obs.set("foo")
assert_that(bool(obs.is_dirty)).is_true()

obs.set("world")  # back to clean value
assert_that(bool(obs.is_dirty)).is_false()
```

## Reactive Dirty State

`is_dirty` returns an Observable that fires only on state transitions (clean ↔ dirty).

```python
obs = Observable[str]("hello")
dirty_changes: list[bool] = []

obs.is_dirty.on_change(lambda d: dirty_changes.append(d))

obs.set("world")  # clean -> dirty
obs.set("another")  # dirty -> dirty (no fire)
obs.set("hello")  # dirty -> clean (back to original)

assert_that(dirty_changes).is_equal_to([True, False])
```

## Boolean Coercion

Observable delegates `__bool__` to its wrapped value.

```python
obs = Observable[int](42)
assert_that(bool(obs)).is_true()

obs = Observable[int](0)
assert_that(bool(obs)).is_false()
```
