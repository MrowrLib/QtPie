# Entry Points

The `@entrypoint` decorator runs your QtPie application. Add it to any `@widget`, `@window`, or `@app` class.

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, Variable, new, widget, entrypoint

@entrypoint
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("Increment", clicked="on_click")

    def on_click(self) -> None:
        self._count += 1
```

Run with `python counter.py` - that's it!

## How It Works

When you run the file directly:

1. Creates a `QApplication` if none exists
2. Instantiates your widget/window/app
3. Shows it
4. Runs the event loop

When imported as a module, it does nothing - the class remains usable normally for testing or composition.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `None` | Window title |
| `size` | `tuple[int, int]` | `None` | Window size (width, height) |
| `dark_mode` | `bool` | `False` | Enable dark mode |
| `light_mode` | `bool` | `False` | Enable light mode |
| `stylesheet` | `str` | `None` | Path to QSS/SCSS file or QRC resource |
| `watch_stylesheet` | `bool` | `False` | Hot-reload stylesheet on changes |
| `scss_search_paths` | `list[str]` | `None` | Directories for SCSS @import |
| `translations` | `str \| list[str]` | `None` | Path(s) to translation YAML files |
| `language` | `str` | `"en"` | Default language code |
| `watch_translations` | `bool` | `False` | Hot-reload translations on changes |

## Usage

=== "Widget"

    ```python
    @entrypoint
    @widget
    class MyApp(Widget):
        _label: QLabel = new("Hello!")
    ```

=== "Window"

    ```python
    @entrypoint
    @window
    class MyApp(Window):
        _label: QLabel = new("Hello!")
    ```

=== "App"

    ```python
    @entrypoint
    @app
    class MyApp(App):
        _label: QLabel = new("Hello!")
    ```

## Stylesheets

### QSS File

```python
@entrypoint(stylesheet="styles/app.qss")
@widget
class MyApp(Widget):
    ...
```

### SCSS File (Auto-Compiled)

```python
@entrypoint(stylesheet="styles/app.scss")
@widget
class MyApp(Widget):
    ...
```

### QRC Resource

```python
@entrypoint(stylesheet=":/styles/app.qss")
@widget
class MyApp(Widget):
    ...
```

### Hot-Reload (Development)

```python
@entrypoint(
    stylesheet="styles/app.scss",
    watch_stylesheet=True  # Reloads when file changes
)
@widget
class MyApp(Widget):
    ...
```

## Translations

```python
from qtpie import t

@entrypoint(
    translations="i18n/messages.yml",
    language="en",
    watch_translations=True
)
@widget
class MyApp(Widget):
    _greeting: QLabel = new(t("Hello"))
```

See [Translations](translations.md) for the full translation system.

## With a Function

You can also decorate a function that returns a widget:

```python
@entrypoint
def main() -> QLabel:
    return QLabel("Hello!")
```

### Async Functions

```python
@entrypoint
async def main() -> QWidget:
    data = await fetch_data()
    return DataViewer(data)
```

## Decorator Order

`@entrypoint` must be the **outermost** decorator:

```python
@entrypoint      # First (outermost)
@widget          # Second
class MyApp(Widget):
    ...
```

## Testing

The decorated class remains instantiable without running the app:

```python
@entrypoint
@widget
class MyApp(Widget):
    _label: QLabel = new("Test")

# In tests - no app runs, class works normally
def test_my_app():
    app = QApplication([])
    w = MyApp()
    assert w._label.text() == "Test"
```

## See Also

- [Widgets](../basics/widgets.md) - Building widgets
- [Windows & Menus](windows-menus.md) - Main windows with menus
- [App](app.md) - Custom application classes
- [Styling](styling.md) - Stylesheet options
- [Translations](translations.md) - Translation system
