# @entrypoint

The `@entrypoint` decorator marks a function or class as the application entry point. When the decorated item's file is run directly (module is `__main__`), it automatically creates a Qt application, runs the entry point, and starts the event loop.

When imported from another module, the decorator simply stores configuration without auto-running, allowing the class/function to be used normally.

## Basic Usage

### Without Parentheses

For default settings, use `@entrypoint` without parentheses:

```python
from qtpie import entrypoint
from qtpy.QtWidgets import QLabel

@entrypoint
def main():
    return QLabel("Hello, World!")
```

Run this file with `python main.py` and it automatically starts the Qt application.

### With Parentheses

To customize the application, use `@entrypoint()` with parameters:

```python
@entrypoint(dark_mode=True, title="My App", size=(800, 600))
def main():
    return QLabel("Hello, World!")
```

## Entry Point Styles

### Function Entry Point

The simplest approach - a function that returns a widget:

```python
from qtpie import entrypoint
from qtpy.QtWidgets import QLabel

@entrypoint
def main():
    return QLabel("Hello, World!")
```

When run directly, this creates a `QApplication`, calls `main()`, shows the returned widget, and starts the event loop.

### Widget Class Entry Point

Use with `@widget` for declarative widgets:

```python
from qtpie import entrypoint, make, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entrypoint
@widget
class MyWidget(QWidget):
    text: QLabel = make(QLabel, "Hello, World!")
    button: QPushButton = make(QPushButton, "Click Me", clicked="on_click")

    def on_click(self):
        self.text.setText("Button Clicked!")
```

The decorator automatically instantiates the widget class, shows it, and runs the app.

### App Class Entry Point

For full control over application lifecycle:

```python
from typing import override
from qtpie import App, entrypoint
from qtpy.QtWidgets import QLabel

@entrypoint
class MyApp(App):
    @override
    def create_window(self):
        return QLabel("Hello from App!")
```

This gives you access to `App` lifecycle hooks like `setup()` and `create_window()`.

### Async Entry Point

Use async functions with `qasync`:

```python
import asyncio
from qtpie import entrypoint
from qtpy.QtWidgets import QLabel

@entrypoint
async def main():
    # Perform async operations
    await asyncio.sleep(1)
    data = await fetch_data()
    return DataViewer(data)
```

The decorator automatically sets up `qasync.QEventLoop` and runs the coroutine.

## Parameters

### dark_mode

**Type:** `bool`
**Default:** `False`

Enables dark mode color scheme for the application.

**Example:**

```python
@entrypoint(dark_mode=True)
def main():
    return QLabel("Dark mode enabled")
```

### light_mode

**Type:** `bool`
**Default:** `False`

Enables light mode color scheme for the application. Typically unnecessary as light mode is the default Qt behavior.

**Example:**

```python
@entrypoint(light_mode=True)
def main():
    return QLabel("Light mode enabled")
```

### title

**Type:** `str | None`
**Default:** `None`

Sets the window title. Applied to the widget returned by the entry point function or created from the decorated class.

**Example:**

```python
@entrypoint(title="My Application v1.0")
def main():
    return QLabel("Hello!")
# Window title will be "My Application v1.0"
```

### size

**Type:** `tuple[int, int] | None`
**Default:** `None`

Sets the initial window size as `(width, height)` in pixels.

**Example:**

```python
@entrypoint(size=(1024, 768))
def main():
    return QLabel("Hello!")
# Window opens at 1024x768 pixels
```

### stylesheet

**Type:** `str | None`
**Default:** `None`

Path to a QSS or SCSS stylesheet to load. The file is loaded and applied to the application. SCSS files are automatically compiled to QSS.

**Example:**

```python
@entrypoint(stylesheet="styles.qss")
def main():
    return QLabel("Styled!")
```

### watch_stylesheet

**Type:** `bool`
**Default:** `False`

Enables hot-reload for the stylesheet. When `True`, changes to the stylesheet file are automatically detected and applied without restarting the app. Useful during development.

**Example:**

```python
@entrypoint(stylesheet="styles.scss", watch_stylesheet=True)
@widget
class MyApp(QWidget):
    pass
# Now edit styles.scss and save - changes appear instantly!
```

### scss_search_paths

**Type:** `Sequence[str]`
**Default:** `()`

Directories to search when resolving SCSS `@import` statements. If empty, the parent directory of the stylesheet is used automatically.

**Example:**

```python
@entrypoint(
    stylesheet="styles/main.scss",
    watch_stylesheet=True,
    scss_search_paths=["styles/partials", "styles/themes"]
)
@widget
class MyApp(QWidget):
    pass
```

With this structure:
```
myapp/
├── styles/
│   ├── main.scss          # @import 'variables';
│   ├── partials/
│   │   └── _variables.scss
│   └── themes/
│       └── _dark.scss
└── main.py
```

### window

**Type:** `type[QWidget] | None`
**Default:** `None`

A widget class to instantiate as the main window. Only used when the entry point function returns `None` or when decorating a non-widget class.

**Example:**

```python
from qtpie import entrypoint

@entrypoint(window=MyMainWindow)
def main():
    # Perform setup, but don't return a widget
    initialize_database()
    # MyMainWindow will be automatically created and shown
```

## Auto-Run Behavior

The `@entrypoint` decorator automatically runs when **both** conditions are met:

1. **Module is `__main__`** - The file is executed directly (`python myapp.py`)
2. **No QApplication exists** - There's no existing Qt application instance

This means:

```python
# myapp.py
@entrypoint
def main():
    return QLabel("Hello!")

# When run directly:
# $ python myapp.py
# → Automatically creates QApplication and starts event loop

# When imported:
# from myapp import main
# → Does nothing, main() can be called manually
```

### Testing Compatibility

The auto-run behavior is disabled when a `QApplication` already exists, making `@entrypoint` safe to use in tests:

```python
# test_myapp.py
from qtpie_test import QtDriver

def test_my_app(qt: QtDriver):
    # This works fine - @entrypoint won't auto-run
    # because qt fixture already created a QApplication
    widget = MyAppWidget()
    qt.track(widget)
    # ... assertions
```

## Complete Examples

### Simple Counter

```python
from qtpie import entrypoint, make, state, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entrypoint(title="Counter", size=(300, 150))
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self):
        self.count += 1
```

### App with Custom Setup

```python
from typing import override
from qtpie import App, entrypoint, make, widget
from qtpy.QtWidgets import QLabel, QMainWindow, QWidget

@widget
class MainWidget(QWidget):
    label: QLabel = make(QLabel, "Application Ready!")

@entrypoint(dark_mode=True, size=(800, 600))
class MyApp(App):
    @override
    def setup(self):
        # Called before window creation
        self.load_stylesheet("styles.qss")
        print("App initialized")

    @override
    def create_window(self):
        # Return the main window widget
        return MainWidget()
```

### Multiple Configuration Options

```python
@entrypoint(
    dark_mode=True,
    title="Production Dashboard",
    size=(1280, 720),
    stylesheet="dashboard.scss",
)
@widget
class Dashboard(QWidget):
    # ... widget implementation
```

### Full Stylesheet Configuration

```python
@entrypoint(
    dark_mode=True,
    title="My App",
    size=(1024, 768),
    stylesheet="styles/main.scss",
    watch_stylesheet=True,  # Hot-reload during development
    scss_search_paths=["styles/partials", "styles/themes"],
)
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Styled with SCSS!")
```

### Function with Window Parameter

```python
from qtpie import entrypoint, make, widget
from qtpy.QtWidgets import QLabel, QWidget

@widget
class MainWindow(QWidget):
    label: QLabel = make(QLabel, "Main Window")

@entrypoint(window=MainWindow, title="My App")
def main():
    # Perform initialization
    load_config()
    connect_database()
    # MainWindow will be automatically created and shown
```

## Order with Other Decorators

When using `@entrypoint` with other decorators, `@entrypoint` should be the **outermost** decorator:

```python
# Correct order
@entrypoint(dark_mode=True)
@widget(layout="vertical")
class MyApp(QWidget):
    pass

# Also correct
@entrypoint
@window(title="My Window")
class MyApp(QMainWindow):
    pass
```

This ensures `@entrypoint` decorates the fully-configured widget class.

## When to Use

Use `@entrypoint` when:

- Building a standalone application with a single entry point file
- You want automatic app creation and event loop management
- Writing simple scripts or demos that should "just run"

Don't use `@entrypoint` when:

- Building a library (use regular `@widget` or `@window`)
- The widget should be reusable as a component
- You need manual control over `QApplication` creation

For library code, prefer explicit app creation:

```python
from qtpie import run_app, widget
from qtpy.QtWidgets import QWidget

@widget  # No @entrypoint
class MyLibraryWidget(QWidget):
    pass

# Users can then do:
if __name__ == "__main__":
    widget = MyLibraryWidget()
    widget.show()
    run_app()
```

## See Also

- [App & Entry Points](../../guides/app.md) - Complete guide to application structure
- [App Class](../../reference/app/app.md) - App class reference
- [run_app()](../../reference/app/run-app.md) - Manual event loop runner
- [@widget](./widget.md) - Widget decorator reference
- [@window](./window.md) - Window decorator reference
