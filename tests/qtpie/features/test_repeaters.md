# Widget Repeaters in QtPie

Widget repeaters automatically generate and synchronize widgets from reactive collections (lists, dicts, sets). They are the QtPie equivalent of Vue's `v-for` or React's `.map()` rendering pattern.

## Overview

Repeaters create one widget per collection item and keep them synchronized as items are added, removed, or modified.

---

## List Repeaters

### Variable[list[T], W] Syntax

The primary pattern: declare a `Variable` with a list type and widget type.

```python
_items: Variable[list[str], QLabel] = new(["a", "b", "c"])
```

Access the repeater via `.widget`:

```python
repeater: WidgetRepeater[str] = instance._items.widget
repeater.widget_count()  # 3
repeater.widget_at(0)    # First QLabel
```

### list[QWidget] = new(bind="...") Syntax

Alternative pattern: separate Variable and widget list.

```python
_items: Variable[list[str]] = new(["a", "b"])
_labels: list[QLabel] = new(bind="_items")
```

The `_labels` field becomes a `WidgetRepeater` instance.

### Primitive Display

Primitives automatically display their string representation:

```python
_items: Variable[list[int], QLabel] = new([10, 20, 30])
# Creates labels showing "10", "20", "30"
```

### Granular Sync Operations

All list mutations are tracked granularly:

```python
instance._items.observable.append("c")       # Adds widget
instance._items.observable.insert(1, "b")    # Inserts at position
instance._items.observable.remove("b")       # Removes specific widget
instance._items.observable.clear()           # Removes all widgets
instance._items.observable[0] = "new"        # Updates widget in place
```

### Format Expressions

Use `bind=` with format strings for custom display:

```python
# {#self} - the item value
_items: Variable[list[int], QLabel] = new([10])(bind="{#self}")

# {#index} - the item's position
_items: Variable[list[str], QLabel] = new(["a", "b"])(bind="{#index}")

# Combined
_items: Variable[list[str], QLabel] = new(["a"])(bind="[{#index}] {#self}")
# Output: "[0] a"
```

### Object Property Binding

For dataclass/object items, reference properties directly:

```python
@dataclass
class Dog:
    name: str
    age: int

_dogs: Variable[list[Dog], QLabel] = new([Dog("Fido", 3)])(bind="{name} is {age}")
# Output: "Fido is 3"
```

### Two-Way Binding

With editable widgets, changes propagate bidirectionally:

```python
_items: Variable[list[str], QLineEdit] = new(["hello"])

# User edits widget -> list updates
edit.setText("world")  # _items.observable[0] becomes "world"

# List changes -> widget updates
_items.observable[0] = "new"  # Widget text becomes "new"
```

### Widget Kwargs

Pass Qt properties via chained call; applied to all items:

```python
_items: Variable[list[str], QLineEdit] = new(["a"])(maxLength=5)
# All QLineEdits have maxLength=5
```

---

## Dict Repeaters

### Declaration

Use `list[QWidget]` bound to a `Variable[dict[K, V]]`:

```python
_items: Variable[dict[str, int]] = new({"Alice": 100})
_labels: list[QLabel] = new(bind="_items")
```

The field becomes a `DictWidgetRepeater`.

### Format with Key/Value

Use `{#key}` and `{#value}` placeholders:

```python
_labels: list[QLabel] = new(bind="_items", format="{#key}: {#value}")
# Output: "Alice: 100"
```

### Object Values

Access properties on dict values:

```python
_dogs: Variable[dict[str, Dog]] = new({"fido": Dog("Fido", 3)})
_labels: list[QLabel] = new(bind="_dogs", format="{#key}: {name} is {age}")
# Output: "fido: Fido is 3"
```

### Granular Sync

Dict mutations create/destroy widgets:

```python
instance._items["b"] = 2              # Creates widget for "b"
del instance._items.observable["a"]   # Removes widget for "a"
```

### Widget Lookup by Key

```python
label = instance._labels.widget_for_key("Alice")
```

---

## Set Repeaters

### Variable[set[T], W] Syntax

```python
_items: Variable[set[str], QLabel] = new({"a", "b", "c"})
```

Access via `.widget` as `SetWidgetRepeater`.

### Granular Sync

```python
instance._items.observable.add("d")       # Creates widget
instance._items.observable.discard("a")   # Removes widget
```

### Format Expressions

Same `{#self}` syntax as list repeaters:

```python
_items: Variable[set[str], QLabel] = new({"hello"})(bind="{#self}")
```

---

## Record Binding Pattern

Repeaters can bind to properties of a widget's record type, updating when the record is set.

### Direct Record Property Binding

```python
@dataclass
class Response:
    headers: dict[str, str]

@widget
class TestClass(Widget[Response]):
    _headers: list[QLabel] = new(bind="headers", format="{#key}: {#value}")

# Set record later
instance.record = Response({"Content-Type": "application/json"})
# Repeater now has 1 widget
```

### Nested Widget Hierarchy

Supports parent-child record propagation:

```python
# Child with list bound to record property
@widget
class ChildWidget(Widget[Response]):
    _headers: list[QLabel] = new(bind="headers", format="{#key}: {#value}")

# Parent with Variable that binds to child's record
@widget
class ParentWidget(Widget):
    response: Variable[Response | None] = new(None)
    _child: ChildWidget = new(bind="response")

# Setting parent's Variable propagates to child
parent.response = Response({"Accept": "text/html"})
# child._headers now has widgets
```

### Bare Annotation Auto-Binding

Child widgets with bare annotations (no `= new()`) automatically bind to parent's record:

```python
@widget
class ChildWidget(Widget[Response]):
    _grandchild: GrandchildWidget  # Bare annotation - auto-binds to record
```

---

## Summary of Placeholders

| Placeholder | Context | Description |
|-------------|---------|-------------|
| `{#self}` | List/Set | Current item value |
| `{#index}` | List | Current item index (0-based) |
| `{#key}` | Dict | Current dict key |
| `{#value}` | Dict | Current dict value |
| `{property}` | Object items | Property on the item object |
