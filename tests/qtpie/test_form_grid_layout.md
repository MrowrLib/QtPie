# Form and Grid Layout Tests

## Form Layout with `label=`

Form layouts (`layout="form"`) require the `label=` parameter on fields, which creates row labels automatically.

```python
@widget(layout="form")
class TestForm(Widget):
    _name: QLineEdit = new(label="Full Name")
    _email: QLineEdit = new(label="Email Address")
```

Works with `Variable[T, W]` by passing `label=` in widget kwargs:

```python
@widget(layout="form")
class TestForm(Widget):
    _age: Variable[int, QSpinBox] = new(25)(label="Age")
```

## Grid Layout with `grid=`

Grid layouts (`layout="grid"`) require the `grid=` parameter for positioning. Use `(row, col)` for basic positioning or `(row, col, rowspan, colspan)` for spanning.

```python
@widget(layout="grid")
class TestGrid(Widget):
    _btn_00: QLabel = new("00", grid=(0, 0))
    _btn_01: QLabel = new("01", grid=(0, 1))
    _btn_10: QLabel = new("10", grid=(1, 0))
    _btn_11: QLabel = new("11", grid=(1, 1))
```

Spanning multiple rows or columns:

```python
@widget(layout="grid")
class TestGrid(Widget):
    # Spans 1 row, 4 cols
    _display: QLineEdit = new(grid=(0, 0, 1, 4))
    # Regular cell
    _btn: QLabel = new("X", grid=(1, 0))
```

## `label=` and `grid=` Passthrough

For non-QWidget types, `label=` and `grid=` pass through to the constructor instead of being intercepted for layout purposes.

```python
class MyConfig:
    def __init__(self, label: str) -> None:
        self.label = label

@widget
class TestWidget(Widget):
    _config: MyConfig = new(label="Test Label")
```

```python
class MyPosition:
    def __init__(self, grid: tuple[int, int]) -> None:
        self.grid = grid

@widget
class TestWidget(Widget):
    _pos: MyPosition = new(grid=(5, 10))
```

## Vertical and Horizontal Layouts

Vertical and horizontal layouts don't require `label=` or `grid=`. These parameters are accepted but ignored.

```python
@widget(layout="vertical")
class TestWidget(Widget):
    _name: QLineEdit = new()
    _email: QLineEdit = new()
```

```python
@widget(layout="horizontal")
class TestWidget(Widget):
    _name: QLineEdit = new(grid=(0, 0))  # grid is ignored but allowed
```
