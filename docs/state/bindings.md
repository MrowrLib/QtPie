# Bindings

Bindings connect Variables to widgets, automatically updating the UI when data changes.

## Declarative Bindings (Recommended)

Use the `bind=` parameter on `new()`:

```python
from qtpie import Widget, Variable, new, widget

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Alice")
    _label: QLabel = new(bind="_name")  # Shows "Alice"
```

When `_name` changes, the label updates automatically.

### Format String Bindings

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Alice")
    _count: Variable[int] = new(42)

    # String interpolation
    _greeting: QLabel = new(bind="Hello, {_name}!")

    # Multiple variables
    _summary: QLabel = new(bind="{_name} has {_count} items")
```

### Expressions in Bindings

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("alice")
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)

    # Method calls
    _upper: QLabel = new(bind="{_name.upper()}")

    # Math expressions
    _sum: QLabel = new(bind="{_x + _y}")

    # Built-in functions
    _length: QLabel = new(bind="Length: {len(_name)}")

    # Format specs
    _price: Variable[float] = new(19.99)
    _formatted: QLabel = new(bind="${_price:.2f}")
```

See [Format Expressions](format-expressions.md) for complete syntax.

## Two-Way Bindings

Input widgets automatically get two-way binding:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Initial")
    _input: QLineEdit = new(bind="_name")
```

- Variable changes → input updates
- User types → Variable updates

## Auto-Binding

Widgets auto-bind to same-named Variables (with underscore stripped):

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Alice")
    name: QLineEdit = new()  # Auto-binds to _name!
```

This works for Variables and record fields.

## Imperative bind() Function

For programmatic binding in `__setup__`:

```python
from qtpie import bind

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Initial")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._label)
```

### Explicit Property

```python
bind(self._name).to(self._label, "text")
```

### One-Way Only

```python
bind(self._name).to(self._input, two_way=False)
```

## Property Bindings

Control visibility and enabled state:

```python
@widget
class MyWidget(Widget):
    _show_panel: Variable[bool] = new(False)
    _panel: QLabel = new("Hidden", visible="_show_panel")

    _can_submit: Variable[bool] = new(False)
    _button: QPushButton = new("Submit", enabled="_can_submit")

    # Expression-based
    _count: Variable[int] = new(0)
    _warning: QLabel = new("Low!", visible="{_count < 5}")
```

See [Property Bindings](property-bindings.md) for details.

## List Bindings

Bind a list Variable to create multiple widgets:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])
    _labels: list[QLabel] = new(bind="_items")
```

With format:

```python
_labels: list[QLabel] = new(
    bind="_items",
    format="#{#index}: {#self}"  # "#0: Buy milk", "#1: Walk dog"
)
```

## Dict Bindings

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
    _labels: list[QLabel] = new(
        bind="_scores",
        format="{#key}: {#value}"  # "Alice: 100", "Bob: 85"
    )
```

## Special Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{#self}` | Current item value (in lists/dicts) |
| `{#index}` | Item index (in lists) |
| `{#key}` | Dict key |
| `{#value}` | Dict value |
| `{#widget}` | Parent widget instance |
| `{#app}` | QApplication instance |
| `{#var}` | Variable value (in Variable[T,W]) |

## Variable[T, W] Inline Binding

```python
@widget
class Form(Widget):
    # Variable + widget, auto-bound
    _name: Variable[str, QLineEdit] = new("")(
        placeholderText="Enter name"
    )

    # Access widget
    def focus(self) -> None:
        self._name.widget.setFocus()
```

The widget displays and edits the Variable's value with two-way binding.

## Record Bindings

With `Widget[T]`, fields auto-bind to record properties:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age
```

Explicit binding:

```python
full_name: QLabel = new(bind="{record.name}")
```

## Widget Bindings (Parent → Child)

Pass Variables to child widgets:

```python
@widget
class CounterDisplay(Widget):
    count: Variable[int]  # Required binding
    _label: QLabel = new(bind="Count: {count}")

@widget
class App(Widget):
    _my_count: Variable[int] = new(0)
    _display: CounterDisplay = new(count="_my_count")
    _button: QPushButton = new("+1", clicked="increment")

    def increment(self) -> None:
        self._my_count += 1  # Display updates!
```

This is like React props - state flows from parent to child.

## Default Property Detection

`bind()` auto-detects the right property:

| Widget Type | Property |
|-------------|----------|
| `QLabel` | `text` |
| `QLineEdit` | `text` |
| `QSpinBox` | `value` |
| `QCheckBox` | `checked` |
| `QComboBox` | `currentText` |

## See Also

- [Variables](variables.md) - Reactive state
- [Format Expressions](format-expressions.md) - Expression syntax
- [Property Bindings](property-bindings.md) - visible= and enabled=
- [Records](../data/records.md) - Record auto-binding
