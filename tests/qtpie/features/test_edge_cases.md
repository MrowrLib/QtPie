# Edge Cases Feature Documentation

This file documents QtPie features and usage patterns demonstrated in `test_edge_cases.py`.

## Variable Types and Initialization

Variables can hold various types including empty/None values:

```python
_text: Variable[str] = new("")                    # Empty string
_maybe: Variable[str | None] = new(None)          # Optional/None
_items: Variable[list[str]] = new([])             # Empty list
_data: Variable[dict[str, int]] = new({})         # Empty dict
```

## Variable Operations

### Rapid Value Changes

Variables support rapid successive updates:

```python
for i in range(100):
    w._count.value = i
```

### List Operations

Variables wrapping lists support list methods directly:

```python
_items: Variable[list[str]] = new([])

# Append and pop work directly on the variable
w._items.append("item")
w._items.pop()
w._items.clear()
```

## Format String Bindings

### Nested Property Access

Access nested object properties in bind expressions:

```python
@widget(record=Person("John", Address("NYC")))
class MyWidget(Widget[Person]):
    city_label: QLabel = new(bind="{record.address.city}")
```

### Math Expressions

Use arithmetic in bindings (reactive to all referenced variables):

```python
_x: Variable[int] = new(10)
_y: Variable[int] = new(5)
result: QLabel = new(bind="{_x + _y}")  # Shows "15"
```

### String Methods

Call methods on variable values:

```python
_name: Variable[str] = new("hello")
upper_label: QLabel = new(bind="{_name.upper()}")  # Shows "HELLO"
```

### Built-in Functions

Use built-in functions like `len()`:

```python
_items: Variable[list[str]] = new(["a", "b", "c"])
count_label: QLabel = new(bind="Count: {len(_items)}")  # Shows "Count: 3"
```

## Two-Way Bindings

### QLineEdit Binding

Bind a QLineEdit to a Variable for two-way sync:

```python
_name: Variable[str] = new("")
name_input: QLineEdit = new(bind="_name")
```

### Variable with Widget Type

`Variable[T, W]` creates both a variable and bound widget:

```python
_name: Variable[str, QLineEdit] = new("")

# Access widget via .widget property
w._name.widget.setText("changed")
```

## Dirty Tracking

### Check Dirty State

```python
w.is_dirty.get()        # Returns bool
w.dirty_fields          # Returns list of dirty field names
```

### Reset Dirty State

```python
w.reset_dirty()  # Clears all dirty fields
```

Setting the same value does not mark as dirty:

```python
_count: Variable[int] = new(5)
w._count.value = 5  # is_dirty remains False
```

## Validation

### Adding Validators

Add named validators in `__setup__`:

```python
def __setup__(self) -> None:
    self.add_validator("_password", "min_len", lambda v: None if len(v) >= 8 else "Min 8 chars")
    self.add_validator("_password", "has_number", lambda v: None if any(c.isdigit() for c in v) else "Need number")
```

### Checking Validity

```python
w.is_valid.get()        # Returns bool (all validators pass)
w.validation_errors     # Returns dict[str, list[str]] of errors
```

### Removing Validators

```python
w.remove_validator("_name", "required")
```

## Widget Repeaters

### List to Widget Binding

Create one widget per list item:

```python
_items: Variable[list[str]] = new(["a", "b", "c"])
items: list[QLabel] = new(bind="_items")
```

The repeater automatically updates when the list changes:

```python
w._items.append("new")   # Creates new QLabel
w._items.clear()         # Removes all widgets
```

## Layout Control

### Exclude from Layout

Use `layout=False` to create a widget without adding it to the layout:

```python
hidden_label: QLabel = new("Hidden", layout=False)
```

For `Variable[T, W]`, chain the call:

```python
_hidden: Variable[str, QLineEdit] = new("")(layout=False)
```

## Instance Independence

Multiple instances of the same widget class have independent state:

```python
w1 = MyWidget()
w2 = MyWidget()

w1._count.value = 10
# w2._count.value is still 0
```

## AppBase Usage

Use `@app` decorator for application-level widgets:

```python
@app(system_tray=False, window=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)
```
