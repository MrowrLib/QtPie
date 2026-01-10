# Format Expressions

Format expressions let you use Python code inside `bind=` strings. Expressions are reactive - when any referenced Variable changes, the expression re-evaluates.

## Basic Syntax

```python
bind="{expression}"
```

## String Interpolation

```python
@widget
class MyWidget(Widget):
    _first: Variable[str] = new("Hello")
    _second: Variable[str] = new("World")
    _label: QLabel = new(bind="{_first} {_second}!")
    # Shows: "Hello World!"
```

## Builtin Functions

Common Python builtins work in expressions:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Hello")
    _items: Variable[list[str]] = new(["a", "b", "c"])
    _x: Variable[int] = new(-5)

    # len()
    _length: QLabel = new(bind="Length: {len(_name)}")  # "Length: 5"

    # min() / max()
    _min: QLabel = new(bind="{min(_items)}")  # "a"

    # abs()
    _abs: QLabel = new(bind="{abs(_x)}")  # "5"

    # round()
    _pi: Variable[float] = new(3.14159)
    _rounded: QLabel = new(bind="{round(_pi, 2)}")  # "3.14"
```

## String Methods

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("  hello  ")

    # Single method
    _upper: QLabel = new(bind="{_name.upper()}")  # "  HELLO  "

    # Method chaining
    _clean: QLabel = new(bind="{_name.strip().upper()}")  # "HELLO"

    # replace()
    _replaced: QLabel = new(bind="{_name.replace('hello', 'world')}")
```

## Math Expressions

```python
@widget
class MyWidget(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(5)
    _z: Variable[int] = new(2)

    # Basic operators
    _sum: QLabel = new(bind="{_x + _y}")      # "15"
    _diff: QLabel = new(bind="{_x - _y}")     # "5"
    _product: QLabel = new(bind="{_x * _y}")  # "50"
    _quotient: QLabel = new(bind="{_x / _y}") # "2.0"

    # Parentheses for order of operations
    _complex: QLabel = new(bind="{(_x + _y) * _z}")  # "30"
```

## Format Specifications

Use Python format specs after the colon:

```python
@widget
class MyWidget(Widget):
    _price: Variable[float] = new(19.99)
    _ratio: Variable[float] = new(0.756)
    _count: Variable[int] = new(42)

    # Float precision
    _formatted: QLabel = new(bind="${_price:.2f}")  # "$19.99"

    # Percentage
    _percent: QLabel = new(bind="{_ratio:.1%}")  # "75.6%"

    # Padding
    _padded: QLabel = new(bind="{_count:05d}")  # "00042"
```

### Expressions with Format Specs

```python
_total: QLabel = new(bind="${_price * 1.1:.2f}")  # Price + 10% tax
```

## Instance Methods

Call methods on the widget:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("World")
    _label: QLabel = new(bind="{greet(_name)}")

    def greet(self, name: str) -> str:
        return f"Hello, {name}!"
```

## Special Placeholders

| Placeholder | Description | Context |
|-------------|-------------|---------|
| `#self` | Variable value (in Variable[T,W]) or widget | Variable context |
| `#var` | Explicit Variable value | Variable[T,W] |
| `#widget` | Parent widget instance | Any |
| `#app` | QApplication instance | Any |
| `#index` | Item index | List repeater |
| `#key` | Dict key | Dict repeater |
| `#value` | Dict value | Dict repeater |

### #self and #var in Variable[T, W]

```python
@widget
class MyWidget(Widget):
    _name: Variable[str, QLabel] = new("hello")(
        bind="Upper: {#self.upper()}"  # #self = "hello"
    )

    _count: Variable[int, QLabel] = new(10)(
        bind="Double: {#var * 2}"  # #var = 10, shows "Double: 20"
    )
```

### #widget for Parent Access

```python
@widget
class MyWidget(Widget):
    title: str = "My Widget"
    _label: QLabel = new(bind="Title: {#widget.title}")
```

### #index in List Repeaters

```python
@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new(["A", "B", "C"])
    _labels: list[QLabel] = new(
        bind="_items",
        format="#{#index}: {#self}"  # "#0: A", "#1: B", "#2: C"
    )
```

### #key and #value in Dict Repeaters

```python
@widget
class MyWidget(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100})
    _labels: list[QLabel] = new(
        bind="_scores",
        format="{#key} scored {#value}"  # "Alice scored 100"
    )
```

## Record Properties

Access record fields in `Widget[T]`:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person("Alice", 30))
class PersonView(Widget[Person]):
    _info: QLabel = new(bind="{name}, {age} years old")
    _upper: QLabel = new(bind="{name.upper()}")
```

## Combining Expressions

Mix literals, variables, and expressions:

```python
@widget
class MyWidget(Widget):
    title: str = "Report"
    _count: Variable[int] = new(5)
    _val: Variable[int, QLabel] = new(10)(
        bind="{#widget.title}: {#var} doubled is {#self * 2}"
        # "Report: 10 doubled is 20"
    )
```

## Error Handling

Invalid expressions display error messages instead of crashing:

```python
@widget
class MyWidget(Widget):
    _value: Variable[int] = new(0)
    _result: QLabel = new(bind="{1 / _value}")  # Shows error for division by zero
```

## Reactivity

All expressions are reactive - they re-evaluate when any referenced Variable changes:

```python
@widget
class MyWidget(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _sum: QLabel = new(bind="{_x + _y}")  # Initially "30"

    def update(self) -> None:
        self._x = 50  # _sum now shows "70"
```

## See Also

- [Bindings](bindings.md) - Binding overview
- [Variables](variables.md) - Reactive state
- [Property Bindings](property-bindings.md) - visible= and enabled=
