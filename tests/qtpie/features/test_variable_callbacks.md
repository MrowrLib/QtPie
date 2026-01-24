# Variable Callbacks in QtPie

Variable callbacks provide reactive hooks that fire when Variable values change. These work across all QtPie class types: Widget, Window, Dialog, Menu, App, WidgetBase, and State.

## onChange - Scalar Value Changes

The `onChange` callback fires whenever a Variable's value changes.

### Basic onChange (No Parameters)

Access the current value via `self.variable_name.value`:

```python
count: Variable[int] = new(0, onChange="_on_changed")

def _on_changed(self) -> None:
    calls.append(self.count.value)
```

### onChange with Value Parameter

Receive the new value directly as a parameter:

```python
name: Variable[str] = new("", onChange="_on_changed")

def _on_changed(self, value: str) -> None:
    calls.append(value)
```

### onChange with Lambda

Use an inline lambda for simple handlers:

```python
count: Variable[int] = new(0, onChange=lambda v: calls.append(v))
```

## List Callbacks - onInsert and onRemove

List Variables support granular insert/remove callbacks.

### onInsert

Fires when items are appended to the list. Receives the item and its index:

```python
items: Variable[list[str]] = new([], onInsert="_on_insert")

def _on_insert(self, item: str, index: int) -> None:
    inserts.append(item)
```

### onRemove (List)

Fires when items are removed. Receives the item and its former index:

```python
items: Variable[list[str]] = new(["a", "b"], onRemove="_on_remove")

def _on_remove(self, item: str, index: int) -> None:
    removes.append(item)
```

### Combined List Callbacks

Use both callbacks together:

```python
items: Variable[list[str]] = new([], onInsert="_on_insert", onRemove="_on_remove")
```

### Lambda Variant

```python
items: Variable[list[str]] = new([], onInsert=lambda item, i: inserts.append(item))
```

## Set Callbacks - onAdd and onRemove

Set Variables use `onAdd` instead of `onInsert`.

### onAdd

Fires when items are added to the set:

```python
tags: Variable[set[str]] = new(set(), onAdd="_on_add")

def _on_add(self, item: str) -> None:
    adds.append(item)
```

### onRemove (Set)

Fires when items are discarded from the set:

```python
tags: Variable[set[str]] = new({"a", "b"}, onRemove="_on_remove")

def _on_remove(self, item: str) -> None:
    removes.append(item)
```

## Dict Callbacks - onSet and onRemove

Dict Variables use `onSet` for additions/updates.

### onSet

Fires when key-value pairs are set. Receives key and value:

```python
config: Variable[dict[str, int]] = new({}, onSet="_on_set")

def _on_set(self, key: str, value: int) -> None:
    sets.append(f"{key}={value}")
```

### onRemove (Dict)

Fires when entries are deleted. Receives key and value:

```python
config: Variable[dict[str, int]] = new({"a": 1}, onRemove="_on_remove")

def _on_remove(self, key: str, value: int) -> None:
    removes.append(f"{key}={value}")
```

## Integration Patterns

### Updating UI from Callbacks

Callbacks can modify widgets in response to Variable changes:

```python
count: Variable[int] = new(0, onChange="_update_label")
label: QLabel = new("Count: 0")

def _update_label(self) -> None:
    self.label.setText(f"Count: {self.count.value}")
```

### Callback Chains

Callbacks can trigger changes to other Variables, creating reactive chains:

```python
input_value: Variable[str] = new("", onChange="_on_input")
output_value: Variable[str] = new("", onChange="_on_output")

def _on_input(self, value: str) -> None:
    self.output_value.value = value.upper()  # Triggers _on_output
```

## Callback Reference Summary

| Variable Type | Available Callbacks | Handler Signature |
|---------------|---------------------|-------------------|
| Scalar (`T`) | `onChange` | `(self) -> None` or `(self, value: T) -> None` |
| `list[T]` | `onInsert` | `(self, item: T, index: int) -> None` |
| `list[T]` | `onRemove` | `(self, item: T, index: int) -> None` |
| `set[T]` | `onAdd` | `(self, item: T) -> None` |
| `set[T]` | `onRemove` | `(self, item: T) -> None` |
| `dict[K, V]` | `onSet` | `(self, key: K, value: V) -> None` |
| `dict[K, V]` | `onRemove` | `(self, key: K, value: V) -> None` |

All callbacks accept either a method name string (e.g., `"_on_changed"`) or a callable/lambda.
