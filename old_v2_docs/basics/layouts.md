# Layouts

QtPie automatically manages widget layouts, making it easy to create structured UIs without manually dealing with Qt's layout managers. You declare the layout type and QtPie handles the rest.

## Layout Types

QtPie supports four layout types through the `layout` parameter in the `@widget` decorator.

### Vertical Layout (Default)

Widgets are stacked vertically from top to bottom:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget  # layout="vertical" is the default
class VerticalExample(Widget):
    title: QLabel = new("Title")
    subtitle: QLabel = new("Subtitle")
    button: QPushButton = new("Click")
```

You can also explicitly specify vertical layout:

```python
@widget(layout="vertical")
class ExplicitVertical(Widget):
    label: QLabel = new("Hello")
```

### Horizontal Layout

Widgets are arranged horizontally from left to right:

```python
@widget(layout="horizontal")
class HorizontalExample(Widget):
    label: QLabel = new("Name:")
    input: QLineEdit = new()
    button: QPushButton = new("Submit")
```

### Form Layout

Creates a two-column form with labels on the left and fields on the right. Each field **must** have a `label=` parameter:

```python
@widget(layout="form")
class FormExample(Widget):
    name: QLineEdit = new(label="Full Name")
    email: QLineEdit = new(label="Email Address")
    age: QSpinBox = new(label="Age")
```

**Important:** Forgetting `label=` in a form layout raises a `TypeError`:

```python
@widget(layout="form")
class BadForm(Widget):
    name: QLineEdit = new()  # Missing label=

widget = BadForm()  # TypeError: requires label=
```

### Grid Layout

Positions widgets in a grid using row/column coordinates. Each field **must** have a `grid=` parameter:

```python
@widget(layout="grid")
class GridExample(Widget):
    # grid=(row, col)
    label_00: QLabel = new("Top Left", grid=(0, 0))
    label_01: QLabel = new("Top Right", grid=(0, 1))
    label_10: QLabel = new("Bottom Left", grid=(1, 0))
    label_11: QLabel = new("Bottom Right", grid=(1, 1))
```

#### Grid Spanning

You can span multiple rows or columns using a 4-tuple: `(row, col, rowspan, colspan)`

```python
@widget(layout="grid")
class Calculator(Widget):
    # Display spans 1 row, 4 columns
    display: QLineEdit = new(grid=(0, 0, 1, 4))

    # Number buttons
    btn_7: QPushButton = new("7", grid=(1, 0))
    btn_8: QPushButton = new("8", grid=(1, 1))
    btn_9: QPushButton = new("9", grid=(1, 2))
    btn_div: QPushButton = new("/", grid=(1, 3))
```

**Important:** Forgetting `grid=` in a grid layout raises a `TypeError`:

```python
@widget(layout="grid")
class BadGrid(Widget):
    button: QPushButton = new("X")  # Missing grid=

widget = BadGrid()  # TypeError: requires grid=
```

### No Layout

Setting `layout=None` creates a widget with no layout manager:

```python
@widget(layout=None)
class CustomLayout(Widget):
    label: QLabel = new("Hello")

widget = CustomLayout()
assert widget.layout() is None
```

This is useful when you need full manual control over widget positioning.

## Layout Margins

Control the spacing around the layout's edges using the `margins` parameter.

### Uniform Margins

Use a single integer to apply the same margin to all sides:

```python
@widget(margins=10)
class UniformMargins(Widget):
    label: QLabel = new("Content")

widget = UniformMargins()
margins = widget.layout().contentsMargins()
assert margins.left() == 10
assert margins.top() == 10
assert margins.right() == 10
assert margins.bottom() == 10
```

### Individual Margins

Use a 4-tuple for `(left, top, right, bottom)`:

```python
@widget(margins=(5, 10, 15, 20))
class CustomMargins(Widget):
    label: QLabel = new("Content")

widget = CustomMargins()
margins = widget.layout().contentsMargins()
assert margins.left() == 5
assert margins.top() == 10
assert margins.right() == 15
assert margins.bottom() == 20
```

## Excluding Widgets from Layout

Sometimes you need a widget to exist but not be part of the automatic layout. Use `layout=False` in the `new()` call:

```python
@widget
class MixedLayout(Widget):
    visible: QLabel = new("I'm in the layout")
    hidden: QLabel = new("I'm not in the layout", layout=False)
    also_visible: QLabel = new("I'm also in the layout")

widget = MixedLayout()
assert widget.layout().count() == 2  # Only visible and also_visible

# But the excluded widget still exists
assert widget.hidden is not None
assert widget.hidden.text() == "I'm not in the layout"
```

This works with `Variable[T, W]` widgets too:

```python
from qtpie import Variable

@widget
class VariableExclusion(Widget):
    visible: QLabel = new("Visible")
    name: Variable[str, QLineEdit] = new("test")(layout=False)
    also_visible: QLabel = new("Also Visible")

widget = VariableExclusion()
assert widget.layout().count() == 2  # Only the labels

# But the Variable widget exists and works
assert widget.name.widget is not None
assert widget.name.widget.text() == "test"
```

## Field Order Matters

Widgets are added to the layout in the order they're defined in the class:

```python
@widget
class OrderExample(Widget):
    first: QLabel = new("First")
    second: QLabel = new("Second")
    third: QLabel = new("Third")

widget = OrderExample()
layout = widget.layout()
assert layout.itemAt(0).widget() == widget.first
assert layout.itemAt(1).widget() == widget.second
assert layout.itemAt(2).widget() == widget.third
```

This predictable ordering makes it easy to reason about your UI structure.

## Variables and Layout

`Variable` fields are never added to the layout because they're not Qt widgets:

```python
from qtpie import Variable

@widget
class VariableExample(Widget):
    count: Variable[int] = new(0)
    label: QLabel = new("Hello")

widget = VariableExample()
assert widget.layout().count() == 1  # Only the QLabel
```

However, `Variable[T, W]` (Variable with widget type) creates a widget that is added to the layout:

```python
@widget
class VariableWidget(Widget):
    name: Variable[str, QLineEdit] = new("")
    label: QLabel = new("Hello")

widget = VariableWidget()
assert widget.layout().count() == 2  # Both the QLineEdit and QLabel
```

## Form Layout Details

### With Regular Widgets

```python
from PySide6.QtWidgets import QLineEdit, QSpinBox

@widget(layout="form")
class UserForm(Widget):
    name: QLineEdit = new(label="Full Name")
    age: QSpinBox = new(label="Age")
    email: QLineEdit = new(label="Email")
```

This creates a standard two-column form:
```
Full Name  [ text input ]
Age        [ spin box   ]
Email      [ text input ]
```

### With Variable Widgets

`Variable[T, W]` in form layouts requires `label=` in the widget kwargs (the second call):

```python
from qtpie import Variable

@widget(layout="form")
class FormWithVariables(Widget):
    # label= goes in the widget kwargs (second parentheses)
    age: Variable[int, QSpinBox] = new(25)(label="Age")

widget = FormWithVariables()
```

**Forgetting the label raises TypeError:**

```python
@widget(layout="form")
class BadFormVariable(Widget):
    age: Variable[int, QSpinBox] = new(25)()  # Missing label=

widget = BadFormVariable()  # TypeError: requires label=
```

## Grid Layout Details

### Basic Positioning

Grid positions use `(row, col)` tuples, with 0-based indexing:

```python
@widget(layout="grid")
class GridPositions(Widget):
    top_left: QLabel = new("0,0", grid=(0, 0))
    top_right: QLabel = new("0,1", grid=(0, 1))
    bottom_left: QLabel = new("1,0", grid=(1, 0))
    bottom_right: QLabel = new("1,1", grid=(1, 1))
```

### Spanning Multiple Cells

Use 4-tuple `(row, col, rowspan, colspan)` to span cells:

```python
@widget(layout="grid")
class SpanningGrid(Widget):
    # Header spans 2 columns
    header: QLabel = new("Header", grid=(0, 0, 1, 2))

    # Content in next row
    left: QLabel = new("Left", grid=(1, 0))
    right: QLabel = new("Right", grid=(1, 1))
```

### With Variable Widgets

`Variable[T, W]` in grid layouts requires `grid=` in the widget kwargs:

```python
from qtpie import Variable

@widget(layout="grid")
class GridWithVariables(Widget):
    value: Variable[int, QSpinBox] = new(10)(grid=(0, 0))
    label: Variable[str, QLabel] = new("Hello")(grid=(0, 1))

widget = GridWithVariables()
```

## Special Cases for Non-QWidget Types

The special layout parameters `label=` and `grid=` are only consumed by QtPie for QWidget types. For non-QWidget types, they pass through to the constructor:

```python
class MyConfig:
    def __init__(self, label: str):
        self.label = label

@widget
class Example(Widget):
    # label= passes to MyConfig.__init__ (not a QWidget)
    config: MyConfig = new(label="Test Label")

widget = Example()
assert widget.config.label == "Test Label"
```

Similarly for `layout=` and `bind=` on non-QWidget types - they're passed to the constructor rather than being consumed by QtPie.

## Ignoring Parameters in Wrong Layout Types

Vertical and horizontal layouts silently ignore `label=` and `grid=` parameters:

```python
@widget(layout="vertical")
class IgnoredParams(Widget):
    # label= is ignored in vertical layout (no error)
    name: QLineEdit = new(label="Name")

@widget(layout="horizontal")
class IgnoredGrid(Widget):
    # grid= is ignored in horizontal layout (no error)
    name: QLineEdit = new(grid=(0, 0))
```

This allows you to add these parameters without breaking your code if you change layout types.

## Common Patterns

### Nested Layouts

Compose widgets with different layouts:

```python
@widget(layout="horizontal")
class ButtonRow(Widget):
    save: QPushButton = new("Save")
    cancel: QPushButton = new("Cancel")

@widget(layout="vertical")
class MainForm(Widget):
    title: QLabel = new("Edit User")
    buttons: ButtonRow = new()
```

### Form with Mixed Widgets

```python
@widget(layout="form")
class RegistrationForm(Widget):
    username: QLineEdit = new(label="Username")
    password: QLineEdit = new(
        label="Password",
        echoMode=QLineEdit.EchoMode.Password
    )
    age: QSpinBox = new(label="Age", minimum=0, maximum=120)
    newsletter: QCheckBox = new(label="Subscribe to newsletter")
```

### Grid-Based Calculator

```python
@widget(layout="grid")
class Calculator(Widget):
    display: QLineEdit = new(
        "0",
        grid=(0, 0, 1, 4),
        readOnly=True,
        alignment=Qt.AlignmentFlag.AlignRight
    )

    # Number pad
    btn_7: QPushButton = new("7", grid=(1, 0))
    btn_8: QPushButton = new("8", grid=(1, 1))
    btn_9: QPushButton = new("9", grid=(1, 2))
    btn_div: QPushButton = new("/", grid=(1, 3))

    btn_4: QPushButton = new("4", grid=(2, 0))
    btn_5: QPushButton = new("5", grid=(2, 1))
    btn_6: QPushButton = new("6", grid=(2, 2))
    btn_mul: QPushButton = new("*", grid=(2, 3))
```

## Summary

- QtPie supports four layout types: `vertical` (default), `horizontal`, `form`, and `grid`
- Set `layout=None` for no automatic layout
- Control margins with `margins=` (int or 4-tuple)
- Form layouts require `label=` on each field
- Grid layouts require `grid=` on each field (2-tuple for position, 4-tuple for spanning)
- Exclude widgets from layout with `layout=False` in `new()`
- Fields are added in definition order
- `Variable` fields without widget types aren't added to layouts
- Nest widgets to create complex layouts from simple building blocks
