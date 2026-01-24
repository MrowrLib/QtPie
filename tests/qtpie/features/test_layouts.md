# QtPie Layout Feature Documentation

This document describes the layout patterns available in QtPie, extracted from the test suite.

## Layout Types Overview

QtPie supports four layout types, specified via the decorator `layout=` parameter:

| Layout Type | Qt Class | Parameter |
|-------------|----------|-----------|
| Vertical (default) | QVBoxLayout | `layout="vertical"` or omit |
| Horizontal | QHBoxLayout | `layout="horizontal"` |
| Form | QFormLayout | `layout="form"` |
| Grid | QGridLayout | `layout="grid"` |

---

## Vertical Layout (Default)

The default layout arranges widgets top-to-bottom.

```python
@widget
class MyWidget(Widget):
    label1: QLabel = new("One")
    label2: QLabel = new("Two")
```

Explicit vertical:

```python
@widget(layout="vertical")
class MyWidget(Widget):
    label1: QLabel = new("One")
    label2: QLabel = new("Two")
```

---

## Horizontal Layout

Arranges widgets left-to-right.

```python
@widget(layout="horizontal")
class MyWidget(Widget):
    btn1: QLabel = new("A")
    btn2: QLabel = new("B")
```

---

## Form Layout

Creates labeled form rows. **Requires `label=` parameter** on each field.

```python
@widget(layout="form")
class MyWidget(Widget):
    name: QLineEdit = new(label="Full Name")
    email: QLineEdit = new(label="Email")
```

Works with Variable types:

```python
@widget(layout="form")
class MyWidget(Widget):
    _age: Variable[int, QSpinBox] = new(25)(label="Age")
```

---

## Grid Layout

Positions widgets in a grid. **Requires `grid=` parameter** on each field.

Basic positioning with `grid=(row, col)`:

```python
@widget(layout="grid")
class MyWidget(Widget):
    btn_00: QLabel = new("00", grid=(0, 0))
    btn_01: QLabel = new("01", grid=(0, 1))
    btn_10: QLabel = new("10", grid=(1, 0))
```

With row/column span `grid=(row, col, rowspan, colspan)`:

```python
@widget(layout="grid")
class MyWidget(Widget):
    display: QLineEdit = new(grid=(0, 0, 1, 4))  # Spans 4 columns
    btn: QLabel = new("X", grid=(1, 0))
```

---

## Excluding Widgets from Layout

Use `layout=False` to create a widget without adding it to the layout.

```python
@widget(layout="vertical")
class MyWidget(Widget):
    included: QLabel = new("Visible")
    excluded: QLabel = new("Hidden from layout", layout=False)
```

The excluded widget is still accessible via `self.excluded`.

---

## Stretch

Adds expandable space to push widgets apart.

Default stretch (factor=1):

```python
@widget(layout="vertical")
class MyWidget(Widget):
    top: QLabel = new("Top")
    _stretch: Stretch = new()
    bottom: QLabel = new("Bottom")
```

Custom stretch factor:

```python
_stretch: Stretch = new(3)
```

Bare annotation shorthand (equivalent to `= new()`):

```python
@widget(layout="vertical")
class MyWidget(Widget):
    top: QLabel = new("Top")
    _stretch: Stretch  # No = new() needed
    bottom: QLabel = new("Bottom")
```

---

## QSpacerItem

Adds fixed-size spacing.

```python
@widget(layout="vertical")
class MyWidget(Widget):
    top: QLabel = new("Top")
    _spacer: QSpacerItem = new(20, 40)
    bottom: QLabel = new("Bottom")
```

With size policy:

```python
_spacer: QSpacerItem = new(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
```

---

## Nested Layouts

Create sub-layouts within the main layout using layout classes as field types.

### Basic Nested Layout

```python
@widget(layout="vertical")
class MyWidget(Widget):
    top: QLabel = new("Top")
    _row: QHBoxLayout = new()
    bottom: QLabel = new("Bottom")
```

### Adding Widgets to Nested Layouts

Use `layout="field_name"` to target a nested layout:

```python
@widget(layout="vertical")
class MyWidget(Widget):
    header: QLabel = new("Header")
    _buttons: QHBoxLayout = new()
    btn1: QLabel = new("OK", layout="_buttons")
    btn2: QLabel = new("Cancel", layout="_buttons")
    footer: QLabel = new("Footer")
```

### Nested Grid Layout

Widgets in nested QGridLayout still require `grid=`:

```python
@widget(layout="vertical")
class MyWidget(Widget):
    header: QLabel = new("Header")
    _grid: QGridLayout = new()
    grid_00: QLabel = new("(0,0)", layout="_grid", grid=(0, 0))
    grid_01: QLabel = new("(0,1)", layout="_grid", grid=(0, 1))
```

### Nested Form Layout

Widgets in nested QFormLayout still require `label=`:

```python
@widget(layout="vertical")
class MyWidget(Widget):
    header: QLabel = new("Header")
    _form: QFormLayout = new()
    name: QLineEdit = new(layout="_form", label="Name:")
    email: QLineEdit = new(layout="_form", label="Email:")
```

### Deeply Nested Layouts

Layouts can be nested multiple levels deep:

```python
@widget(layout="vertical")
class MyWidget(Widget):
    _level1: QHBoxLayout = new()
    _level2: QVBoxLayout = new(layout="_level1")
    _level3: QHBoxLayout = new(layout="_level2")
    deep_label: QLabel = new("Deep", layout="_level3")
```

### Stretch/Spacer in Nested Layouts

```python
@widget(layout="vertical")
class MyWidget(Widget):
    _row: QHBoxLayout = new()
    left: QLabel = new("Left", layout="_row")
    _stretch: Stretch = new(layout="_row")
    right: QLabel = new("Right", layout="_row")
```

### Excluding Nested Layout from Parent

```python
_hidden_row: QHBoxLayout = new(layout=False)
```

---

## Variable[T, W] in Layouts

Variable fields work in all layout types:

```python
# In form layout
_age: Variable[int, QSpinBox] = new(25)(label="Age")

# In grid layout
_value: Variable[int, QSpinBox] = new(10)(grid=(0, 0))

# In nested layouts
_name: Variable[str, QLineEdit] = new("Hello")(layout="_row")
_email: Variable[str, QLineEdit] = new("")(layout="_form", label="Email:")
```

---

## Key Conventions

1. **Default is vertical** - Omit `layout=` for QVBoxLayout
2. **Form requires `label=`** - Every field in form layout needs a label
3. **Grid requires `grid=`** - Every field in grid layout needs position
4. **Nested layouts by string** - Use `layout="field_name"` to target nested layouts
5. **Bare `Stretch` works** - No `= new()` required for default stretch
6. **Field order preserved** - Widgets appear in declaration order
