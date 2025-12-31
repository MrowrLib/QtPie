# Color Schemes

Control your application's color scheme (dark mode / light mode) with simple functions.

## Overview

QtPie provides three functions for managing color schemes:

- `enable_dark_mode()` - Switch to dark mode
- `enable_light_mode()` - Switch to light mode
- `set_color_scheme()` - Set a specific scheme using the `ColorScheme` enum

These functions work whether you call them before or after creating your `QApplication` instance.

## Basic Usage

### Standalone Functions

```python
from qtpie import enable_dark_mode, enable_light_mode

# Enable dark mode
enable_dark_mode()

# Enable light mode
enable_light_mode()
```

### Using the Enum

```python
from qtpie import set_color_scheme, ColorScheme

# Set dark mode
set_color_scheme(ColorScheme.Dark)

# Set light mode
set_color_scheme(ColorScheme.Light)
```

## How It Works

The color scheme functions automatically detect whether a `QApplication` instance exists:

**If an app exists** (you've already created `QApplication` or `App`):
- Uses Qt 6.8+ runtime API to change the scheme immediately
- Changes take effect without restarting

**If no app exists yet**:
- Sets environment variables (`QT_QPA_PLATFORM`)
- The scheme will be applied when the app is created

This means you can call these functions anywhere in your code and they'll do the right thing.

## With the App Class

The `App` class provides convenience parameters and methods:

### Via Constructor

```python
from qtpie import App

# Create app with dark mode
app = App(
    name="MyApp",
    version="1.0",
    dark_mode=True,
)

# Or light mode
app = App(
    name="MyApp",
    version="1.0",
    light_mode=True,
)
```

### Via Methods

```python
from qtpie import App

app = App(name="MyApp", version="1.0")

# Switch to dark mode
app.enable_dark_mode()

# Switch to light mode
app.enable_light_mode()
```

## Runtime Switching

You can change the color scheme at any time, even after your app is running:

```python
from qtpie import widget, make, enable_dark_mode, enable_light_mode
from qtpy.QtWidgets import QWidget, QPushButton

@widget
class ThemeSwitcher(QWidget):
    dark_button: QPushButton = make(QPushButton, "Dark Mode", clicked="switch_dark")
    light_button: QPushButton = make(QPushButton, "Light Mode", clicked="switch_light")

    def switch_dark(self) -> None:
        enable_dark_mode()

    def switch_light(self) -> None:
        enable_light_mode()
```

## Complete Example

```python
from qtpie import entrypoint, widget, make, enable_dark_mode, enable_light_mode
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@entrypoint
@widget
class ThemeDemo(QWidget):
    label: QLabel = make(QLabel, "Choose your theme")
    dark_btn: QPushButton = make(QPushButton, "Dark Mode", clicked="go_dark")
    light_btn: QPushButton = make(QPushButton, "Light Mode", clicked="go_light")

    def go_dark(self) -> None:
        enable_dark_mode()
        self.label.setText("Dark mode enabled!")

    def go_light(self) -> None:
        enable_light_mode()
        self.label.setText("Light mode enabled!")
```

## API Reference

### `enable_dark_mode(app=None)`

Enable dark mode color scheme.

**Parameters:**
- `app` (optional): `QGuiApplication` instance. If `None`, uses `QApplication.instance()`

**Example:**
```python
from qtpie import enable_dark_mode

enable_dark_mode()
```

### `enable_light_mode(app=None)`

Enable light mode color scheme.

**Parameters:**
- `app` (optional): `QGuiApplication` instance. If `None`, uses `QApplication.instance()`

**Example:**
```python
from qtpie import enable_light_mode

enable_light_mode()
```

### `set_color_scheme(scheme, app=None)`

Set a specific color scheme.

**Parameters:**
- `scheme`: `ColorScheme.Dark` or `ColorScheme.Light`
- `app` (optional): `QGuiApplication` instance. If `None`, uses `QApplication.instance()`

**Example:**
```python
from qtpie import set_color_scheme, ColorScheme

set_color_scheme(ColorScheme.Dark)
```

### `ColorScheme`

Enum with two values:
- `ColorScheme.Dark` - Dark color scheme
- `ColorScheme.Light` - Light color scheme

## See Also

- [Class Helpers](class-helpers.md) - Add/remove CSS classes dynamically
- [App Class](../app/app.md) - App-level color scheme methods
- [Styling](../../basics/styling.md) - CSS and styling basics
