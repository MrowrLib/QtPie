# QtPie

**Declarative UI framework for Qt/PySide6**

QtPie brings React/Vue-style declarative patterns to desktop app development. Define *what* your UI should look like, not *how* to build it.

## Quick Example

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

That's it. Run `python counter.py` and you have a working app with:

- Automatic layout management
- Reactive data binding
- Declarative signal connections

## Key Features

### Declarative Widgets

Define widgets as classes with type-annotated fields. No manual `__init__`, no `addWidget()` calls.

```python
@widget
class MyWidget(Widget):
    label: QLabel = new("Hello")
    button: QPushButton = new("Click Me")
```

### Reactive State

`Variable[T]` provides reactive state that automatically updates bound widgets.

```python
_name: Variable[str] = new("")
_greeting: QLabel = new(bind="Hello, {_name}!")
```

### Record Types

Bind entire dataclasses to widgets with `Widget[T]`.

```python
@dataclass
class Person:
    name: str
    age: int

@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age
```

### Built-in Validation & Dirty Tracking

```python
_name: Variable[str] = new("", validate=lambda v: None if v else "Required")
_save_btn: QPushButton = new("Save", enabled="{is_valid and view_model.is_dirty}")
```

### Translations

```python
label: QLabel = new(t("Hello"))  # Translatable string
set_language("fr")  # Switch languages at runtime
```

## Installation

```bash
pip install qtpie
```

Or with uv:

```bash
uv add qtpie
```

## Next Steps

- [Hello World Tutorial](start/hello-world.md) - Build your first QtPie app
- [Key Concepts](start/concepts.md) - Understand the core ideas
- [Why QtPie?](why-qtpie.md) - See the before/after comparison
