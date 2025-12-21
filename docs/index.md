# QtPie

**Declarative UI for Qt/PySide6**

---

## The Problem

Qt is powerful but verbose. Building UIs requires endless boilerplate:

```python
class Counter(QWidget):
    def __init__(self):
        super().__init__()
        self.count = 0

        # Create layout
        layout = QVBoxLayout(self)

        # Create and configure label
        self.label = QLabel(f"Count: {self.count}")
        layout.addWidget(self.label)

        # Create button
        self.button = QPushButton("+1")
        self.button.clicked.connect(self.increment)
        layout.addWidget(self.button)

    def increment(self):
        self.count += 1
        # Manually update the label text
        self.label.setText(f"Count: {self.count}")
```

That's 20+ lines for a simple counter.

---

## The Solution

QtPie brings React-style declarative patterns to Qt:

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@entry_point
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1  # That's it. Label updates automatically.
```

**8 lines.** Clean. Declarative. Type-safe.

---

## Key Features

### Reactive State

Change a value, widgets update automatically:

```python
count: int = state(0)
label: QLabel = make(QLabel, bind="Count: {count}")

# Later...
self.count += 1  # Label updates instantly
```

[Learn more about Reactive State →](data/state.md)

### Format Expressions

Powerful template syntax in bindings:

```python
# Simple formatting
label: QLabel = make(QLabel, bind="Count: {count}")

# Multiple variables
label: QLabel = make(QLabel, bind="{first} {last}")

# Expressions and methods
label: QLabel = make(QLabel, bind="{name.upper()}")

# Format specs
label: QLabel = make(QLabel, bind="Total: ${price * 1.1:.2f}")
```

[Learn more about Format Expressions →](data/format.md)

### Signal Connections

Connect signals by method name:

```python
button: QPushButton = make(QPushButton, "Save", clicked="save")

def save(self) -> None:
    # Handle the click
    pass
```

[Learn more about Signals →](basics/signals.md)

### Smart Layouts

Automatic layout management:

```python
@widget  # Vertical layout by default
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    middle: QLabel = make(QLabel, "Middle")
    bottom: QLabel = make(QLabel, "Bottom")

@widget(layout="horizontal")  # Or horizontal
class Row(QWidget):
    left: QLabel = make(QLabel, "Left")
    right: QLabel = make(QLabel, "Right")

@widget(layout="form")  # Or form layout
class Form(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Name:")
    email: QLineEdit = make(QLineEdit, form_label="Email:")
```

[Learn more about Layouts →](basics/layouts.md)

### CSS Classes & Styling

Qt stylesheets with CSS-like class selectors:

```python
@widget(classes=["card", "shadow"])
class MyWidget(QWidget):
    pass

# Later...
widget.add_class("highlighted")
widget.remove_class("shadow")
```

[Learn more about Styling →](basics/styling.md)

### Model Widgets

Auto-bind form fields to data models:

```python
from dataclasses import dataclass


@dataclass
class Person:
    name: str = ""
    age: int = 0


@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # Auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # Auto-binds to model.age


editor = PersonEditor()
editor.set_model(Person(name="Alice", age=30))
# Widgets now show "Alice" and 30
```

[Learn more about Model Widgets →](data/model-widgets.md)

---

## Installation

```bash
pip install qtpie
# or
uv add qtpie
```

QtPie requires Python 3.13+ and PySide6 (or PyQt6).

[Full installation guide →](start/install.md)

---

## Hello World

The simplest QtPie app:

```python
from qtpie import entry_point, make, widget
from qtpy.QtWidgets import QLabel, QWidget


@entry_point
@widget
class Hello(QWidget):
    label: QLabel = make(QLabel, "Hello, World!")
```

Run it:

```bash
python hello.py
```

The `@entry_point` decorator handles app initialization and starts the event loop automatically.

[More examples →](start/hello-world.md)

---

## Why QtPie?

| Before (Vanilla Qt) | After (QtPie) |
|---------------------|---------------|
| 40+ lines of boilerplate | 8 lines of declarations |
| Manual layout management | Automatic layout from field order |
| Manual signal connections | `clicked="method_name"` |
| Manual state synchronization | Reactive `state()` + `bind=` |
| String-based object names | Type-safe field access |
| Runtime errors | Compile-time type checking (pyright) |

QtPie is **not** a new framework - it's a thin declarative layer over Qt. You still have full access to all Qt APIs.

---

## Learn More

- [Getting Started](start/hello-world.md) - Build your first app
- [Key Concepts](start/concepts.md) - Understand decorators, factories, and bindings
- [Reactive State](data/state.md) - Master the `state()` system
- [Testing](guides/testing.md) - Write tests with `qtpie_test`
- [Examples](examples.md) - Gallery of sample apps

---

## Type Safety

QtPie is built with **pyright strict mode** - no compromises:

- Full type inference for widget fields
- Generic `Widget[T]` base class for model widgets
- No `Any` types in public APIs
- Works perfectly with VS Code, PyCharm, and other IDEs

---

## License

MIT
