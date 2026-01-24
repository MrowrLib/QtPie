# @entrypoint Decorator - Usage Patterns

The `@entrypoint` decorator provides a declarative way to configure and run QtPie applications. It handles QApplication setup, stylesheets, dark mode, window configuration, and i18n.

## Basic Usage

### Minimal Entrypoint (No Config)

```python
@entrypoint
def my_main() -> QLabel:
    return QLabel("Hi")
```

### Entrypoint on Widget Class

```python
@entrypoint
@widget
class TestWidget(Widget):
    label: QLabel = new("Hello!")
```

Note: `@entrypoint` goes **above** `@widget`.

## Configuration Options

### Dark Mode and Window Settings

```python
@entrypoint(dark_mode=True, title="My App", size=(1024, 768))
@widget
class TestWidget(Widget):
    label: QLabel = new("Test")
```

### Light Mode

```python
@entrypoint(light_mode=True)
@widget
class MyApp(Widget):
    ...
```

## Stylesheet Support

### QSS Stylesheet

```python
@entrypoint(stylesheet="styles.qss")
def my_main() -> QLabel:
    return QLabel("Hi")
```

### SCSS Stylesheet with Watch Mode

```python
@entrypoint(stylesheet="styles.scss", watch_stylesheet=True)
def my_main() -> QLabel:
    return QLabel("Styled")
```

Hot-reloads stylesheet on file changes during development.

### SCSS with Search Paths

```python
@entrypoint(
    stylesheet="styles.scss",
    scss_search_paths=["path/to/partials", "path/to/themes"],
)
def my_main() -> QLabel:
    return QLabel("Hi")
```

### SCSS Output Path

```python
@entrypoint(
    stylesheet="styles.scss",
    scss_output="compiled/styles.qss",
    watch_stylesheet=True,
)
```

Writes compiled QSS to a specified location instead of temp directory.

### QRC Resource Stylesheet

```python
@entrypoint(stylesheet=":/styles/app.qss")
def my_main() -> QLabel:
    return QLabel("Hi")
```

Note: `watch_stylesheet` is ignored for QRC paths (can't watch bundled resources).

## Application Identity (QSettings Support)

### Organization and Application Name

```python
@entrypoint(org="MyCompany", app="MyProduct")
@widget
class TestWidget(Widget):
    label: QLabel = new("Hello")
```

Used by Qt for `QSettings` storage paths.

## Function-Based Entrypoints

### Return Widget

```python
@entrypoint(dark_mode=True)
def my_main() -> QLabel:
    return QLabel("Hi")
```

### Return QApplication

```python
@entrypoint(dark_mode=True, title="Test App")
def my_main() -> App:
    return App()
```

The returned `App` instance is used for running the event loop.

## Key Behaviors

1. **Auto-run detection**: Only runs automatically when the module is `__main__` and no `QApplication` exists
2. **Preserves callable**: Decorated functions/classes remain usable normally
3. **Config storage**: Configuration is stored as `_qtpie_entry_config` attribute on the decorated object

## EntryConfig Defaults

| Parameter | Default |
|-----------|---------|
| `dark_mode` | `False` |
| `light_mode` | `False` |
| `title` | `None` |
| `size` | `None` |
| `stylesheet` | `None` |
| `watch_stylesheet` | `False` |
| `scss_search_paths` | `()` |
| `scss_output` | `None` |
| `org` | `None` |
| `app` | `None` |
| `window` | `None` |
