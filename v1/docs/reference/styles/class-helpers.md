# Class Helpers

CSS-like class helpers for Qt widgets.

Qt doesn't have native CSS classes, but QtPie provides class helpers that use dynamic properties to achieve similar functionality. These helpers manage a `"class"` property as a list of strings and handle the unpolish/polish dance to refresh styles automatically.

## Quick Example

```python
from qtpie.styles import add_class, remove_class, toggle_class, has_class
from qtpy.QtWidgets import QPushButton

button = QPushButton("Click me")

# Add a class
add_class(button, "primary")

# Toggle a class (useful for states)
toggle_class(button, "active")

# Check for a class
if has_class(button, "primary"):
    print("This is a primary button!")

# Remove a class
remove_class(button, "active")
```

In your QSS/stylesheets, match classes using attribute selectors:

```css
QPushButton[class~="primary"] {
    background-color: #007bff;
    color: white;
}

QPushButton[class~="active"] {
    border: 2px solid gold;
}

QLabel[class~="error"] {
    color: red;
    font-weight: bold;
}
```

## Core Functions

### `add_class(widget, class_name)`

Adds a CSS class to a widget. No-op if the class is already present (won't duplicate).

```python
from qtpie.styles import add_class
from qtpy.QtWidgets import QLabel

label = QLabel("Warning!")
add_class(label, "warning")
add_class(label, "warning")  # No duplicate - still just one "warning" class
```

### `remove_class(widget, class_name)`

Removes a CSS class from a widget. No-op if the class is not present.

```python
from qtpie.styles import remove_class
from qtpy.QtWidgets import QPushButton

button = QPushButton("Submit")
add_class(button, "disabled")
remove_class(button, "disabled")  # Class is gone
remove_class(button, "disabled")  # No error - just does nothing
```

### `toggle_class(widget, class_name)`

Toggles a CSS class on a widget. Adds it if not present, removes it if present.

```python
from qtpie.styles import toggle_class
from qtpy.QtWidgets import QCheckBox

checkbox = QCheckBox("Enable feature")

# First toggle - adds the class
toggle_class(checkbox, "checked")

# Second toggle - removes the class
toggle_class(checkbox, "checked")
```

### `has_class(widget, class_name)`

Returns `True` if the widget has the specified class, `False` otherwise.

```python
from qtpie.styles import has_class, add_class
from qtpy.QtWidgets import QWidget

widget = QWidget()
add_class(widget, "active")

if has_class(widget, "active"):
    print("Widget is active!")  # This will print

if has_class(widget, "inactive"):
    print("Widget is inactive!")  # This won't print
```

## Bulk Operations

### `add_classes(widget, class_names)`

Adds multiple CSS classes at once. More efficient than calling `add_class()` multiple times.

```python
from qtpie.styles import add_classes
from qtpy.QtWidgets import QWidget

widget = QWidget()
add_classes(widget, ["card", "shadow", "rounded"])
```

### `has_any_class(widget, class_names)`

Returns `True` if the widget has any of the specified classes.

```python
from qtpie.styles import has_any_class, add_class
from qtpy.QtWidgets import QWidget

widget = QWidget()
add_class(widget, "primary")

if has_any_class(widget, ["primary", "secondary"]):
    print("Widget has a priority class!")  # This will print
```

### `replace_class(widget, old_class, new_class)`

Replaces one class with another in-place. Preserves the position in the class list. No-op if the old class is not present.

```python
from qtpie.styles import replace_class, add_classes, get_classes
from qtpy.QtWidgets import QWidget

widget = QWidget()
add_classes(widget, ["foo", "bar"])

replace_class(widget, "foo", "baz")

print(get_classes(widget))  # ["baz", "bar"] - order preserved
```

## Low-Level Functions

### `get_classes(widget)`

Returns the list of CSS classes on a widget. Returns an empty list if no classes are set.

```python
from qtpie.styles import get_classes, add_classes
from qtpy.QtWidgets import QWidget

widget = QWidget()
print(get_classes(widget))  # []

add_classes(widget, ["foo", "bar"])
print(get_classes(widget))  # ["foo", "bar"]
```

### `set_classes(widget, classes, *, refresh=True)`

Sets the CSS classes on a widget, replacing any existing classes. Optionally refreshes styles (default: `True`).

```python
from qtpie.styles import set_classes
from qtpy.QtWidgets import QWidget

widget = QWidget()
set_classes(widget, ["foo", "bar"])

# Replace all classes
set_classes(widget, ["baz", "qux"])

# Set classes without triggering a style refresh (rare)
set_classes(widget, ["new"], refresh=False)
```

## Practical Examples

### Dynamic Button States

```python
from qtpie import widget, make
from qtpie.styles import add_class, toggle_class
from qtpy.QtWidgets import QPushButton, QWidget

@widget
class DynamicButton(QWidget):
    button: QPushButton = make(QPushButton, "Toggle", clicked="on_toggle")
    active: bool = False

    def setup(self) -> None:
        add_class(self.button, "toggle-button")

    def on_toggle(self) -> None:
        self.active = not self.active
        toggle_class(self.button, "active")
```

Stylesheet:
```css
QPushButton[class~="toggle-button"] {
    background-color: #ccc;
}

QPushButton[class~="toggle-button"][class~="active"] {
    background-color: #4CAF50;
    color: white;
}
```

### Form Validation Feedback

```python
from qtpie import widget, make
from qtpie.styles import add_class, remove_class
from qtpy.QtWidgets import QLineEdit, QWidget

@widget
class EmailInput(QWidget):
    email: QLineEdit = make(QLineEdit, textChanged="validate")

    def validate(self) -> None:
        text = self.email.text()
        is_valid = "@" in text and "." in text

        if is_valid:
            remove_class(self.email, "error")
            add_class(self.email, "valid")
        else:
            remove_class(self.email, "valid")
            add_class(self.email, "error")
```

Stylesheet:
```css
QLineEdit[class~="error"] {
    border: 2px solid #f44336;
    background-color: #ffebee;
}

QLineEdit[class~="valid"] {
    border: 2px solid #4CAF50;
    background-color: #e8f5e9;
}
```

### Multiple State Classes

```python
from qtpie import widget, make
from qtpie.styles import add_classes, replace_class
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@widget
class StatusIndicator(QWidget):
    status_label: QLabel = make(QLabel, "Idle")
    start_button: QPushButton = make(QPushButton, "Start", clicked="start_process")

    def setup(self) -> None:
        add_classes(self.status_label, ["status", "idle"])

    def start_process(self) -> None:
        replace_class(self.status_label, "idle", "processing")
        self.status_label.setText("Processing...")

    def complete_process(self) -> None:
        replace_class(self.status_label, "processing", "complete")
        self.status_label.setText("Complete!")
```

Stylesheet:
```css
QLabel[class~="status"] {
    padding: 8px;
    border-radius: 4px;
    font-weight: bold;
}

QLabel[class~="idle"] {
    background-color: #e0e0e0;
    color: #666;
}

QLabel[class~="processing"] {
    background-color: #fff3cd;
    color: #856404;
}

QLabel[class~="complete"] {
    background-color: #d4edda;
    color: #155724;
}
```

## How It Works

Under the hood, class helpers:

1. Store classes as a dynamic property named `"class"` with a list value
2. Use Qt's attribute selector syntax: `Widget[class~="name"]`
3. Trigger style refresh by calling `unpolish()` then `polish()` on the widget
4. Prevent duplicates automatically

This means you can use CSS-like patterns in Qt without losing type safety or performance.

## See Also

- [Styling Basics](../../basics/styling.md) - Introduction to styling in QtPie
- [@widget decorator](../decorators/widget.md) - The `classes=[]` parameter
- [Color Schemes](./color-schemes.md) - Dark mode and color scheme helpers
