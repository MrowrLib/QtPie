# Format String Expressions

QtPie's `bind=` parameter supports complex Python expressions within format strings, enabling powerful declarative UI patterns. Any expression valid in Python can be used, and all bindings are reactive - they automatically update when referenced variables change.

## Basic Expressions

### Variable References

The simplest form - just reference a variable:

```python
@widget
class Example(Widget):
    _name: Variable[str] = new("Alice")
    _label: QLabel = new(bind="{_name}")  # Shows "Alice"
```

### String Literals

Mix variables with static text:

```python
@widget
class Greeting(Widget):
    _name: Variable[str] = new("World")
    _label: QLabel = new(bind="Hello, {_name}!")  # Shows "Hello, World!"
```

## Builtin Functions

All Python builtin functions work in expressions:

```python
@widget
class Builtins(Widget):
    _name: Variable[str] = new("Hello")
    _count: Variable[int] = new(-42)
    _items: Variable[list[str]] = new(["a", "b", "c"])

    # String length
    _len_label: QLabel = new(bind="Length: {len(_name)}")  # "Length: 5"

    # Absolute value
    _abs_label: QLabel = new(bind="Abs: {abs(_count)}")  # "Abs: 42"

    # Type conversion
    _str_label: QLabel = new(bind="String: {str(_count)}")  # "String: -42"

    # Min/max with multiple variables
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _min_label: QLabel = new(bind="Min: {min(_x, _y)}")  # "Min: 10"
    _max_label: QLabel = new(bind="Max: {max(_x, _y)}")  # "Max: 20"

    # Rounding
    _price: Variable[float] = new(3.14159)
    _rounded: QLabel = new(bind="{round(_price, 2)}")  # "3.14"
```

## String Methods

All string methods are available:

```python
@widget
class StringMethods(Widget):
    _text: Variable[str] = new("hello world")

    # Case conversion
    _upper: QLabel = new(bind="{_text.upper()}")  # "HELLO WORLD"
    _lower: QLabel = new(bind="{_text.lower()}")  # "hello world"
    _title: QLabel = new(bind="{_text.title()}")  # "Hello World"

    # Whitespace handling
    _name: Variable[str] = new("  Alice  ")
    _stripped: QLabel = new(bind="{_name.strip()}")  # "Alice"

    # Replacement
    _replaced: QLabel = new(bind="{_text.replace('world', 'there')}")  # "hello there"

    # Method chaining
    _messy: Variable[str] = new("  HELLO  ")
    _clean: QLabel = new(bind="{_messy.strip().lower()}")  # "hello"
```

## Math Expressions

Arithmetic operations work as expected:

```python
@widget
class Math(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)

    # Basic operations
    _sum: QLabel = new(bind="{_x + _y}")  # "30"
    _diff: QLabel = new(bind="{_x - _y}")  # "-10"
    _product: QLabel = new(bind="{_x * _y}")  # "200"
    _quotient: QLabel = new(bind="{_x / _y}")  # "0.5"

    # Complex expressions with parentheses
    _z: Variable[int] = new(5)
    _result: QLabel = new(bind="{(_x + _y) * _z}")  # "(10 + 20) * 5 = 150"

    # With format string context
    _labeled: QLabel = new(bind="Sum: {_x + _y}, Product: {_x * _y}")
```

## Format Specifications

Python's format specification mini-language works:

```python
@widget
class FormatSpecs(Widget):
    # Float precision
    _price: Variable[float] = new(19.99)
    _formatted_price: QLabel = new(bind="${_price:.2f}")  # "$19.99"

    # Percentage
    _rate: Variable[float] = new(0.157)
    _percentage: QLabel = new(bind="{_rate:.1%}")  # "15.7%"

    # Zero padding
    _num: Variable[int] = new(42)
    _padded: QLabel = new(bind="{_num:05d}")  # "00042"

    # Format spec on expressions
    _cost: Variable[float] = new(10.0)
    _tax_rate: Variable[float] = new(0.1)
    _total: QLabel = new(bind="Total: ${_cost * (1 + _tax_rate):.2f}")  # "Total: $11.00"
```

## Instance Methods

Call methods on your widget from bindings:

```python
@widget
class Methods(Widget):
    _name: Variable[str] = new("World")

    # Simple method call
    _greeting: QLabel = new(bind="{get_greeting()}")

    def get_greeting(self) -> str:
        return "Hello!"

    # Method that uses variables
    _custom: QLabel = new(bind="{greet(_name)}")

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"
```

## Special Placeholders

QtPie provides special placeholders for common scenarios:

### `{#self}` - Widget or Value Reference

In a regular binding, `#self` refers to the widget instance:

```python
@widget
class SelfWidget(Widget):
    title: str = "My Widget"
    _label: QLabel = new(bind="{#self.title}")  # Accesses widget.title
    _name_label: QLabel = new(bind="{#self.objectName()}")  # Calls widget method
```

In a `Variable[T, W]` context, `#self` refers to the **variable's value**, not the widget:

```python
@widget
class SelfValue(Widget):
    # #self is the string value "Hello", not the QLabel
    _name: Variable[str, QLabel] = new("Hello")(bind="Value: {#self}")

    # Use methods on the value
    _upper: Variable[str, QLabel] = new("hello")(bind="{#self.upper()}")  # "HELLO"

    # Use functions on the value
    _len: Variable[str, QLabel] = new("Hello")(bind="Length: {len(#self)}")  # "Length: 5"
```

### `{#var}` - Explicit Value Reference

An alias for the variable's value (same as `#self` in `Variable[T, W]` context):

```python
@widget
class VarPlaceholder(Widget):
    _count: Variable[int, QLabel] = new(10)(bind="Count: {#var}")  # "Count: 10"
    _double: Variable[int, QLabel] = new(5)(bind="Double: {#var * 2}")  # "Double: 10"
```

### `{#widget}` - Parent Widget Reference

Access the parent widget from within a `Variable[T, W]` binding:

```python
@widget
class WidgetRef(Widget):
    title: str = "MyApp"
    version: str = "1.0"

    _header: Variable[str, QLabel] = new("")(
        bind="{#widget.title} v{#widget.version}"
    )  # "MyApp v1.0"
```

### `{#index}`, `{#key}`, `{#value}` - Collection Placeholders

Used in list and dict repeaters (covered in separate documentation):

```python
@widget
class Collections(Widget):
    # List: #index and #self
    _numbers: Variable[list[int], QLabel] = new([1, 2, 3])(
        bind="Item {#index}: {#self}"  # "Item 0: 1", "Item 1: 2", etc.
    )

    # Dict: #key and #value
    _scores: Variable[dict[str, int], QLabel] = new({"Alice": 100})(
        bind="{#key}: {#value} points"  # "Alice: 100 points"
    )
```

## Combined Expressions

Mix multiple expression types:

```python
@widget
class Combined(Widget):
    _first: Variable[str] = new("hello")
    _second: Variable[str] = new("world")

    # Multiple expressions in one string
    _both: QLabel = new(bind="{_first.upper()} {_second.upper()}")  # "HELLO WORLD"

    # Math and string operations
    _items: Variable[list[str]] = new(["a", "b", "c"])
    _count_label: QLabel = new(bind="{len(_items)} items")  # "3 items"

    # Complex formatting
    _name: Variable[str] = new("alice")
    _greeting: QLabel = new(bind="Hello, {_name.title()}!")  # "Hello, Alice!"
```

## Reactivity

All bindings are reactive. When any referenced variable changes, the expression is automatically re-evaluated:

```python
@widget
class Reactive(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _sum: QLabel = new(bind="Sum: {_x + _y}")  # Initially shows "Sum: 30"

    def update_values(self):
        self._x.value = 50  # Label automatically updates to "Sum: 70"
        self._y.value = 5   # Label automatically updates to "Sum: 55"
```

Even complex expressions with multiple variables update correctly:

```python
@widget
class ComplexReactive(Widget):
    _a: Variable[int] = new(2)
    _b: Variable[int] = new(3)
    _c: Variable[int] = new(4)
    _result: QLabel = new(bind="{(_a + _b) * _c}")  # Shows "20"

    def change_any(self):
        self._a.value = 5  # Result updates to "32" = (5 + 3) * 4
        self._b.value = 7  # Result updates to "48" = (5 + 7) * 4
        self._c.value = 2  # Result updates to "24" = (5 + 7) * 2
```

## Working with Record Types

Expressions work with `Widget[T]` record fields:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonView(Widget[Person]):
    # Access record fields directly
    _upper_name: QLabel = new(bind="{name.upper()}")

    # Math on record fields
    _age_doubled: QLabel = new(bind="{age * 2}")

    # Combine multiple fields
    _info: QLabel = new(bind="{name} is {age} years old")

w = PersonView()
w.record_state.observable.name.set("Alice")
w.record_state.observable.age.set(30)
# _upper_name shows "ALICE"
# _age_doubled shows "60"
# _info shows "Alice is 30 years old"
```

## Error Handling

Invalid expressions or runtime errors are caught and displayed:

```python
@widget
class Errors(Widget):
    # Undefined variable - shows error message
    _bad: QLabel = new(bind="{undefined_variable}")

    # Division by zero - shows error message
    _zero: Variable[int] = new(0)
    _bad_math: QLabel = new(bind="{1 / _zero}")
```

The error messages are displayed in the widget rather than crashing your application.

## Best Practices

1. **Keep expressions simple** - Complex logic belongs in methods, not format strings
2. **Prefer methods for reuse** - If you use an expression multiple times, make it a method
3. **Use format specs for display** - Format numbers, dates, etc., for user-facing text
4. **Leverage reactivity** - Let QtPie handle updates rather than manually updating widgets
5. **Test edge cases** - Ensure your expressions handle empty strings, zero values, etc.

## Common Patterns

### Conditional text with methods

```python
@widget
class ItemCounter(Widget):
    _count: Variable[int] = new(1)
    _label: QLabel = new(bind="{item_text()}")

    def item_text(self) -> str:
        count = self._count.value
        return f"{count} item{'s' if count != 1 else ''}"
```

### Computed properties

```python
@widget
class Cart(Widget):
    _subtotal: Variable[float] = new(100.0)
    _tax_rate: Variable[float] = new(0.08)

    # Computed total
    _total: QLabel = new(bind="Total: ${_subtotal * (1 + _tax_rate):.2f}")
```

### Dynamic status display

```python
@widget
class Status(Widget):
    _status: Variable[str] = new("active")
    _count: Variable[int] = new(42)

    _label: QLabel = new(bind="{_status.upper()}: {_count} items")
```
