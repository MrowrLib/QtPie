# Styling

QtPie supports Qt StyleSheets (QSS) with SCSS compilation, hot-reloading, and CSS class helpers.

## Quick Start

```python
from qtpie import Widget, new, widget, enable_dark_mode

enable_dark_mode()  # Enable system dark mode

@widget
class StyledApp(Widget):
    _button: QPushButton = new("Click", classes=["primary"])
```

## Color Scheme

Set light or dark mode programmatically:

```python
from qtpie import enable_dark_mode, enable_light_mode, set_color_scheme, ColorScheme

# Simple helpers
enable_dark_mode()
enable_light_mode()

# Or use the enum
set_color_scheme(ColorScheme.Dark)
set_color_scheme(ColorScheme.Light)
```

Call these before creating widgets for best results.

## Object Names and CSS Classes

### On Widgets

```python
@widget(name="main-panel", classes=["card", "elevated"])
class MainPanel(Widget):
    pass

panel = MainPanel()
# panel.objectName() == "main-panel"
# CSS classes: ["card", "elevated"]
```

### On Fields

```python
@widget
class Form(Widget):
    _title: QLabel = new("Title", name="form-title", classes=["heading"])
    _input: QLineEdit = new(name="user-input", classes=["input", "large"])
```

### On Variable[T, W]

```python
@widget
class Form(Widget):
    _name: Variable[str, QLineEdit] = new("")(
        name="name-field",
        classes=["input", "required"]
    )
```

### Default Object Names

Without explicit `name=`, QtPie sets default object names:

| Context | Default objectName |
|---------|-------------------|
| Widget class | Class name (e.g., "MyWidget") |
| Widget field | Field name (e.g., "_button") |
| Variable widget | Field name (e.g., "_name") |
| List item | Field name (e.g., "_labels") |

## CSS Class Helpers

Programmatically manage CSS classes on any widget:

```python
from qtpie import (
    get_classes, set_classes, add_class, add_classes,
    remove_class, replace_class, toggle_class, has_class, has_any_class
)

# Get/set classes
set_classes(widget, ["foo", "bar"])
classes = get_classes(widget)  # ["foo", "bar"]

# Add classes
add_class(widget, "active")
add_classes(widget, ["highlighted", "large"])

# Check classes
if has_class(widget, "active"):
    pass
if has_any_class(widget, ["error", "warning"]):
    pass

# Remove classes
remove_class(widget, "active")

# Replace class (preserves position)
replace_class(widget, "old-class", "new-class")

# Toggle class
toggle_class(widget, "selected")  # Adds if missing, removes if present
```

## Stylesheets

### Loading QSS Files

```python
from qtpie import load_stylesheet

# From filesystem
qss = load_stylesheet(qss_path="./styles/app.qss")
widget.setStyleSheet(qss)

# From Qt resources
qss = load_stylesheet(qrc_path=":/styles/app.qss")

# Fallback: try local first, then QRC
qss = load_stylesheet(
    qss_path="./styles/app.qss",
    qrc_path=":/styles/app.qss"
)
```

### SCSS Compilation

Compile SCSS to QSS with variable support:

```python
from qtpie import compile_scss

compile_scss(
    scss_path="./styles/main.scss",
    qss_path="./styles/main.qss"
)
```

With import search paths:

```python
compile_scss(
    scss_path="./styles/main.scss",
    qss_path="./styles/main.qss",
    search_paths=["./styles/core", "./styles/themes"]
)
```

Example SCSS:

```scss
// styles/core/_variables.scss
$primary-color: #3498db;
$base-size: 16px;

// styles/main.scss
@import 'variables';

QPushButton.primary {
    background-color: $primary-color;
    font-size: $base-size;
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
}

QPushButton.primary:hover {
    background-color: darken($primary-color, 10%);
}
```

### Hot-Reload Watchers

Watch files and auto-apply changes during development:

```python
from qtpie import watch_qss, watch_scss, watch_styles

# Watch QSS file
watcher = watch_qss(widget, "./styles/app.qss")

# Watch SCSS with compilation
watcher = watch_scss(
    widget,
    scss_path="./styles/main.scss",
    qss_path="./styles/main.qss",
    search_paths=["./styles/core"]
)

# Auto-detect: returns QssWatcher or ScssWatcher
watcher = watch_styles(widget, "./styles/app.qss")
watcher = watch_styles(
    widget,
    "./styles/app.qss",
    scss_path="./styles/main.scss"
)
```

Watchers:
- Apply styles immediately on creation
- Watch for file changes and auto-reload
- Handle file creation (watch non-existent files)
- Track SCSS imports (recompile when partials change)

## Using Classes in QSS

Reference CSS classes in stylesheets using the `.class` selector:

```scss
/* Target by class */
QPushButton.primary {
    background-color: #3498db;
    color: white;
}

QPushButton.danger {
    background-color: #e74c3c;
}

/* Target by object name */
#form-title {
    font-size: 24px;
    font-weight: bold;
}

/* Combine */
QLineEdit.input.large {
    font-size: 18px;
    padding: 12px;
}
```

## Complete Example

```python
from qtpie import Widget, Variable, new, widget, entrypoint
from qtpie import enable_dark_mode, watch_scss, add_class, remove_class

@entrypoint
@widget(name="login-form", classes=["card"])
class LoginForm(Widget):
    _title: QLabel = new("Login", classes=["heading"])

    _username: Variable[str, QLineEdit] = new("")(
        placeholderText="Username",
        classes=["input"]
    )
    _password: Variable[str, QLineEdit] = new("")(
        placeholderText="Password",
        classes=["input"],
        echoMode=QLineEdit.EchoMode.Password
    )

    _login_btn: QPushButton = new(
        "Login",
        classes=["button", "primary"],
        clicked="on_login"
    )
    _error: QLabel = new("", classes=["error"], visible="{len(_error_text) > 0}")
    _error_text: Variable[str] = new("")

    def __setup__(self) -> None:
        enable_dark_mode()
        # Hot-reload styles during development
        watch_scss(
            self,
            scss_path="./styles/login.scss",
            qss_path="./styles/login.qss"
        )

    def on_login(self) -> None:
        if not self._username.value:
            self._error_text = "Username required"
            add_class(self._username.widget, "invalid")
        else:
            remove_class(self._username.widget, "invalid")
            # ... login logic
```

## See Also

- [Widgets](../basics/widgets.md) - Widget basics
- [Variables](../state/variables.md) - Variable[T, W] syntax
