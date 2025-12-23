# Why QtPie?

*"It's opinionated in a way that reflects actual experience with Qt pain."*

---

## The Philosophy

QtPie exists because writing Qt UIs in Python shouldn't feel like writing Java in 2005.

We believe:

- **Declarative beats procedural** for UI code
- **Convention beats configuration** for common patterns
- **Type safety is non-negotiable**, even in dynamic Python
- **Magic is fine** if the magic actually works

If you've ever written `super().__init__()` followed by `layout = QVBoxLayout(self)` followed by `layout.addWidget(...)` six times in a row, QtPie is for you.

---

## Convention > Configuration

This is the Rails philosophy, and it works.

When you write this:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
```

QtPie assumes:

- You want a vertical layout (override with `layout="horizontal"`)
- You want fields added in declaration order (override with `layout="none"`)
- You want `name` bound to `model.name` (override with `bind="other_field"`)
- You want the object name to be "PersonEditor" (override with `name="custom"`)

Every default can be overridden. But you probably won't need to.

This isn't about hiding complexity. It's about not making you repeat yourself for the 90% case.

---

## Declarative > Procedural

Procedural code describes *how*:

```python
def __init__(self):
    super().__init__()
    layout = QVBoxLayout(self)
    self.label = QLabel("Count: 0")
    layout.addWidget(self.label)
    self.button = QPushButton("Add")
    self.button.clicked.connect(self.increment)
    layout.addWidget(self.button)
```

Declarative code describes *what*:

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")
```

Same result. Half the lines. Reads like documentation.

When you come back to this code in six months, which version tells you what the UI looks like at a glance?

---

## Why Not QML?

QML is Qt's answer to declarative UI. It's good at what it does. But it asks a lot:

| | QML | QtPie |
|---|-----|-------|
| Language | New DSL to learn | Python you already know |
| Styling | Custom system | QSS (+ SCSS support) |
| Two-way binding | Manual wiring | Automatic |
| Type checking | Runtime errors | Pyright strict |
| Files | Split .qml/.py | All Python |
| Debugging | Cross-language | Python stack traces |

QML makes sense for some projects. But if you're already in Python, if you already know QSS, if you want real type safety - QtPie keeps you in familiar territory while giving you the declarative benefits.

---

## Yes, It's Magic

People said the same thing about Ruby on Rails.

"It's too magical." "I can't see what's happening." "Python should be explicit."

And yet Rails won, because convention over configuration turned out to be what developers actually wanted. The magic wasn't the problem - bad magic was the problem.

QtPie's magic:

- **Decorators transform classes** - `@widget` adds `@dataclass` behavior, sets up layouts, processes bindings
- **`make()` lies to the type checker** - Returns `field()` at runtime, claims to return `T` for IDE support
- **Signal detection is heuristic** - Checks if an attribute has `.connect()` to decide signal vs property

This magic is tested. It's consistent. It has escape hatches.

```python
@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click")

    def setup(self):
        # Escape hatch: raw Qt, no magic
        self.button.clicked.disconnect()
        self.button.clicked.connect(lambda: print("raw qt"))
```

---

## Type Safety Matters

Most Python UI frameworks give up on types. `*args, **kwargs` everywhere. `Any` return values. "Just trust us."

QtPie doesn't:

```python
@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")  # IDE knows: QLabel

    def setup(self):
        self.label.setText("World")  # Autocomplete works
        self.label.setValu(42)       # Red squiggle: typo caught
```

We run Pyright in strict mode. Zero errors. Zero `type: ignore` comments.

Your IDE should help you write correct code. That requires real types, not `Any`.

---

## Still Qt

QtPie doesn't replace Qt. It's a declarative layer on top.

Everything Qt offers is still there:

- All widget classes
- All signals and slots
- All styling with QSS
- All layouts
- All events

You can mix QtPie widgets with raw Qt widgets. You can call Qt methods directly. You can subclass Qt classes.

```python
@widget
class MyWidget(QWidget):
    def paintEvent(self, event):
        # Raw Qt painting, no QtPie involved
        painter = QPainter(self)
        painter.drawText(10, 10, "Low-level access")
```

QtPie makes the common case easy. It doesn't take the complex case away.

---

## Built for Production

This isn't a proof-of-concept. QtPie includes:

- **Data binding** with nested paths and optional chaining
- **Validation** with per-field error tracking
- **Dirty tracking** to know when models changed
- **Undo/redo** with configurable depth and debouncing
- **SCSS compilation** with hot reload
- **Testing utilities** that actually have type hints

Because real apps need more than widgets.
