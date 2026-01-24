# Styles Watcher - Usage Patterns

This document describes the stylesheet watching features in QtPie, enabling live-reload of QSS and SCSS stylesheets during development.

## watch_qss - QSS File Watcher

Watches a QSS file and automatically applies changes to a widget.

```python
from qtpie.styles import watch_qss

watcher = watch_qss(widget, "path/to/styles.qss")
# Stylesheet is applied immediately if file exists
# Widget.styleSheet() updates automatically on file changes
watcher.stop()  # Stop watching when done
```

**Key behaviors:**
- Applies stylesheet immediately if file exists
- Watches for file changes and reapplies automatically
- Handles file creation (watches non-existent files)
- Handles editor save patterns (delete + recreate)

## watch_scss - SCSS Compiler + Watcher

Compiles SCSS to QSS and watches for changes. Requires libsass.

```python
from qtpie.styles import watch_scss

watcher = watch_scss(widget, "styles.scss", "output.qss")
# Compiles SCSS to QSS immediately, applies to widget
# Recompiles on any SCSS change
watcher.stop()
```

### SCSS with Import Paths

Watch multiple SCSS directories (partials, themes, etc.):

```python
watcher = watch_scss(
    widget,
    "main.scss",
    "output.qss",
    search_paths=["partials/", "themes/"]
)
```

Changes to imported files (e.g., `_variables.scss`) trigger recompilation.

### SCSS Variable Example

```scss
$color: purple;
QWidget { background-color: $color; }
```

## watch_styles - Convenience Function

Unified API that returns the appropriate watcher type:

```python
from qtpie.styles import watch_styles

# Returns ScssWatcher when scss_path provided
watcher = watch_styles(widget, "output.qss", scss_path="styles.scss")

# Returns QssWatcher when only qss_path provided
watcher = watch_styles(widget, "styles.qss")
```

## Watcher Classes

Direct access to watcher classes for more control:

```python
from qtpie.styles.watcher import QssWatcher, ScssWatcher

# Both emit stylesheetApplied signal when stylesheet is updated
watcher.stylesheetApplied.connect(on_styles_applied)
```

## Testing Patterns

When testing stylesheet watchers, use signal-based waiting:

```python
from qtpy.QtCore import QEventLoop, QTimer

def wait_for_signal(watcher, timeout_ms=2000):
    loop = QEventLoop()
    watcher.stylesheetApplied.connect(loop.quit)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
```

## QtDriver Integration

Use `qt.track(widget)` to ensure proper widget cleanup in tests:

```python
def test_example(qt: QtDriver, tmp_path: Path):
    widget = QWidget()
    qt.track(widget)
    watcher = watch_qss(widget, str(tmp_path / "styles.qss"))
    # ... test logic ...
    watcher.stop()
```
