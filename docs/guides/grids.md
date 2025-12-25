# Grid Layouts

Grid layouts arrange widgets in rows and columns, like a spreadsheet or calculator. Use `layout="grid"` to create a `QGridLayout` and position widgets with the `grid` parameter.

## Basic Grid Positioning

Use `grid=(row, col)` to place widgets at specific positions:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QPushButton, QWidget

@widget(layout="grid")
class ButtonGrid(QWidget):
    btn_00: QPushButton = make(QPushButton, "Top Left", grid=(0, 0))
    btn_01: QPushButton = make(QPushButton, "Top Right", grid=(0, 1))
    btn_10: QPushButton = make(QPushButton, "Bottom Left", grid=(1, 0))
    btn_11: QPushButton = make(QPushButton, "Bottom Right", grid=(1, 1))
```

This creates a 2x2 grid:

```
┌─────────────┬──────────────┐
│  Top Left   │  Top Right   │  row 0
├─────────────┼──────────────┤
│ Bottom Left │ Bottom Right │  row 1
└─────────────┴──────────────┘
  col 0         col 1
```

**Important:** Widgets without a `grid` parameter are not added to grid layouts.

## Spanning Columns

Use `grid=(row, col, rowspan, colspan)` to make widgets span multiple columns:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLineEdit, QPushButton, QWidget

@widget(layout="grid")
class Calculator(QWidget):
    display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))  # spans 4 columns
    btn_7: QPushButton = make(QPushButton, "7", grid=(1, 0))
    btn_8: QPushButton = make(QPushButton, "8", grid=(1, 1))
    btn_9: QPushButton = make(QPushButton, "9", grid=(1, 2))
    btn_div: QPushButton = make(QPushButton, "/", grid=(1, 3))
```

The display spans all 4 columns:

```
┌──────────────────────────────────┐
│            display               │  row 0 (colspan=4)
├────────┬────────┬────────┬───────┤
│   7    │   8    │   9    │   /   │  row 1
└────────┴────────┴────────┴───────┘
  col 0   col 1   col 2    col 3
```

## Spanning Rows

Use `grid=(row, col, rowspan, colspan)` to make widgets span multiple rows:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QPushButton, QWidget

@widget(layout="grid")
class SidePanel(QWidget):
    top: QPushButton = make(QPushButton, "Top", grid=(0, 0))
    bottom: QPushButton = make(QPushButton, "Bottom", grid=(1, 0))
    side: QPushButton = make(QPushButton, "+", grid=(0, 1, 2, 1))  # spans 2 rows
```

The side button spans 2 rows:

```
┌────────┬───────┐
│  Top   │   +   │  row 0
├────────┤       │  rowspan=2
│ Bottom │       │  row 1
└────────┴───────┘
  col 0   col 1
```

## Real-World Example: Calculator

Here's a complete calculator layout demonstrating all grid features:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLineEdit, QPushButton, QWidget

@widget(layout="grid")
class Calculator(QWidget):
    # Display spans entire top row
    display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))

    # Number pad
    btn_7: QPushButton = make(QPushButton, "7", grid=(1, 0))
    btn_8: QPushButton = make(QPushButton, "8", grid=(1, 1))
    btn_9: QPushButton = make(QPushButton, "9", grid=(1, 2))
    btn_4: QPushButton = make(QPushButton, "4", grid=(2, 0))
    btn_5: QPushButton = make(QPushButton, "5", grid=(2, 1))
    btn_6: QPushButton = make(QPushButton, "6", grid=(2, 2))

    # Plus button spans 2 rows
    btn_plus: QPushButton = make(QPushButton, "+", grid=(1, 3, 2, 1))
```

Layout visualization:

```
┌───────────────────────────────┐
│          display              │  row 0 (colspan=4)
├───────┬───────┬───────┬───────┤
│   7   │   8   │   9   │   +   │  row 1
├───────┼───────┼───────┤       │  rowspan=2
│   4   │   5   │   6   │       │  row 2
└───────┴───────┴───────┴───────┘
```

## Grid Position Format

The `grid` parameter accepts two formats:

1. **Basic:** `grid=(row, col)` - places widget at position with default size (1x1)
2. **Spanning:** `grid=(row, col, rowspan, colspan)` - widget spans multiple cells

```python
# Basic positioning (1x1 cell)
btn: QPushButton = make(QPushButton, "Click", grid=(0, 0))

# Span 2 rows, 1 column
tall: QPushButton = make(QPushButton, "Tall", grid=(0, 1, 2, 1))

# Span 1 row, 3 columns
wide: QLineEdit = make(QLineEdit, grid=(2, 0, 1, 3))

# Span 2 rows, 2 columns
big: QPushButton = make(QPushButton, "Big", grid=(0, 0, 2, 2))
```

## Field Naming Conventions

Fields follow the standard QtPie underscore conventions:

- `foo` and `_foo` - Added to the grid
- `_foo_` - **Excluded** from the grid (starts AND ends with `_`)

```python
@widget(layout="grid")
class MyGrid(QWidget):
    btn: QPushButton = make(QPushButton, "Visible", grid=(0, 0))     # In grid
    _private: QLabel = make(QLabel, "Private", grid=(0, 1))          # In grid
    _excluded_: QLabel = make(QLabel, "Hidden", grid=(0, 2))         # NOT in grid
```

Use `_foo_` naming for widgets you manage manually.

## See Also

- [Layouts](../basics/layouts.md) - Overview of all layout types
- [Form Layouts](forms.md) - Two-column form layouts with labels
- [@widget](../reference/decorators/widget.md) - Full decorator reference
- [make()](../reference/factories/make.md) - Widget factory function
