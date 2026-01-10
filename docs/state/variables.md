# Variables

`Variable[T]` provides reactive state management. When a Variable changes, bound widgets update automatically.

## Basic Usage

```python
from qtpie import Widget, Variable, new, widget

@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("+1", clicked="increment")

    def increment(self) -> None:
        self._count += 1  # Label updates automatically!
```

## Creating Variables

```python
@widget
class MyWidget(Widget):
    # String with default
    _name: Variable[str] = new("hello")

    # Integer
    _count: Variable[int] = new(42)

    # Float
    _ratio: Variable[float] = new(3.14)

    # Boolean
    _enabled: Variable[bool] = new(True)
```

## Reading and Writing

### Using .value

```python
# Read
current = self._count.value

# Write
self._count.value = 100
```

### Direct Assignment

```python
# This also works!
self._count = 100
```

### Augmented Assignment

```python
self._count += 1
self._count -= 5
self._count *= 2
self._count /= 2
```

## List Variables

`Variable[list[T]]` creates a reactive list:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new()  # Starts empty
    _labels: list[QLabel] = new(bind="_items")

    def add_item(self, text: str) -> None:
        self._items.append(text)  # New label appears!

    def clear(self) -> None:
        self._items.clear()  # All labels removed
```

### List Operations

All standard list operations are reactive:

```python
self._items.append("new")
self._items.insert(0, "first")
self._items.remove("item")
self._items.pop()
self._items.clear()
self._items[0] = "updated"
```

## Dict Variables

`Variable[dict[K, V]]` creates a reactive dictionary:

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new()
    _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}")

    def set_score(self, name: str, score: int) -> None:
        self._scores[name] = score  # Labels update
```

### Dict Operations

```python
self._scores["Alice"] = 100
del self._scores["Bob"]
self._scores.clear()
self._scores.update({"Charlie": 90})
```

## Complex Type Variables

`Variable[T]` with dataclasses creates reactive field access:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(Widget):
    _person: Variable[Person] = new(default=Person("Alice", 30))
    _name: QLabel = new(bind="{_person.name}")
    _age: QLabel = new(bind="Age: {_person.age}")

    def birthday(self) -> None:
        self._person.age += 1  # Age label updates!
```

## Per-Instance State

Each widget instance gets its own Variable values:

```python
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)

a = Counter()
b = Counter()

a._count = 10
b._count = 20

# a._count.value == 10
# b._count.value == 20
```

## Dirty Tracking

Variables track whether they've been modified:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    def check_dirty(self) -> bool:
        return self._name.is_dirty.get()
```

See [Dirty Tracking](../data/dirty-tracking.md) for widget-level tracking.

## Variable[T, W] - Inline Widgets

Create a Variable with an attached widget:

```python
@widget
class LoginForm(Widget):
    # Variable + QLineEdit in one field
    _username: Variable[str, QLineEdit] = new("")
    _password: Variable[str, QLineEdit] = new("")

    # Access the widget
    def focus_username(self) -> None:
        self._username.widget.setFocus()
```

### Chained Syntax

Configure the widget with chained call:

```python
_username: Variable[str, QLineEdit] = new("")(
    placeholderText="Enter username"
)

_password: Variable[str, QLineEdit] = new("")(
    placeholderText="Enter password",
    echoMode=QLineEdit.EchoMode.Password
)

_count: Variable[int, QSpinBox] = new(50)(
    minimum=0,
    maximum=100
)
```

### Signal Connections

Connect signals in the widget kwargs:

```python
@widget
class SearchForm(Widget):
    _query: Variable[str, QLineEdit] = new("")(
        placeholderText="Search...",
        returnPressed="on_search",
        textChanged="on_text_changed"
    )

    def on_search(self) -> None:
        print(f"Searching: {self._query.value}")

    def on_text_changed(self) -> None:
        # Live search as user types
        pass
```

### Layout Order

Variable[T, W] widgets appear in declaration order, interleaved with regular widgets:

```python
@widget
class MixedForm(Widget):
    _label1: QLabel = new("First")
    _name: Variable[str, QLineEdit] = new("")
    _label2: QLabel = new("Second")
    _age: Variable[int, QSpinBox] = new(0)

# Layout order: _label1, _name.widget, _label2, _age.widget
```

### Complex Types with Widget

For complex types, use `Variable[T, Widget[T]]`:

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str
    age: int

@widget(layout="form")
class DogEditor(Widget[Dog]):
    name: QLineEdit = new(label="Name")
    age: QSpinBox = new(label="Age")

@widget
class App(Widget):
    _dog: Variable[Dog, DogEditor] = new(default=Dog("Fido", 3))

    def update_dog(self) -> None:
        # Proxy field access - updates editor automatically
        self._dog.name = "Rex"
        self._dog.age = 5
```

## Binding Variables

Variables can be bound to widgets with `bind=`:

```python
@widget
class Display(Widget):
    _name: Variable[str] = new("Alice")

    # Simple binding
    _label: QLabel = new(bind="_name")

    # Format string
    _greeting: QLabel = new(bind="Hello, {_name}!")

    # Expression
    _length: QLabel = new(bind="Length: {len(_name)}")
```

See [Bindings](bindings.md) for complete binding documentation.

## When to Use Variables

| Scenario | Use |
|----------|-----|
| Reactive state that updates UI | `Variable[T]` |
| Form input fields | `Variable[T, QLineEdit]` |
| Dynamic lists | `Variable[list[T]]` |
| Key-value data | `Variable[dict[K, V]]` |
| Complex data objects | `Variable[T]` with dataclass |
| Static display only | Plain QLabel (no Variable) |

## See Also

- [Bindings](bindings.md) - Binding Variables to widgets
- [Format Expressions](format-expressions.md) - Expression syntax
- [Property Bindings](property-bindings.md) - visible= and enabled=
- [Dirty Tracking](../data/dirty-tracking.md) - Track changes
