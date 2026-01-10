# Form and Grid Layout Tests

## Form Layout with `label=`

Form layouts use `label=` parameter to specify row labels. Each field gets a label in the left column.

```python
@widget(layout="form")
class TestForm(Widget):
    _name: QLineEdit = new(label="Full Name")
    _email: QLineEdit = new(label="Email Address")
```

Form layouts require `label=` for all fields - omitting it raises `TypeError`.

```python
@widget(layout="form")
class TestForm(Widget):
    _name: QLineEdit = new()  # Missing label=

with pytest.raises(TypeError, match="requires label="):
    qt.track(TestForm())
```

## Grid Layout with `grid=`

Grid layouts use `grid=` parameter to specify (row, col) or (row, col, rowspan, colspan) positioning.

```python
@widget(layout="grid")
class TestGrid(Widget):
    _btn_00: QLabel = new("00", grid=(0, 0))
    _btn_01: QLabel = new("01", grid=(0, 1))
    _btn_10: QLabel = new("10", grid=(1, 0))
    _btn_11: QLabel = new("11", grid=(1, 1))
```

Grid layouts support rowspan and colspan via 4-tuple syntax:

```python
@widget(layout="grid")
class TestGrid(Widget):
    # Spans 1 row, 4 cols
    _display: QLineEdit = new(grid=(0, 0, 1, 4))
    # Regular cell
    _btn: QLabel = new("X", grid=(1, 0))
```

Grid layouts require `grid=` for all fields - omitting it raises `TypeError`.

## Variable[T, W] with Form/Grid Layouts

`Variable[T, W]` fields work in form/grid layouts by passing `label=` or `grid=` in the widget kwargs (second call).

```python
@widget(layout="form")
class TestForm(Widget):
    _age: Variable[int, QSpinBox] = new(25)(label="Age")

@widget(layout="grid")
class TestGrid(Widget):
    _value: Variable[int, QSpinBox] = new(10)(grid=(0, 0))
    _label: Variable[str, QLabel] = new("Hello")(grid=(0, 1))
```

## Passthrough for Non-QWidget Types

`label=` and `grid=` parameters pass through to constructors for non-QWidget types instead of being consumed by layout logic.

```python
class MyConfig:
    def __init__(self, label: str) -> None:
        self.label = label

@widget
class TestWidget(Widget):
    _config: MyConfig = new(label="Test Label")

w = qt.track(TestWidget())
assert w._config.label == "Test Label"
```

## Vertical/Horizontal Layouts

Vertical and horizontal layouts don't require `label=` or `grid=` parameters. If provided, these parameters are accepted but ignored.

```python
@widget(layout="vertical")
class TestWidget(Widget):
    _name: QLineEdit = new()
    _email: QLineEdit = new()

@widget(layout="horizontal")
class TestWidget(Widget):
    _name: QLineEdit = new(grid=(0, 0))  # grid is ignored but allowed
```
