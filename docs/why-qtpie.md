# Why QtPie?

Qt is powerful, but verbose. QtPie fixes that.

## The Problem

A simple counter widget in plain Qt requires:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class Counter(QWidget):
    def __init__(self) -> None:
        super().__init__()

        # Create layout
        layout = QVBoxLayout(self)

        # Create widgets
        self.count = 0
        self.label = QLabel(f"Count: {self.count}")
        self.button = QPushButton("Increment")

        # Add to layout
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        # Connect signals
        self.button.clicked.connect(self.on_click)

    def on_click(self) -> None:
        self.count += 1
        self.label.setText(f"Count: {self.count}")  # Manual update!
```

**Problems:**

- Boilerplate `__init__` with `super().__init__()`
- Manual layout creation and widget adding
- Manual signal connections
- Manual UI updates when state changes

## The Solution

The same widget in QtPie:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, Variable, new, widget

@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("Increment", clicked="on_click")

    def on_click(self) -> None:
        self._count += 1  # UI updates automatically!
```

**Benefits:**

- No `__init__` boilerplate
- Automatic layout (vertical by default)
- Declarative signal connections (`clicked="on_click"`)
- Reactive updates (change `_count`, label updates)
- Composable: pass state to children via Variable bindings

## Feature Comparison

| Feature | Plain Qt | QtPie |
|---------|----------|-------|
| Layout setup | Manual | Automatic |
| Widget creation | Imperative | Declarative |
| Signal connections | `.connect()` calls | `clicked="method"` |
| Signal forwarding | Manual wiring | `clicked="my_signal"` |
| State management | Manual updates | Reactive `Variable[T]` |
| Parent-child state | Signals/callbacks | Variable bindings |
| Data binding | DIY | Built-in `bind=` |
| Form layouts | Manual `addRow()` | `label=` parameter |
| Menus | Manual QMenu/QAction | Declarative `@menu` |
| Validation | DIY | Built-in validators |
| Dirty tracking | DIY | Built-in |
| Translations | QTranslator setup | `t()` + YAML |
| Async handlers | Manual threading | `@slot` decorator |
| Type safety | Partial | Full (pyright strict) |

## Design Philosophy

### Declarative Over Imperative

Define *what* your UI should be, not *how* to build it. Let QtPie handle the plumbing.

### Type Safety First

QtPie is built for pyright strict mode. No `Any` leakage, full autocomplete support, catch errors at edit time.

### Convention Over Configuration

Sensible defaults that just work:

- Vertical layout by default
- Field names become objectNames
- Fields matching record properties auto-bind

### Minimal API Surface

A few powerful primitives that compose well:

- `@widget` / `@window` / `@menu` decorators
- `Widget`, `Window`, `Menu` base classes
- `Widget[T]`, `Window[T]`, `Menu[T]` for record-bound views
- `new()` factory for declaring fields
- `Variable[T]` for reactive state
- `bind=` for data binding

## When to Use QtPie

**Great for:**

- Form-heavy applications
- Data entry and editing
- CRUD interfaces
- Apps with complex parent-child widget communication
- Menu-driven applications
- Prototyping
- Apps with reactive state
- Internationalized apps

**Consider plain Qt for:**

- Custom painting / graphics
- Performance-critical rendering
- Highly custom widget behavior
- Existing large Qt codebases

QtPie builds on Qt - you can always drop down to plain Qt APIs when needed.
