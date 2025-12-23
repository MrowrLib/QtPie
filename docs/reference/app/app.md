# App Class

The `App` class is a `QApplication` subclass with lifecycle hooks and async support built-in. It provides a clean way to structure your application with optional lifecycle hooks for setup, styling, and window creation.

## Overview

`App` extends `QApplication` with:

- **Lifecycle hooks** - `setup()`, `setup_styles()`, `create_window()`
- **Dark/light mode support** - Built-in color scheme management
- **Stylesheet loading** - Easy QSS/SCSS file loading
- **qasync integration** - Async/await support out of the box

## Basic Usage

### Simple App

The simplest way to use `App` is to instantiate it directly:

```python
from qtpie import App
from qtpy.QtWidgets import QLabel

app = App("My Application")
window = QLabel("Hello World!")
window.show()
app.run()  # Blocks until app quits
```

### With Dark Mode

Enable dark mode at app creation:

```python
from qtpie import App

app = App("My Application", dark_mode=True)
window = MyMainWindow()
window.show()
app.run()
```

## Subclassing App

Subclass `App` to use lifecycle hooks:

```python
from typing import override
from qtpie import App
from qtpy.QtWidgets import QWidget

class MyApp(App):
    @override
    def setup(self) -> None:
        # Called after App initialization
        print("App is ready!")

    @override
    def setup_styles(self) -> None:
        # Called after setup()
        self.load_stylesheet("styles.qss")

    @override
    def create_window(self) -> QWidget | None:
        # Called by @entrypoint to create main window
        return MyMainWindow()
```

## Constructor

```python
App(
    name: str = "Application",
    *,
    version: str = "1.0.0",
    dark_mode: bool = False,
    light_mode: bool = False,
    argv: Sequence[str] | None = None,
)
```

**Parameters:**

- `name` - Application name (sets `QApplication.applicationName`)
- `version` - Application version (sets `QApplication.applicationVersion`)
- `dark_mode` - Enable dark mode color scheme
- `light_mode` - Enable light mode color scheme
- `argv` - Command-line arguments (defaults to `sys.argv`)

**Note:** Only one of `dark_mode` or `light_mode` should be True.

## Lifecycle Hooks

### setup()

Called after `App` initialization. Use for general setup tasks:

```python
class MyApp(App):
    @override
    def setup(self) -> None:
        # Initialize services, configure app-wide settings
        self.database = Database.connect()
        self.config = load_config()
```

### setup_styles()

Called after `setup()`. Use for loading stylesheets:

```python
class MyApp(App):
    @override
    def setup_styles(self) -> None:
        self.load_stylesheet("resources/styles.qss")
```

### create_window()

Called by `@entrypoint` to create the main window. Return a `QWidget` to show:

```python
class MyApp(App):
    @override
    def create_window(self) -> QWidget | None:
        return MyMainWindow()
```

**Hook Execution Order:**

1. `App.__init__()` runs (color scheme applied, QApplication initialized)
2. `setup()` called
3. `setup_styles()` called
4. `create_window()` called (only when used with `@entrypoint`)

## Methods

### load_stylesheet()

Load a stylesheet from a file:

```python
def load_stylesheet(
    self,
    path: str,
    *,
    qrc_path: str | None = None,
) -> None
```

**Parameters:**

- `path` - Path to a `.qss` or `.scss` file
- `qrc_path` - Optional Qt resource path for fallback

**Example:**

```python
class MyApp(App):
    @override
    def setup_styles(self) -> None:
        # Load QSS file
        self.load_stylesheet("styles/main.qss")

        # Load SCSS file (auto-compiled)
        self.load_stylesheet("styles/theme.scss")
```

**Note:** If the file doesn't exist, the method fails silently (no exception raised).

### enable_dark_mode()

Enable dark mode color scheme:

```python
app.enable_dark_mode()
```

### enable_light_mode()

Enable light mode color scheme:

```python
app.enable_light_mode()
```

### run()

Run the application event loop. Blocks until the app quits:

```python
def run(self) -> int
```

**Returns:** Application exit code (always 0 currently)

**Example:**

```python
app = App("My Application")
window = MyWidget()
window.show()
exit_code = app.run()  # Blocks here
sys.exit(exit_code)
```

### run_async()

Run the application in an existing async context:

```python
async def run_async(self) -> int
```

**Returns:** Application exit code

**Example:**

```python
async def main():
    app = App("My Application")
    window = MyWidget()
    window.show()

    # Do async work
    await some_async_task()

    # Now run the app
    await app.run_async()
```

## Using with @entrypoint

The `App` class works seamlessly with `@entrypoint`:

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

When you run this file directly (`python my_app.py`):

1. `@entrypoint` detects it's the main module
2. Creates an instance of `MyApp`
3. Calls lifecycle hooks (`setup`, `setup_styles`)
4. Calls `create_window()` to get the main window
5. Shows the window
6. Starts the event loop

**With configuration:**

```python
@entrypoint(dark_mode=True, title="My Application", size=(800, 600))
class MyApp(App):
    @override
    def setup(self) -> None:
        self.load_stylesheet("styles.qss")

    @override
    def create_window(self):
        return MyMainWindow()
```

## Complete Examples

### App with Lifecycle Hooks

```python
from typing import override
from qtpie import App, widget, make
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@widget
class MainWindow(QWidget):
    label: QLabel = make(QLabel, "Welcome!")
    button: QPushButton = make(QPushButton, "Click Me")

class MyApp(App):
    @override
    def setup(self) -> None:
        print(f"Starting {self.applicationName()} v{self.applicationVersion()}")

    @override
    def setup_styles(self) -> None:
        self.load_stylesheet("resources/dark-theme.qss")

    @override
    def create_window(self) -> QWidget:
        return MainWindow()

if __name__ == "__main__":
    app = MyApp("My Application", version="2.0.0", dark_mode=True)

    # create_window() not automatically called - do it manually
    window = app.create_window()
    if window:
        window.show()

    app.run()
```

### Using with @entrypoint (Recommended)

```python
from typing import override
from qtpie import App, entrypoint, widget, make
from qtpy.QtWidgets import QWidget, QLabel

@widget
class MainWindow(QWidget):
    label: QLabel = make(QLabel, "Hello World!")

@entrypoint(dark_mode=True, title="My App", size=(600, 400))
class MyApp(App):
    @override
    def setup(self) -> None:
        # App-level initialization
        self.config = load_app_config()

    @override
    def setup_styles(self) -> None:
        self.load_stylesheet("resources/styles.qss")

    @override
    def create_window(self) -> QWidget:
        return MainWindow()

# When run directly, @entrypoint handles everything:
# - Creates MyApp instance
# - Calls lifecycle hooks
# - Calls create_window()
# - Shows window
# - Runs event loop
```

### Dark Mode Toggle

```python
from typing import override
from qtpie import App, widget, make
from qtpy.QtWidgets import QWidget, QPushButton

@widget
class MainWindow(QWidget):
    dark_btn: QPushButton = make(QPushButton, "Dark Mode", clicked="toggle_dark")
    light_btn: QPushButton = make(QPushButton, "Light Mode", clicked="toggle_light")

    def toggle_dark(self) -> None:
        app = App.instance()
        if isinstance(app, App):
            app.enable_dark_mode()

    def toggle_light(self) -> None:
        app = App.instance()
        if isinstance(app, App):
            app.enable_light_mode()

app = App("Theme Demo")
window = MainWindow()
window.show()
app.run()
```

### Custom App Subclass

```python
from typing import override
from qtpie import App
from qtpy.QtWidgets import QWidget

class GameApp(App):
    """Custom app for a game with game-specific setup."""

    def __init__(self) -> None:
        super().__init__(
            name="My Game",
            version="1.0.0",
            dark_mode=True,
        )
        self.score: int = 0
        self.level: int = 1

    @override
    def setup(self) -> None:
        # Load game resources
        self.load_assets()
        self.init_audio()

    @override
    def setup_styles(self) -> None:
        self.load_stylesheet("game-ui.qss")

    def load_assets(self) -> None:
        print("Loading game assets...")

    def init_audio(self) -> None:
        print("Initializing audio system...")

# Use the custom app
app = GameApp()
# ... rest of game setup
```

## See Also

- [run_app()](run-app.md) - Standalone event loop runner
- [@entrypoint](../decorators/entrypoint.md) - Application entry point decorator
- [Color Schemes](../styles/color-schemes.md) - Dark/light mode management
- [SCSS Hot Reload](../../guides/scss.md) - Stylesheet development workflow
