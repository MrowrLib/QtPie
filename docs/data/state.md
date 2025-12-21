# Reactive State

Make your widgets reactive with `state()`. Assignment triggers automatic UI updates.

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="count")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1  # That's it. Label updates automatically.
```

## What is `state()`?

`state()` makes a field **reactive**:

- Assignment triggers updates: `self.count = 42`
- Compound assignments work: `self.count += 1`
- Bound widgets update automatically
- No manual UI refresh code needed

## Basic Usage

### Primitives

For primitives (int, str, float, bool), type is inferred from the default value:

```python
@widget
class Editor(QWidget):
    count: int = state(0)
    name: str = state("")
    price: float = state(0.0)
    active: bool = state(False)
```

### Binding to State

Use `bind` to connect widgets to state fields:

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="count")
```

When `self.count` changes, the label updates automatically.

### Two-Way Binding

Input widgets get two-way binding:

```python
@widget
class Editor(QWidget):
    name: str = state("")
    age: int = state(0)

    name_edit: QLineEdit = make(QLineEdit, bind="name")
    age_spin: QSpinBox = make(QSpinBox, bind="age")
```

Changes flow both ways:
- `self.name = "Alice"` → widget shows "Alice"
- User types "Bob" → `self.name` becomes "Bob"

### Multiple Widgets, Same State

Multiple widgets can bind to the same state field:

```python
@widget
class Editor(QWidget):
    count: int = state(0)

    spin1: QSpinBox = make(QSpinBox, bind="count")
    spin2: QSpinBox = make(QSpinBox, bind="count")
    label: QLabel = make(QLabel, bind="count")
```

All three stay synchronized automatically.

## Objects and Optionals

### Using `state[Type]()`

For objects or optional types, use the explicit type parameter syntax:

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogEditor(QWidget):
    dog: Dog | None = state[Dog | None]()  # Starts as None
```

You can also provide a default:

```python
@widget
class DogEditor(QWidget):
    dog: Dog = state[Dog](Dog(name="Buddy", age=3))
```

Or use type inference when default is provided:

```python
@widget
class DogEditor(QWidget):
    dog: Dog = state(Dog(name="Buddy", age=3))  # Type inferred from Dog()
```

### Nested Bindings

Bind to nested properties using dot notation:

```python
@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogEditor(QWidget):
    dog: Dog = state(Dog(name="Buddy", age=3))

    name_edit: QLineEdit = make(QLineEdit, bind="dog.name")
    age_spin: QSpinBox = make(QSpinBox, bind="dog.age")
```

Two-way binding works for nested properties:
- User types "Max" → `self.dog.name` becomes "Max"
- `self.dog = Dog("Rex", 5)` → widgets show "Rex" and 5

### Optional Chaining

For optional objects, use `?` for safe access:

```python
@widget
class DogEditor(QWidget):
    dog: Dog | None = state[Dog | None]()

    name_edit: QLineEdit = make(QLineEdit, bind="dog?.name")
```

When `dog` is `None`, the widget shows empty text instead of crashing.

## Format Strings

Combine state fields with text using format strings:

### Simple Formatting

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
```

Label shows: "Count: 0", "Count: 1", "Count: 2"...

### Multiple Fields

```python
@widget
class NameDisplay(QWidget):
    first: str = state("John")
    last: str = state("Doe")

    label: QLabel = make(QLabel, bind="{first} {last}")
```

Label shows: "John Doe"

Update either field and the label updates:

```python
def update_name(self) -> None:
    self.first = "Jane"  # Label becomes "Jane Doe"
    self.last = "Smith"  # Label becomes "Jane Smith"
```

### With Nested Paths

```python
@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogGreeter(QWidget):
    dog: Dog = state(Dog(name="Buddy", age=3))
    label: QLabel = make(QLabel, bind="Hello, {dog.name}!")
```

Label shows: "Hello, Buddy!"

### Complex Formats

```python
@widget
class Status(QWidget):
    current: int = state(5)
    total: int = state(10)

    label: QLabel = make(QLabel, bind="{current} / {total} items")
```

Label shows: "5 / 10 items"

## Expressions

Format strings support Python expressions:

### Math

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="{count + 5}")
```

Shows: 5, 6, 7... (always 5 more than count)

### Format Specs

```python
@widget
class PriceDisplay(QWidget):
    price: float = state(10.0)
    label: QLabel = make(QLabel, bind="Total: ${price * 1.1:.2f}")
```

Shows: "Total: $11.00"

### Method Calls

```python
@widget
class NameDisplay(QWidget):
    name: str = state("hello")
    label: QLabel = make(QLabel, bind="{name.upper()}")
```

Shows: "HELLO"

Works with nested paths:

```python
@widget
class DogDisplay(QWidget):
    dog: Dog = state(Dog(name="buddy"))
    label: QLabel = make(QLabel, bind="{dog.name.upper()}")
```

Shows: "BUDDY"

### Conditionals

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="{count if count > 0 else 'none'}")
```

Shows: "none" when count is 0, otherwise shows the number.

### Builtin Functions

```python
@widget
class LengthDisplay(QWidget):
    name: str = state("hello")
    label: QLabel = make(QLabel, bind="Length: {len(name)}")
```

Shows: "Length: 5"

### Multiple Variables

```python
@widget
class Calculator(QWidget):
    a: int = state(10)
    b: int = state(20)

    label: QLabel = make(QLabel, bind="{a} + {b} = {a + b}")
```

Shows: "10 + 20 = 30"

### Self References

You can use `self` in expressions:

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Value: {self.count + self.count}")
```

Shows: "Value: 0", "Value: 2", "Value: 4"...

## Complete Example

```python
from dataclasses import dataclass
from qtpie import widget, make, state
from qtpy.QtWidgets import QWidget, QLabel, QLineEdit, QSpinBox, QPushButton

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogCounter(QWidget):
    # State fields
    count: int = state(0)
    dog: Dog = state(Dog(name="Buddy", age=3))

    # Widgets with bindings
    name_edit: QLineEdit = make(QLineEdit, bind="dog.name")
    age_spin: QSpinBox = make(QSpinBox, bind="dog.age")

    info: QLabel = make(QLabel, bind="{dog.name}, age {dog.age}")
    count_label: QLabel = make(QLabel, bind="Count: {count}")

    up: QPushButton = make(QPushButton, "+", clicked="increment")
    down: QPushButton = make(QPushButton, "-", clicked="decrement")
    reset: QPushButton = make(QPushButton, "Reset", clicked="reset")

    def increment(self) -> None:
        self.count += 1

    def decrement(self) -> None:
        self.count -= 1

    def reset(self) -> None:
        self.count = 0
        self.dog = Dog(name="Buddy", age=3)
```

All widgets update automatically as state changes.

## How It Works

Under the hood, `state()` creates a `ReactiveDescriptor` powered by `ObservableProxy` from the `observant` library:

- **Primitives** (int, str, etc.) are wrapped in a container object
- **Objects** (dataclasses, etc.) are wrapped directly
- Assignments trigger observer notifications
- Bound widgets subscribe to state changes
- Two-way binding connects widget signals back to state

You don't need to understand this to use it. Just remember:

**Assignment triggers updates. That's it.**

## See Also

- [Format Expressions](format.md) - More on format string bindings
- [Model Widgets](model-widgets.md) - `Widget[T]` for form editing
- [Signals](../basics/signals.md) - Connecting buttons and actions
- [`make()`](../reference/factories/make.md) - Widget factory with bind parameter
