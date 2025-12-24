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
├── lib/
│   └── qtpie/             # THE LIBRARY - this is what we're building
│       ├── decorators/    # @widget, @window, @menu, @action, @entry_point
│       ├── factories/     # make(), stretch(), separator()
│       ├── bindings/      # Data binding (bind, registry)
│       ├── styles/        # SCSS/QSS, classes, watcher
│       ├── app.py         # App class, run_app()
│       ├── widget_base.py # Widget[T] base class
│       └── testing/       # Test framework (qtpie.testing)
│           ├── driver.py  # QtDriver - strongly-typed test API
│           └── plugin.py  # pytest plugin (provides `qt` fixture)
│
├── samples/               # Example apps using qtpie
│   └── single_file_apps/  # Single-file app examples
│
├── tests/                 # All tests live here
│   ├── unit/              # Unit tests for qtpie library
│   └── e2e/               # End-to-end tests
│
├── DRAFT/                 # OLD drafts - reference only, don't modify
│
├── tech-docs/             # Design documents (historical reference)
│   └── DRAFTING_SUMMARY.md   # Feature comparison of drafts
│
├── TODO.md                # Development roadmap with phases and status
└── CLAUDE.md              # You are here
```

---

## Key Packages

### `qtpie` - The Main Library

What users import:

```python
from qtpie import (
    # Decorators
    widget, window, menu, action, entry_point,
    # Factories
    make, make_later, stretch, separator,
    # Base classes
    Widget, ModelWidget,
    # App
    App, run_app,
    # Bindings
    bind, register_binding,
    # Styles
    ColorScheme, enable_dark_mode, enable_light_mode, set_color_scheme,
)
```

### `qtpie.testing` - Test Framework

Strongly-typed wrapper around pytest-qt. Install with `uv add "qtpie[test]"`.

Why not just pytest-qt?
1. pytest-qt uses `*args, **kwargs` everywhere - no type safety
2. We want helpers specific to qtpie patterns
3. Better API: `qt.click(button)` vs `qtbot.mouseClick(button, Qt.LeftButton)`

```python
from qtpie.testing import QtDriver

def test_something(qt: QtDriver) -> None:
    widget = MyWidget()
    qt.track(widget)  # cleanup after test
    qt.click(widget.button)
    assert_that(widget.label.text()).is_equal_to("Clicked!")
```

---

## The DRAFT Folder

Contains **old experimental implementations**. Don't modify these - they're reference material.

When stuck, check the drafts for inspiration:
- `DRAFT/**/widget.py` - various @widget implementations
- `DRAFT/**/make.py` - various make() implementations

The `tech-docs/DRAFTING_SUMMARY.md` compares features across drafts.

---

## Tech Stack

- **Python 3.13+** - using new type parameter syntax (`def foo[T]()`)
- **qtpy** - Qt abstraction (works with PySide6 or PyQt6)
- **PySide6** - the Qt binding we're testing with
- **pytest + pytest-qt** - testing (wrapped by qtpie.testing)
- **assertpy** - fluent assertions
- **pyright strict** - VERY strict type checking, no compromises
- **ruff** - linting and formatting
- **uv** - package management (workspace with multiple packages)

---

## Related Libraries

**observant** - Observable/reactive data library, also authored by the user.

- Owner: Same author as QtPie
- Purpose: Used for data binding to provide reactive model objects
- Note: Can be modified as needed to better support QtPie integration

---

## Running Things

**Run tests frequently!**

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run unit tests only
uv run python -m pytest tests/unit/ -v

# Type check
uv run pyright lib/qtpie/ tests/unit/

# Lint
uv run ruff check lib/qtpie/ tests/unit/

# Format
uv run ruff format lib/qtpie/ tests/unit/
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

## Code Style - No Unnecessary Bullshit

**Don't add imports or code that isn't actually needed.**

- **NO `from __future__ import annotations`** - Python 3.13+ doesn't need it. Only use if you have actual forward references (rare).
- **NO unnecessary imports** - Don't import things "just in case"
- **NO cargo-cult patterns** - If you can't explain why something is needed, don't add it
- **NO defensive coding against impossible cases** - Trust the type system
- **NO premature abstractions** - Write concrete code first

When in doubt, leave it out. Simpler is better.

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
from qtpie.testing import QtDriver
from assertpy import assert_that

def test_counter_increments(qt: QtDriver) -> None:
    w = CounterWidget()
    qt.track(w)

    qt.click(w.button)

    assert_that(w.count).is_equal_to(1)
    assert_that(w.label.text()).is_equal_to("Count: 1")
```

### Data binding

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget()
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # auto-binds to model.age
```

### App entry point

```python
from qtpie import entry_point, widget, make

@entry_point
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Hello!")
```
