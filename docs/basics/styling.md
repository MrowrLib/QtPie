# Styling with QSS

QtPie provides powerful styling capabilities through Qt Style Sheets (QSS), CSS classes, object names, SCSS compilation, and color scheme support.

## Object Names

Every widget gets an `objectName` automatically, which you can use in QSS selectors.

### Default Object Names

If you don't specify a `name=`, QtPie uses sensible defaults:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget
class MyDefaultWidget(Widget):
    _button: QPushButton = new("Click")
    _label: QLabel = new("Hello")

# Automatic objectNames:
# - Widget: "MyDefaultWidget" (class name)
# - _button: "_button" (field name)
# - _label: "_label" (field name)
```

You can target these in QSS:

```python
@widget(stylesheet="""
#MyDefaultWidget {
    background-color: white;
}
#_button {
    color: blue;
}
#_label {
    font-weight: bold;
}
""")
class MyStyledWidget(Widget):
    _button: QPushButton = new("Click")
    _label: QLabel = new("Hello")
```

### Custom Object Names

Override the default with `name=`:

```python
@widget(name="main-window")
class MainWindow(Widget):
    _save_btn: QPushButton = new("Save", name="action-button")
    _title: QLabel = new("Title", name="page-title")

# objectNames:
# - Widget: "main-window"
# - _save_btn: "action-button"
# - _title: "page-title"
```

Set names on the decorator for the widget itself:

```python
@widget(name="custom-widget")
class MyWidget(Widget):
    pass

w = MyWidget()
assert w.objectName() == "custom-widget"
```

Set names on fields using `new()`:

```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new("Click", name="submit-button")

w = MyWidget()
assert w._button.objectName() == "submit-button"
```

## CSS Classes

QtPie provides a comprehensive CSS class system similar to web development.

### Setting Classes

Set classes on widgets using the `classes=` parameter:

```python
from qtpie import Widget, new, widget

@widget(classes=["card", "primary"])
class CardWidget(Widget):
    _button: QPushButton = new("Click", classes=["btn", "btn-primary"])
    _label: QLabel = new("Text", classes=["text", "large"])
```

### Using Classes in QSS

Target CSS classes in stylesheets using the `.` selector:

```python
@widget(
    classes=["dark-theme"],
    stylesheet="""
.card {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 10px;
}
.btn-primary {
    background-color: #007bff;
    color: white;
}
.text.large {
    font-size: 16px;
}
"""
)
class StyledWidget(Widget):
    _card: QWidget = new(classes=["card"])
    _button: QPushButton = new("Action", classes=["btn-primary"])
    _label: QLabel = new("Title", classes=["text", "large"])
```

### Runtime Class Manipulation

QtPie provides helper functions to manipulate classes at runtime:

```python
from qtpie.styles import (
    add_class,
    add_classes,
    get_classes,
    has_class,
    has_any_class,
    remove_class,
    replace_class,
    set_classes,
    toggle_class,
)

# Get current classes
classes = get_classes(widget)  # Returns list[str]

# Set classes (replaces all existing)
set_classes(widget, ["foo", "bar"])

# Add single class (no duplicates)
add_class(widget, "active")
add_class(widget, "active")  # No effect - already has it

# Add multiple classes
add_classes(widget, ["disabled", "highlighted"])

# Check if class exists
if has_class(widget, "active"):
    print("Widget is active")

# Check if any class exists
if has_any_class(widget, ["error", "warning"]):
    print("Widget has error or warning")

# Remove class
remove_class(widget, "active")

# Replace class (swaps in same position)
replace_class(widget, "old-class", "new-class")

# Toggle class (add if missing, remove if present)
toggle_class(widget, "selected")
```

**Refresh Behavior:** Most class functions automatically refresh the widget's stylesheet by default. Use `refresh=False` to skip:

```python
set_classes(widget, ["foo"], refresh=False)
```

### Classes with Variable[T, W]

Set classes on Variable widget using the second call:

```python
from PySide6.QtWidgets import QLineEdit
from qtpie import Variable, Widget, new, widget

@widget
class MyWidget(Widget):
    _name: Variable[str, QLineEdit] = new("")(classes=["input", "bordered"])

w = MyWidget()
assert get_classes(w._name.widget) == ["input", "bordered"]
```

### Classes on List/Dict Items

CSS classes apply to each item in repeaters:

```python
from qtpie import Variable, Widget, new, widget

@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Task 1", "Task 2"])
    _labels: list[QLabel] = new(bind="_items", classes=["todo-item", "pending"])

w = TodoList()
for label in w._labels:
    assert get_classes(label) == ["todo-item", "pending"]
```

Dynamically added items also get the classes:

```python
w._items.append("Task 3")
# New label automatically has ["todo-item", "pending"]
```

## Stylesheets

### Inline Stylesheets

Apply QSS directly to widgets using `stylesheet=` (or lowercase `stylesheet=`):

```python
@widget(stylesheet="background-color: #f0f0f0;")
class MyWidget(Widget):
    _label: QLabel = new("Hello", stylesheet="color: red; font-weight: bold;")
```

The `stylesheet` parameter is an alias for `styleSheet` (Qt's camelCase property):

```python
# These are equivalent:
@widget(stylesheet="...")
@widget(styleSheet="...")

# And for fields:
_label: QLabel = new("Text", stylesheet="...")
_label: QLabel = new("Text", styleSheet="...")
```

### External QSS Files

Load stylesheets from local `.qss` files:

```python
from qtpie.styles import load_stylesheet

@widget
class MyWidget(Widget):
    def __setup__(self) -> None:
        qss = load_stylesheet(qss_path="./styles/app.qss")
        self.setStyleSheet(qss)
```

### QRC Resources

Load stylesheets from Qt Resource files (`.qrc`):

```python
from qtpie.styles import load_stylesheet

@widget
class MyWidget(Widget):
    def __setup__(self) -> None:
        # Load from compiled QRC resource
        qss = load_stylesheet(qrc_path=":/styles/app.qss")
        self.setStyleSheet(qss)
```

**Fallback behavior:** If both paths are provided, local takes precedence:

```python
# Tries local first, falls back to QRC if local doesn't exist
qss = load_stylesheet(
    qss_path="./styles/app.qss",
    qrc_path=":/styles/app.qss"
)
```

**Missing files:** If the file doesn't exist, `load_stylesheet()` returns an empty string (no exception raised).

## SCSS Compilation

QtPie can compile SCSS to QSS using the `compile_scss()` function.

### Basic Compilation

```python
from qtpie.styles import compile_scss

compile_scss(
    scss_path="./styles/app.scss",
    qss_path="./styles/app.qss"
)
```

### With Import Search Paths

SCSS files can use `@import` to include partials:

```python
compile_scss(
    scss_path="./styles/main.scss",
    qss_path="./styles/main.qss",
    search_paths=["./styles/partials", "./styles/themes"]
)
```

**Example SCSS structure:**

```
styles/
  main.scss
  partials/
    _variables.scss
    _mixins.scss
  themes/
    _dark.scss
```

In `main.scss`:

```scss
@import 'variables';
@import 'mixins';
@import 'dark';

QPushButton {
    background-color: $primary-color;
    font-size: $base-font-size;
}
```

### Automatic Directory Creation

The output directory is created automatically if it doesn't exist:

```python
compile_scss(
    scss_path="./src/styles.scss",
    qss_path="./build/nested/deep/output.qss"  # Creates ./build/nested/deep/
)
```

### Error Handling

**Missing SCSS file:**

```python
compile_scss(scss_path="./nonexistent.scss", qss_path="./out.qss")
# Raises: FileNotFoundError: SCSS file not found: ./nonexistent.scss
```

**Syntax errors:**

```python
# bad.scss contains: QPushButton { color: $undefined_variable; }
compile_scss(scss_path="./bad.scss", qss_path="./out.qss")
# Raises: SassError: Undefined variable: "$undefined_variable"
```

### SCSS Variables Example

```scss
// _variables.scss
$primary-color: #007bff;
$secondary-color: #6c757d;
$font-size-base: 14px;
$border-radius: 4px;

// main.scss
@import 'variables';

QPushButton {
    background-color: $primary-color;
    color: white;
    font-size: $font-size-base;
    border-radius: $border-radius;
}

QPushButton:hover {
    background-color: darken($primary-color, 10%);
}
```

## Color Schemes

QtPie provides helpers for dark/light mode.

### Setting Color Scheme

```python
from qtpie.styles import ColorScheme, set_color_scheme

# Set dark mode
set_color_scheme(ColorScheme.Dark)

# Set light mode
set_color_scheme(ColorScheme.Light)
```

### Convenience Functions

```python
from qtpie.styles import enable_dark_mode, enable_light_mode

enable_dark_mode()
enable_light_mode()
```

### Before QApplication Exists

If you call `set_color_scheme()` before creating `QApplication`, QtPie stores the preference and applies it when the app is created:

```python
from qtpie.styles import enable_dark_mode

# Called before QApplication exists
enable_dark_mode()

# Later, when QApplication is created, dark mode is automatically applied
app = QApplication([])
```

**Windows-specific:** On Windows, QtPie sets the `QT_QPA_PLATFORM` environment variable:

```python
enable_dark_mode()
# Sets: QT_QPA_PLATFORM=windows:darkmode=2

enable_light_mode()
# Sets: QT_QPA_PLATFORM=windows:darkmode=0
```

### With Existing QApplication

If `QApplication` already exists, the color scheme is applied immediately:

```python
from PySide6.QtWidgets import QApplication
from qtpie.styles import enable_dark_mode

app = QApplication([])
enable_dark_mode()  # Takes effect immediately via app.styleHints()
```

### Explicit App Parameter

You can pass an explicit app instance:

```python
from qtpie.styles import set_color_scheme, ColorScheme

app = QApplication([])
set_color_scheme(ColorScheme.Dark, app)
```

## Combining Object Names and Classes

Use both for maximum flexibility:

```python
@widget(name="settings-panel", classes=["panel", "elevated"])
class SettingsPanel(Widget):
    _save_btn: QPushButton = new(
        "Save",
        name="primary-action",
        classes=["btn", "btn-primary"]
    )
```

Style with specificity:

```scss
// Target by ID (most specific)
#settings-panel {
    background-color: white;
}

// Target by class (reusable)
.panel {
    border: 1px solid #ccc;
}
.panel.elevated {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

// Target button by ID and class
#primary-action.btn-primary {
    background-color: #007bff;
}
```

## Best Practices

### Use Classes for Reusable Styles

```python
# GOOD - classes are reusable
@widget(classes=["card"])
class UserCard(Widget):
    _avatar: QLabel = new(classes=["avatar", "rounded"])
    _name: QLabel = new(classes=["text", "bold"])

@widget(classes=["card"])
class ProductCard(Widget):
    _image: QLabel = new(classes=["avatar", "rounded"])
    _title: QLabel = new(classes=["text", "bold"])
```

### Use Object Names for Unique Widgets

```python
# GOOD - unique widgets get IDs
@widget
class MainWindow(Widget):
    _sidebar: QWidget = new(name="main-sidebar")
    _content: QWidget = new(name="main-content")
```

### Keep Stylesheets Separate from Logic

```python
# GOOD - stylesheet in separate file
@widget
class MyWidget(Widget):
    def __setup__(self) -> None:
        qss = load_stylesheet(qss_path="./styles/mywidget.qss")
        self.setStyleSheet(qss)
```

### Use SCSS for Complex Stylesheets

```python
# GOOD - SCSS with variables, mixins, nesting
# Compile during build: compile_scss("styles/app.scss", "dist/app.qss")
```

## Non-QWidget Classes

For non-QWidget types, `name=` and `classes=` are passed to the constructor as kwargs:

```python
class CustomClass:
    def __init__(self, name: str = "", classes: list[str] | None = None):
        self.name = name
        self.classes = classes or []

@widget
class MyWidget(Widget):
    _custom: CustomClass = new(name="my-config", classes=["config", "primary"])

w = MyWidget()
assert w._custom.name == "my-config"
assert w._custom.classes == ["config", "primary"]
```

## Gotchas

### Classes Don't Apply to Non-QWidgets

CSS classes only work with `QWidget` descendants. For non-QWidget types, they're just passed as constructor arguments.

### QSS Cascade Order

Qt applies stylesheets from parent to child. More specific selectors override less specific ones:

```python
@widget(stylesheet="QLabel { color: blue; }")
class MyWidget(Widget):
    # This will be blue (parent stylesheet)
    _label1: QLabel = new("Blue")

    # This will be red (more specific)
    _label2: QLabel = new("Red", stylesheet="color: red;")
```

### Refresh Performance

Calling `set_classes()` or `add_class()` triggers a stylesheet refresh. For bulk changes, use `refresh=False` and manually refresh once:

```python
# BAD - refreshes 100 times
for widget in widgets:
    add_class(widget, "active")

# GOOD - refresh once at the end
for widget in widgets:
    add_class(widget, "active", refresh=False)
widget.style().unpolish(widget)
widget.style().polish(widget)
```

### Default Names Use Field Names

If you're using private fields (e.g., `_button`), the default objectName will be `_button` (with underscore), which requires escaping in some contexts:

```css
/* Must use #_button, not #button */
#_button {
    color: red;
}
```

Consider using explicit names for public-facing widgets:

```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new("Click", name="submit-button")  # Cleaner in CSS
```
