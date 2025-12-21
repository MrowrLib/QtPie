# SCSS Hot Reload

QtPie provides built-in support for SCSS (Sassy CSS) compilation and hot-reloading. This means you can write your stylesheets in SCSS with variables, imports, and nesting, and see changes reflected instantly in your running application.

## Why SCSS?

SCSS is a superset of CSS that adds powerful features:
- **Variables**: Define colors, sizes, and other values once and reuse them
- **Imports**: Split styles across multiple files for better organization
- **Nesting**: Write cleaner, more maintainable selectors
- **Functions and mixins**: Create reusable style patterns

Since Qt stylesheets (QSS) are CSS-like, SCSS compiles perfectly to QSS.

## Quick Start

The simplest way to use SCSS with hot reload is the `watch_scss()` function:

```python
from qtpie import entry_point, widget, make
from qtpie.styles import watch_scss
from qtpy.QtWidgets import QWidget, QPushButton

@entry_point
@widget
class MyApp(QWidget):
    button: QPushButton = make(QPushButton, "Click Me")

    def setup(self) -> None:
        # Watch SCSS file and auto-reload on changes
        self.watcher = watch_scss(
            target=self,
            scss_path="styles.scss",
            qss_path="output.qss",
        )
```

Create `styles.scss`:

```scss
$primary: #007bff;
$padding: 8px;

QPushButton {
    background-color: $primary;
    padding: $padding;
    color: white;
}
```

Now when you edit and save `styles.scss`, your app automatically reloads the styles!

## How It Works

QtPie's SCSS hot reload system has three parts:

1. **Compiler** (`compile_scss`) - Compiles SCSS to QSS
2. **Watcher** (`watch_scss`) - Watches files and triggers recompilation
3. **Hot reload** - Applies new styles to your widget without restarting

The watcher handles tricky edge cases like:
- Editor save behaviors (delete + recreate)
- Imported file changes
- Files that don't exist yet
- Debouncing rapid changes

## Basic Setup

### Single SCSS File

For a simple app with one SCSS file:

```python
from qtpie import widget, App
from qtpie.styles import watch_scss
from qtpy.QtWidgets import QWidget

@widget
class MainWindow(QWidget):
    def setup(self) -> None:
        self.watcher = watch_scss(
            target=self,
            scss_path="styles.scss",
            qss_path="styles.qss",
        )

app = App("My App")
window = MainWindow()
window.show()
app.run()
```

### Application-Level Styles

To apply styles to the entire application:

```python
from qtpie import App
from qtpie.styles import watch_scss

class MyApp(App):
    def setup_styles(self) -> None:
        # Apply to entire app (self is QApplication)
        self.watcher = watch_scss(
            target=self,
            scss_path="app.scss",
            qss_path="app.qss",
        )

app = MyApp("My App")
# ... create and show widgets
app.run()
```

## Using @import

Split your styles across multiple files for better organization.

### Project Structure

```
myapp/
├── styles/
│   ├── main.scss           # Main file
│   └── partials/           # Imported files
│       ├── _variables.scss
│       └── _buttons.scss
└── main.py
```

### partials/_variables.scss

```scss
$primary: #007bff;
$padding: 8px;
$text-color: #ffffff;
```

### partials/_buttons.scss

```scss
QPushButton {
    background-color: $primary;
    padding: $padding;
    color: $text-color;
}
```

### main.scss

```scss
@import "variables";
@import "buttons";
```

### Python Code

```python
from qtpie import widget
from qtpie.styles import watch_scss
from qtpy.QtWidgets import QWidget

@widget
class MyWidget(QWidget):
    def setup(self) -> None:
        self.watcher = watch_scss(
            target=self,
            scss_path="styles/main.scss",
            qss_path="styles/output.qss",
            search_paths=["styles/partials"],  # Where to find imports
        )
```

When you change any file in `partials/`, the watcher detects it and recompiles automatically!

## Multiple Search Paths

For larger projects, you might have imports from multiple directories:

```
myapp/
├── styles/
│   ├── main.scss
│   ├── core/              # Base variables, mixins
│   │   └── _variables.scss
│   └── themes/            # Theme-specific styles
│       └── _theme.scss
```

```python
self.watcher = watch_scss(
    target=self,
    scss_path="styles/main.scss",
    qss_path="styles/output.qss",
    search_paths=[
        "styles/core",
        "styles/themes",
    ],
)
```

The watcher monitors all search paths, so changing any imported file triggers a recompile.

## Watch Functions

QtPie provides three watch functions:

### watch_scss()

For SCSS files that need compilation:

```python
from qtpie.styles import watch_scss

watcher = watch_scss(
    target=widget,           # QWidget or QApplication
    scss_path="styles.scss", # Input SCSS file
    qss_path="output.qss",   # Output QSS file
    search_paths=None,       # Optional: list of import directories
)
```

### watch_qss()

For plain QSS files (no compilation):

```python
from qtpie.styles import watch_qss

watcher = watch_qss(
    target=widget,
    qss_path="styles.qss",
)
```

### watch_styles()

Convenience function that auto-detects:

```python
from qtpie.styles import watch_styles

# With SCSS
watcher = watch_styles(
    target=widget,
    qss_path="output.qss",
    scss_path="styles.scss",      # If provided, uses watch_scss
    search_paths=["partials"],
)

# Without SCSS (just watches QSS)
watcher = watch_styles(
    target=widget,
    qss_path="styles.qss",       # No scss_path = uses watch_qss
)
```

## Compile Without Watching

If you just want to compile once (e.g., in a build script):

```python
from qtpie.styles import compile_scss

compile_scss(
    scss_path="styles.scss",
    qss_path="output.qss",
    search_paths=["partials"],
)
```

This raises `FileNotFoundError` if the SCSS file doesn't exist, or `SassError` if there are syntax errors.

## Watcher Lifecycle

Keep a reference to the watcher! If it gets garbage collected, the watching stops:

```python
# GOOD - watcher stays alive
class MyWidget(QWidget):
    def setup(self) -> None:
        self.watcher = watch_scss(...)  # Stored as instance variable

# BAD - watcher gets garbage collected
class MyWidget(QWidget):
    def setup(self) -> None:
        watch_scss(...)  # No reference! Stops working immediately
```

To manually stop watching:

```python
self.watcher.stop()
```

## Watching Non-Existent Files

The watcher works even if files don't exist yet:

```python
# File doesn't exist yet
watcher = watch_qss(widget, "styles.qss")

# Later... create the file
Path("styles.qss").write_text("QPushButton { color: red; }")

# Watcher detects it and applies styles automatically!
```

This is useful during development when you're creating files on the fly.

## Editor Compatibility

The watcher handles different editor save behaviors:

- **VSCode, Sublime**: Modify file in-place (works great)
- **Vim, Emacs**: Delete and recreate (works great - watcher re-arms)
- **All editors**: Debounces rapid changes (150ms) to avoid flicker

## Signals

Both `QssWatcher` and `ScssWatcher` emit a `stylesheetApplied` signal when styles are reloaded:

```python
from qtpie.styles import watch_scss

watcher = watch_scss(...)

def on_styles_applied() -> None:
    print("Styles reloaded!")

watcher.stylesheetApplied.connect(on_styles_applied)
```

## Development Workflow

Here's a typical workflow:

1. Create your SCSS file with variables and structure
2. Set up `watch_scss()` in your widget's `setup()` method
3. Run your app
4. Edit SCSS files in your favorite editor
5. Save the file
6. See changes instantly in your running app!

No restarts, no manual recompilation - just edit and save.

## Examples from Tests

### Simple Hot Reload

```python
from qtpie.styles import watch_qss
from qtpy.QtWidgets import QWidget

widget = QWidget()

# Create and watch QSS file
qss_file = Path("styles.qss")
qss_file.write_text("QWidget { background-color: red; }")

watcher = watch_qss(widget, str(qss_file))

# Change the file
qss_file.write_text("QWidget { background-color: blue; }")

# Widget stylesheet updates automatically!
```

### SCSS with Imports

```python
from qtpie.styles import watch_scss
from qtpy.QtWidgets import QWidget

widget = QWidget()

# Create partials
partials = Path("partials")
partials.mkdir()

variables = partials / "_variables.scss"
variables.write_text("$bg: orange;")

# Main file with import
main = Path("main.scss")
main.write_text("@import 'variables'; QWidget { background: $bg; }")

# Watch with search path
watcher = watch_scss(
    widget,
    str(main),
    "output.qss",
    search_paths=["partials"],
)

# Change imported file
variables.write_text("$bg: pink;")

# Watcher detects the change and recompiles!
```

## See Also

- [Styling Basics](../basics/styling.md) - CSS classes and selectors
- [Color Schemes](../reference/styles/color-schemes.md) - Dark/light mode
- [App & Entry Points](app.md) - Using App.setup_styles()
