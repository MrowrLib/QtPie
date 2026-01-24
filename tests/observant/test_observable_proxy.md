# ObservableProxy Usage Patterns

This document describes the usage patterns for `ObservableProxy` in the Observant library.

## Overview

`ObservableProxy` wraps any Python object and makes its fields reactive. Field access returns `Observable` instances that can be subscribed to for change notifications.

## Basic Usage

### Creating a Proxy

Wrap any object (typically a dataclass) with `ObservableProxy`:

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)
```

### Accessing Fields

Field access returns an `Observable`. Use `.get()` to read values:

```python
name_obs = proxy.name  # Returns Observable[str]
assert proxy.name.get() == "Alice"
```

### Setting Field Values

Two ways to set values - via Observable or direct assignment:

```python
proxy.name.set("Bob")   # Via Observable
proxy.name = "Bob"      # Direct assignment (also reactive)
```

### Unwrapping

Get the original object back with `unwrap()`:

```python
original = proxy.unwrap()  # Returns the original Person
```

## Change Callbacks

### Proxy-Level Callbacks

Subscribe to any change on the proxied object:

```python
proxy.on_change(lambda: print("something changed"))
```

### Field-Level Callbacks

Subscribe to changes on specific fields:

```python
proxy.name.on_change(lambda v: print(f"name is now {v}"))
```

### Multiple Callbacks

Register multiple callbacks - all fire on change:

```python
proxy.on_change(lambda: results.append(1))
proxy.on_change(lambda: results.append(2))
```

## Dirty Tracking

Track whether fields have changed from their initial state.

### Checking Dirty State

```python
bool(proxy.is_dirty)  # True if any field changed
proxy.dirty_fields    # List of changed field names
```

### Resetting Dirty State

```python
proxy.reset_dirty()  # Marks all fields as clean
```

### Subscribing to Dirty Changes

`is_dirty` is itself an Observable:

```python
proxy.is_dirty.on_change(lambda d: print(f"dirty={d}"))
```

### Disabling Dirty Tracking

```python
proxy = ObservableProxy(person, dirty_tracking=False)
```

## Nested Objects

Nested objects are automatically wrapped as proxies.

### Accessing Nested Fields

```python
dog = Dog("Buddy", 5, Breed("Labrador", "Canada"))
proxy = ObservableProxy(dog)

proxy.breed.name.get()  # "Labrador"
proxy.breed.name.set("Golden Retriever")
```

### Nested Change Propagation

Changes to nested objects fire parent callbacks:

```python
proxy.on_change(lambda: print("dog changed"))
proxy.breed.name.set("Golden Retriever")  # Fires parent callback
```

### Nested Dirty Propagation

Nested changes mark parent as dirty:

```python
proxy.breed.name.set("Golden Retriever")
bool(proxy.is_dirty)        # True
bool(proxy.breed.is_dirty)  # True
proxy.dirty_fields          # Contains "breed"
```

## List Fields

List fields are automatically converted to `ObservableList`.

### Accessing and Modifying Lists

```python
proxy.tags[0]              # Access by index
len(proxy.tags)            # Get length
proxy.tags.append("new")   # Modify list
proxy.tags.to_list()       # Convert to regular list
```

### List Change Callbacks

List modifications fire proxy callbacks and mark dirty:

```python
proxy.on_change(lambda: print("changed"))
proxy.tags.append("moderator")  # Fires callback, marks dirty
```

## Dict Fields

Dict fields are automatically converted to `ObservableDict`.

### Accessing and Modifying Dicts

```python
proxy.metadata["age"]          # Access by key
len(proxy.metadata)            # Get length
proxy.metadata["score"] = 100  # Set value
proxy.metadata.to_dict()       # Convert to regular dict
```

### Dict Change Callbacks

Dict modifications fire proxy callbacks and mark dirty:

```python
proxy.on_change(lambda: print("changed"))
proxy.metadata["score"] = 100  # Fires callback, marks dirty
```

## Method Passthrough

Methods on proxied objects are callable directly (not wrapped):

```python
class Service:
    def add_item(self, item: str) -> str:
        return item

proxy = ObservableProxy(service)
result = proxy.add_item("test")  # Calls method directly
```

## Pre-existing Observable Fields

If the wrapped object already has `Observable`, `ObservableList`, or `ObservableDict` fields, they are returned directly (not re-wrapped):

```python
class ServiceWithObservables:
    def __init__(self):
        self.count: Observable[int] = Observable(0)
        self.items: ObservableList[str] = ObservableList([])

service = ServiceWithObservables()
proxy = ObservableProxy(service)

proxy.count         # Returns the same Observable instance
proxy.items         # Returns the same ObservableList instance
```

You can subscribe to these observables through the proxy:

```python
proxy.count.on_change(lambda v: print(f"count={v}"))
service.count.set(5)  # Subscriber fires
```

## Sibling Proxies

Multiple proxies wrapping the same object stay synchronized:

```python
proxy1 = ObservableProxy(person)
proxy2 = ObservableProxy(person)

proxy2.on_change(lambda: print("proxy2 notified"))
proxy1.name.set("Bob")  # proxy2's callback fires
```

Field observables and callbacks are synchronized:

```python
proxy2.name.on_change(lambda v: print(f"name={v}"))
proxy1.name.set("Bob")  # proxy2's field callback fires
```

## Type Signature

```python
ObservableProxy[T](
    target: T,
    dirty_tracking: bool = True
)
```

## Key Methods

| Method | Description |
|--------|-------------|
| `unwrap()` | Returns the original wrapped object |
| `on_change(callback)` | Subscribe to any change on the proxy |
| `is_dirty` | Observable[bool] for dirty state |
| `dirty_fields` | List of field names that have changed |
| `reset_dirty()` | Mark all fields as clean |
