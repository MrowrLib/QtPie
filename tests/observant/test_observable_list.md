# ObservableList Usage Patterns

Documentation of `ObservableList` usage patterns extracted from test cases.

## Creating an ObservableList

ObservableList is a generic typed container. Create empty or with initial items.

```python
from observant import ObservableList

obs = ObservableList[int]()              # Empty list
obs = ObservableList[int]([1, 2, 3])     # With initial items
```

## Standard List Operations

ObservableList supports all standard Python list operations.

```python
obs.append(42)           # Add item at end
obs.extend([2, 3])       # Add multiple items
obs.insert(1, 2)         # Insert at index
obs.remove(2)            # Remove by value
item = obs.pop()         # Remove and return last
item = obs.pop(0)        # Remove and return at index
obs.clear()              # Remove all items
```

## Index-Based Access

Supports standard indexing, containment checks, and iteration.

```python
obs[1] = 99              # Set item at index
del obs[1]               # Delete item at index
value = obs[0]           # Get item at index
2 in obs                 # Check containment
list(obs)                # Iterate to regular list
obs.index(2)             # Find index of value
obs.count(2)             # Count occurrences
```

## Converting to List

Use `to_list()` to get a plain Python list copy.

```python
obs = ObservableList[int]([1, 2, 3])
plain_list = obs.to_list()  # Returns [1, 2, 3]
```

## Atomic Replace

Replace all items in one operation. Does NOT fire individual insert callbacks.

```python
obs = ObservableList[int]([1, 2, 3])
obs.replace([4, 5])      # Now contains [4, 5]
```

## Generic Change Callback

Subscribe to any mutation with `on_change()`. Callback receives no arguments.

```python
obs = ObservableList[int]()
obs.on_change(lambda: print("list changed"))
obs.append(1)  # Prints: "list changed"
```

## Granular Insert Callback

Get notified of insertions with index and item.

```python
obs = ObservableList[str](["a", "b"])
obs.on_insert(lambda idx, item: print(f"inserted {item} at {idx}"))
obs.append("c")   # Prints: "inserted c at 2"
obs.insert(1, "x")  # Prints: "inserted x at 1"
```

## Granular Remove Callback

Get notified of removals with index and item.

```python
obs = ObservableList[str](["a", "b", "c"])
obs.on_remove(lambda idx, item: print(f"removed {item} from {idx}"))
obs.remove("b")   # Prints: "removed b from 1"
obs.pop()         # Prints: "removed c from 2"
del obs[0]        # Prints: "removed a from 0"
```

## Granular Replace Callback

Get notified when item is replaced at an index.

```python
obs = ObservableList[str](["a", "b", "c"])
obs.on_replace(lambda idx, old, new: print(f"{old} -> {new} at {idx}"))
obs[1] = "B"      # Prints: "b -> B at 1"
```

## Clear Callback

Get notified when list is cleared, receives all removed items.

```python
obs = ObservableList[str](["a", "b", "c"])
obs.on_clear(lambda items: print(f"cleared: {items}"))
obs.clear()       # Prints: "cleared: ['a', 'b', 'c']"
```

## Replace Fires Clear Callback

The `replace()` method fires the clear callback with old items, but does NOT fire insert callbacks.

```python
obs = ObservableList[int]([1, 2])
obs.on_clear(lambda items: print(f"old items: {items}"))
obs.on_insert(lambda idx, item: print("insert"))  # Never fires!
obs.replace([3, 4, 5])  # Prints: "old items: [1, 2]"
```

## Multiple Callbacks

Multiple callbacks can be registered; all fire in order.

```python
obs = ObservableList[int]()
obs.on_change(lambda: print("first"))
obs.on_change(lambda: print("second"))
obs.append(42)    # Prints: "first" then "second"
```

## Duplicate Callback Prevention

Same callback function is only registered once.

```python
def my_callback():
    print("called")

obs.on_change(my_callback)
obs.on_change(my_callback)  # Ignored - already registered
obs.append(1)  # Prints "called" only once
```

## Dirty Tracking

Lists track whether they've been modified since creation or last reset.

```python
obs = ObservableList[int]([1, 2, 3])
bool(obs.is_dirty)        # False - newly created

obs.append(4)
bool(obs.is_dirty)        # True - modified

obs.reset_dirty()
bool(obs.is_dirty)        # False - reset to clean
```

## Smart Dirty Detection

List becomes clean if reverted to its clean state.

```python
obs = ObservableList[int]([1, 2])
obs.reset_dirty()

obs.append(3)             # Now dirty
obs.pop()                 # Back to [1, 2]
bool(obs.is_dirty)        # False - matches clean state
```

## Observable Dirty State

The `is_dirty` property is itself observable.

```python
obs = ObservableList[int]()
obs.is_dirty.on_change(lambda dirty: print(f"dirty={dirty}"))

obs.append(1)       # Prints: "dirty=True"
obs.reset_dirty()   # Prints: "dirty=False"
```

## Combining Granular and Generic Callbacks

Both granular and generic callbacks fire on mutations.

```python
obs = ObservableList[str]()
obs.on_insert(lambda idx, item: print(f"insert:{item}"))
obs.on_change(lambda: print("change"))
obs.append("a")     # Prints: "insert:a" then "change"
```
