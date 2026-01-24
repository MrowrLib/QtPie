# ObservableDict Usage Patterns

This document summarizes usage patterns for `ObservableDict` from the Observant library, based on test file analysis.

## Basic Initialization

Create an observable dictionary with type parameters for key and value types.

```python
obs = ObservableDict[str, int]()
obs = ObservableDict[str, int]({"a": 1, "b": 2})
```

## Standard Dict Operations

`ObservableDict` supports all standard Python dict operations.

```python
obs["key"] = 42           # Set item
value = obs["key"]        # Get item
del obs["key"]            # Delete item
value = obs.get("key", 99)  # Get with default
```

## Removal Operations

Multiple methods for removing items.

```python
val = obs.pop("key")        # Remove and return value
val = obs.pop("key", 99)    # With default for missing
key, val = obs.popitem()    # Remove and return arbitrary pair
obs.clear()                 # Remove all items
```

## Bulk Update Methods

Update multiple items or replace all content.

```python
obs.update({"b": 2, "c": 3})   # Merge items (triggers per-item callbacks)
obs.replace({"x": 1, "y": 2})  # Atomic replacement (no per-item callbacks)
```

## Conditional Set

Set value only if key doesn't exist.

```python
val = obs.setdefault("key", 99)  # Returns existing or sets/returns default
```

## Iteration and Views

Standard dict iteration patterns work.

```python
for key in obs: ...
obs.keys()
obs.values()
obs.items()
obs.to_dict()  # Convert to regular dict
```

## Generic Change Callback

Subscribe to any mutation with `on_change`.

```python
obs.on_change(lambda: print("Dict changed"))
```

## Granular Callbacks

Subscribe to specific mutation types with typed callbacks.

```python
obs.on_insert(lambda key, value: ...)        # New key added
obs.on_replace(lambda key, old, new: ...)    # Existing key updated
obs.on_remove(lambda key, value: ...)        # Key removed
obs.on_clear(lambda items: ...)              # Dict cleared
```

## Callback Behavior Notes

- `on_insert` fires for new keys only, NOT when updating existing keys
- `on_replace` fires when updating existing keys only
- `replace()` fires `on_clear` then `on_change`, but NOT `on_insert` per item
- Both granular callbacks and `on_change` fire together when applicable
- Duplicate callbacks are ignored (same function added twice only fires once)

## Dirty Tracking

Track whether the dict has been modified since last reset.

```python
obs.is_dirty           # Observable[bool] - reactive dirty state
bool(obs.is_dirty)     # Check if dirty
obs.reset_dirty()      # Mark as clean
```

## Reactive Dirty State

The `is_dirty` property is itself an Observable, allowing reactive subscriptions.

```python
obs.is_dirty.on_change(lambda dirty: print(f"Dirty: {dirty}"))
```

## Auto-Revert to Clean

If modifications result in state identical to clean state, dirty becomes false automatically.

```python
obs = ObservableDict[str, int]({"a": 1})
obs.reset_dirty()
obs["b"] = 2          # Now dirty
del obs["b"]          # Back to {"a": 1}, now clean
```
