# state()

Reactive state fields that automatically update bound widgets.

## Overview

`state()` creates a reactive field that tracks changes and notifies any widgets bound to it. When you update a state field, all bound widgets automatically refresh to reflect the new value.

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="count")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")

    def increment(self) -> None:
        self.count += 1  # Label updates automatically
```

This is the declarative, reactive heart of QtPie. No manual signal/slot connections. No `setText()` calls. Just update the state.

## Basic Usage

### Simple State with Default Value

The most common usage - type is inferred from the default:

```python
@widget
class Editor(QWidget):
    name: str = state("")
    age: int = state(0)
    score: float = state(0.0)
    active: bool = state(False)
```

### Explicit Type Parameters

Use `state[Type]()` when you need to specify the type explicitly, typically for optional fields:

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogEditor(QWidget):
    dog: Dog | None = state[Dog | None]()  # Starts as None

    # Can also provide a default
    dog_with_default: Dog | None = state[Dog | None](None)
```

### Objects as State

State works with any Python object, not just primitives:

```python
@dataclass
class Config:
    debug: bool = False
    max_retries: int = 3

@widget
class App(QWidget):
    config: Config = state(Config(debug=True, max_retries=5))
```

## Binding to State

### Simple Binding

Bind a widget to a state field by name:

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="count")

    def setup(self) -> None:
        self.count = 42  # Label shows "42"
```

### Two-Way Binding

Input widgets automatically create two-way bindings:

```python
@widget
class Editor(QWidget):
    name: str = state("")
    age: int = state(0)

    name_edit: QLineEdit = make(QLineEdit, bind="name")
    age_spin: QSpinBox = make(QSpinBox, bind="age")

    def setup(self) -> None:
        # State → Widget
        self.name = "Alice"  # name_edit updates
        self.age = 25        # age_spin updates

        # Widget → State (user types)
        # When user edits name_edit, self.name updates
        # When user changes age_spin, self.age updates
```

### Multiple Widgets, Same State

Multiple widgets can bind to the same state field. They all stay in sync:

```python
@widget
class Editor(QWidget):
    count: int = state(0)
    spin1: QSpinBox = make(QSpinBox, bind="count")
    spin2: QSpinBox = make(QSpinBox, bind="count")
    label: QLabel = make(QLabel, bind="count")

    def setup(self) -> None:
        # Update state - all widgets update
        self.count = 10

        # Or update via widget - state and other widgets update
        self.spin1.setValue(20)  # count, spin2, and label all update
```

## Format String Bindings

Combine state fields with text using format strings:

### Simple Format

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")

    def increment(self) -> None:
        self.count += 1  # Label shows "Count: 1", "Count: 2", etc.
```

### Multiple Fields

Reference multiple state fields in one format string:

```python
@widget
class NameDisplay(QWidget):
    first: str = state("John")
    last: str = state("Doe")
    label: QLabel = make(QLabel, bind="{first} {last}")

    def setup(self) -> None:
        self.first = "Jane"  # Label shows "Jane Doe"
        self.last = "Smith"  # Label shows "Jane Smith"
```

### With Static Text

Mix state fields with static text:

```python
@widget
class Status(QWidget):
    current: int = state(5)
    total: int = state(10)
    label: QLabel = make(QLabel, bind="{current} / {total} items")
```

## Expression Bindings

Format strings support full Python expressions:

### Math Operations

```python
@widget
class Calculator(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="{count + 5}")

    def setup(self) -> None:
        self.count = 10  # Label shows "15"
```

### Multiple Variables in Expressions

```python
@widget
class Calculator(QWidget):
    a: int = state(10)
    b: int = state(20)
    label: QLabel = make(QLabel, bind="{a} + {b} = {a + b}")
```

### Format Specifications

Use Python's format spec for number formatting:

```python
@widget
class PriceDisplay(QWidget):
    price: float = state(10.0)
    label: QLabel = make(QLabel, bind="Total: ${price * 1.1:.2f}")

    def setup(self) -> None:
        self.price = 99.99  # Label shows "Total: $109.99"
```

### Method Calls

```python
@widget
class NameDisplay(QWidget):
    name: str = state("hello")
    label: QLabel = make(QLabel, bind="{name.upper()}")

    def setup(self) -> None:
        self.name = "world"  # Label shows "WORLD"
```

### Ternary Expressions

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="{count if count > 0 else 'none'}")

    def setup(self) -> None:
        self.count = 5  # Label shows "5"
        self.count = 0  # Label shows "none"
```

### Builtin Functions

```python
@widget
class LengthDisplay(QWidget):
    name: str = state("hello")
    label: QLabel = make(QLabel, bind="Length: {len(name)}")
```

## Nested State Bindings

For object-type state fields, bind to nested properties:

### Basic Nested Binding

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

Two-way binding works with nested paths - editing the widget updates the nested property.

### Nested Paths in Format Strings

```python
@widget
class DogGreeter(QWidget):
    dog: Dog = state(Dog(name="Buddy", age=3))
    label: QLabel = make(QLabel, bind="Hello, {dog.name}!")

    def setup(self) -> None:
        self.dog = Dog(name="Max", age=5)  # Label shows "Hello, Max!"
```

### Nested Methods

```python
@widget
class DogDisplay(QWidget):
    dog: Dog = state(Dog(name="buddy"))
    label: QLabel = make(QLabel, bind="{dog.name.upper()}")
```

### Mixed Simple and Nested

```python
@widget
class DogInfo(QWidget):
    count: int = state(1)
    dog: Dog = state(Dog(name="Rex"))
    label: QLabel = make(QLabel, bind="Dog #{count}: {dog.name}")
```

### Optional Chaining

Use `?` for optional fields to handle None gracefully:

```python
@widget
class DogEditor(QWidget):
    dog: Dog | None = state[Dog | None]()
    name_edit: QLineEdit = make(QLineEdit, bind="dog?.name")

    def setup(self) -> None:
        # dog is None - widget shows empty string
        self.dog = Dog(name="Rex")  # Now shows "Rex"
```

## Working with State

### Assignment and Operations

State fields behave like normal Python fields:

```python
@widget
class Counter(QWidget):
    count: int = state(0)

    def increment(self) -> None:
        self.count += 1

    def decrement(self) -> None:
        self.count -= 1

    def reset(self) -> None:
        self.count = 0

    def double(self) -> None:
        self.count *= 2
```

### Multiple State Fields

State fields are independent:

```python
@widget
class Form(QWidget):
    name: str = state("")
    age: int = state(0)
    active: bool = state(False)

    name_edit: QLineEdit = make(QLineEdit, bind="name")
    age_spin: QSpinBox = make(QSpinBox, bind="age")

    def setup(self) -> None:
        # Each field operates independently
        self.name = "Alice"
        self.age = 30
        self.active = True
```

## Advanced: Direct Observable Access

For advanced scenarios, access the underlying Observable:

```python
from qtpie.state import get_state_observable

@widget
class Counter(QWidget):
    count: int = state(0)

    def setup(self) -> None:
        observable = get_state_observable(self, "count")
        if observable:
            # Manually subscribe to changes
            observable.on_change(lambda value: print(f"Changed to {value}"))

            # Read/write via observable
            current = observable.get()
            observable.set(42)
```

This is rarely needed - bindings handle most cases automatically.

## Type Signatures

```python
# Basic usage - type inferred from default
def state(default: T) -> T: ...

# No default
def state() -> None: ...

# Explicit type parameter
def state[Type]() -> Type: ...
def state[Type](default: Type | None) -> Type: ...
```

## Implementation Details

State is powered by [Observant](https://mrowrlib.github.io/observant.py/)'s [ObservableProxy](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/) ([PyPI](https://pypi.org/project/observant/)):

- Primitive values (int, str, bool, etc.) are wrapped in a container
- Object values are proxied directly
- Assignment triggers change notifications to all bindings
- Two-way bindings connect widget signals back to state

## See Also

- [bind()](../bindings/bind.md) - Manual binding function
- [make()](make.md) - Widget factory with bind parameter
- [Reactive State guide](../../data/state.md) - Detailed guide with more examples
- [Format Expressions guide](../../data/format.md) - Deep dive into format bindings
- [Model Widgets](../../data/model-widgets.md) - Widget[T] for form editing
- [Observant Integration](../../guides/observant.md) - Understanding the reactive layer
