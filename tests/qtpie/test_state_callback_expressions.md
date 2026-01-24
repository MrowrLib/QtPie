# State Callback Expressions

This document describes the callback expression DSL used in QtPie's `State` class for reactive event handling on `Variable` fields.

## Overview

State callback expressions allow you to declaratively wire up reactions to Variable changes using a `{expression}` syntax. These expressions are passed as `onChange`, `onInsert`, `onRemove`, `onAdd`, or `onSet` parameters to `new()`.

---

## onChange - React to Value Changes

Triggers when a Variable's value changes.

### Call a method

```python
value: Variable[str] = new("", onChange="{_on_changed()}")
```

### Pass the new value to a method

Use `#args` to pass the changed value:

```python
value: Variable[str] = new("", onChange="{_on_changed(#args)}")

def _on_changed(self, val: str) -> None:
    print(f"New value: {val}")
```

### Emit an Event

```python
value: Variable[str] = new("", onChange="{on_save()}")
on_save: Event
```

### Emit an Event with the changed value

```python
value: Variable[str] = new("", onChange="{on_data(#args)}")
on_data: Event[str]
```

---

## onInsert - React to List Insertions

Triggers when items are added to a `Variable[list[T]]`.

### Call a method

```python
items: Variable[list[str]] = new([], onInsert="{_on_add()}")
```

### Receive (item, index)

```python
items: Variable[list[str]] = new([], onInsert="{_on_add(#args)}")

def _on_add(self, item: str, index: int) -> None:
    print(f"Added {item} at index {index}")
```

---

## onRemove - React to Removals

Triggers when items are removed from a list or set.

### List removal (receives item, index)

```python
items: Variable[list[str]] = new(["a", "b"], onRemove="{_on_removed(#args)}")

def _on_removed(self, item: str, index: int) -> None:
    print(f"Removed {item} from index {index}")
```

### Set removal (receives item only)

```python
items: Variable[set[str]] = new({"a", "b"}, onRemove="{_on_removed(#args)}")

def _on_removed(self, item: str) -> None:
    print(f"Removed {item}")
```

---

## onAdd - React to Set Additions

Triggers when items are added to a `Variable[set[T]]`.

```python
items: Variable[set[str]] = new(set(), onAdd="{_on_added(#args)}")

def _on_added(self, item: str) -> None:
    print(f"Added {item}")
```

---

## onSet - React to Dict Key Assignment

Triggers when a key is set in a `Variable[dict[K, V]]`.

```python
items: Variable[dict[str, int]] = new({}, onSet="{_on_set(#args)}")

def _on_set(self, key: str, value: int) -> None:
    print(f"Set {key} = {value}")
```

---

## Special Placeholders

| Placeholder | Description |
|-------------|-------------|
| `#args` | The callback arguments (value, item, key/value, etc.) |
| `#self` | Explicit reference to the State instance |

### Using #self explicitly

```python
value: Variable[str] = new("", onChange="{#self.process()}")
```

---

## Complex Expressions

### Literals and multiple arguments

```python
value: Variable[str] = new("", onChange="{_on_changed('literal', 123)}")
```

### Reference other Variables

```python
count: Variable[int] = new(42)
trigger: Variable[str] = new("", onChange="{_on_changed(count)}")
```

### Math expressions

```python
count: Variable[int] = new(10)
trigger: Variable[str] = new("", onChange="{_on_changed(count * 2)}")
```

---

## Assignment Expressions

Expressions can directly assign to Variables.

### Simple assignment

```python
count: Variable[int] = new(0)
trigger: Variable[str] = new("", onChange="{count = 42}")
```

### Compound assignment operators

```python
count: Variable[int] = new(10)
trigger: Variable[str] = new("", onChange="{count += 1}")
```

Supported operators: `+=`, `-=`, `*=`, `/=`, `//=`, `%=`, `**=`, `|=`, `&=`

### Assign computed value

```python
a: Variable[int] = new(10)
b: Variable[int] = new(20)
result: Variable[int] = new(0)
trigger: Variable[str] = new("", onChange="{result = a + b}")
```

### Assign method return value

```python
result: Variable[int] = new(0)
trigger: Variable[str] = new("", onChange="{result = _compute()}")

def _compute(self) -> int:
    return 999
```

---

## Parent-Child Event Propagation

Child states can call methods or emit events on parent states.

### Child emits parent's Event

```python
@state
class ChildState(State):
    value: Variable[str] = new("", onChange="{on_parent_save()}")

@state
class ParentState(State):
    on_parent_save: Event
    children: Variable[list[Any]] = new([])

# When child.value changes, parent.on_parent_save is emitted
```

### Child calls parent's method

```python
@state
class ChildState(State):
    value: Variable[str] = new("", onChange="{_parent_handler()}")

@state
class ParentState(State):
    children: Variable[list[Any]] = new([])

    def _parent_handler(self) -> None:
        print("parent_called")
```

---

## Naming Convention

Variables with underscore prefix (e.g., `_count`) can be referenced without the underscore in expressions:

```python
_count: Variable[int] = new(0)
trigger: Variable[str] = new("", onChange="{count += 1}")  # finds _count
```
