# @entrypoint

```python
@entrypoint(
    *,
    dark_mode: bool = False,
    light_mode: bool = False,
    title: str | None = None,
    size: tuple[int, int] | None = None,
    stylesheet: str | None = None,
    watch_stylesheet: bool = False,
    scss_search_paths: list[str] | None = None,
    window: type[QWidget] | None = None,
    translations: str | list[str] | None = None,
    language: str = "en",
    watch_translations: bool = False
)
```

Marks a function or class as the application entry point. When the decorated module is run as `__main__`, QtPie automatically creates a QApplication, runs the entry point, and starts the event loop.

## Parameters

### dark_mode
**Type:** `bool`
**Default:** `False`

Enable dark mode color scheme for the application.

```python
@entrypoint(dark_mode=True)
@widget
class MyApp(Widget):
    label: QLabel = new("Dark mode enabled")
```

### light_mode
**Type:** `bool`
**Default:** `False`

Enable light mode color scheme for the application.

```python
@entrypoint(light_mode=True)
@widget
class MyApp(Widget):
    label: QLabel = new("Light mode enabled")
```

Note: Only one of `dark_mode` or `light_mode` should be `True`. If both are `False`, the system default is used.

### title
**Type:** `str | None`
**Default:** `None`

Window title to display.

```python
@entrypoint(title="My Application v1.0")
def main():
    return MyWidget()
```

If `None`, the window title is not set (Qt defaults to empty or class name).

### size
**Type:** `tuple[int, int] | None`
**Default:** `None`

Window dimensions as `(width, height)` in pixels.

```python
@entrypoint(size=(1024, 768))
@widget
class MyApp(Widget):
    label: QLabel = new("Window is 1024x768")
```

If `None`, the window uses its natural size.

### stylesheet
**Type:** `str | None`
**Default:** `None`

Path to a stylesheet file. Supports three formats:

**QSS Files:**
```python
@entrypoint(stylesheet="styles.qss")
def main():
    return MyWidget()
```

**SCSS Files:**
```python
@entrypoint(stylesheet="styles.scss")
def main():
    return MyWidget()
```

**QRC Resources:**
```python
@entrypoint(stylesheet=":/styles/app.qss")
def main():
    return MyWidget()
```

If the file doesn't exist, no stylesheet is applied (fails silently).

### watch_stylesheet
**Type:** `bool`
**Default:** `False`

Enable hot-reload for stylesheet files. When `True`, the stylesheet recompiles and reloads automatically when the file changes.

```python
@entrypoint(
    stylesheet="styles.scss",
    watch_stylesheet=True
)
@widget
class MyApp(Widget):
    label: QLabel = new("Styles hot-reload on save")
```

**Notes:**
- Only works for filesystem paths (not QRC resources)
- SCSS files recompile on each change
- Useful during development; disable in production

### scss_search_paths
**Type:** `list[str] | None`
**Default:** `None`

Directories to search when resolving SCSS `@import` statements.

```python
@entrypoint(
    stylesheet="main.scss",
    scss_search_paths=["./themes", "./partials", "./vendor"]
)
def main():
    return MyWidget()
```

If `None` and the stylesheet is an SCSS file, the parent directory of the SCSS file is used as the search path.

### window
**Type:** `type[QWidget] | None`
**Default:** `None`

A widget class to instantiate as the main window. Useful for decoupling entry point logic from window classes.

```python
@widget
class MainWindow(Widget):
    label: QLabel = new("Main Window")

@entrypoint(window=MainWindow)
def main():
    print("Initializing application...")
    # No need to return anything
```

If both `window=` is set and the entry function returns a widget, the function's return value takes precedence.

### translations
**Type:** `str | list[str] | None`
**Default:** `None`

Path to a translation YAML file, or list of paths.

```python
# Single file
@entrypoint(translations="translations.yml")
def main():
    return MyWidget()

# Multiple files (merged)
@entrypoint(translations=["base.yml", "overrides.yml"])
def main():
    return MyWidget()
```

See the [Translations guide](../../guides/translations.md) for YAML format.

### language
**Type:** `str`
**Default:** `"en"`

Language code to use for translations.

```python
@entrypoint(
    translations="translations.yml",
    language="fr"  # Use French
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))  # Shows "Bonjour"
```

Common codes: `"en"`, `"fr"`, `"de"`, `"es"`, `"ja"`, etc.

### watch_translations
**Type:** `bool`
**Default:** `False`

Enable hot-reload for translation files. When `True`, translation changes automatically retranslate all widgets.

```python
@entrypoint(
    translations="translations.yml",
    language="fr",
    watch_translations=True
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))
```

Useful during development for testing translations.

## Behavior

### Auto-Run Conditions

The `@entrypoint` decorator only auto-runs when **both** of these are true:

1. The decorated module's `__module__` is `"__main__"` (i.e., run directly)
2. No `QApplication` instance exists yet

```python
# app.py
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Hello")

# Run directly - auto-starts
# $ python app.py

# Import elsewhere - does NOT auto-start
# from app import MyApp
# widget = MyApp()  # Works normally
```

This allows entry point modules to be imported in tests without side effects.

### Entry Point Types

The decorator accepts several types of targets:

**Widget Class:**
```python
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Hello")
```

**Function Returning a Widget:**
```python
@entrypoint
def main():
    return QLabel("Hello")
```

**Sync or Async Function:**
```python
@entrypoint
async def main():
    data = await fetch_data()
    return DataViewer(data)
```

Async functions run in a qasync event loop with CTRL-C handling.

**App Subclass:**
```python
@entrypoint
class MyApp(App):
    def create_window(self):
        return MainWindow()
```

### Execution Flow

When auto-run triggers, the decorator:

1. Creates a `QApplication` (or uses the decorated App subclass)
2. Applies `dark_mode` or `light_mode` if configured
3. Loads and applies `stylesheet` if configured
4. Loads `translations` if configured
5. Executes the entry point:
   - For App subclasses: calls `create_window()` if defined
   - For functions: calls the function and captures the return value
   - For widget classes: instantiates the class
6. Applies `title` and `size` to the window if provided
7. Shows the window
8. Runs the event loop (blocking)

### Return Values

Functions decorated with `@entrypoint` can return:

- A `QWidget` instance (shown as main window)
- `None` (no window shown, but event loop runs if `window=` is set)
- Any other value (ignored)

```python
@entrypoint
def main():
    label = QLabel("I'll be shown")
    return label  # This widget becomes the main window

@entrypoint(window=MyWindow)
def main():
    print("Setup complete")
    # No return - MyWindow is still shown via window= param
```

## Examples

### Minimal Entry Point

```python
from qtpie import entrypoint
from qtpy.QtWidgets import QLabel

@entrypoint
def main():
    return QLabel("Hello, QtPie!")
```

### Full Configuration

```python
@entrypoint(
    title="MyApp Pro",
    size=(1280, 720),
    dark_mode=True,
    stylesheet="styles.scss",
    watch_stylesheet=True,
    scss_search_paths=["./themes"],
    translations=["translations.yml"],
    language="en",
    watch_translations=True
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Welcome"))
```

### App Subclass with Lifecycle

```python
@entrypoint(title="Database App")
class MyApp(App):
    def __setup__(self):
        self.db = connect_database()

    def create_window(self):
        return MainWindow(self.db)
```

### Async Entry Point

```python
@entrypoint(title="Async App")
async def main():
    # Fetch data asynchronously
    users = await fetch_users()
    weather = await fetch_weather()

    # Create and return window with data
    return DashboardWindow(users, weather)
```

### Testing-Friendly Entry Point

```python
# app.py
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Production App")

# test_app.py
from app import MyApp

def test_app_creation(qapp):
    # @entrypoint doesn't run because this is a test module
    app = MyApp()
    assert app.label.text() == "Production App"
```

### Multiple Files, Same Window

```python
# windows.py
@widget
class MainWindow(Widget):
    label: QLabel = new("Main")

# dev.py
from windows import MainWindow

@entrypoint(
    window=MainWindow,
    stylesheet="dev.scss",
    watch_stylesheet=True
)
def dev():
    print("Dev mode")

# prod.py
from windows import MainWindow

@entrypoint(
    window=MainWindow,
    stylesheet="prod.qss"
)
def prod():
    print("Production mode")
```

Run `python dev.py` for dev mode with hot-reload, or `python prod.py` for production.

## Notes

- The decorator can be used with or without parentheses: `@entrypoint` or `@entrypoint()`
- Configuration is stored on the target's `_qtpie_entry_config` attribute
- CTRL-C (SIGINT) is handled gracefully - sends `quit()` to the app
- QRC stylesheet paths (starting with `:/`) ignore `watch_stylesheet`
- If a stylesheet file doesn't exist, it's silently ignored (no error)
- Dark/light mode applies platform-specific color schemes before any stylesheet

## See Also

- [App & Entry Points Guide](../../guides/app.md) - Comprehensive guide with patterns
- [App Class](../classes/app.md) - QApplication subclass with lifecycle hooks
- [run_app()](../functions/run_app.md) - Standalone event loop runner
