# Observant Library Reference

The Observant library provides reactive primitives that power QtPie's data binding system. While most users interact with these through `Variable[T]` and `Widget[T]`, the underlying primitives are available for advanced use cases.

## Observable[T]

A single reactive value with change callbacks.

```python
from observant import Observable

obs = Observable[int](42)

# Get/set value
value = obs.get()  # 42
obs.set(100)

# Subscribe to changes
obs.on_change(lambda v: print(f"Changed to: {v}"))
obs.set(200)  # Prints: "Changed to: 200"
```

### Key Properties

- `get()` - Get current value
- `set(value)` - Set new value (triggers callbacks)
- `on_change(callback)` - Register change listener
- Duplicate callbacks are ignored

## ObservableList[T]

A reactive list with granular change callbacks.

```python
from observant import ObservableList

obs = ObservableList[int]([1, 2, 3])

# Standard list operations
obs.append(4)
obs.extend([5, 6])
obs.insert(0, 0)
obs.remove(3)
item = obs.pop()
del obs[0]
obs[0] = 100

# Conversion
items = obs.to_list()
```

### Change Callbacks

```python
# Generic - any mutation
obs.on_change(lambda: print("List changed"))

# Granular - specific operations
obs.on_insert(lambda idx, item: print(f"Insert: {item} at {idx}"))
obs.on_remove(lambda idx, item: print(f"Remove: {item} from {idx}"))
obs.on_replace(lambda idx, old, new: print(f"Replace: {old} -> {new}"))
obs.on_clear(lambda items: print(f"Cleared: {items}"))
```

### Dirty Tracking

```python
obs = ObservableList[int]([1, 2])
obs.reset_dirty()

obs.append(3)
print(obs.is_dirty.get())  # True

obs.pop()  # Back to [1, 2]
print(obs.is_dirty.get())  # False (reverted to clean state)

# Subscribe to dirty changes
obs.is_dirty.on_change(lambda d: print(f"Dirty: {d}"))
```

## ObservableDict[K, V]

A reactive dictionary with granular change callbacks.

```python
from observant import ObservableDict

obs = ObservableDict[str, int]({"a": 1, "b": 2})

# Standard dict operations
obs["c"] = 3
del obs["a"]
obs.update({"d": 4})
obs.setdefault("e", 5)
obs.pop("b")
obs.clear()

# Conversion
data = obs.to_dict()
```

### Change Callbacks

```python
# Generic
obs.on_change(lambda: print("Dict changed"))

# Granular
obs.on_insert(lambda k, v: print(f"Insert: {k}={v}"))  # New keys only
obs.on_replace(lambda k, old, new: print(f"Update: {k}: {old}->{new}"))  # Existing keys
obs.on_remove(lambda k, v: print(f"Remove: {k}"))
obs.on_clear(lambda items: print(f"Cleared: {items}"))
```

### Dirty Tracking

Same pattern as ObservableList:

```python
obs = ObservableDict[str, int]({"a": 1})
obs.reset_dirty()

obs["b"] = 2
print(obs.is_dirty.get())  # True

del obs["b"]
print(obs.is_dirty.get())  # False (reverted)
```

## ObservableSet[T]

A reactive set with granular change callbacks.

```python
from observant import ObservableSet

obs = ObservableSet[int]({1, 2, 3})

# Standard set operations
obs.add(4)
obs.remove(1)
obs.discard(99)  # No error if missing
obs.update({5, 6})
obs.clear()

# Set algebra (non-mutating)
obs.union({7, 8})
obs.intersection({2, 3})
obs.difference({1})

# In-place operations
obs.intersection_update({2, 3})
obs.difference_update({1})

# Conversion
data = obs.to_set()
```

### Change Callbacks

```python
obs.on_change(lambda: print("Set changed"))
obs.on_add(lambda item: print(f"Added: {item}"))
obs.on_remove(lambda item: print(f"Removed: {item}"))
obs.on_clear(lambda items: print(f"Cleared: {items}"))
```

### Validation

```python
obs = ObservableSet[int]()
obs.add_validator("not_empty", lambda s: None if len(s) > 0 else "Set must not be empty")

print(obs.is_valid.get())  # False
obs.add(1)
print(obs.is_valid.get())  # True

# Subscribe to validation changes
obs.is_valid.on_change(lambda v: print(f"Valid: {v}"))
```

## ObservableProxy[T]

Wraps any object, making all fields reactive.

```python
from dataclasses import dataclass
from observant import ObservableProxy

@dataclass
class Person:
    name: str
    age: int

person = Person("Alice", 30)
proxy = ObservableProxy(person)

# Field access returns Observable
name_obs = proxy.name
print(name_obs.get())  # "Alice"

# Direct assignment works too
proxy.name = "Bob"
print(person.name)  # "Bob" (original updated)
```

### Change Callbacks

```python
# Proxy-level: any field change
proxy.on_change(lambda: print("Person changed"))

# Field-level: specific field
proxy.name.on_change(lambda v: print(f"Name: {v}"))
```

### Dirty Tracking

```python
proxy = ObservableProxy(person)

print(proxy.is_dirty.get())  # False
proxy.name = "Charlie"
print(proxy.is_dirty.get())  # True
print(proxy.dirty_fields)    # ["name"]

proxy.reset_dirty()
print(proxy.is_dirty.get())  # False
```

### Nested Objects

Nested objects are automatically wrapped:

```python
@dataclass
class Company:
    name: str
    ceo: Person

company = Company("Acme", Person("Alice", 30))
proxy = ObservableProxy(company)

# Access nested proxy
proxy.ceo.name = "Bob"  # Works!
print(company.ceo.name)  # "Bob"

# Callbacks propagate up
proxy.on_change(lambda: print("Company changed"))
proxy.ceo.age = 31  # Triggers parent callback
```

### List/Dict Fields

Collections are wrapped automatically:

```python
@dataclass
class Team:
    name: str
    members: list[str]
    metadata: dict[str, int]

team = Team("Dev", ["Alice"], {"size": 1})
proxy = ObservableProxy(team)

# List operations
proxy.members.append("Bob")  # Marks dirty

# Dict operations
proxy.metadata["priority"] = 5  # Marks dirty
```

### Disable Dirty Tracking

For performance, disable dirty tracking:

```python
proxy = ObservableProxy(person, dirty_tracking=False)
proxy.name = "Bob"  # Works, but no dirty tracking
# proxy.is_dirty  # Raises RuntimeError
```

## Validation

Observable collections support named validators:

```python
obs = ObservableSet[int]()

# Add validator (returns None for valid, error message for invalid)
obs.add_validator("min_size", lambda s: None if len(s) >= 2 else "Need at least 2 items")

# Check validity
print(obs.is_valid.get())  # False
print(obs.validation_errors.get())  # {"min_size": ["Need at least 2 items"]}

# Subscribe to validity changes
obs.is_valid.on_change(lambda valid: print(f"Valid: {valid}"))

# Remove validator
obs.remove_validator("min_size")
```

## When to Use Directly

Most users should use QtPie's `Variable[T]` and `Widget[T]` instead. Use Observant directly for:

- Custom reactive data structures
- Non-widget reactive state
- Building custom QtPie extensions
- Testing reactive logic in isolation

## See Also

- [Variables](../state/variables.md) - QtPie's Variable abstraction
- [Records](../data/records.md) - Widget[T] with ObservableProxy
- [Dirty Tracking](../data/dirty-tracking.md) - User-facing dirty tracking
- [Validation](../data/validation.md) - User-facing validation
