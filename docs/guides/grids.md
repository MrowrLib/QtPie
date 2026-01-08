# Grid Layouts

QtPie supports `QGridLayout` for precise widget positioning with the `layout="grid"` parameter. Widgets are positioned using the `grid=` parameter.

## Basic Grid Layout

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget(layout="grid")
class GridExample(Widget):
    # grid=(row, col)
    top_left: QLabel = new("A", grid=(0, 0))
    top_right: QLabel = new("B", grid=(0, 1))
    bottom_left: QLabel = new("C", grid=(1, 0))
    bottom_right: QLabel = new("D", grid=(1, 1))
```

This creates a 2x2 grid:

```
+---+---+
| A | B |
+---+---+
| C | D |
+---+---+
```

## Row and Column Spanning

Use the full `grid=(row, col, rowspan, colspan)` tuple:

```python
@widget(layout="grid")
class SpanningGrid(Widget):
    # Header spans 2 columns
    header: QLabel = new("Header", grid=(0, 0, 1, 2))

    # Sidebar spans 2 rows
    sidebar: QLabel = new("Sidebar", grid=(1, 0, 2, 1))

    # Content cells
    content1: QLabel = new("Content 1", grid=(1, 1))
    content2: QLabel = new("Content 2", grid=(2, 1))
```

Layout:

```
+--------+----------+
|      Header       |
+--------+----------+
|        | Content1 |
| Side   +----------+
| bar    | Content2 |
+--------+----------+
```

## Calculator Layout Example

A classic calculator demonstrates grid power:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Variable, Widget, new, widget

@widget(layout="grid")
class Calculator(Widget):
    _display: Variable[str, QLabel] = new("0")(grid=(0, 0, 1, 4))

    # Row 1
    btn7: QPushButton = new("7", grid=(1, 0), clicked="on_digit")
    btn8: QPushButton = new("8", grid=(1, 1), clicked="on_digit")
    btn9: QPushButton = new("9", grid=(1, 2), clicked="on_digit")
    btn_div: QPushButton = new("/", grid=(1, 3), clicked="on_op")

    # Row 2
    btn4: QPushButton = new("4", grid=(2, 0), clicked="on_digit")
    btn5: QPushButton = new("5", grid=(2, 1), clicked="on_digit")
    btn6: QPushButton = new("6", grid=(2, 2), clicked="on_digit")
    btn_mul: QPushButton = new("*", grid=(2, 3), clicked="on_op")

    # Row 3
    btn1: QPushButton = new("1", grid=(3, 0), clicked="on_digit")
    btn2: QPushButton = new("2", grid=(3, 1), clicked="on_digit")
    btn3: QPushButton = new("3", grid=(3, 2), clicked="on_digit")
    btn_sub: QPushButton = new("-", grid=(3, 3), clicked="on_op")

    # Row 4
    btn0: QPushButton = new("0", grid=(4, 0, 1, 2), clicked="on_digit")
    btn_eq: QPushButton = new("=", grid=(4, 2), clicked="on_equals")
    btn_add: QPushButton = new("+", grid=(4, 3), clicked="on_op")

    def on_digit(self) -> None:
        sender = self.sender()
        if sender:
            digit = sender.text()
            if self._display.value == "0":
                self._display.value = digit
            else:
                self._display.value += digit

    def on_op(self) -> None:
        pass  # Handle operators

    def on_equals(self) -> None:
        pass  # Calculate result
```

## Grid with Margins and Spacing

Control grid appearance:

```python
@widget(layout="grid", margins=10)
class SpacedGrid(Widget):
    a: QLabel = new("A", grid=(0, 0))
    b: QLabel = new("B", grid=(0, 1))
    c: QLabel = new("C", grid=(1, 0))
    d: QLabel = new("D", grid=(1, 1))
```

## Grid with Variables

Grids work with reactive Variables:

```python
@widget(layout="grid")
class ReactiveGrid(Widget):
    _x: Variable[int] = new(0)
    _y: Variable[int] = new(0)

    # Display current position
    pos_label: QLabel = new(bind="Position: ({_x}, {_y})", grid=(0, 0, 1, 2))

    # Control buttons
    up_btn: QPushButton = new("Up", grid=(1, 0, 1, 2), clicked="move_up")
    left_btn: QPushButton = new("Left", grid=(2, 0), clicked="move_left")
    right_btn: QPushButton = new("Right", grid=(2, 1), clicked="move_right")
    down_btn: QPushButton = new("Down", grid=(3, 0, 1, 2), clicked="move_down")

    def move_up(self) -> None:
        self._y -= 1

    def move_down(self) -> None:
        self._y += 1

    def move_left(self) -> None:
        self._x -= 1

    def move_right(self) -> None:
        self._x += 1
```

## Dashboard Layout

Combine spans for dashboard-style layouts:

```python
@widget(layout="grid")
class Dashboard(Widget):
    # Top stats row
    stat1: QLabel = new("Users: 1,234", grid=(0, 0))
    stat2: QLabel = new("Sales: $5,678", grid=(0, 1))
    stat3: QLabel = new("Active: 89", grid=(0, 2))

    # Main chart (spans 2 rows, 2 cols)
    chart: QWidget = new(grid=(1, 0, 2, 2))

    # Side panel (spans 2 rows)
    sidebar: QWidget = new(grid=(1, 2, 2, 1))

    # Bottom toolbar (spans all columns)
    toolbar: QWidget = new(grid=(3, 0, 1, 3))
```

## Mixing Grid with Other Widgets

Exclude widgets from grid layout:

```python
@widget(layout="grid")
class MixedLayout(Widget):
    # In the grid
    cell1: QLabel = new("Grid Cell 1", grid=(0, 0))
    cell2: QLabel = new("Grid Cell 2", grid=(0, 1))

    # Not in the grid (hidden helper widget)
    helper: QTimer = new(layout=False)
```

## Grid Parameter Summary

| Parameter | Format | Description |
|-----------|--------|-------------|
| `grid=(row, col)` | 2-tuple | Position at row, column |
| `grid=(row, col, rowspan, colspan)` | 4-tuple | Position with spanning |

Indices are 0-based. Spanning defaults to 1 if not specified.

## Tips and Best Practices

1. **Plan your grid first** - Sketch the layout before coding
2. **Use spanning wisely** - Headers and footers often span multiple columns
3. **Keep grids simple** - For complex layouts, nest widgets with different layouts
4. **Zero-based indexing** - First row is 0, first column is 0
5. **Consistent sizing** - Use Qt size policies for flexible grids

## Common Patterns

### Two-Column Settings

```python
@widget(layout="grid")
class SettingsPanel(Widget):
    lbl_theme: QLabel = new("Theme:", grid=(0, 0))
    theme: QComboBox = new(grid=(0, 1))

    lbl_font: QLabel = new("Font Size:", grid=(1, 0))
    font: QSpinBox = new(grid=(1, 1))

    lbl_auto: QLabel = new("Auto-save:", grid=(2, 0))
    auto: QCheckBox = new(grid=(2, 1))
```

### Login Form

```python
@widget(layout="grid")
class LoginPanel(Widget):
    logo: QLabel = new("MyApp", grid=(0, 0, 1, 2))

    lbl_user: QLabel = new("Username:", grid=(1, 0))
    username: QLineEdit = new(grid=(1, 1))

    lbl_pass: QLabel = new("Password:", grid=(2, 0))
    password: QLineEdit = new(grid=(2, 1))

    login_btn: QPushButton = new("Login", grid=(3, 0, 1, 2))
```

## See Also

- [Layouts](../basics/layouts.md) - All layout types
- [Forms](forms.md) - Form-specific layouts with labels
- [Widgets](../basics/widgets.md) - Widget basics
