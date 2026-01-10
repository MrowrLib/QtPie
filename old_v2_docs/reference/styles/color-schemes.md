# Color Schemes

Control your application's color scheme (dark/light mode) with QtPie's color scheme helpers.

## Overview

QtPie provides a simple API for managing color schemes in Qt applications. The system handles both scenarios:

- **Before QApplication exists**: Sets environment variables (Windows) or stores the preference for later application
- **After QApplication exists**: Uses Qt 6.8+ runtime API to switch schemes dynamically

## ColorScheme Enum

```python
from qtpie.styles import ColorScheme

class ColorScheme(Enum):
    Dark = "dark"
    Light = "light"
```

Enum representing available color schemes.

### Values

- `ColorScheme.Dark` - Dark color scheme
- `ColorScheme.Light` - Light color scheme

## set_color_scheme()

```python
def set_color_scheme(
    scheme: ColorScheme,
    app: QGuiApplication | None = None,
) -> None
```

Set the application color scheme.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `scheme` | `ColorScheme` | The color scheme to apply (Dark or Light) |
| `app` | `QGuiApplication \| None` | Optional app instance. If None, uses `QApplication.instance()` |

### Behavior

**When QApplication exists:**
- Uses Qt 6.8+ `styleHints().setColorScheme()` API
- Changes apply immediately to the running application

**When no QApplication exists:**
- **Windows**: Sets `QT_QPA_PLATFORM` environment variable (`windows:darkmode=2` for dark, `windows:darkmode=0` for light)
- **macOS/Linux**: Stores preference and applies it when `QApplication` is created

### Examples

```python
from qtpie.styles import ColorScheme, set_color_scheme

# Set before app creation (recommended)
set_color_scheme(ColorScheme.Dark)
app = QApplication([])

# Set on existing app
app = QApplication([])
set_color_scheme(ColorScheme.Dark, app)

# Set using instance lookup
app = QApplication([])
set_color_scheme(ColorScheme.Light)  # Finds app automatically
```

## enable_dark_mode()

```python
def enable_dark_mode(app: QGuiApplication | None = None) -> None
```

Convenience function to enable dark mode. Equivalent to `set_color_scheme(ColorScheme.Dark, app)`.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | `QGuiApplication \| None` | Optional app instance. If None, uses `QApplication.instance()` |

### Examples

```python
from qtpie.styles import enable_dark_mode

# Before app creation
enable_dark_mode()
app = QApplication([])

# On existing app
app = QApplication([])
enable_dark_mode()

# With explicit app reference
app = QApplication([])
enable_dark_mode(app)
```

## enable_light_mode()

```python
def enable_light_mode(app: QGuiApplication | None = None) -> None
```

Convenience function to enable light mode. Equivalent to `set_color_scheme(ColorScheme.Light, app)`.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | `QGuiApplication \| None` | Optional app instance. If None, uses `QApplication.instance()` |

### Examples

```python
from qtpie.styles import enable_light_mode

# Before app creation
enable_light_mode()
app = QApplication([])

# Toggle between modes at runtime
app = QApplication([])
enable_dark_mode()  # Switch to dark
# ... later ...
enable_light_mode()  # Switch to light
```

## Complete Example

```python
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from qtpie.styles import ColorScheme, enable_dark_mode, enable_light_mode, set_color_scheme

class ThemeSwitcher(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.label = QLabel("Color Scheme Demo")
        layout.addWidget(self.label)

        dark_btn = QPushButton("Dark Mode")
        dark_btn.clicked.connect(lambda: enable_dark_mode())
        layout.addWidget(dark_btn)

        light_btn = QPushButton("Light Mode")
        light_btn.clicked.connect(lambda: enable_light_mode())
        layout.addWidget(light_btn)

# Set initial scheme before app creation
set_color_scheme(ColorScheme.Dark)

app = QApplication([])
window = ThemeSwitcher()
window.show()
app.exec()
```

## Platform-Specific Behavior

### Windows
When setting color scheme before app creation, QtPie sets the `QT_QPA_PLATFORM` environment variable:
- Dark mode: `windows:darkmode=2`
- Light mode: `windows:darkmode=0`

### macOS and Linux
When setting color scheme before app creation, QtPie stores the preference and applies it via Qt's runtime API when the app is initialized.

### Runtime Switching
All platforms support runtime switching via Qt 6.8+ `styleHints().setColorScheme()` API when the application is running.

## Notes

- Color scheme changes are applied globally to the application
- Qt's native widgets will automatically adjust their appearance based on the color scheme
- Custom QSS stylesheets may need additional logic to respond to scheme changes
- The color scheme setting persists only for the current application session
