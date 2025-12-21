# Layouts

QtPie automatically handles layouts for you. Just specify the layout type and define your widgets - no manual `addWidget()` calls needed.

## Layout Types

The `@widget` decorator accepts a `layout` parameter:

```python
@widget(layout="vertical")   # QVBoxLayout (default)
@widget(layout="horizontal") # QHBoxLayout
@widget(layout="form")       # QFormLayout
@widget(layout="grid")       # QGridLayout
@widget(layout="none")       # No layout
```

## Vertical Layout (Default)

Vertical layout stacks widgets top to bottom. This is the default.

```python
from qtpie import widget, make
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@widget()  # layout="vertical" is the default
class MyWidget(QWidget):
    header: QLabel = make(QLabel, "Welcome")
    button: QPushButton = make(QPushButton, "Click Me")
    footer: QLabel = make(QLabel, "Footer")
```

You can also use `@widget` without parentheses when using defaults:

```python
@widget  # Same as @widget(layout="vertical")
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")
```

## Horizontal Layout

Horizontal layout arranges widgets left to right.

```python
@widget(layout="horizontal")
class Toolbar(QWidget):
    left: QLabel = make(QLabel, "Left")
    right: QLabel = make(QLabel, "Right")
```

## Form Layout

Form layouts create label/field pairs, perfect for data entry forms.

Use `form_label` in `make()` to specify the label text:

```python
from qtpy.QtWidgets import QLineEdit, QSpinBox

@widget(layout="form")
class PersonForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    email: QLineEdit = make(QLineEdit, form_label="Email")
    age: QSpinBox = make(QSpinBox, form_label="Age")
```

This creates:
```
Name:   [          ]
Email:  [          ]
Age:    [  0  ]
```

### Form without labels

You can omit `form_label` - the field will still be added to the form:

```python
@widget(layout="form")
class MyForm(QWidget):
    name: QLineEdit = make(QLineEdit)  # No label
```

### Form styling

Form layouts automatically get a `"form"` class for styling:

```python
@widget(layout="form", classes=["card"])
class MyForm(QWidget):
    pass

# widget.property("class") => ["card", "form"]
```

## Grid Layout

Grid layouts place widgets in rows and columns. Use `grid=(row, col)` to position each widget.

### Basic positioning

```python
@widget(layout="grid")
class MyGrid(QWidget):
    btn_00: QPushButton = make(QPushButton, "00", grid=(0, 0))
    btn_01: QPushButton = make(QPushButton, "01", grid=(0, 1))
    btn_10: QPushButton = make(QPushButton, "10", grid=(1, 0))
    btn_11: QPushButton = make(QPushButton, "11", grid=(1, 1))
```

This creates:
```
[00] [01]
[10] [11]
```

### Spanning columns

Use `grid=(row, col, rowspan, colspan)` to span multiple cells:

```python
@widget(layout="grid")
class Calculator(QWidget):
    display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))  # spans 4 columns
    btn_0: QPushButton = make(QPushButton, "0", grid=(1, 0))
    btn_1: QPushButton = make(QPushButton, "1", grid=(1, 1))
    btn_2: QPushButton = make(QPushButton, "2", grid=(1, 2))
    btn_3: QPushButton = make(QPushButton, "3", grid=(1, 3))
```

This creates:
```
[       display        ]
[0]  [1]  [2]  [3]
```

### Spanning rows

```python
@widget(layout="grid")
class MyGrid(QWidget):
    top: QPushButton = make(QPushButton, "T", grid=(0, 0))
    bottom: QPushButton = make(QPushButton, "B", grid=(1, 0))
    side: QPushButton = make(QPushButton, "+", grid=(0, 1, 2, 1))  # spans 2 rows
```

This creates:
```
[T]  [ + ]
[B]  [   ]
```

### Real-world example: Calculator

```python
@widget(layout="grid")
class Calculator(QWidget):
    display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))
    btn_7: QPushButton = make(QPushButton, "7", grid=(1, 0))
    btn_8: QPushButton = make(QPushButton, "8", grid=(1, 1))
    btn_9: QPushButton = make(QPushButton, "9", grid=(1, 2))
    btn_plus: QPushButton = make(QPushButton, "+", grid=(1, 3, 2, 1))  # tall +
    btn_4: QPushButton = make(QPushButton, "4", grid=(2, 0))
    btn_5: QPushButton = make(QPushButton, "5", grid=(2, 1))
    btn_6: QPushButton = make(QPushButton, "6", grid=(2, 2))
```

### Widgets without grid position

Widgets without a `grid` parameter are **not added** to the layout:

```python
@widget(layout="grid")
class MyGrid(QWidget):
    positioned: QPushButton = make(QPushButton, "Visible", grid=(0, 0))
    not_positioned: QPushButton = make(QPushButton, "Not in layout")  # exists but not visible
```

## No Layout

Use `layout="none"` when you need manual control:

```python
@widget(layout="none")
class CustomWidget(QWidget):
    label: QLabel = make(QLabel, "I'll position this myself")

    def setup(self) -> None:
        # Manual positioning
        self.label.move(10, 10)
```

The widget will have no layout manager (`widget.layout()` returns `None`).

## Spacers (Box Layouts Only)

Use `spacer()` to add flexible space in vertical or horizontal layouts.

### Basic spacer

```python
from qtpie import spacer
from qtpy.QtWidgets import QSpacerItem

@widget(layout="vertical")
class MyWidget(QWidget):
    header: QLabel = make(QLabel, "Header")
    gap: QSpacerItem = spacer(1)  # stretches to fill space
    footer: QLabel = make(QLabel, "Footer")
```

This pushes the footer to the bottom.

### Stretch factors

The `factor` controls how space is distributed:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    spacer1: QSpacerItem = spacer(1)    # gets 1/3 of space
    middle: QLabel = make(QLabel, "Middle")
    spacer2: QSpacerItem = spacer(2)    # gets 2/3 of space
    bottom: QLabel = make(QLabel, "Bottom")
```

### Fixed-size gaps

Use `min_size` for a minimum gap:

```python
@widget(layout="horizontal")
class MyWidget(QWidget):
    left: QLabel = make(QLabel, "Left")
    gap: QSpacerItem = spacer(min_size=20)  # at least 20px
    right: QLabel = make(QLabel, "Right")
```

Use `min_size` and `max_size` together for a fixed gap:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    gap: QSpacerItem = spacer(min_size=50, max_size=50)  # exactly 50px
    bottom: QLabel = make(QLabel, "Bottom")
```

### Spacers in form and grid layouts

Spacers are **ignored** in form and grid layouts - they only work in box layouts (vertical/horizontal).

## Field Order

Widgets are added to layouts in **declaration order**:

```python
@widget()
class MyWidget(QWidget):
    first: QLabel = make(QLabel, "1")   # Added first
    second: QLabel = make(QLabel, "2")  # Added second
    third: QLabel = make(QLabel, "3")   # Added third
```

## Private Fields

Fields starting with `_` are **not added** to layouts:

```python
@widget()
class MyWidget(QWidget):
    visible: QLabel = make(QLabel, "Visible")
    _helper: QLabel = make(QLabel, "Not in layout")  # exists but not in layout
```

This is useful for helper widgets you'll position manually.

## Non-Widget Fields

Only `QWidget` fields are added to layouts. Other types (int, str, etc.) are ignored:

```python
@widget()
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")
    counter: int = 0        # not added to layout
    name: str = "widget"    # not added to layout
```

## Nested Layouts

You can nest widgets to create complex layouts:

```python
@widget(layout="horizontal")
class Toolbar(QWidget):
    new_btn: QPushButton = make(QPushButton, "New")
    save_btn: QPushButton = make(QPushButton, "Save")

@widget()
class MainWindow(QWidget):
    toolbar: Toolbar = make(Toolbar)
    content: QLabel = make(QLabel, "Content here")
```

Since `Toolbar` is itself a widget with a layout, it becomes a single horizontal toolbar in the vertical `MainWindow` layout.

## See Also

- [Widgets](widgets.md) - The `@widget` decorator
- [Styling](styling.md) - CSS classes and QSS
- [Form Layouts Guide](../guides/forms.md) - In-depth form examples
- [Grid Layouts Guide](../guides/grids.md) - In-depth grid examples
