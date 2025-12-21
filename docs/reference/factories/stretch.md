# spacer()

Add flexible space and gaps to box layouts (vertical/horizontal).

The `spacer()` factory creates `QSpacerItem` instances that push widgets apart or to specific positions in your layout.

## Basic Usage

```python
from qtpie import widget, make, spacer
from qtpy.QtWidgets import QWidget, QLabel, QSpacerItem

@widget(layout="vertical")
class MyWidget(QWidget):
    header: QLabel = make(QLabel, "Header")
    gap: QSpacerItem = spacer(1)  # Push footer to bottom
    footer: QLabel = make(QLabel, "Footer")
```

Without the spacer, both labels would be at the top. The spacer stretches to fill available space, pushing the footer to the bottom.

## Signature

```python
def spacer(
    factor: int = 0,
    *,
    min_size: int = 0,
    max_size: int = 0,
) -> QSpacerItem: ...
```

**Parameters:**

- **factor** - Stretch factor. `0` = minimal spacer, `>0` = proportional stretching
- **min_size** - Minimum size in pixels (in the layout direction)
- **max_size** - Maximum size in pixels (in the layout direction). Use `0` for unlimited

**Returns:** `QSpacerItem` (stored on the widget instance)

## When to Use

**Box layouts only** - `spacer()` only works in vertical and horizontal layouts. It's ignored in form and grid layouts.

```python
# ✅ Works in vertical layouts
@widget(layout="vertical")
class MyWidget(QWidget):
    gap: QSpacerItem = spacer(1)

# ✅ Works in horizontal layouts
@widget(layout="horizontal")
class MyWidget(QWidget):
    gap: QSpacerItem = spacer(1)

# ❌ Ignored in form layouts
@widget(layout="form")
class MyForm(QWidget):
    gap: QSpacerItem = spacer(1)  # Won't appear

# ❌ Ignored in grid layouts
@widget(layout="grid")
class MyGrid(QWidget):
    gap: QSpacerItem = spacer(1)  # Won't appear
```

## Stretch Factors

The `factor` parameter controls how space is distributed between multiple spacers.

### factor=0: Minimal Spacer

Creates a minimal spacer that takes up very little space:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    header: QLabel = make(QLabel, "Header")
    gap: QSpacerItem = spacer()  # Default factor=0
    footer: QLabel = make(QLabel, "Footer")
```

### factor=1: Full Stretch

Creates a spacer that expands to fill available space:

```python
@widget(layout="vertical")
class ToolPanel(QWidget):
    toolbar: QPushButton = make(QPushButton, "Toolbar")
    stretch: QSpacerItem = spacer(1)  # Takes all available space
    footer: QLabel = make(QLabel, "Footer")
```

This pushes the footer all the way to the bottom.

### Multiple Stretch Factors

When you have multiple spacers, the `factor` determines their relative sizes:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    spacer1: QSpacerItem = spacer(1)    # Gets 1/3 of space
    middle: QLabel = make(QLabel, "Middle")
    spacer2: QSpacerItem = spacer(2)    # Gets 2/3 of space
    bottom: QLabel = make(QLabel, "Bottom")
```

`spacer1` with factor 1 gets 1 part, `spacer2` with factor 2 gets 2 parts. So `spacer2` will be twice as tall as `spacer1`.

## Size Constraints

Control spacer size with `min_size` and `max_size`.

### Minimum Size

Create a gap of at least a certain size:

```python
@widget(layout="horizontal")
class MyWidget(QWidget):
    left: QLabel = make(QLabel, "Left")
    gap: QSpacerItem = spacer(min_size=20)  # At least 20px wide
    right: QLabel = make(QLabel, "Right")
```

In vertical layouts, `min_size` controls height. In horizontal layouts, it controls width.

### Fixed Size

Set `min_size == max_size` for an exact size:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    gap: QSpacerItem = spacer(min_size=50, max_size=50)  # Exactly 50px
    bottom: QLabel = make(QLabel, "Bottom")
```

This creates a fixed 50-pixel gap that won't shrink or expand.

### Minimum + Stretch

Combine `min_size` with a stretch `factor` for an expanding spacer with a minimum:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    gap: QSpacerItem = spacer(1, min_size=30)  # At least 30px, but can expand
    bottom: QLabel = make(QLabel, "Bottom")
```

The spacer will be at least 30 pixels but can grow to fill available space.

### Maximum Size

Limit how large a spacer can grow:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    gap: QSpacerItem = spacer(max_size=200)  # Won't exceed 200px
    bottom: QLabel = make(QLabel, "Bottom")
```

## Common Patterns

### Push to Bottom

Push content to the bottom of a vertical layout:

```python
@widget(layout="vertical")
class Dialog(QWidget):
    content: QLabel = make(QLabel, "Main content here...")
    stretch: QSpacerItem = spacer(1)
    ok_button: QPushButton = make(QPushButton, "OK")
```

### Push to Right

Push content to the right in a horizontal layout:

```python
@widget(layout="horizontal")
class Toolbar(QWidget):
    title: QLabel = make(QLabel, "Document.txt")
    stretch: QSpacerItem = spacer(1)
    close_btn: QPushButton = make(QPushButton, "X")
```

### Center Content

Use spacers on both sides to center content:

```python
@widget(layout="horizontal")
class CenteredWidget(QWidget):
    left_spacer: QSpacerItem = spacer(1)
    content: QLabel = make(QLabel, "Centered!")
    right_spacer: QSpacerItem = spacer(1)
```

### Toolbar with Grouping

Separate toolbar button groups:

```python
@widget(layout="horizontal")
class Toolbar(QWidget):
    # File operations
    new_btn: QPushButton = make(QPushButton, "New")
    open_btn: QPushButton = make(QPushButton, "Open")
    save_btn: QPushButton = make(QPushButton, "Save")

    # Visual separation
    group_gap: QSpacerItem = spacer(min_size=20)

    # Edit operations
    undo_btn: QPushButton = make(QPushButton, "Undo")
    redo_btn: QPushButton = make(QPushButton, "Redo")

    # Push settings to far right
    right_spacer: QSpacerItem = spacer(1)
    settings_btn: QPushButton = make(QPushButton, "Settings")
```

### Multiple Content Areas

Distribute space between sections:

```python
@widget(layout="vertical")
class ToolPanel(QWidget):
    toolbar: QPushButton = make(QPushButton, "Toolbar")
    spacer1: QSpacerItem = spacer(1)
    content: QLabel = make(QLabel, "Content Area")
    spacer2: QSpacerItem = spacer()  # Minimal gap
    footer: QLabel = make(QLabel, "Status: Ready")
```

## Accessing Spacers

Spacer fields are stored on the widget instance as `QSpacerItem` objects:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    header: QLabel = make(QLabel, "Header")
    gap: QSpacerItem = spacer(1)
    footer: QLabel = make(QLabel, "Footer")

widget = MyWidget()
print(type(widget.gap))  # <class 'qtpy.QtWidgets.QSpacerItem'>
```

You can access spacer properties but rarely need to modify them:

```python
# Get size hint
height = widget.gap.sizeHint().height()

# Get size policy
policy = widget.gap.sizePolicy()
```

## Field Ordering

Spacers respect field declaration order like any other widget field:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    first: QLabel = make(QLabel, "1")    # Top
    spacer1: QSpacerItem = spacer(1)      # Space
    second: QLabel = make(QLabel, "2")    # Middle
    spacer2: QSpacerItem = spacer(1)      # Space
    third: QLabel = make(QLabel, "3")     # Bottom
```

The labels are evenly distributed with equal spacing between them.

## Private Fields

Don't use underscore prefix for spacer fields - they'll be completely ignored:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    header: QLabel = make(QLabel, "Header")
    _gap: QSpacerItem = spacer(1)  # ❌ Won't work! Underscores are ignored
    footer: QLabel = make(QLabel, "Footer")
```

Use a regular field name:

```python
@widget(layout="vertical")
class MyWidget(QWidget):
    header: QLabel = make(QLabel, "Header")
    gap: QSpacerItem = spacer(1)  # ✅ Works
    footer: QLabel = make(QLabel, "Footer")
```

## How It Works

Under the hood, `spacer()` creates a dataclass field with metadata:

```python
# What spacer() returns
field(init=False, default=None, metadata={
    "qtpie_spacer": SpacerConfig(factor=1, min_size=0, max_size=0)
})
```

The `@widget` decorator:
1. Detects fields with spacer metadata
2. Creates the `QSpacerItem` with the right size policy
3. Adds it to the box layout with the specified stretch factor
4. Stores the spacer instance on the widget

The size policy is determined by the parameters:
- `min_size == max_size` → `Fixed` policy
- `max_size > 0` → `Maximum` policy
- `factor > 0` → `Expanding` policy
- Otherwise → `Minimum` policy

## Limitations

**Box layouts only** - Spacers are only processed in vertical and horizontal layouts. They're silently ignored in:
- Form layouts (`layout="form"`)
- Grid layouts (`layout="grid"`)
- No layout (`layout="none"`)

For grid layouts, use empty grid cells or column/row stretch factors instead.

## See Also

- [Layouts](../../basics/layouts.md) - Layout types and field ordering
- [Widgets](../../basics/widgets.md) - The `@widget` decorator
- [make()](make.md) - Widget factory function
