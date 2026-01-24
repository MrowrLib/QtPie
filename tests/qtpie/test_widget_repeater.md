# WidgetRepeater Usage Patterns

Documentation extracted from `test_widget_repeater.py` demonstrating QtPie's list/dict binding features.

---

## Basic Declaration

Create a repeater with `Variable[list[T], W]` syntax - one widget per list item:

```python
_numbers: Variable[list[int], QLineEdit] = new([1, 2, 3])
```

The `.widget` property returns a `WidgetRepeater[T]`, not the widget type `W`.

---

## Accessing Repeater Widgets

Use `widget_count()` and `widget_at(index)` to access child widgets:

```python
repeater: WidgetRepeater[int] = w._numbers.widget
assert repeater.widget_count() == 3
assert isinstance(repeater.widget_at(0), QSpinBox)
```

---

## Granular List Sync Operations

### Append

```python
w._items.observable.append("c")  # Adds widget to layout
```

### Insert at Index

```python
w._items.observable.insert(1, "b")  # Inserts widget at position 1
```

### Remove

```python
w._items.observable.remove("b")  # Removes corresponding widget
```

### Replace (Index Assignment)

```python
w._items.observable[0] = "new"  # Updates widget value in-place
```

### Clear

```python
w._items.observable.clear()  # Removes all widgets
```

---

## Two-Way Binding (Primitives)

Primitives (`int`, `str`) bind bidirectionally between widget and list:

```python
# Widget type determines binding mechanism
_numbers: Variable[list[int], QSpinBox] = new([1, 2, 3])

# Editing spinbox updates list
spin.setValue(99)
assert w._numbers.observable[1] == 99

# Changing list updates widget
w._numbers.observable[0] = 42
assert repeater.widget_at(0).value() == 42
```

---

## Object Binding with Format Strings

### Single Property Binding

```python
_dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3)])(bind="{name}")
```

### Multiple Properties in Format

```python
_dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3)])(bind="{name} is {age} years old")
```

### Two-Way Object Property Binding

```python
_dogs: Variable[list[Dog], QLineEdit] = new([Dog("Rover", 3)])(bind="{name}")
# Editing the field updates dog.name
```

---

## Special Placeholders

| Placeholder | Description |
|------------|-------------|
| `{#self}` | The item value itself |
| `{#index}` | Zero-based index of item in list |
| `{#key}` | Dict key (for dict bindings) |
| `{#value}` | Dict value (for dict bindings) |

### Index Placeholder

```python
_items: Variable[list[str], QLabel] = new(["a", "b", "c"])(bind="{#index}")
# Shows "0", "1", "2"
```

### Combined Placeholders

```python
_items: Variable[list[str], QLabel] = new(["a", "b"])(bind="Index {#index}: {#self}")
# Shows "Index 0: a", "Index 1: b"
```

---

## Widget Kwargs Applied to All Items

Chain call to apply widget properties to every generated widget:

```python
_names: Variable[list[str], QLineEdit] = new(["a", "b"])(maxLength=5)
# Every QLineEdit gets maxLength=5, including newly appended ones
```

---

## List of Widgets Bound to Variable

Alternative syntax using `list[W]` with `bind=` pointing to a Variable:

```python
_dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
_labels: list[QLabel] = new(bind="_dogs", format="{name} is {age} years old")
```

This creates a `WidgetRepeater` that syncs with the `_dogs` Variable.

---

## Dict Binding

Bind to `dict[K, V]` variables using `list[QWidget]` syntax:

```python
_dogs_dict: Variable[dict[str, Dog]] = new({"Fido": Dog("Fido", 3)})
_labels: list[QLabel] = new(bind="_dogs_dict", format="{#key} is {age} years old")
```

Creates a `DictWidgetRepeater` with access to `{#key}` and `{#value}` placeholders.

### Dict Key Lookup

```python
label = w._labels.widget_for_key("Fido")  # Get widget by dict key
```

### Dict Updates

```python
w._items["b"] = 2  # Adds new widget automatically
```

---

## Callable Format

Use a lambda/function for custom formatting:

```python
_labels: list[QLabel] = new(
    bind="_dogs",
    format=lambda d: f"{d.name.upper()} - {d.age}"
)
```

---

## Layout Integration

WidgetRepeater integrates into parent widget's layout like any other widget:

```python
@widget
class Test(Widget):
    _label: QLabel = new("Before")
    _numbers: Variable[list[int], QLabel] = new([1, 2])
    _label2: QLabel = new("After")
# Layout has 3 items: label, repeater container, label2
```

---

## Key Classes

- `WidgetRepeater[T]` - Manages widgets for `list[T]` binding
- `DictWidgetRepeater[K, V]` - Manages widgets for `dict[K, V]` binding
- Both are returned as `.widget` when using `Variable[list/dict[...], W]`
