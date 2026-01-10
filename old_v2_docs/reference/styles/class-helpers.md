# CSS Class Helpers

CSS-like class management for Qt widgets using dynamic properties and QSS attribute selectors.

## Overview

Qt doesn't have native CSS classes, but QtPie provides helpers that use dynamic properties to achieve similar functionality. Classes are stored as a list of strings in the widget's `"class"` property and can be matched in QSS using attribute selectors.

## Usage in QSS

Match classes using the `~=` attribute selector:

```css
/* Match widgets with "primary" class */
QPushButton[class~="primary"] {
    background-color: #007bff;
    color: white;
}

/* Match widgets with "error" class */
QLabel[class~="error"] {
    color: #dc3545;
    font-weight: bold;
}

/* Match widgets with "disabled" class */
QWidget[class~="disabled"] {
    opacity: 0.5;
}
```

## get_classes()

```python
def get_classes(widget: QObject) -> list[str]
```

Get the list of CSS classes on a widget.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to query |

### Returns

List of class names. Returns empty list if no classes are set.

### Examples

```python
from qtpie.styles import get_classes, set_classes

widget = QWidget()
set_classes(widget, ["primary", "active"])

classes = get_classes(widget)
print(classes)  # ["primary", "active"]

# Empty widget returns empty list
empty_widget = QWidget()
print(get_classes(empty_widget))  # []
```

## set_classes()

```python
def set_classes(widget: QObject, classes: list[str], *, refresh: bool = True) -> None
```

Set the CSS classes on a widget, replacing any existing classes.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to modify |
| `classes` | `list[str]` | List of class names to set |
| `refresh` | `bool` | Whether to refresh styles (default: `True`) |

### Style Refresh

When `refresh=True` (default), the function triggers Qt's unpolish/polish cycle to reapply stylesheets. Set `refresh=False` to defer style updates (useful when making multiple changes).

### Examples

```python
from qtpie.styles import set_classes

# Set classes with automatic style refresh
widget = QPushButton("Click Me")
set_classes(widget, ["primary", "large"])

# Set without refresh (for performance)
set_classes(widget, ["primary", "large"], refresh=False)

# Replace all classes
set_classes(widget, ["secondary"])  # Removes "primary" and "large"
```

## add_class()

```python
def add_class(widget: QObject, class_name: str) -> None
```

Add a single CSS class to a widget. No-op if the class is already present.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to modify |
| `class_name` | `str` | Class name to add |

### Examples

```python
from qtpie.styles import add_class, get_classes

button = QPushButton("Submit")
add_class(button, "primary")
print(get_classes(button))  # ["primary"]

# Adding again does nothing
add_class(button, "primary")
print(get_classes(button))  # ["primary"] (not duplicated)

# Add another class
add_class(button, "large")
print(get_classes(button))  # ["primary", "large"]
```

## add_classes()

```python
def add_classes(widget: QObject, class_names: list[str]) -> None
```

Add multiple CSS classes to a widget. Skips classes that are already present.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to modify |
| `class_names` | `list[str]` | List of class names to add |

### Examples

```python
from qtpie.styles import add_classes, get_classes

label = QLabel("Status")
add_classes(label, ["info", "bordered"])
print(get_classes(label))  # ["info", "bordered"]

# Add overlapping classes (no duplicates)
add_classes(label, ["bordered", "rounded"])
print(get_classes(label))  # ["info", "bordered", "rounded"]
```

## has_class()

```python
def has_class(widget: QObject, class_name: str) -> bool
```

Check if a widget has a specific CSS class.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to check |
| `class_name` | `str` | Class name to check for |

### Returns

`True` if the widget has the class, `False` otherwise.

### Examples

```python
from qtpie.styles import add_class, has_class

button = QPushButton("Click")
add_class(button, "primary")

if has_class(button, "primary"):
    print("Button is primary")  # Prints

if has_class(button, "secondary"):
    print("Button is secondary")  # Doesn't print
```

## has_any_class()

```python
def has_any_class(widget: QObject, class_names: list[str]) -> bool
```

Check if a widget has any of the given CSS classes.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to check |
| `class_names` | `list[str]` | List of class names to check for |

### Returns

`True` if the widget has at least one of the classes, `False` otherwise.

### Examples

```python
from qtpie.styles import set_classes, has_any_class

widget = QWidget()
set_classes(widget, ["active", "selected"])

# Check for multiple classes
if has_any_class(widget, ["active", "disabled"]):
    print("Widget is active or disabled")  # Prints (has "active")

if has_any_class(widget, ["disabled", "hidden"]):
    print("Widget is disabled or hidden")  # Doesn't print
```

## remove_class()

```python
def remove_class(widget: QObject, class_name: str) -> None
```

Remove a CSS class from a widget. No-op if the class is not present.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to modify |
| `class_name` | `str` | Class name to remove |

### Examples

```python
from qtpie.styles import set_classes, remove_class, get_classes

button = QPushButton("Submit")
set_classes(button, ["primary", "large"])

remove_class(button, "large")
print(get_classes(button))  # ["primary"]

# Removing non-existent class does nothing
remove_class(button, "tiny")
print(get_classes(button))  # ["primary"] (unchanged)
```

## replace_class()

```python
def replace_class(widget: QObject, old_class: str, new_class: str) -> None
```

Replace one CSS class with another, preserving class order. No-op if the old class is not present.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to modify |
| `old_class` | `str` | Class name to replace |
| `new_class` | `str` | Class name to replace with |

### Examples

```python
from qtpie.styles import set_classes, replace_class, get_classes

button = QPushButton("Toggle")
set_classes(button, ["primary", "small"])

replace_class(button, "primary", "secondary")
print(get_classes(button))  # ["secondary", "small"]

# Replacing non-existent class does nothing
replace_class(button, "large", "tiny")
print(get_classes(button))  # ["secondary", "small"] (unchanged)
```

## toggle_class()

```python
def toggle_class(widget: QObject, class_name: str) -> None
```

Toggle a CSS class on a widget. Adds the class if not present, removes it if present.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widget` | `QObject` | The widget to modify |
| `class_name` | `str` | Class name to toggle |

### Examples

```python
from qtpie.styles import toggle_class, get_classes

button = QPushButton("Toggle")

toggle_class(button, "active")
print(get_classes(button))  # ["active"]

toggle_class(button, "active")
print(get_classes(button))  # [] (removed)

# Toggle multiple times
toggle_class(button, "selected")
toggle_class(button, "active")
print(get_classes(button))  # ["selected", "active"]
```

## Complete Example

```python
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from qtpie.styles import add_class, has_class, remove_class, toggle_class

# Define QSS styles
stylesheet = """
QPushButton[class~="primary"] {
    background-color: #007bff;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton[class~="danger"] {
    background-color: #dc3545;
    color: white;
}

QPushButton[class~="large"] {
    font-size: 16px;
    padding: 12px 24px;
}

QPushButton[class~="disabled"] {
    opacity: 0.5;
}
"""

class StyledButtons(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Primary button
        self.primary_btn = QPushButton("Primary")
        add_class(self.primary_btn, "primary")
        layout.addWidget(self.primary_btn)

        # Danger button with large size
        self.danger_btn = QPushButton("Delete")
        add_class(self.danger_btn, "danger")
        add_class(self.danger_btn, "large")
        layout.addWidget(self.danger_btn)

        # Toggle button
        self.toggle_btn = QPushButton("Toggle Disabled")
        add_class(self.toggle_btn, "primary")
        self.toggle_btn.clicked.connect(self.on_toggle)
        layout.addWidget(self.toggle_btn)

    def on_toggle(self):
        toggle_class(self.toggle_btn, "disabled")
        is_disabled = has_class(self.toggle_btn, "disabled")
        self.toggle_btn.setEnabled(not is_disabled)

app = QApplication([])
app.setStyleSheet(stylesheet)

window = StyledButtons()
window.show()
app.exec()
```

## Notes

- Classes are stored in the `"class"` dynamic property as a `list[str]`
- By default, modifying classes triggers Qt's unpolish/polish cycle to refresh styles
- Use `refresh=False` in `set_classes()` when making multiple updates for better performance
- The `~=` QSS selector matches any widget where the class list contains the specified value
- Class names are case-sensitive
- All functions work with any `QObject`, not just `QWidget`
