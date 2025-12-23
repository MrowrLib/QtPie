# Styling

QtPie provides CSS-like class helpers and color scheme utilities to make styling your Qt applications cleaner and more maintainable.

## CSS Classes

Qt doesn't have native CSS classes, but QtPie uses dynamic properties to achieve similar functionality. This lets you write QSS (Qt Style Sheets) that feel more like web CSS.

### Setting Classes on Widgets

Use the `classes` parameter on `@widget` to assign CSS classes:

```python
from qtpie import widget
from qtpy.QtWidgets import QWidget

@widget(classes=["card", "shadow"])
class MyWidget(QWidget):
    pass
```

This sets a `class` property on the widget containing `["card", "shadow"]`.

### Manipulating Classes at Runtime

QtPie provides helpers to add, remove, and toggle classes dynamically:

```python
from qtpie.styles import add_class, remove_class, toggle_class, has_class

# Add a class
add_class(widget, "active")

# Remove a class
remove_class(widget, "active")

# Toggle a class (add if not present, remove if present)
toggle_class(widget, "highlighted")

# Check if widget has a class
if has_class(widget, "error"):
    print("Widget has error styling")
```

#### Additional Helpers

```python
from qtpie.styles import (
    add_classes,      # Add multiple classes at once
    get_classes,      # Get list of all classes
    set_classes,      # Replace all classes
    replace_class,    # Swap one class for another
    has_any_class,    # Check if widget has any of the given classes
)

# Add multiple classes
add_classes(widget, ["primary", "large"])

# Replace a class
replace_class(widget, "primary", "secondary")

# Check multiple classes
if has_any_class(widget, ["error", "warning"]):
    print("Widget needs attention")
```

### Using Classes in QSS

In your Qt Style Sheets, match classes using attribute selectors with the `~=` operator:

```css
/* Match any QPushButton with the "primary" class */
QPushButton[class~="primary"] {
    background-color: #007bff;
    color: white;
    border-radius: 4px;
}

/* Match labels with the "error" class */
QLabel[class~="error"] {
    color: red;
    font-weight: bold;
}

/* Combine with other selectors */
QPushButton[class~="primary"]:hover {
    background-color: #0056b3;
}
```

The `~=` operator matches if the class list contains the given value.

## Color Schemes

QtPie provides simple helpers for dark and light mode:

```python
from qtpie.styles import enable_dark_mode, enable_light_mode, set_color_scheme, ColorScheme

# Enable dark mode
enable_dark_mode()

# Enable light mode
enable_light_mode()

# Or use the enum directly
set_color_scheme(ColorScheme.Dark)
```

### How It Works

The color scheme functions work in two ways:

1. **Before app creation**: Sets environment variables that Qt will use when the app starts
2. **After app creation**: Uses Qt 6.8+ runtime API to change the scheme immediately

This means you can call these functions either before or after creating your `QApplication`:

```python
from qtpie import entrypoint, widget
from qtpie.styles import enable_dark_mode
from qtpy.QtWidgets import QWidget

# Option 1: Enable before app runs
enable_dark_mode()

@entrypoint
@widget
class MyApp(QWidget):
    pass

# Option 2: Enable after app exists
@entrypoint
@widget
class MyApp(QWidget):
    def setup(self) -> None:
        enable_dark_mode()  # Works here too
```

## SCSS Support

QtPie has built-in support for SCSS compilation and hot reload during development. This lets you write stylesheets in SCSS and have them automatically compiled to QSS.

### Quick Options

**For app-wide styles**, use `@entrypoint` with stylesheet options:

```python
from qtpie import entrypoint, widget
from qtpy.QtWidgets import QWidget

@entrypoint(stylesheet="styles.scss", watch_stylesheet=True)
@widget
class MyApp(QWidget):
    pass
```

**For component-scoped styles**, use the `@stylesheet` decorator:

```python
from qtpie import stylesheet, widget
from qtpy.QtWidgets import QWidget

@stylesheet("card.scss", watch=True)
@widget
class Card(QWidget):
    pass
```

For details on SCSS imports, file watching, and manual control, see the [SCSS Hot Reload guide](../guides/scss.md).

## Example: Themed Button Widget

Here's a complete example combining classes, runtime manipulation, and QSS:

```python
from qtpie import widget, make
from qtpie.styles import toggle_class, enable_dark_mode
from qtpy.QtWidgets import QWidget, QPushButton

@widget(classes=["themed"])
class ThemedButton(QWidget):
    button: QPushButton = make(
        QPushButton,
        "Toggle Primary",
        clicked="toggle_primary"
    )

    def setup(self) -> None:
        # Apply a stylesheet using classes
        self.setStyleSheet("""
            QPushButton[class~="primary"] {
                background-color: #007bff;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton[class~="primary"]:hover {
                background-color: #0056b3;
            }
            QPushButton {
                background-color: #e0e0e0;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)

    def toggle_primary(self) -> None:
        toggle_class(self.button, "primary")
```

## See Also

- [Windows & Menus](../guides/windows-menus.md) - Window styling
- [SCSS Hot Reload](../guides/scss.md) - Advanced styling with SCSS
- [@stylesheet Decorator](../reference/decorators/stylesheet.md) - Component-scoped styles
- [Class Helpers Reference](../reference/styles/class-helpers.md) - Complete API
- [Color Schemes Reference](../reference/styles/color-schemes.md) - Complete API
