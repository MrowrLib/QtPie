# ObservableSet Usage Patterns

`ObservableSet[T]` is a reactive set collection that provides change notifications, dirty tracking, and validation.

## Creating an ObservableSet

```python
from observant import ObservableSet

# Empty set with type parameter
obs = ObservableSet[int]()

# Initialize with items
obs = ObservableSet[int]({1, 2, 3})
```

## Basic Set Operations

Standard Python set operations are supported:

```python
obs.add(42)                    # Add single item
obs.remove(2)                  # Remove item (raises if missing)
obs.discard(99)                # Remove item (no error if missing)
item = obs.pop()               # Remove and return arbitrary item
obs.clear()                    # Remove all items
obs.update({2, 3})             # Add multiple items
```

## Atomic Replace

Replace all items atomically (fires `on_clear` but NOT individual `on_add` callbacks):

```python
obs = ObservableSet[int]({1, 2, 3})
obs.replace({4, 5})  # Now contains {4, 5}
```

## Set Algebra Operations

Mutating operations (modify in place):

```python
obs.intersection_update({2, 3, 4})        # Keep only common items
obs.difference_update({2, 4})              # Remove items in other
obs.symmetric_difference_update({2, 3, 4}) # Keep items in either but not both
```

Non-mutating operations (return regular `set`):

```python
result = obs.union({3, 4})               # Union (original unchanged)
result = obs.intersection({2, 3, 4})     # Intersection
result = obs.difference({2, 4})          # Difference
result = obs.symmetric_difference({2, 3, 4})
```

## Membership and Iteration

```python
if 2 in obs:
    pass

for item in obs:
    print(item)

regular_set = obs.to_set()
```

## Set Relationships

```python
obs.issubset({1, 2, 3})      # True if all items in other
obs.issuperset({1, 2})       # True if contains all items from other
obs.isdisjoint({3, 4})       # True if no common items
```

## Change Callbacks

### Generic on_change

Fires on any modification:

```python
obs = ObservableSet[int]()
obs.on_change(lambda: print("changed"))
obs.add(1)  # Prints "changed"
```

Callbacks do NOT fire for no-ops (adding duplicate, discarding missing):

```python
obs = ObservableSet[int]({1})
obs.on_change(lambda: changes.append("x"))
obs.add(1)  # No callback - item already present
```

### Granular Callbacks

```python
obs.on_add(lambda item: print(f"added: {item}"))
obs.on_remove(lambda item: print(f"removed: {item}"))
obs.on_clear(lambda items: print(f"cleared: {items}"))
```

Both granular and generic callbacks fire together:

```python
obs.on_add(lambda item: events.append(f"add:{item}"))
obs.on_change(lambda: events.append("change"))
obs.add("a")  # events = ["add:a", "change"]
```

### Callback Deduplication

Same callback function is not added twice:

```python
def cb():
    results.append(1)

obs.on_change(cb)
obs.on_change(cb)  # Ignored - already registered
obs.add(42)        # cb fires once
```

## Dirty Tracking

Track whether set has changed from its "clean" state:

```python
obs = ObservableSet[int]({1, 2, 3})
bool(obs.is_dirty)  # False - newly created

obs.add(4)
bool(obs.is_dirty)  # True

obs.reset_dirty()   # Mark current state as clean
bool(obs.is_dirty)  # False
```

Dirty state is smart - reverting to original state clears dirty:

```python
obs = ObservableSet[int]({1, 2})
obs.reset_dirty()
obs.add(3)          # is_dirty = True
obs.remove(3)       # is_dirty = False (back to {1, 2})
```

The `is_dirty` property is itself observable:

```python
obs.is_dirty.on_change(lambda d: print(f"dirty: {d}"))
```

## Validation

Add validators that check the current set state:

```python
obs = ObservableSet[int]()
obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")

bool(obs.is_valid)  # False - empty set fails validator
obs.add(1)
bool(obs.is_valid)  # True - validator now passes
```

Access validation errors:

```python
errors = obs.validation_errors.get()      # {"not_empty": ["Set must not be empty"]}
messages = obs.validation_error_messages.get()  # ["Set must not be empty"]
```

The `is_valid` property is observable:

```python
obs.is_valid.on_change(lambda v: print(f"valid: {v}"))
```

## Equality

ObservableSet compares equal to both other ObservableSets and regular sets:

```python
obs1 = ObservableSet[int]({1, 2, 3})
obs2 = ObservableSet[int]({1, 2, 3})
obs1 == obs2          # True
obs1 == {1, 2, 3}     # True
```
