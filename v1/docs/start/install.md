# Installation

## Requirements

**Python 3.13 or later** is required. QtPie uses modern Python features including the new type parameter syntax.

**Qt binding**: QtPie works with either:

- **PySide6** (recommended) - Official Qt for Python, LGPL licensed
- **PyQt6** - Alternative Qt binding, GPL/commercial licensed

QtPie will automatically detect which binding is available. If both are installed, it prefers PySide6.

## Install QtPie

=== "uv"

    ```bash
    uv add qtpie
    ```

    Then add a Qt binding:

    === "PySide6 (recommended)"

        ```bash
        uv add pyside6
        ```

    === "PyQt6"

        ```bash
        uv add pyqt6
        ```

=== "pip"

    ```bash
    pip install qtpie
    ```

    This installs QtPie but NOT a Qt binding. Install one separately:

    === "PySide6 (recommended)"

        ```bash
        pip install pyside6
        ```

    === "PyQt6"

        ```bash
        pip install pyqt6
        ```

=== "poetry"

    ```bash
    poetry add qtpie
    ```

    Then add a Qt binding:

    === "PySide6 (recommended)"

        ```bash
        poetry add pyside6
        ```

    === "PyQt6"

        ```bash
        poetry add pyqt6
        ```

## Verify Installation

```python
from qtpie import entrypoint, widget, make
from qtpy.QtWidgets import QWidget, QLabel

@entrypoint
@widget
class HelloWorld(QWidget):
    label: QLabel = make(QLabel, "Hello, QtPie!")
```

Save this to `hello.py` and run:

```bash
python hello.py
```

A window should appear with "Hello, QtPie!". Success!

## Qt Backend Selection

QtPie uses [qtpy](https://github.com/spyder-ide/qtpy) for Qt abstraction, which supports multiple Qt bindings.

**Default behavior**: qtpy automatically selects the first available binding in this order:

1. PySide6
2. PyQt6
3. PySide2 (not recommended)
4. PyQt5 (not recommended)

**Force a specific backend** with the `QT_API` environment variable:

```bash
# Linux/macOS
export QT_API=pyside6

# Windows (cmd)
set QT_API=pyside6

# Windows (PowerShell)
$env:QT_API = "pyside6"
```

Then run your app. Valid values: `pyside6`, `pyqt6`, `pyside2`, `pyqt5`.

## Optional Dependencies

QtPie includes optional features that require additional packages:

### SCSS Support

QtPie can compile SCSS to QSS stylesheets with hot reloading during development.

**Already included!** QtPie automatically installs `mrowrpurr-pyscss` for SCSS compilation.

No extra install needed. Just use `.scss` files:

```python
from qtpie import App

app = App()
app.load_stylesheet("styles/main.scss")  # Auto-compiles to QSS
```

See [SCSS Hot Reload](../guides/scss.md) for details.

### Testing Framework

For testing QtPie apps, install with the `test` extra:

=== "uv"

    ```bash
    uv add "qtpie[test]"
    ```

=== "poetry"

    ```bash
    poetry add "qtpie[test]"
    ```

=== "pip"

    ```bash
    pip install "qtpie[test]"
    ```

This provides the `QtDriver` test helper. See [Testing Guide](../guides/testing.md).

### Reactive Models

QtPie's data binding works with plain dataclasses and observant models.

**Already included!** QtPie automatically installs `observant` for reactive state.

Use `state()` for reactive fields:

```python
from qtpie import widget, state, make

@widget
class Counter(QWidget):
    count: int = state(0)  # Reactive state
    label: QLabel = make(QLabel, bind="Count: {count}")
```

See [Reactive State](../data/state.md) for details.

## Troubleshooting

### "No module named 'qtpy.QtWidgets'"

You haven't installed a Qt binding. Install PySide6 or PyQt6:

=== "uv"

    ```bash
    uv add pyside6
    ```

=== "poetry"

    ```bash
    poetry add pyside6
    ```

=== "pip"

    ```bash
    pip install pyside6
    ```

### "Could not find QtPie"

Make sure you're using Python 3.13+:

```bash
python --version
```

If you're using an older Python, upgrade or use a version manager like `pyenv` or `uv`.

### Import errors with multiple Qt versions

If you have both PySide6 and PyQt6 installed and get import errors, force a specific backend:

```bash
export QT_API=pyside6
```

### Still stuck?

Check the [GitHub Issues](https://github.com/MrowrLib/QtPie/issues) or file a new one.

## Next Steps

Now that QtPie is installed, let's build your first app:

[Hello World →](hello-world.md)
