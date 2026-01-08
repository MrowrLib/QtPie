# App & Entry Points

The `@entrypoint` decorator and `App` class provide a streamlined way to bootstrap QtPie applications. They handle QApplication setup, event loop management, and lifecycle hooks automatically.

## The @entrypoint Decorator

The `@entrypoint` decorator marks a function or class as your application's entry point. When the decorated module is run directly (as `__main__`), QtPie automatically creates a QApplication, executes your entry point, and starts the event loop.

### Basic Usage

```python
from qtpie import entrypoint, widget, Widget, new
from qtpy.QtWidgets import QLabel

@entrypoint
@widget
class HelloWorld(Widget):
    label: QLabel = new("Hello, QtPie!")
```

Run this file directly (`python my_app.py`) and QtPie handles the rest. No manual QApplication setup needed.

### Entry Point Types

The `@entrypoint` decorator works with several patterns:

**Widget Class**

```python
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Hello!")
```

**Function Returning a Widget**

```python
@entrypoint
def main():
    return QLabel("Hello from function!")
```

**App Subclass with Lifecycle Hooks**

```python
@entrypoint
class MyApp(App):
    def __setup__(self):
        print("App initialized!")

    def create_window(self):
        return MyMainWindow()
```

**Async Function**

```python
@entrypoint
async def main():
    data = await fetch_initial_data()
    return DataViewer(data)
```

Async functions automatically run in a qasync event loop with proper signal handling (CTRL-C support).

### Configuration Parameters

The `@entrypoint` decorator accepts configuration for window setup and styling:

```python
@entrypoint(
    title="My Application",
    size=(1024, 768),
    dark_mode=True
)
@widget
class MyApp(Widget):
    label: QLabel = new("Hello!")
```

**Available Parameters:**

- `title`: Window title (string)
- `size`: Window dimensions as `(width, height)` tuple
- `dark_mode`: Enable dark color scheme (bool)
- `light_mode`: Enable light color scheme (bool)
- `stylesheet`: Path to QSS/SCSS file or QRC resource
- `watch_stylesheet`: Enable hot-reload for stylesheets (bool)
- `scss_search_paths`: List of directories for SCSS `@import` resolution
- `window`: Widget class to use as main window (alternative to function return)
- `translations`: Path or list of paths to translation YAML files
- `language`: Language code (e.g., "en", "fr", "de")
- `watch_translations`: Enable hot-reload for translations (bool)

### Stylesheets

QtPie supports three stylesheet types:

**QSS Files**

```python
@entrypoint(stylesheet="styles.qss")
@widget
class MyApp(Widget):
    label: QLabel = new("Styled content")
```

**SCSS Files with Hot-Reload**

```python
@entrypoint(
    stylesheet="styles.scss",
    watch_stylesheet=True,
    scss_search_paths=["./themes", "./partials"]
)
@widget
class MyApp(Widget):
    label: QLabel = new("SCSS styled content")
```

With `watch_stylesheet=True`, the stylesheet recompiles and reloads automatically when you save changes during development.

**QRC Resources**

```python
@entrypoint(stylesheet=":/styles/app.qss")
@widget
class MyApp(Widget):
    label: QLabel = new("QRC styled content")
```

QRC paths (starting with `:/`) load stylesheets from compiled Qt resources. Note that `watch_stylesheet` is ignored for QRC paths.

### Translations

Enable i18n support with translation YAML files:

```python
@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))  # Shows "Bonjour" in French
```

See the [Translations guide](translations.md) for YAML format details.

### Decorator Without Parentheses

The decorator works with or without parentheses:

```python
@entrypoint
def main():
    return QLabel("No parens needed")

@entrypoint()  # Also valid
def main():
    return QLabel("With parens")
```

### Import vs. Run Behavior

The `@entrypoint` decorator only auto-runs when the module is `__main__`:

```python
# my_app.py
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Hello!")

# Run directly - auto-starts
# $ python my_app.py

# Import elsewhere - does NOT auto-start
# from my_app import MyApp
# app = QApplication([])
# window = MyApp()  # Works normally
```

This allows entry point modules to be imported in tests without side effects.

## The App Class

The `App` class is a QApplication subclass with lifecycle hooks and qasync integration. Use it when you need more control than `@entrypoint` provides.

### Basic Usage

```python
from qtpie import App

app = App("My Application", dark_mode=True)
window = MyMainWindow()
window.show()
app.run()  # Blocks until app quits
```

### Constructor Parameters

```python
App(
    name="Application",      # Application name
    version="1.0.0",        # Application version
    dark_mode=False,        # Enable dark color scheme
    light_mode=False,       # Enable light color scheme
    argv=None               # Command-line args (defaults to sys.argv)
)
```

### Lifecycle Hooks

Override these methods in App subclasses for custom initialization:

**`__setup__()`**

Called after QApplication initialization:

```python
class MyApp(App):
    def __setup__(self):
        self.load_stylesheet("styles.qss")
        print("App initialized")
```

**`create_window()`**

Called by `@entrypoint` to create the main window:

```python
class MyApp(App):
    def create_window(self):
        return MyMainWindow()

# Used with @entrypoint
@entrypoint
class MyApp(App):
    def create_window(self):
        return MyMainWindow()
```

### Methods

**`run()`**

Start the application event loop with qasync support:

```python
app = App()
window = MyWindow()
window.show()
exit_code = app.run()  # Blocks until quit
```

**`run_async()`**

Run within an existing async context:

```python
async def main():
    app = App()
    window = MyWindow()
    window.show()
    await app.run_async()
```

**`load_stylesheet(path, *, qrc_path=None)`**

Load a QSS or SCSS stylesheet:

```python
app = App()
app.load_stylesheet("styles.qss")
# or with QRC fallback
app.load_stylesheet("styles.qss", qrc_path=":/styles/default.qss")
```

**`enable_dark_mode()` / `enable_light_mode()`**

Toggle color schemes at runtime:

```python
app = App()
app.enable_dark_mode()  # Switch to dark
app.enable_light_mode()  # Switch to light
```

### App Subclasses with @entrypoint

Combine App subclasses with `@entrypoint` for maximum control:

```python
@entrypoint(title="My App", size=(1024, 768))
class MyApp(App):
    def __setup__(self):
        self.load_stylesheet("styles.scss")
        self.database = connect_database()

    def create_window(self):
        return MainWindow(self.database)
```

The `@entrypoint` decorator will:
1. Instantiate your App subclass
2. Apply dark/light mode if configured
3. Apply stylesheet if configured
4. Call `create_window()` if defined
5. Apply window config (title, size) to the returned window
6. Show the window and run the event loop

## The run_app() Function

The `run_app()` function is a standalone helper that runs any QApplication with qasync integration and CTRL-C handling.

```python
from qtpy.QtWidgets import QApplication, QLabel
from qtpie import run_app

app = QApplication([])
label = QLabel("Hello")
label.show()
run_app(app)  # Blocks until quit
```

This is useful when you have a vanilla QApplication but want qasync support without subclassing App.

### Signal Handling

`run_app()` automatically handles CTRL-C (SIGINT) gracefully:

```python
app = QApplication([])
window = MyWindow()
window.show()
run_app(app)  # Press CTRL-C to quit cleanly
```

The signal handler calls `app.quit()`, allowing cleanup code to run before exit.

### Async Support

`run_app()` sets up a qasync event loop, enabling async/await in your Qt application:

```python
from qtpie import run_app
import asyncio

app = QApplication([])

async def background_task():
    while True:
        print("Background work")
        await asyncio.sleep(1)

asyncio.create_task(background_task())
window = MyWindow()
window.show()
run_app(app)
```

## Common Patterns

### Simple Script Entry Point

```python
@entrypoint
def main():
    label = QLabel("Quick test")
    label.resize(400, 200)
    return label
```

### Production Application

```python
@entrypoint(
    title="MyApp Pro",
    size=(1280, 720),
    stylesheet="styles.scss",
    watch_stylesheet=True,  # Dev only
    translations=["translations.yml", "custom.yml"],
    language="en"
)
class ProductionApp(App):
    def __setup__(self):
        self.config = load_config()
        self.db = connect_database(self.config.db_url)

    def create_window(self):
        return MainWindow(self.db)
```

### Testing Without Auto-Run

```python
# app.py
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Hello!")

# test_app.py
from app import MyApp

def test_my_app(qapp):
    # MyApp doesn't auto-run in tests because module != __main__
    widget = MyApp()
    assert widget.label.text() == "Hello!"
```

### Multiple Entry Points

Use the `window=` parameter to decouple entry logic from window classes:

```python
# windows.py
@widget
class MainWindow(Widget):
    label: QLabel = new("Main Window")

@widget
class AdminWindow(Widget):
    label: QLabel = new("Admin Mode")

# main.py
from windows import MainWindow

@entrypoint(window=MainWindow)
def main():
    print("Starting main app")

# admin.py
from windows import AdminWindow

@entrypoint(window=AdminWindow)
def admin():
    print("Starting admin app")
```

Run `python main.py` or `python admin.py` to launch different windows with the same underlying widget classes.
