# QtPie - Context for Claude

## What Is This?

**QtPie** is a declarative UI library for Qt/PySide6 in Python. Think React/Vue patterns but for desktop apps.

### The Problem

Qt is powerful but verbose. A simple widget requires:
- Manual `__init__` with `super().__init__()`
- Manual layout creation and widget adding
- Manual signal/slot connections
- Lots of boilerplate

### The Solution

Declarative decorators + dataclass-like syntax:

```python
# BEFORE: 40+ lines of boilerplate
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.label = QLabel("Hello")
        layout.addWidget(self.label)
        self.button = QPushButton("Click")
        self.button.clicked.connect(self.on_click)
        layout.addWidget(self.button)
    ...

# AFTER: Clean, declarative
@widget()
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")
    button: QPushButton = make(QPushButton, "Click", clicked="on_click")

    def on_click(self) -> None:
        ...
```

---

## Repo Structure

```
QtPie/
├── qtpie/                 # THE LIBRARY - this is what we're building
│   ├── decorators/        # @widget, @window, etc.
│   └── factories/         # make(), make_form_row(), etc.
│
├── qtpie_test/            # Test framework wrapper around pytest-qt
│   ├── driver.py          # QtDriver - strongly-typed test API
│   └── plugin.py          # pytest plugin (provides `qt` fixture)
│
├── qtpie_samples/         # Example apps using qtpie
│   └── samples/
│       └── regular_qt_app/  # "Before" example (plain Qt, no qtpie)
│
├── tests/                 # All tests live here
│   ├── samples/           # Tests for sample apps
│   └── test_qtpie/        # Tests for qtpie library itself
│
├── DRAFT/                 # OLD drafts - reference only, don't modify
│   ├── drafting/          # One draft version
│   ├── more_recent_drafting/  # Another draft version
│   └── other_drafting/    # Yet another draft version
│
├── tech-docs/             # Design documents
│   ├── DRAFTING_SUMMARY.md   # Feature comparison of drafts
│   └── QTPIE_TEST_LIBRARY.md # qtpie_test design doc
│
├── TODO.md                # Development roadmap with phases
└── CLAUDE.md              # You are here
```

---

## Key Packages

### `qtpie` - The Main Library

What users import. Currently exports:
- `widget` - decorator for QWidget subclasses
- `make` - factory for creating child widgets

```python
from qtpie import widget, make
```

### `qtpie_test` - Test Framework

Strongly-typed wrapper around pytest-qt. Why not just pytest-qt?
1. pytest-qt uses `*args, **kwargs` everywhere - no type safety
2. We want helpers specific to qtpie patterns
3. Better API: `qt.click(button)` vs `qtbot.mouseClick(button, Qt.LeftButton)`

```python
from qtpie_test import QtDriver

def test_something(qt: QtDriver) -> None:
    widget = MyWidget()
    qt.track(widget)  # cleanup after test
    qt.click(widget.button)
    assert_that(widget.label.text()).is_equal_to("Clicked!")
```

### `qtpie_samples` - Example Apps

Reference implementations. The `regular_qt_app` shows "vanilla Qt" without qtpie - useful for comparison.

---

## The DRAFT Folder

Contains **old experimental implementations**. Don't modify these - they're reference material.

When stuck, check the drafts for inspiration:
- `DRAFT/**/widget.py` - various @widget implementations
- `DRAFT/**/make.py` - various make() implementations

The `tech-docs/DRAFTING_SUMMARY.md` compares features across drafts.

---

## Tech Stack

- **Python 3.12+** - using new type parameter syntax (`def foo[T]()`)
- **qtpy** - Qt abstraction (works with PySide6 or PyQt6)
- **PySide6** - the Qt binding we're testing with
- **pytest + pytest-qt** - testing (wrapped by qtpie_test)
- **assertpy** - fluent assertions
- **pyright strict** - VERY strict type checking, no compromises
- **ruff** - linting and formatting
- **uv** - package management (workspace with multiple packages)

---

## Running Things

**Run tests frequently!** Coverage runs automatically with every test run.

```bash
# Run qtpie tests (coverage prints automatically)
uv run python -m pytest tests/test_qtpie/ -v

# Run all tests
uv run python -m pytest tests/ -v

# Generate HTML coverage report (detailed line-by-line view)
uv run python -m pytest tests/test_qtpie/ --cov-report=html
# then open htmlcov/index.html in a browser

# Type check
uv run pyright qtpie/ tests/test_qtpie/

# Lint
uv run ruff check qtpie/ tests/test_qtpie/

# Format
uv run ruff format qtpie/ tests/test_qtpie/
```

Note: Use `python -m pytest` instead of just `pytest` due to workspace editable install quirk.

---

## Design Principles

1. **Declarative over imperative** - define what, not how
2. **Type safety** - pyright strict, no `Any` leakage, no ignore comments
3. **Zero magic strings** - signals connected by method reference when possible
4. **Dataclass patterns** - `@dataclass_transform()` for IDE support
5. **Test-driven** - write tests first, then implement
6. **Minimal API surface** - few things that compose well

---

## Current State (Phase 4 Complete)

Working features:
- `@widget()` and `@widget` (with/without parens)
- `layout="vertical"` | `"horizontal"` | `"form"` | `"grid"` | `"none"`
- `name` parameter (objectName)
- `classes` parameter (CSS-like)
- Lifecycle hooks (`setup()`, `setup_layout()`, etc.)
- `make()` with positional args, kwargs, signal connections
- `@window()` decorator for QMainWindow
- `@action()` and `@menu()` decorators
- `stretch()` for layout spacing
- 96 tests, 85% coverage, 0 pyright errors, 0 ruff errors

See `TODO.md` for the full roadmap.

---

## Quick Reference

### Creating a widget

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@widget(name="Counter", classes=["card"], layout="vertical")
class CounterWidget(QWidget):
    label: QLabel = make(QLabel, "Count: 0")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")
    count: int = 0

    def setup(self) -> None:
        # Called after all fields initialized
        pass

    def increment(self) -> None:
        self.count += 1
        self.label.setText(f"Count: {self.count}")
```

### Writing a test

```python
from qtpie import widget, make
from qtpie_test import QtDriver
from assertpy import assert_that

def test_counter_increments(qt: QtDriver) -> None:
    w = CounterWidget()
    qt.track(w)

    qt.click(w.button)

    assert_that(w.count).is_equal_to(1)
    assert_that(w.label.text()).is_equal_to("Count: 1")
```
