# run_app()

Standalone function to run a QApplication with qasync event loop support.

## Overview

`run_app()` is a helper function that sets up qasync and runs any QApplication. Unlike the standard `app.exec()`, it provides full async/await support for modern Python async code.

**Key differences from `@entrypoint`:**
- `@entrypoint` - Declarative decorator that automatically creates the app and runs it when module is `__main__`
- `run_app()` - Imperative function you call explicitly to run an existing QApplication instance

## Basic Usage

```python
from qtpy.QtWidgets import QApplication, QLabel
from qtpie import run_app

app = QApplication([])
label = QLabel("Hello World!")
label.show()

run_app(app)  # Blocks until app quits
```

## Why Use run_app()?

Standard Qt uses `app.exec()` to run the event loop, but this doesn't support async/await:

```python
# Standard Qt - no async support
app = QApplication([])
window = MyWindow()
window.show()
app.exec()  # Can't use async/await in slots
```

With `run_app()`, you get:
- Full async/await support in signals and slots
- Compatibility with asyncio libraries
- Better integration with modern Python async code

```python
# QtPie - full async support
from qtpie import run_app

app = QApplication([])
window = MyWindow()  # Can use async slots!
window.show()
run_app(app)
```

## API Reference

```python
def run_app(app: QApplication) -> int
```

**Parameters:**
- `app: QApplication` - The QApplication instance to run

**Returns:**
- `int` - The application exit code (always 0 currently)

**Behavior:**
1. Sets up qasync event loop for the application
2. Runs until the application quits
3. Blocks until `app.quit()` is called

## Examples

### With Plain QApplication

```python
from qtpy.QtWidgets import QApplication, QLabel
from qtpie import run_app

app = QApplication([])

label = QLabel("Hello run_app")
label.show()

run_app(app)  # Sets up qasync and runs event loop
```

### With Custom QApplication Subclass

Works with any QApplication subclass:

```python
from qtpy.QtWidgets import QApplication
from qtpie import run_app

class CustomApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        # Custom initialization
        self.setApplicationName("My App")

app = CustomApp([])
window = MyWindow()
window.show()

run_app(app)
```

### With QtPie's App Class

The `App` class has a `run()` method that calls `run_app()` internally:

```python
from qtpie import App

app = App("My App", dark_mode=True)
window = MyWindow()
window.show()

# These are equivalent:
app.run()           # Convenience method
run_app(app)        # Direct call
```

### Exit Codes

```python
from qtpy.QtWidgets import QApplication, QPushButton
from qtpie import run_app

app = QApplication([])

button = QPushButton("Quit")
button.clicked.connect(app.quit)
button.show()

exit_code = run_app(app)
print(f"App exited with code: {exit_code}")  # Always 0 currently
```

## When to Use run_app() vs @entrypoint

### Use `run_app()` when:
- You need manual control over app creation and initialization
- You're working with existing QApplication code
- You want explicit event loop startup
- You're integrating QtPie into a larger application

```python
from qtpy.QtWidgets import QApplication
from qtpie import run_app

app = QApplication([])

# Manual setup
app.setApplicationName("My App")
app.setStyle("Fusion")

# Create and show UI
window = MyWindow()
window.show()

# Explicit run
run_app(app)
```

### Use `@entrypoint` when:
- You want declarative, automatic app lifecycle
- You're creating a standalone application
- You want single-file app simplicity
- You prefer the "run when main" pattern

```python
from qtpie import entrypoint, widget, make
from qtpy.QtWidgets import QWidget, QLabel

@entrypoint
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Hello!")

# That's it! Runs automatically when python myapp.py
```

## Integration with Async Code

The qasync integration allows you to use async/await in your Qt application:

```python
import asyncio
from qtpy.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
from qtpie import run_app

async def fetch_data():
    await asyncio.sleep(1)
    return "Data loaded!"

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.button = QPushButton("Load Data")
        self.button.clicked.connect(self.on_click)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)

    async def on_click(self):
        self.button.setText("Loading...")
        data = await fetch_data()
        self.button.setText(data)

app = QApplication([])
widget = MyWidget()
widget.show()

run_app(app)  # Enables async slots to work
```

## Implementation Details

Under the hood, `run_app()`:
1. Creates a `qasync.QEventLoop` for the QApplication
2. Sets it as the asyncio event loop
3. Connects to `app.aboutToQuit` signal
4. Runs the event loop until the quit signal fires
5. Returns exit code 0

This is the same mechanism used by `App.run()` and `@entrypoint`.

## See Also

- [App Class](app.md) - QApplication subclass with lifecycle hooks
- [@entrypoint](../decorators/entry-point.md) - Declarative entry point decorator
- [App & Entry Points Guide](../../guides/app.md) - Complete guide to application lifecycle
