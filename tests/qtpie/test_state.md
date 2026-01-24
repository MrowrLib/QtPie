# QtPie State System - Usage Patterns

This document extracts usage patterns from the State test file, demonstrating how to use QtPie's `State` class for reactive state management without Qt widget dependencies.

## What is State?

`State` is a QtPie primitive for reactive state management that works independently of Qt widgets. It provides the same `Variable` system as `Widget` but without UI dependencies - useful for business logic, view models, and shared application state.

---

## Basic State Definition

Use the `@state` decorator with the `State` base class. Define reactive fields using `Variable[T]` with `new()`.

```python
from qtpie import State, Variable, new, state

@state
class MyState(State):
    count: Variable[int] = new(0)
    name: Variable[str] = new("default")
    active: Variable[bool] = new(False)
```

Usage:
```python
s = MyState()
s.count.value = 5
print(s.name.value)  # "default"
```

---

## Reactive Variable Subscriptions

Variables are reactive - subscribe to changes via the underlying observable.

```python
@state
class MyState(State):
    count: Variable[int] = new(0)

s = MyState()
s.count.observable.on_change(lambda v: print(f"Count is now {v}"))
s.count.value = 1  # Prints: "Count is now 1"
```

---

## Constructor Initialization

Pass initial values via constructor kwargs. Supports partial overrides.

```python
@state
class MyState(State):
    count: Variable[int] = new(0)
    name: Variable[str] = new("default")

# Override only count, name uses default
s = MyState(count=42)
```

---

## Observable/Variable Injection

Pass an `Observable` or `Variable` to share reactive state across instances.

```python
from observant import Observable

@state
class MyState(State):
    count: Variable[int] = new(0)

external = Observable(42)
s = MyState(count=external)

# Bidirectional sync
external.set(100)
assert s.count.value == 100
```

Share Variable between State instances:
```python
s1 = MyState()
s2 = MyState(count=s1.count)
# s1 and s2 share the same reactive value
```

---

## Bare Variables (Required Fields)

Omit `= new()` to create required fields that must be provided at construction.

```python
@state
class MyState(State):
    kind: Variable[str]  # Bare - required, no default
    count: Variable[int] = new(0)  # Has default

s = MyState(kind="Request")  # kind is required
```

Bare variables can receive static values, Observables, or other Variables.

---

## The `__setup__` Lifecycle Hook

Called after `__init__` and after constructor kwargs are applied. Use for derived state initialization.

```python
@state
class MyState(State):
    count: Variable[int] = new(0)
    doubled: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.doubled.value = self.count.value * 2

s = MyState(count=5)
assert s.doubled.value == 10
```

---

## onChange Callback

React to value changes with `onChange` parameter in `new()`.

```python
@state
class MyState(State):
    count: Variable[int] = new(0, onChange="_on_count_changed")

    def _on_count_changed(self, value: int) -> None:
        print(f"Count changed to {value}")
```

Lambda variant:
```python
count: Variable[int] = new(0, onChange=lambda v: print(v))
```

---

## List Variables

`Variable[list[T]]` provides reactive list operations.

```python
@state
class MyState(State):
    items: Variable[list[str]] = new(["a", "b", "c"])

s = MyState()
s.items.append("d")
s.items.remove("a")
s.items.insert(0, "first")
s.items.clear()
```

List-specific callbacks:
```python
@state
class MyState(State):
    items: Variable[list[str]] = new(
        [],
        onInsert="_on_insert",
        onRemove="_on_remove"
    )

    def _on_insert(self, item: str, index: int) -> None:
        print(f"Inserted {item} at {index}")

    def _on_remove(self, item: str) -> None:
        print(f"Removed {item}")
```

---

## Dict Variables

`Variable[dict[K, V]]` provides reactive dict operations.

```python
@state
class MyState(State):
    config: Variable[dict[str, int]] = new({"theme": 1})

s = MyState()
s.config["new_key"] = 42
del s.config["theme"]
```

Dict-specific callbacks:
```python
@state
class MyState(State):
    config: Variable[dict[str, int]] = new(
        {},
        onSet="_on_set",
        onRemove="_on_remove"
    )

    def _on_set(self, key: str, value: int) -> None:
        print(f"Set {key}={value}")

    def _on_remove(self, key: str, value: int) -> None:
        print(f"Removed {key}")
```

---

## Set Variables

`Variable[set[T]]` provides reactive set operations.

```python
@state
class MyState(State):
    tags: Variable[set[str]] = new(set(), onAdd="_on_add", onRemove="_on_remove")

    def _on_add(self, item: str) -> None:
        print(f"Added tag: {item}")

s = MyState()
s.tags.add("python")
s.tags.discard("python")
```

---

## State Dependency Injection

Inject one State into another via bare Variable.

```python
@state
class ConfigState(State):
    theme: Variable[str] = new("dark")

@state
class AppState(State):
    config: Variable[ConfigState]  # Injected dependency

config = ConfigState()
app = AppState(config=config)

# Access injected state
print(app.config.value.theme.value)  # "dark"
```

---

## Parent-Child State Hierarchy

Child States created via `new()` have `state_parent` set automatically. Bare Variables in children resolve from parent.

```python
@state
class ChildState(State):
    count: Variable[int]  # Bare - resolves from parent

@state
class ParentState(State):
    count: Variable[int] = new(42)
    child: Variable[ChildState] = new()

parent = ParentState()
child = parent.child.value

# Child's bare Variable shares parent's Variable
assert child.count.value == 42
assert child.state_parent is parent
```

---

## Events on State

Use `Event` for void signals, `Event[T]` for typed signals.

```python
from qtpie import Event

@state
class MyState(State):
    on_save: Event = new(on="_on_save")
    on_value: Event[int] = new(on="_on_value")

    def _on_save(self) -> None:
        print("Save triggered")

    def _on_value(self, x: int) -> None:
        print(f"Value: {x}")

s = MyState()
s.on_save.emit()
s.on_value.emit(42)
```

Lambda handlers:
```python
on_save: Event = new(on=lambda: print("Saved!"))
on_value: Event[int] = new(on=lambda x: print(x))
```

Tuple args for multiple parameters:
```python
on_data: Event[tuple[int, str]] = new(on="_on_data")

def _on_data(self, num: int, text: str) -> None:
    print(f"{num}: {text}")
```

---

## Decorator-Level Event Wiring

Wire events via decorator kwargs as alternative to `new(on=...)`.

```python
@state(on_save="_handle_save")
class MyState(State):
    on_save: Event

    def _handle_save(self) -> None:
        print("Saved!")
```

---

## Summary of `new()` Parameters for State

| Parameter | Description |
|-----------|-------------|
| `new(value)` | Initial value for Variable |
| `onChange="method"` | Method called on any value change |
| `onInsert="method"` | List: called on item insert |
| `onRemove="method"` | List/Dict/Set: called on item remove |
| `onAdd="method"` | Set: called on item add |
| `onSet="method"` | Dict: called on key set |
| `on="method"` | Event: handler to connect |

Callbacks can be:
- String method name: `"_on_change"`
- Lambda: `lambda v: print(v)`
- Expression string: `"{_log()}"`
