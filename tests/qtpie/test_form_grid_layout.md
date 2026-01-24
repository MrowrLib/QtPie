# Form and Grid Layout Patterns in QtPie

This document describes the usage patterns for form and grid layouts in QtPie, extracted from the test file.

## Form Layout with `label=`

Form layouts use `QFormLayout` and require the `label=` parameter on each field to create labeled rows.

```python
@widget(layout="form")
class TestForm(Widget):
    _name: QLineEdit = new(label="Full Name")
    _email: QLineEdit = new(label="Email Address")
```

### Form Layout with Variable[T, W]

When using `Variable[T, W]` in a form layout, pass `label=` in the widget kwargs (second call).

```python
@widget(layout="form")
class TestForm(Widget):
    _age: Variable[int, QSpinBox] = new(25)(label="Age")
```

## Grid Layout with `grid=`

Grid layouts use `QGridLayout` and require the `grid=` parameter specifying position as a tuple.

### Basic Position (row, col)

```python
@widget(layout="grid")
class TestGrid(Widget):
    _btn_00: QLabel = new("00", grid=(0, 0))
    _btn_01: QLabel = new("01", grid=(0, 1))
    _btn_10: QLabel = new("10", grid=(1, 0))
```

### With Row/Column Span (row, col, rowspan, colspan)

```python
@widget(layout="grid")
class TestGrid(Widget):
    _display: QLineEdit = new(grid=(0, 0, 1, 4))  # Spans 4 columns
    _btn: QLabel = new("X", grid=(1, 0))
```

### Grid Layout with Variable[T, W]

```python
@widget(layout="grid")
class TestGrid(Widget):
    _value: Variable[int, QSpinBox] = new(10)(grid=(0, 0))
    _label: Variable[str, QLabel] = new("Hello")(grid=(0, 1))
```

## Vertical/Horizontal Layouts

These standard layouts do NOT require `label=` or `grid=` parameters.

```python
@widget(layout="vertical")
class TestWidget(Widget):
    _name: QLineEdit = new()
    _email: QLineEdit = new()

@widget(layout="horizontal")
class TestWidget(Widget):
    _name: QLineEdit = new()
    _email: QLineEdit = new()
```

Note: `label=` and `grid=` are accepted but ignored in vertical/horizontal layouts.

## Form Row Visibility

When using `visible=` on a widget in a `QFormLayout`, the entire row (including label) is hidden/shown.

### Simple Variable Binding

```python
@widget(layout="form")
class TestForm(Widget):
    _show: Variable[bool] = new(True)
    _name: QLineEdit = new(label="Name", visible="_show")
```

### Expression Binding

```python
@widget(layout="form")
class TestForm(Widget):
    _count: Variable[int] = new(5)
    _name: QLineEdit = new(label="Name", visible="{_count > 3}")
```

### Nested Layout Targeting

Use `layout=` to place widgets in a specific named layout while still supporting visibility.

```python
@widget
class TestForm(Widget):
    _show: Variable[bool] = new(False)
    _form_layout: QFormLayout = new()
    _name: QLineEdit = new(label="Name", layout="_form_layout", visible="_show")
```

## Passthrough Behavior for Non-QWidget Types

When a field is NOT a QWidget subclass, `label=` and `grid=` are passed through to the constructor.

```python
class MyConfig:
    def __init__(self, label: str) -> None:
        self.label = label

@widget
class TestWidget(Widget):
    _config: MyConfig = new(label="Test Label")  # Passed to MyConfig.__init__
```
