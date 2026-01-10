# Widgets

Widgets are the building blocks of QtPie applications. The `@widget` decorator transforms a class into a declarative Qt widget.

## Basic Widget

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click Me")
```

That's it! Fields become widgets, automatically added to a vertical layout.

## The @widget Decorator

Every Widget subclass **must** use the `@widget` decorator:

```python
@widget
class MyWidget(Widget):
    ...
```

Without it, instantiation raises `TypeError`.

## Field Declaration with new()

Use `new()` to declare widget fields:

```python
@widget
class MyWidget(Widget):
    # Positional args go to widget constructor
    _label: QLabel = new("Hello World")

    # Keyword args become setXXX() calls
    _styled: QLabel = new("Red text", styleSheet="color: red;")

    # Multiple properties
    _fancy: QLabel = new("Fancy", toolTip="A tooltip", enabled=False)
```

## Layouts

### Default: Vertical

```python
@widget
class MyWidget(Widget):
    _a: QLabel = new("First")
    _b: QLabel = new("Second")
    _c: QLabel = new("Third")
# Stacked vertically
```

### Horizontal

```python
@widget(layout="horizontal")
class MyWidget(Widget):
    _a: QLabel = new("Left")
    _b: QLabel = new("Right")
```

### No Layout

```python
@widget(layout=None)
class MyWidget(Widget):
    _label: QLabel = new("Manual positioning")
```

### Layout Margins

```python
# All sides
@widget(margins=10)
class MyWidget(Widget):
    ...

# Individual: (left, top, right, bottom)
@widget(margins=(5, 10, 5, 10))
class MyWidget(Widget):
    ...
```

## Excluding Widgets from Layout

Use `layout=False` to create a widget without adding it to the layout:

```python
@widget
class MyWidget(Widget):
    _visible: QLabel = new("In layout")
    _floating: QLabel = new("Not in layout", layout=False)
    _also_visible: QLabel = new("In layout")
```

## Signal Connections

Connect signals declaratively:

```python
@widget
class MyWidget(Widget):
    # Connect to method by name
    _button: QPushButton = new("Click", clicked="on_click")

    # Connect to lambda
    _other: QPushButton = new("Other", clicked=lambda: print("clicked"))

    def on_click(self) -> None:
        print("Button clicked!")
```

### Multiple Signals

```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new(
        "Press Me",
        pressed=lambda: print("pressed"),
        released=lambda: print("released"),
    )
```

### Signal Forwarding

Forward widget signals to custom signals for component communication:

```python
from PySide6.QtCore import Signal

@widget
class Counter(Widget):
    # Custom signal
    increment_requested = Signal()

    # Forward button click to custom signal
    _button: QPushButton = new("+", clicked="increment_requested")

@widget
class App(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")

    # Connect child's custom signal to parent method
    counter: Counter = new(increment_requested="_on_increment")

    def _on_increment(self) -> None:
        self._count += 1
```

Signal arguments are forwarded automatically:

```python
@widget
class MyWidget(Widget):
    value_changed = Signal(int)
    _slider: QSlider = new(valueChanged="value_changed")

# slider.valueChanged(42) → value_changed(42)
```

Signals with fewer parameters ignore extra arguments:

```python
@widget
class MyWidget(Widget):
    # clicked emits bool, but our signal takes no args
    simple_clicked = Signal()
    _button: QPushButton = new("Click", clicked="simple_clicked")
```

## Widget Properties

Set properties via decorator kwargs:

```python
@widget(windowTitle="My Window")
class MyWidget(Widget):
    ...

@widget(title="My Window")  # 'title' is an alias for 'windowTitle'
class MyWidget(Widget):
    ...

@widget(minimumWidth=400, minimumHeight=300)
class MyWidget(Widget):
    ...
```

### Property Aliases

| Alias | Qt Property |
|-------|-------------|
| `title` | `windowTitle` |
| `stylesheet` | `styleSheet` |

```python
@widget(stylesheet="background: yellow;")
class MyWidget(Widget):
    ...
```

## The __setup__ Hook

Override `__setup__()` for initialization after all fields are created:

```python
@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello")

    def __setup__(self) -> None:
        # Layout is ready, all widgets exist
        self._label.setText("Modified in setup")
```

## Non-Widget Fields

You can declare non-QWidget fields too:

```python
class Config:
    def __init__(self, name: str = "default") -> None:
        self.name = name

@widget
class MyWidget(Widget):
    _config: Config = new(name="custom")
    _label: QLabel = new("Hello")
```

## Variable Fields

`Variable[T]` fields hold reactive state (not added to layout):

```python
from qtpie import Variable

@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")

    def increment(self) -> None:
        self._count += 1  # UI updates automatically
```

See [Variables](../state/variables.md) for details.

## Nested Widgets

Compose widgets by including them as fields:

```python
@widget
class Header(Widget):
    _title: QLabel = new("Title")

@widget
class Footer(Widget):
    _copyright: QLabel = new("2024")

@widget
class Page(Widget):
    _header: Header = new()
    _content: QLabel = new("Content goes here")
    _footer: Footer = new()
```

## Required Bindings with ref()

Use `ref()` for expressions that reference parent-bound fields:

```python
from dataclasses import dataclass
from qtpie import ref

@dataclass
class Dog:
    name: str = ""

@widget
class DogDisplay(Widget):
    dog: Variable[Dog]  # Required - no default
    _label: QLabel = new(text=ref("Dog: {dog.name}"))

@widget(record=Dog("Rover"))
class ParentWidget(Widget[Dog]):
    _display: DogDisplay = new(dog="record")  # Bind dog to record
```

## See Also

- [Variables](../state/variables.md) - Reactive state
- [Bindings](../state/bindings.md) - Data binding patterns
- [App & Entry Points](../guides/app.md) - Building applications
