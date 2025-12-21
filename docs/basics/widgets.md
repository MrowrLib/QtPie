# Widgets

The `@widget` decorator and `make()` factory are the foundation of QtPie. They transform verbose Qt code into clean, declarative definitions.

## The `@widget` Decorator

The `@widget` decorator turns a class into a fully-functional Qt widget with automatic layout and lifecycle management.

### Basic Usage

```python
from qtpie import widget
from qtpy.QtWidgets import QWidget

@widget
class MyWidget(QWidget):
    pass
```

This creates a widget with:
- A vertical layout (default)
- An auto-generated object name ("My" - derived from class name)
- Automatic initialization (no `__init__` needed)

### With or Without Parentheses

Both forms work:

```python
@widget
class MyWidget(QWidget):
    pass

@widget()
class MyWidget(QWidget):
    pass
```

Use parentheses when you need to pass parameters.

## Declaring Child Widgets

Child widgets are declared as typed fields. QtPie automatically adds them to the layout in declaration order.

### Using `make()`

The `make()` factory provides clean syntax for creating widgets:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello World")
    button: QPushButton = make(QPushButton, "Click Me")
```

This is much cleaner than the traditional approach:

```python
# Traditional Qt - verbose!
from dataclasses import field

@widget()
class MyWidget(QWidget):
    label: QLabel = field(default_factory=lambda: QLabel("Hello World"))
    button: QPushButton = field(default_factory=lambda: QPushButton("Click Me"))
```

### Constructor Arguments

Pass any arguments the widget's constructor accepts:

```python
from qtpy.QtWidgets import QLineEdit, QSlider
from qtpy.QtCore import Qt

@widget
class MyWidget(QWidget):
    # Positional args
    label: QLabel = make(QLabel, "Initial Text")

    # Keyword args for properties
    edit: QLineEdit = make(QLineEdit, placeholderText="Enter name")

    # Multiple args
    slider: QSlider = make(QSlider, Qt.Orientation.Horizontal)
```

Any keyword argument that isn't a signal name is set as a property on the widget.

## Signal Connections

Connect signals right in the `make()` call - no separate wiring needed.

### Method Name (String)

```python
@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click", clicked="on_click")
    click_count: int = 0

    def on_click(self):
        self.click_count += 1
```

The string `"on_click"` tells QtPie to connect the `clicked` signal to the `on_click` method.

### Lambda or Callable

```python
@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click", clicked=lambda: print("Clicked!"))
```

### Multiple Signals

```python
from qtpy.QtWidgets import QSlider

@widget
class MyWidget(QWidget):
    slider: QSlider = make(
        QSlider,
        valueChanged="on_value_changed",
        sliderReleased="on_released"
    )

    def on_value_changed(self, value: int):
        print(f"Value: {value}")

    def on_released(self):
        print("Released!")
```

## Layout Types

Control the layout with the `layout` parameter.

### Vertical (Default)

```python
@widget  # or @widget(layout="vertical")
class MyWidget(QWidget):
    first: QLabel = make(QLabel, "Top")
    second: QLabel = make(QLabel, "Bottom")
```

Widgets stack top-to-bottom.

### Horizontal

```python
@widget(layout="horizontal")
class MyWidget(QWidget):
    left: QLabel = make(QLabel, "Left")
    right: QLabel = make(QLabel, "Right")
```

Widgets flow left-to-right.

### No Layout

```python
@widget(layout="none")
class MyWidget(QWidget):
    pass
```

No layout is created. Useful when you need manual layout control.

## Widget Naming

The `name` parameter sets the widget's `objectName` (used for QSS styling).

### Auto-Generated Name

```python
@widget
class CounterWidget(QWidget):
    pass

# objectName will be "Counter" (strips "Widget" suffix)
```

```python
@widget
class Editor(QWidget):
    pass

# objectName will be "Editor" (no suffix to strip)
```

### Explicit Name

```python
@widget(name="MyCustomName")
class MyWidget(QWidget):
    pass

# objectName will be "MyCustomName"
```

## CSS Classes

The `classes` parameter adds CSS-like classes for styling.

```python
@widget(classes=["card", "shadow"])
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Styled!")
```

This sets a `class` property on the widget that can be used in QSS selectors. See the [Styling](styling.md) guide for details.

## Private Fields

Fields starting with `_` are not added to the layout:

```python
@widget
class MyWidget(QWidget):
    public: QLabel = make(QLabel, "Visible")
    _hidden: QLabel = make(QLabel, "Not in layout")
```

Only `public` will be added to the layout. `_hidden` still exists as an attribute but you control its placement.

## Non-Widget Fields

You can mix widget and non-widget fields:

```python
@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Count: 0")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    # Non-widget fields
    count: int = 0
    name: str = "Counter"

    def increment(self):
        self.count += 1
        self.label.setText(f"Count: {self.count}")
```

Only the `QLabel` and `QPushButton` are added to the layout. The `int` and `str` fields are just regular attributes.

## Lifecycle Hooks

Override these methods to hook into the widget lifecycle:

```python
from typing import override
from qtpy.QtWidgets import QLayout

@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Initial")

    @override
    def setup(self):
        # Called first - after fields initialized, before layout
        self.label.setText("Modified in setup")

    @override
    def setup_values(self):
        # Called after setup - for initializing data
        pass

    @override
    def setup_bindings(self):
        # Called after setup_values - for manual data bindings
        pass

    @override
    def setup_layout(self, layout: QLayout):
        # Called after widgets added to layout
        # NOT called if layout="none"
        pass

    @override
    def setup_styles(self):
        # Called after layout - for styling
        pass

    @override
    def setup_events(self):
        # Called after styles - for event filters
        pass

    @override
    def setup_signals(self):
        # Called last - for additional signal connections
        pass
```

The hooks are called in this order:
1. `setup()`
2. `setup_values()`
3. `setup_bindings()`
4. `setup_layout()` (if layout exists)
5. `setup_styles()`
6. `setup_events()`
7. `setup_signals()`

Most of the time, you only need `setup()`.

## Accessing Child Widgets

All child widgets are available as typed attributes:

```python
@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")
    button: QPushButton = make(QPushButton, "Click", clicked="on_click")

    def on_click(self):
        # Access child widgets directly
        current = self.label.text()
        self.label.setText(f"{current}!")
```

The `self.label` and `self.button` attributes are fully typed - your IDE will autocomplete their methods.

## Complete Example

Here's a working counter widget that demonstrates many features:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@widget(name="Counter", classes=["card"])
class CounterWidget(QWidget):
    label: QLabel = make(QLabel, "Count: 0")
    increment_btn: QPushButton = make(QPushButton, "+1", clicked="increment")
    decrement_btn: QPushButton = make(QPushButton, "-1", clicked="decrement")
    reset_btn: QPushButton = make(QPushButton, "Reset", clicked="reset")

    count: int = 0

    def increment(self):
        self.count += 1
        self._update_display()

    def decrement(self):
        self.count -= 1
        self._update_display()

    def reset(self):
        self.count = 0
        self._update_display()

    def _update_display(self):
        self.label.setText(f"Count: {self.count}")
```

## What's Next?

- Learn about [Layouts](layouts.md) - form, grid, and nested layouts
- Explore [Signals](signals.md) - advanced signal patterns
- Add [Styling](styling.md) - CSS classes and SCSS

For reactive data binding that eliminates manual updates, see [Reactive State](../data/state.md).
