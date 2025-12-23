# @stylesheet

The `@stylesheet` decorator applies a QSS or SCSS stylesheet to a widget class. Unlike `@entrypoint`'s stylesheet option (which applies to the entire application), `@stylesheet` scopes styles to the decorated widget and its children.

## Basic Usage

```python
from qtpie import stylesheet, widget
from qtpy.QtWidgets import QWidget

@stylesheet("card.qss")
@widget
class Card(QWidget):
    pass
```

The stylesheet is loaded when the widget is instantiated and applied via `widget.setStyleSheet()`.

## Parameters

### path (positional, required)

**Type:** `str`

Path to a QSS or SCSS stylesheet file. SCSS files are automatically compiled to QSS.

```python
@stylesheet("styles.qss")  # Plain QSS
class MyWidget(QWidget):
    pass

@stylesheet("styles.scss")  # SCSS (compiled automatically)
class MyWidget(QWidget):
    pass
```

### watch

**Type:** `bool`
**Default:** `False`

Enable hot-reload. When `True`, changes to the stylesheet file are automatically detected and applied without restarting the app.

```python
@stylesheet("styles.scss", watch=True)
@widget
class MyWidget(QWidget):
    pass
# Edit styles.scss and save - widget updates instantly!
```

### scss_search_paths

**Type:** `list[str] | None`
**Default:** `None`

Directories to search when resolving SCSS `@import` statements. If `None`, the stylesheet's parent directory is used automatically.

```python
@stylesheet(
    "main.scss",
    watch=True,
    scss_search_paths=["partials/", "themes/"]
)
@widget
class MyWidget(QWidget):
    pass
```

## Examples

### Simple QSS

```python
from qtpie import stylesheet, widget, make
from qtpy.QtWidgets import QWidget, QLabel

@stylesheet("card.qss")
@widget
class Card(QWidget):
    title: QLabel = make(QLabel, "Card Title")
```

`card.qss`:
```css
QWidget {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
}

QLabel {
    font-size: 18px;
    font-weight: bold;
}
```

### SCSS with Hot Reload

```python
from qtpie import stylesheet, widget, make
from qtpy.QtWidgets import QWidget, QPushButton

@stylesheet("button.scss", watch=True)
@widget
class StyledButton(QWidget):
    button: QPushButton = make(QPushButton, "Click Me")
```

`button.scss`:
```scss
$primary: #007bff;
$radius: 4px;

QPushButton {
    background-color: $primary;
    color: white;
    border-radius: $radius;
    padding: 8px 16px;

    &:hover {
        background-color: darken($primary, 10%);
    }
}
```

### SCSS with Imports

Project structure:
```
myapp/
├── styles/
│   ├── card.scss
│   └── partials/
│       ├── _variables.scss
│       └── _mixins.scss
└── widgets/
    └── card.py
```

`card.py`:
```python
from qtpie import stylesheet, widget, make
from qtpy.QtWidgets import QWidget, QLabel

@stylesheet(
    "styles/card.scss",
    watch=True,
    scss_search_paths=["styles/partials"]
)
@widget
class Card(QWidget):
    title: QLabel = make(QLabel, "Card")
```

`styles/partials/_variables.scss`:
```scss
$bg-color: #f8f9fa;
$border-color: #dee2e6;
$text-color: #212529;
```

`styles/card.scss`:
```scss
@import 'variables';

QWidget {
    background-color: $bg-color;
    border: 1px solid $border-color;
}

QLabel {
    color: $text-color;
}
```

### On App Subclass

You can also use `@stylesheet` on `App` subclasses to apply app-wide styles:

```python
from qtpie import App, stylesheet

@stylesheet("app.scss", watch=True)
class MyApp(App):
    def create_window(self):
        return MainWindow()
```

Note: When used on `App`, the stylesheet is applied to the entire application, similar to `@entrypoint(stylesheet=...)`.

## Combining with @widget

The `@stylesheet` decorator works seamlessly with `@widget`. Place `@stylesheet` on the outside:

```python
@stylesheet("styles.scss", watch=True)
@widget(layout="vertical", classes=["card"])
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")
    button: QPushButton = make(QPushButton, "Click")
```

## Comparison with Other Approaches

| Approach | Scope | Best For |
|----------|-------|----------|
| `@stylesheet` on widget | Widget + children | Component-level styles, reusable styled components |
| `@entrypoint(stylesheet=...)` | Entire app | App-wide styles, simple apps |
| `@stylesheet` on App | Entire app | App-wide styles with App subclass |
| `watch_scss()` / `watch_qss()` | Manual target | Maximum control, dynamic paths |

### When to Use @stylesheet

- **Component libraries**: Style reusable widgets independently
- **Scoped styles**: Keep styles isolated to specific widgets
- **Multiple stylesheets**: Different widgets with different styles

### When to Use @entrypoint(stylesheet=...)

- **Single-file apps**: Simple setup, one stylesheet for everything
- **App-wide themes**: Consistent styling across all widgets

## Watcher Lifecycle

When `watch=True`, a file watcher is created and stored on the widget instance. The watcher:

- Automatically stops when the widget is garbage collected
- Can be manually stopped via `widget._stylesheet_watcher.stop()`
- Handles editor save behaviors (delete + recreate, rapid saves)

## Graceful Error Handling

If the stylesheet file doesn't exist:

- No error is raised
- The widget's stylesheet is set to empty string
- If `watch=True`, the watcher monitors for the file to be created

This allows you to start your app before creating the stylesheet file.

## See Also

- [SCSS Hot Reload Guide](../../guides/scss.md) - Detailed SCSS workflow
- [@entrypoint](./entrypoint.md) - App-level stylesheet option
- [Styling Basics](../../basics/styling.md) - CSS classes and QSS fundamentals
- [Class Helpers](../styles/class-helpers.md) - Dynamic class manipulation
