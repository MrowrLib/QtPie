# Installation

## Requirements

- Python 3.13+
- PySide6 or PyQt6

## Install with pip

```bash
pip install qtpie
```

## Install with uv (recommended)

```bash
uv add qtpie
```

## Install with test extras

If you want to use QtPie's testing framework:

```bash
pip install "qtpie[test]"
```

Or with uv:

```bash
uv add "qtpie[test]"
```

## Qt Backend

QtPie uses [qtpy](https://github.com/spyder-ide/qtpy) for Qt abstraction, so it works with either PySide6 or PyQt6.

Install your preferred Qt binding:

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

## Dependencies

QtPie automatically installs:

- `qtpy` - Qt abstraction layer
- `qasync` - Async support for Qt
- `pyyaml` - YAML parsing for translations
- `typer` - CLI framework

## Next Steps

- [Hello World Tutorial](hello-world.md) - Build your first app
- [Key Concepts](concepts.md) - Understand the fundamentals
