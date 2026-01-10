# Installation

## Requirements

- Python 3.13+
- PySide6 or PyQt6

## Install QtPie

=== "uv"

    ```bash
    uv add qtpie
    ```

=== "poetry"

    ```bash
    poetry add qtpie
    ```

=== "pip"

    ```bash
    pip install qtpie
    ```

## Install with test extras

If you want to use QtPie's testing framework:

=== "uv"

    ```bash
    uv add "qtpie[test]"
    ```

=== "poetry"

    ```bash
    poetry add qtpie --extras test
    ```

=== "pip"

    ```bash
    pip install "qtpie[test]"
    ```

## Qt Backend

QtPie uses [qtpy](https://github.com/spyder-ide/qtpy) for Qt abstraction, so it works with either PySide6 or PyQt6.

Install your preferred Qt binding:

=== "uv"

    ```bash
    # PySide6 (recommended)
    uv add PySide6

    # Or PyQt6
    uv add PyQt6
    ```

=== "poetry"

    ```bash
    # PySide6 (recommended)
    poetry add PySide6

    # Or PyQt6
    poetry add PyQt6
    ```

=== "pip"

    ```bash
    # PySide6 (recommended)
    pip install PySide6

    # Or PyQt6
    pip install PyQt6
    ```

## Verify Installation

```python
from qtpie import widget, Widget, new

@widget
class Hello(Widget):
    pass

print("QtPie installed successfully!")
```

## Next Steps

- [Widgets](basics/widgets.md) - Learn about declarative widgets
- [Variables](state/variables.md) - Understand reactive state
