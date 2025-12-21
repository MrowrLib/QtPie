# App & Entry Points

QtPie provides three ways to launch your application:

1. **`@entry_point` decorator** - The simplest approach for single-file apps
2. **`App` class** - Full control with lifecycle hooks
3. **`run_app()` function** - Use any QApplication with qasync support

---

## The `@entry_point` Decorator

The `@entry_point` decorator is the easiest way to create a runnable app. When you run the file directly (as `__main__`), it automatically creates a QApplication and starts the event loop.

### Function Entry Point

The simplest form - just return a widget:

```python
from qtpie import entry_point
from qtpy.QtWidgets import QLabel

@entry_point
def main():
    return QLabel("Hello, World!")
```

Run it: `python my_app.py`

That's it! No manual app creation, no event loop boilerplate.

### Widget Class Entry Point

Combine with `@widget` for declarative UI:

```python
from qtpie import entry_point, make, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entry_point
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Count: 0")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")
    count: int = 0

    def increment(self):
        self.count += 1
        self.label.setText(f"Count: {self.count}")
```

### Configuration Options

Customize the app with parameters:

```python
@entry_point(
    dark_mode=True,
    title="My Application",
    size=(800, 600)
)
@widget
class MyApp(QWidget):
    ...
```

Available options:

- `dark_mode: bool` - Enable dark mode color scheme
- `light_mode: bool` - Enable light mode color scheme
- `title: str` - Set window title
- `size: tuple[int, int]` - Set window size (width, height)
- `stylesheet: str` - Path to QSS/SCSS file to load
- `window: type[QWidget]` - Widget class to instantiate as main window

### How It Works

The `@entry_point` decorator is smart about when to run:

- **When file is run directly** (`__main__`): Creates app, shows window, starts event loop
- **When imported**: Does nothing - just stores configuration

This means you can use the same class in tests or as a library:

```python
# my_app.py
@entry_point
@widget
class Counter(QWidget):
    ...

# test_app.py
from my_app import Counter  # Doesn't auto-run

def test_counter():
    widget = Counter()  # Just creates the widget
    assert widget.count == 0
```

### Async Entry Points

Entry points can be async functions:

```python
@entry_point
async def main():
    data = await fetch_data_async()
    return DataViewer(data)
```

The decorator handles qasync setup automatically.

---

## The `App` Class

For more control, subclass `App` (which extends `QApplication`):

```python
from typing import override
from qtpie import App, entry_point
from qtpy.QtWidgets import QLabel

@entry_point
class MyApp(App):
    @override
    def create_window(self):
        return QLabel("Hello from App!")
```

### Lifecycle Hooks

The `App` class provides hooks for custom initialization:

```python
from typing import override
from qtpie import App

class MyApp(App):
    @override
    def setup(self):
        """Called after App initialization."""
        print("App is ready!")
        # Set up services, load config, etc.

    @override
    def setup_styles(self):
        """Called during initialization for stylesheets."""
        self.load_stylesheet("styles.qss")

    @override
    def create_window(self):
        """Return the main window widget."""
        return MyMainWindow()
```

Hook order:
1. `__init__` - App initialization
2. `setup()` - General setup
3. `setup_styles()` - Load stylesheets

When using `@entry_point`, it also calls:
4. `create_window()` - Creates and shows the window
5. Event loop starts

### App Constructor

```python
app = App(
    name="My Application",      # App name (default: "Application")
    version="1.0.0",             # App version (default: "1.0.0")
    dark_mode=True,              # Enable dark mode
    light_mode=False,            # Enable light mode
    argv=sys.argv                # Command-line args
)
```

### Dark/Light Mode

Enable color schemes during initialization or at runtime:

```python
# At initialization
app = App(dark_mode=True)

# At runtime
app.enable_dark_mode()
app.enable_light_mode()
```

### Loading Stylesheets

```python
app = MyApp()
app.load_stylesheet("styles.qss")
app.load_stylesheet("styles.scss")  # SCSS works too
```

With QRC resources:

```python
app.load_stylesheet(
    "styles.qss",
    qrc_path=":/styles/main.qss"
)
```

### Running the App

The `App` class has two run methods:

```python
# Blocking - runs until app quits
app = MyApp()
window = app.create_window()
window.show()
exit_code = app.run()  # Blocks here
```

```python
# Async - for use in existing event loop
app = MyApp()
window = app.create_window()
window.show()
exit_code = await app.run_async()
```

---

## The `run_app()` Function

A standalone helper that works with any `QApplication`:

```python
from qtpie import run_app
from qtpy.QtWidgets import QApplication, QLabel

app = QApplication([])
label = QLabel("Hello!")
label.show()

run_app(app)  # Sets up qasync and runs event loop
```

### Why `run_app()`?

Standard Qt applications use `app.exec()`, but that doesn't support async/await. The `run_app()` function sets up qasync automatically, giving you:

- Full async/await support in signals/slots
- Compatibility with asyncio libraries
- Better integration with modern Python async code

### Using with Standard QApplication

```python
from qtpy.QtWidgets import QApplication
from qtpie import run_app

app = QApplication([])

# Set up your UI
window = MyWindow()
window.show()

# Run with qasync support
exit_code = run_app(app)
```

### Using with Custom QApplication

Works with any QApplication subclass:

```python
class CustomApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        # Custom initialization

app = CustomApp([])
# ... set up UI ...
run_app(app)
```

---

## Comparison: Which Should I Use?

### Use `@entry_point` when:
- Building single-file apps
- Want minimal boilerplate
- Don't need app lifecycle hooks
- Prototyping or creating examples

```python
@entry_point
@widget
class QuickApp(QWidget):
    ...
```

### Use `App` class when:
- Need lifecycle hooks (`setup()`, `setup_styles()`)
- Want to manage app state centrally
- Building larger applications with services/config
- Need custom QApplication subclass behavior

```python
@entry_point
class MyApp(App):
    def setup(self):
        self.load_config()
        self.init_database()
```

### Use `run_app()` when:
- Integrating QtPie into existing codebases
- Already have QApplication instance
- Need maximum control over app creation
- Using custom QApplication subclass

```python
app = QApplication([])
# ... existing setup code ...
run_app(app)
```

---

## Complete Examples

### Simple Counter (Function Entry Point)

```python
from qtpie import entry_point, make, widget, state
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entry_point
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self):
        self.count += 1
```

### App with Configuration (App Class)

```python
from typing import override
from qtpie import App, entry_point, make, widget
from qtpy.QtWidgets import QLabel, QWidget

@widget
class MainWindow(QWidget):
    label: QLabel = make(QLabel, "Welcome!")

@entry_point(dark_mode=True, title="My App", size=(1024, 768))
class MyApp(App):
    @override
    def setup(self):
        self.load_stylesheet("assets/styles.scss")

    @override
    def create_window(self):
        return MainWindow()
```

### Manual Control (run_app Function)

```python
from qtpie import run_app, App, make, widget
from qtpy.QtWidgets import QLabel, QWidget

@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello!")

# Manual setup
app = App("My Application", dark_mode=True)
app.load_stylesheet("styles.qss")

widget = MyWidget()
widget.show()

# Run
exit_code = run_app(app)
```

---

## Advanced: Async Applications

Full async example with background tasks:

```python
import asyncio
from qtpie import entry_point, make, widget, state
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entry_point
@widget
class AsyncCounter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    start_btn: QPushButton = make(QPushButton, "Start", clicked="start_counting")

    async def start_counting(self):
        self.start_btn.setEnabled(False)
        for i in range(10):
            await asyncio.sleep(1)
            self.count += 1
        self.start_btn.setEnabled(True)
```

The `run_app()` function (used internally by `@entry_point`) sets up qasync automatically, so async/await just works.

---

## Testing Entry Points

When writing tests, the `@entry_point` decorator won't auto-run because:

1. Tests import modules (not `__main__`)
2. pytest-qt creates QApplication already

```python
from qtpie_test import QtDriver
from my_app import MyApp  # Has @entry_point, won't auto-run

def test_my_app(qt: QtDriver):
    app = MyApp()  # Just creates the widget
    qt.track(app)

    assert app.label.text() == "Hello!"
```

See [Testing Guide](testing.md) for more details.

---

## See Also

- [Testing](testing.md) - Testing QtPie applications
- [@entry_point Reference](../reference/decorators/entry-point.md) - Full decorator API
- [App Class Reference](../reference/app/app.md) - Complete App class documentation
- [run_app() Reference](../reference/app/run-app.md) - Function details
