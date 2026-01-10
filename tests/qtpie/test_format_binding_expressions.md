# Format Binding Expressions

Tests for complex Python expressions in `bind=` format strings.

## Builtin Functions

Python builtin functions work in format bindings: `len()`, `str()`, `int()`, `abs()`, `min()`, `max()`, `round()`.

```python
@widget
class Test(Widget):
    _name: Variable[str] = new("Hi")
    _label: QLabel = new(bind="{len(_name)}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("2")

w._name.value = "Hello World"
assert_that(w._label.text()).is_equal_to("11")
```

```python
@widget
class Test(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _min_label: QLabel = new(bind="{min(_x, _y)}")
    _max_label: QLabel = new(bind="{max(_x, _y)}")

w = qt.track(Test())
assert_that(w._min_label.text()).is_equal_to("10")
assert_that(w._max_label.text()).is_equal_to("20")
```

## String Methods

String methods work: `upper()`, `lower()`, `title()`, `strip()`, `replace()`. Methods can be chained.

```python
@widget
class Test(Widget):
    _name: Variable[str] = new("hello")
    _label: QLabel = new(bind="{_name.upper()}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("HELLO")

w._name.value = "world"
assert_that(w._label.text()).is_equal_to("WORLD")
```

```python
@widget
class Test(Widget):
    _name: Variable[str] = new("  HELLO  ")
    _label: QLabel = new(bind="{_name.strip().lower()}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("hello")
```

## Math Expressions

Math expressions with operators: `+`, `-`, `*`, `/`. Complex expressions with parentheses work.

```python
@widget
class Test(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(5)
    _label: QLabel = new(bind="{_x + _y}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("15")

w._x.value = 20
assert_that(w._label.text()).is_equal_to("25")
```

```python
@widget
class Test(Widget):
    _x: Variable[int] = new(2)
    _y: Variable[int] = new(3)
    _z: Variable[int] = new(4)
    _label: QLabel = new(bind="{(_x + _y) * _z}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("20")  # (2 + 3) * 4
```

## Format Specifications

Python format specs work: float precision, percentage, padding, width.

```python
@widget
class Test(Widget):
    _price: Variable[float] = new(19.99)
    _label: QLabel = new(bind="${_price:.2f}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("$19.99")
```

```python
@widget
class Test(Widget):
    _price: Variable[float] = new(10.0)
    _tax_rate: Variable[float] = new(0.1)
    _label: QLabel = new(bind="${_price * (1 + _tax_rate):.2f}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("$11.00")
```

## #self Placeholder

`#self` accesses the widget instance. Useful for accessing widget properties.

```python
@widget
class Test(Widget):
    title: str = "My Title"
    _label: QLabel = new(bind="{#self.title}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("My Title")
```

## Instance Methods

Instance methods can be called from format expressions.

```python
@widget
class Test(Widget):
    _name: Variable[str] = new("World")
    _label: QLabel = new(bind="{greet(_name)}")

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("Hello, World!")
```

## Combined Expressions

Multiple expression types can be combined in one format string.

```python
@widget
class Test(Widget):
    _first: Variable[str] = new("hello")
    _second: Variable[str] = new("world")
    _label: QLabel = new(bind="{_first.upper()} {_second.upper()}")

w = qt.track(Test())
assert_that(w._label.text()).is_equal_to("HELLO WORLD")
```

## Error Handling

Invalid expressions and exceptions are caught gracefully, displaying error messages instead of crashing.

```python
@widget
class Test(Widget):
    _value: Variable[int] = new(0)
    _label: QLabel = new(bind="{1 / _value}")

w = qt.track(Test())
# Division by zero should be caught
assert_that(w._label.text()).contains("error")
```

## Record Property Expressions

Expressions work on record (dataclass) properties in `Widget[T]`.

```python
@dataclass
class Counter:
    count: int = 0

@widget
class Test(Widget[Counter]):
    _label: QLabel = new(bind="{count * 2}")

w = qt.track(Test())
w._qtpie.record_state.observable.count.set(21)
assert_that(w._label.text()).is_equal_to("42")
```

## Variable[T, QWidget] Special Placeholders

In `Variable[T, QWidget]` with `bind=`, special placeholders have specific meanings:
- `#self` - the Variable's value (not the widget)
- `#var` - alias for the Variable's value
- `#widget` - the parent widget instance

```python
@widget
class Test(Widget):
    _name: Variable[str, QLabel] = new("hello")(bind="Upper: {#self.upper()}")

w = qt.track(Test())
assert_that(w._name.widget.text()).is_equal_to("Upper: HELLO")
```

```python
@widget
class Test(Widget):
    _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")

w = qt.track(Test())
assert_that(w._count.widget.text()).is_equal_to("Double: 20")
```

```python
@widget
class Test(Widget):
    title: str = "MyWidget"
    _label: Variable[str, QLabel] = new("x")(bind="Widget title: {#widget.title}")

w = qt.track(Test())
assert_that(w._label.widget.text()).is_equal_to("Widget title: MyWidget")
```

```python
@widget
class Test(Widget):
    title: str = "Test"
    _val: Variable[int, QLabel] = new(5)(bind="{#widget.title}: {#self} doubled is {#var * 2}")

w = qt.track(Test())
assert_that(w._val.widget.text()).is_equal_to("Test: 5 doubled is 10")
```
