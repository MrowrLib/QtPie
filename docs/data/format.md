# Format Expressions

Format expressions let you create dynamic text by embedding Python expressions inside `bind` strings. When any bound state changes, the text automatically updates.

Think of it like f-strings, but reactive.

## Simple Format Strings

The most common use case: embedding a state value in text.

```python
from qtpie import widget, state, make
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1
```

When `count` changes, the label updates automatically:
- Initial: `"Count: 0"`
- After click: `"Count: 1"`
- After 10 clicks: `"Count: 10"`

## Multiple Variables

You can reference multiple state fields in one format string.

```python
@widget
class NameDisplay(QWidget):
    first: str = state("John")
    last: str = state("Doe")
    label: QLabel = make(QLabel, bind="{first} {last}")
```

When either `first` or `last` changes, the label updates. Both fields are tracked independently.

```python
@widget
class Status(QWidget):
    current: int = state(5)
    total: int = state(10)
    label: QLabel = make(QLabel, bind="{current} / {total} items")
```

Output: `"5 / 10 items"`

## Expressions

Format bindings aren't limited to simple variables - you can use Python expressions.

### Math

```python
@widget
class Calculator(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="{count + 5}")
```

When `count` is 10, displays: `"15"`

### Multiple Variables in Expressions

```python
@widget
class Calculator(QWidget):
    a: int = state(10)
    b: int = state(20)
    label: QLabel = make(QLabel, bind="{a} + {b} = {a + b}")
```

Output: `"10 + 20 = 30"`

### Method Calls

```python
@widget
class NameDisplay(QWidget):
    name: str = state("hello")
    label: QLabel = make(QLabel, bind="{name.upper()}")
```

Output: `"HELLO"`

### Builtin Functions

```python
@widget
class LengthDisplay(QWidget):
    name: str = state("hello")
    label: QLabel = make(QLabel, bind="Length: {len(name)}")
```

Output: `"Length: 5"`

### Ternary Expressions

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="{count if count > 0 else 'none'}")
```

When `count` is 0: `"none"`
When `count` is 5: `"5"`

## Format Specs

Use Python's format specification mini-language for number formatting.

```python
@widget
class PriceDisplay(QWidget):
    price: float = state(10.0)
    label: QLabel = make(QLabel, bind="Total: ${price * 1.1:.2f}")
```

Output: `"Total: $11.00"`

When `price` is 99.99: `"Total: $109.99"`

The `:.2f` ensures two decimal places.

## Nested Paths

Format expressions work with nested object properties.

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogGreeter(QWidget):
    dog: Dog = state(Dog(name="Buddy", age=3))
    label: QLabel = make(QLabel, bind="Hello, {dog.name}!")
```

Output: `"Hello, Buddy!"`

### With Method Calls

```python
@widget
class DogDisplay(QWidget):
    dog: Dog = state(Dog(name="buddy"))
    label: QLabel = make(QLabel, bind="{dog.name.upper()}")
```

Output: `"BUDDY"`

### Mixing Simple and Nested

```python
@widget
class DogInfo(QWidget):
    count: int = state(1)
    dog: Dog = state(Dog(name="Rex"))
    label: QLabel = make(QLabel, bind="Dog #{count}: {dog.name}")
```

Output: `"Dog #1: Rex"`

## Widget[T] Model Fields

Format expressions work seamlessly with `Widget[T]` model bindings.

```python
from qtpie import Widget

@dataclass
class User:
    name: str = ""
    age: int = 0

@widget
class UserDisplay(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit, bind="name")
    age: QSpinBox = make(QSpinBox, bind="age")
    label: QLabel = make(QLabel, bind="{name}, age {age}")
```

The `{name}` and `{age}` in the format string refer to the model fields, not the widget fields.

When the user types "Alice" and sets age to 25:
Output: `"Alice, age 25"`

### Widget Names vs Model Fields

If a widget field has the same name as a model field, format expressions prefer the **model field**.

```python
@widget
class UserDisplay(QWidget, Widget[User]):
    # Widget named "name" (QLineEdit)
    name: QLineEdit = make(QLineEdit, bind="name")
    age: QSpinBox = make(QSpinBox, bind="age")
    # {name} and {age} refer to MODEL fields, not the QLineEdit/QSpinBox widgets
    info: QLabel = make(QLabel, bind="Name: {name}, Age: {age}")
```

This is intentional - in format strings, you almost always want the data value, not the widget.

## Self Reference

You can use `self` to access the widget instance.

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Value: {self.count + self.count}")
```

Output: `"Value: 0"`
After incrementing to 10: `"Value: 20"`

This is useful when you need to call widget methods or access non-state attributes.

## How It Works

Format bindings are detected by the presence of `{` and `}` in the bind string. When found:

1. **Parse**: Extract all `{expression}` fields using Python's `string.Formatter`
2. **Analyze**: Use AST parsing to find all variable names in expressions
3. **Subscribe**: Create subscriptions to all referenced state/model observables
4. **Compute**: Evaluate expressions and format the result string
5. **Update**: Re-run computation whenever any subscribed observable changes

### What Gets Tracked

For simple names like `{count}`:
- Tracks the `count` field directly

For expressions like `{count + 5}`:
- Parses the AST to find all variable names
- Tracks each variable separately

For nested paths like `{dog.name}`:
- Tracks both the nested property AND the top-level object
- Updates when either changes

### Expression Evaluation

Expressions are evaluated using Python's `eval()` with:
- Access to all referenced state/model fields
- Access to common builtins (len, min, max, etc.)
- No access to dangerous operations (imports, file I/O, etc.)

### Non-Reactive Attributes

Format expressions can reference **any** widget attribute, not just `state()` fields or `Widget[T]` model properties:

```python
@widget
class Mixed(QWidget):
    count: int = state(0)              # Reactive - triggers updates
    greeting: str = "Hello"            # NOT reactive - regular attribute

    label: QLabel = make(QLabel, bind="{greeting}, count is {count}")
```

The label shows `"Hello, count is 0"` initially. When `count` changes, the entire format string re-evaluates, reading `greeting`'s **current** value.

However, changing `greeting` alone won't trigger an update - only reactive fields (`state()` or `Widget[T]` model fields) trigger re-computation.

**Use case**: Static text combined with dynamic values, or attributes you only change alongside reactive fields.

## Simple vs Format Binding

When should you use format expressions vs simple bindings?

**Simple binding** (`bind="count"`):
- Single value, no formatting needed
- Two-way binding supported (for input widgets)
- Slightly more efficient

**Format binding** (`bind="Count: {count}"`):
- Need text around the value
- Multiple values in one string
- Need expressions or formatting
- One-way binding only (read-only display)

For labels and read-only text, format expressions are perfect. For input widgets where you want two-way binding, use simple bindings.

## See Also

- [Reactive State](state.md) - Using `state()` to create reactive fields
- [Record Widgets](record-widgets.md) - Working with `Widget[T]` for form binding
- [make()](../reference/factories/make.md) - The `bind` parameter in detail
- [Observant Integration](../guides/observant.md) - Understanding the reactive layer
