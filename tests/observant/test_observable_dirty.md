# Observable Dirty Tracking - Usage Patterns

This documents the dirty tracking feature of `Observable` from the `observant` library.

## Core Concept

Dirty tracking monitors whether an Observable's value has changed from its "clean" baseline. Useful for detecting unsaved changes in forms.

## Creating an Observable

Standard Observable creation - starts clean (not dirty):

```python
from observant import Observable

obs = Observable[str]("hello")
```

## Checking Dirty State

Access `is_dirty` property and convert to bool:

```python
is_changed = bool(obs.is_dirty)
```

## Value Changes and Dirty State

Setting a different value makes it dirty:

```python
obs.set("world")  # is_dirty becomes True
```

Setting the same value does NOT make it dirty:

```python
obs.set("hello")  # is_dirty stays False (same as original)
```

## Resetting Dirty State

`reset_dirty()` marks current value as the new clean baseline:

```python
obs.set("world")
obs.reset_dirty()  # "world" is now the clean value
obs.set("foo")     # is_dirty becomes True
obs.set("world")   # is_dirty becomes False (back to clean value)
```

## Subscribing to Dirty State Changes

`is_dirty` is itself an Observable - subscribe to state transitions:

```python
obs.is_dirty.on_change(lambda dirty: print(f"Dirty: {dirty}"))
```

**Key behavior**: Callback fires only on state transitions (clean→dirty, dirty→clean), not on every value change.

```python
obs.set("world")   # fires: True (clean → dirty)
obs.set("another") # NO fire (dirty → dirty)
obs.set("hello")   # fires: False (dirty → clean, back to original)
```

## Observable __bool__ Behavior

Observable supports `bool()` conversion based on its value:

```python
obs = Observable[int](42)
bool(obs)  # True

obs = Observable[int](0)
bool(obs)  # False
```
