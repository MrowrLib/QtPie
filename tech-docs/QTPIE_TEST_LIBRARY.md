# qtpie_test Library

A strongly-typed, modern testing library for Qt applications that wraps pytest-qt with a cleaner API.

## Goals

1. **Fully typed** - No `*args, **kwargs` wrappers. Every method has proper type hints that pyright understands.
2. **Modern Python** - Snake_case, keyword-only args, clean API design.
3. **Hide pytest-qt internals** - Users interact only with our API. pytest-qt is an implementation detail.
4. **Extensible** - Room to grow with QtPie-specific test helpers as the framework evolves.

## Why This Exists

pytest-qt is great, but it has typing issues:

```python
# pytest-qt's mouseClick - no type hints, just forwards to QTest
@staticmethod
def mouseClick(*args, **kwargs):
    qt_api.QtTest.QTest.mouseClick(*args, **kwargs)
```

This causes pyright errors with strict type checking. Our wrapper calls `QTest.mouseClick` directly with proper types:

```python
def click(
    self,
    widget: QWidget,
    *,
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    QTest.mouseClick(widget, button, modifiers)
```

## Architecture

```
qtpie_test/
  __init__.py      # Exports QtDriver
  driver.py        # QtDriver class - the main API
  plugin.py        # pytest plugin that provides the `qt` fixture
  pyproject.toml   # Package config with pytest11 entry point
```

### How the Fixture Works

1. `pyproject.toml` registers a pytest11 entry point:
   ```toml
   [project.entry-points.pytest11]
   qtpie_test = "qtpie_test.plugin"
   ```

2. `plugin.py` defines the `qt` fixture that wraps pytest-qt's `qtbot`:
   ```python
   @pytest.fixture
   def qt(qtbot: QtBot) -> QtDriver:
       return QtDriver(qtbot)
   ```

3. Tests automatically get the `qt` fixture - no imports needed in conftest.py

## Usage

```python
from qtpie_test import QtDriver
from samples.my_app import MainWindow

class TestMainWindow:
    def test_button_click(self, qt: QtDriver) -> None:
        window = MainWindow()
        qt.track(window)  # Register for cleanup

        qt.click(window.button)

        assert window.label.text() == "Clicked!"
```

### Running Tests

**Important:** Use `python -m pytest` to ensure workspace packages are on the path:

```bash
uv run python -m pytest tests/ -v
```

Using `uv run pytest` directly won't work because pytest runs from root and can't find workspace packages.

## Current API

### `qt.track(*widgets)`
Register widgets for automatic cleanup after the test. Equivalent to `qtbot.addWidget()`.

```python
qt.track(window)
qt.track(window, dialog, popup)  # Multiple at once
```

### `qt.click(widget, *, button, modifiers)`
Click on a widget. Fully typed.

```python
qt.click(button)  # Left click
qt.click(button, button=Qt.MouseButton.RightButton)  # Right click
qt.click(button, modifiers=Qt.KeyboardModifier.ControlModifier)  # Ctrl+click
```

### `qt.double_click(widget, *, button, modifiers)`
Double-click on a widget.

```python
qt.double_click(item)
```

## Future Functionality Ideas

### Input Simulation
- `qt.type(widget, text)` - Type text into a widget
- `qt.press(key)` - Press a key
- `qt.key_combo(widget, "Ctrl+S")` - Key combinations with string syntax
- `qt.drag(from_widget, to_widget)` - Drag and drop

### Waiting
- `qt.wait_for(signal, timeout)` - Wait for a signal
- `qt.wait_until(condition, timeout)` - Wait for a condition
- `qt.wait(ms)` - Simple delay

### Assertions (maybe)
- `qt.assert_visible(widget)`
- `qt.assert_text(widget, expected)`
- `qt.assert_enabled(widget)`

### QtPie-Specific Helpers
As QtPie develops, we'll add helpers for:
- Testing reactive bindings
- Testing style changes
- Testing component state
- Snapshot testing for widget trees

### Context Managers
```python
with qt.wait_for(window.loaded):
    window.load_data()

with qt.capture_exceptions() as errors:
    qt.click(broken_button)
assert len(errors) == 1
```

### Fluent API (maybe)
```python
qt.on(window.button).click().expect_text(window.label, "Clicked!")
```

## Dependencies

- `pytest-qt` - The underlying Qt testing framework
- `pyside6` - Qt bindings (could be made flexible for PyQt in future)

## Package Structure in Workspace

```
QtPie/
  qtpie_test/           # This library
    pyproject.toml
    __init__.py
    driver.py
    plugin.py
  tests/
    pyproject.toml      # Depends on qtpie_test
    conftest.py
    samples/
      test_regular_qt_app.py
```

The `tests/` package depends on `qtpie_test` in its pyproject.toml:
```toml
[project]
dependencies = [
  "qtpie_test",
]

[tool.uv.sources]
qtpie_test = {workspace = true}
```
