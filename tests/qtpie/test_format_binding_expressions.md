# Format Binding Expressions in QtPie

This document describes the DSL and conventions for using Python expressions within `bind=` format strings in QtPie widgets.

## Basic Syntax

Format bindings use curly braces `{}` to embed expressions that are evaluated and displayed reactively.

```python
_label: QLabel = new(bind="{_name}")
```

Expressions automatically update when any referenced `Variable` changes.

---

## Builtin Functions

Python builtins like `len()`, `str()`, `int()`, `abs()`, `min()`, `max()`, and `round()` work inside expressions.

```python
_name: Variable[str] = new("Hello")
_label: QLabel = new(bind="{len(_name)}")  # Shows "5"
```

```python
_x: Variable[int] = new(10)
_y: Variable[int] = new(20)
_label: QLabel = new(bind="{min(_x, _y)}")  # Shows "10"
```

---

## String Methods

Call string methods directly on string Variables.

```python
_name: Variable[str] = new("hello")
_label: QLabel = new(bind="{_name.upper()}")  # Shows "HELLO"
```

Method chaining is supported:

```python
_name: Variable[str] = new("  HELLO  ")
_label: QLabel = new(bind="{_name.strip().lower()}")  # Shows "hello"
```

Common methods: `.upper()`, `.lower()`, `.title()`, `.strip()`, `.replace()`

---

## Math Expressions

Arithmetic operators work between Variables.

```python
_x: Variable[int] = new(10)
_y: Variable[int] = new(20)
_label: QLabel = new(bind="{_x + _y}")  # Shows "30"
```

Parentheses for grouping:

```python
_x: Variable[int] = new(2)
_y: Variable[int] = new(3)
_z: Variable[int] = new(4)
_label: QLabel = new(bind="{(_x + _y) * _z}")  # Shows "20"
```

---

## Format Specifications

Python format specs (after `:`) work for number formatting.

```python
_price: Variable[float] = new(19.99)
_label: QLabel = new(bind="${_price:.2f}")  # Shows "$19.99"
```

```python
_rate: Variable[float] = new(0.157)
_label: QLabel = new(bind="{_rate:.1%}")  # Shows "15.7%"
```

```python
_num: Variable[int] = new(42)
_label: QLabel = new(bind="{_num:05d}")  # Shows "00042"
```

Format specs work on computed expressions:

```python
_price: Variable[float] = new(10.0)
_tax: Variable[float] = new(0.1)
_label: QLabel = new(bind="${_price * (1 + _tax):.2f}")  # Shows "$11.00"
```

---

## Instance Methods

Call widget instance methods directly in expressions.

```python
@widget
class Test(Widget):
    _label: QLabel = new(bind="{get_greeting()}")

    def get_greeting(self) -> str:
        return "Hello!"
```

Methods can accept Variable arguments:

```python
_name: Variable[str] = new("World")
_label: QLabel = new(bind="{greet(_name)}")

def greet(self, name: str) -> str:
    return f"Hello, {name}!"
```

---

## The `#self` Placeholder

`#self` refers to the widget instance, allowing access to widget properties.

```python
@widget
class Test(Widget):
    title: str = "My Title"
    _label: QLabel = new(bind="{#self.title}")  # Shows "My Title"
```

---

## Variable[T, QWidget] Pattern

When using `Variable[T, QLabel]` with `bind=`, special placeholders apply:

### `#self` - The Variable's Value

```python
_name: Variable[str, QLabel] = new("Hello")(bind="Value: {#self}!")
# Shows "Value: Hello!"
```

Works with methods on the value:

```python
_name: Variable[str, QLabel] = new("hello")(bind="{#self.upper()}")
# Shows "HELLO"
```

### `#var` - Alias for Variable's Value

```python
_count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")
# Shows "Double: 20"
```

### `#widget` - Parent Widget Instance

```python
title: str = "MyWidget"
_label: Variable[str, QLabel] = new("x")(bind="Title: {#widget.title}")
# Shows "Title: MyWidget"
```

### Combining Placeholders

```python
title: str = "Test"
_val: Variable[int, QLabel] = new(5)(bind="{#widget.title}: {#self} doubled is {#var * 2}")
# Shows "Test: 5 doubled is 10"
```

---

## Record Field Binding

For `Widget[T]` with a dataclass record, access record fields directly.

```python
@dataclass
class Person:
    name: str = ""

@widget
class Test(Widget[Person]):
    _label: QLabel = new(bind="{name.upper()}")  # Binds to record.name
```

---

## Multiple Expressions

Combine multiple expressions in one format string.

```python
_first: Variable[str] = new("hello")
_second: Variable[str] = new("world")
_label: QLabel = new(bind="{_first.upper()} {_second.upper()}")
# Shows "HELLO WORLD"
```

---

## Error Handling / Fallbacks

Invalid expressions or exceptions result in empty string, enabling the `or` fallback pattern.

```python
_value: Variable[str | None] = new(None)
_label: QLabel = new(bind="{_value or 'N/A'}")  # Shows "N/A"
```

---

## Reactivity

All expressions are fully reactive. When any referenced Variable changes, the expression re-evaluates automatically.

```python
_x: Variable[int] = new(10)
_y: Variable[int] = new(5)
_label: QLabel = new(bind="{_x + _y}")  # Initially "15"

# Later:
w._x.value = 20  # _label automatically updates to "25"
```
