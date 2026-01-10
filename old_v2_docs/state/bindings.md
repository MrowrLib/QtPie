# Bindings

Bindings connect Variables to widget properties, creating reactive relationships where changes flow automatically between state and UI. QtPie provides the `bind()` function for manual binding and automatic binding via the `bind=` parameter in `new()`.

## The bind() Function

Use `bind()` to manually connect a Variable to a widget property.

### Basic One-Way Binding

The simplest form binds a Variable to a widget, updating the widget when the Variable changes:

```python
from PySide6.QtWidgets import QLabel
from qtpie import Widget, Variable, bind, new, widget

@widget
class Example(Widget):
    _name: Variable[str] = new("Hello")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._label)

# Initial: label shows "Hello"
# After: widget._name.value = "World" → label shows "World"
```

When no property name is specified, `bind()` uses the default property for that widget type:
- `QLabel` → `text`
- `QLineEdit` → `text`
- `QSpinBox` → `value`

### Explicit Property Names

Specify which property to bind to:

```python
@widget
class Example(Widget):
    _name: Variable[str] = new("Hello")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._label, "text")
```

### Two-Way Binding

By default, bindings are two-way when the widget supports signals for property changes:

```python
from PySide6.QtWidgets import QLineEdit
from qtpie import Widget, Variable, bind, new, widget

@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _input: QLineEdit = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._input)

# Variable → Widget
widget._name.value = "Alice"
print(widget._input.text())  # "Alice"

# Widget → Variable
widget._input.setText("Bob")
print(widget._name.value)  # "Bob"
```

This works automatically for widgets like `QLineEdit` (which has `textChanged` signal) and `QSpinBox` (which has `valueChanged` signal).

### One-Way Binding Only

Disable two-way binding with `two_way=False`:

```python
@widget
class Example(Widget):
    _name: Variable[str] = new("Initial")
    _input: QLineEdit = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._input, two_way=False)

# Variable → Widget works
widget._name.value = "From Variable"
print(widget._input.text())  # "From Variable"

# Widget → Variable does NOT work
widget._input.setText("From Widget")
print(widget._name.value)  # Still "From Variable"
```

## The bind= Parameter

The `bind=` parameter in `new()` creates declarative bindings at field definition time. This is the preferred approach for simple bindings.

### Simple Variable Binding

Bind a widget to a Variable by name:

```python
from PySide6.QtWidgets import QLabel, QLineEdit
from qtpie import Widget, Variable, new, widget

@widget
class UserProfile(Widget):
    _username: Variable[str] = new("guest")

    # Bind label to _username Variable
    username_label: QLabel = new(bind="_username")

# username_label automatically shows "guest"
# When _username changes, label updates automatically
```

The `bind=` parameter accepts a string with the Variable field name. QtPie looks up the Variable at runtime and creates the binding.

### Format String Bindings

Use format strings to create dynamic text from Variables:

```python
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)

    # Simple interpolation
    count_label: QLabel = new(bind="Count: {_count}")

    # Multiple variables
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    sum_label: QLabel = new(bind="Sum: {_x + _y}")
```

Format strings support:
- Variable references: `{_varname}`
- Expressions: `{_count * 2}`, `{_x + _y}`
- String methods: `{_name.upper()}`
- Built-in functions: `{len(_items)}`
- Python format specs: `{_price:.2f}`

### Method Calls in Bindings

Call instance methods inside format strings:

```python
@widget
class Example(Widget):
    _name: Variable[str] = new("hello")

    # Built-in functions
    length_label: QLabel = new(bind="Length: {len(_name)}")

    # String methods
    upper_label: QLabel = new(bind="Upper: {_name.upper()}")

    # Custom instance methods
    def compute_display(self) -> str:
        return self._name.value.title()

    computed_label: QLabel = new(bind="Display: {compute_display()}")
```

### Complex Expressions

Format bindings support arbitrary Python expressions:

```python
@widget
class Calculator(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _z: Variable[int] = new(5)

    # Math operations
    sum_label: QLabel = new(bind="Sum: {_x + _y}")
    product_label: QLabel = new(bind="Product: {_x * _y}")

    # Parentheses for precedence
    complex_label: QLabel = new(bind="Result: {(_x + _y) * _z}")

    # Comparisons (result is True/False)
    compare_label: QLabel = new(bind="X > Y: {_x > _y}")

    # String concatenation
    _first: Variable[str] = new("Hello")
    _last: Variable[str] = new("World")
    greeting_label: QLabel = new(bind="{_first} {_last}!")
```

### Format Specifications

Use Python's format specification mini-language:

```python
@widget
class Prices(Widget):
    _price: Variable[float] = new(19.99)

    # Two decimal places
    price_label: QLabel = new(bind="Price: ${_price:.2f}")

    _percent: Variable[float] = new(0.156)
    # Percentage
    percent_label: QLabel = new(bind="Discount: {_percent:.1%}")

    _count: Variable[int] = new(42)
    # Padding with zeros
    padded_label: QLabel = new(bind="ID: {_count:05d}")
```

### Binding Lists

When you bind a list Variable to a widget field, QtPie treats it specially based on the field type.

For `list[QWidget]` fields, QtPie creates a `WidgetRepeater`:

```python
from PySide6.QtWidgets import QLabel
from qtpie import Widget, Variable, new, widget

@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])

    # Creates one QLabel per item
    item_labels: list[QLabel] = new(bind="_items")

# item_labels is a list of QLabels, automatically managed
# Adding to _items creates a new label
# Removing from _items deletes the corresponding label
```

### List Bindings with Format Strings

Customize how list items are displayed:

```python
@widget
class NumberList(Widget):
    _numbers: Variable[list[int]] = new([1, 2, 3, 4, 5])

    # Use {#index} and {#self} placeholders
    number_labels: list[QLabel] = new(
        bind="_numbers",
        format="Item #{#index}: {#self}"
    )
    # Creates labels: "Item #0: 1", "Item #1: 2", etc.
```

Special placeholders for list bindings:
- `{#self}` - The current item value
- `{#index}` - The item's index in the list

You can use expressions with these:

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[list[int]] = new([100, 85, 92])

    score_labels: list[QLabel] = new(
        bind="_scores",
        format="Place {#index + 1}: {#self} points"
    )
    # "Place 1: 100 points", "Place 2: 85 points", etc.
```

### Dict Bindings

Dictionary Variables create one widget per key-value pair:

```python
@widget
class Settings(Widget):
    _config: Variable[dict[str, int]] = new({"width": 800, "height": 600})

    config_labels: list[QLabel] = new(
        bind="_config",
        format="{#key}: {#value}"
    )
    # Creates: "width: 800", "height: 600"
```

Special placeholders for dict bindings:
- `{#key}` - The dictionary key
- `{#value}` - The dictionary value (same as `{#self}`)

### Binding Complex Objects

When binding lists of custom objects, you can access their fields directly:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLabel
from qtpie import Widget, Variable, new, widget

@dataclass
class Dog:
    name: str
    age: int

@widget
class DogList(Widget):
    _dogs: Variable[list[Dog]] = new([
        Dog("Fido", 3),
        Dog("Rex", 5),
    ])

    # Access fields directly in format string
    dog_labels: list[QLabel] = new(
        bind="_dogs",
        format="{name} is {age} years old"
    )
    # Creates: "Fido is 3 years old", "Rex is 5 years old"

    # Or use #self for the whole object
    dog_str_labels: list[QLabel] = new(
        bind="_dogs",
        format="Dog: {#self}"
    )
    # Uses Dog.__str__() or repr()
```

## Reactivity

All bindings are reactive. When any referenced Variable changes, the binding re-evaluates and updates the widget:

```python
@widget
class ReactiveExample(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)

    sum_label: QLabel = new(bind="Sum: {_x + _y}")

# Initially shows "Sum: 30"
widget._x.value = 50
# Automatically updates to "Sum: 70"
```

QtPie tracks all Variables referenced in a format string and subscribes to their changes. When any Variable updates, the entire expression is re-evaluated.

### Multiple Dependencies

A single binding can depend on multiple Variables:

```python
@widget
class Profile(Widget):
    _first: Variable[str] = new("John")
    _last: Variable[str] = new("Doe")
    _age: Variable[int] = new(30)

    info_label: QLabel = new(
        bind="{_first} {_last}, age {_age}"
    )

# Changing any Variable updates the label
widget._first.value = "Jane"  # "Jane Doe, age 30"
widget._age.value = 31        # "Jane Doe, age 31"
```

### Conditional Logic in Bindings

You can use conditional expressions (ternary operator):

```python
@widget
class StatusDisplay(Widget):
    _count: Variable[int] = new(0)

    status_label: QLabel = new(
        bind="Status: {'Empty' if _count == 0 else f'{_count} items'}"
    )

# Shows "Status: Empty" when count is 0
# Shows "Status: 5 items" when count is 5
```

## Type Conversion

QtPie automatically converts types when setting widget properties.

### Primitive Types

Numbers and booleans are converted to strings for text widgets:

```python
@widget
class Display(Widget):
    _count: Variable[int] = new(42)
    _price: Variable[float] = new(19.99)
    _enabled: Variable[bool] = new(True)

    count_label: QLabel = new(bind="Count: {_count}")
    price_label: QLabel = new(bind="Price: {_price}")
    enabled_label: QLabel = new(bind="Enabled: {_enabled}")

# Shows: "Count: 42", "Price: 19.99", "Enabled: True"
```

### Custom Classes

For custom classes, QtPie uses the `__str__` method:

```python
@dataclass
class Person:
    name: str
    age: int

    def __str__(self) -> str:
        return f"{self.name} ({self.age})"

@widget
class Display(Widget):
    _person: Variable[Person] = new(default=Person("Alice", 30))

    person_label: QLabel = new(bind="{_person}")
    # Shows: "Alice (30)"
```

### None Values

`None` is converted to an empty string for text properties:

```python
@widget
class Example(Widget):
    _value: Variable[str | None] = new(None)

    value_label: QLabel = new(bind="{_value}")
    # Shows empty string when _value is None
```

## Special Placeholders Reference

| Placeholder | Context | Description |
|-------------|---------|-------------|
| `{#self}` | Variable[T, W] | The Variable's value |
| `{#var}` | Variable[T, W] | Explicit alias for Variable's value |
| `{#widget}` | Variable[T, W] | The parent Widget instance |
| `{#index}` | List/Dict repeater | Item index |
| `{#key}` | Dict repeater | Dictionary key |
| `{#value}` | Dict repeater | Dictionary value (same as `{#self}`) |

### Using #self in Variable[T, W]

When you have a `Variable[T, W]` (Variable with widget), use `{#self}` to reference the Variable's value in the widget's own binding:

```python
@widget
class Example(Widget):
    # Bind the Variable's widget to show the Variable's value
    _name: Variable[str, QLabel] = new("Hello")(bind="Value: {#self}")

    # Shows "Value: Hello"
    # Updates automatically when _name changes
```

This is useful for inline widgets that display their own values with formatting.

### Using #widget

Reference the parent widget's attributes or methods:

```python
@widget
class Example(Widget):
    title: str = "MyWidget"
    _count: Variable[int] = new(5)

    _label: Variable[str, QLabel] = new("x")(
        bind="{#widget.title}: count={#self}"
    )
    # Shows "MyWidget: count=x"
```

### Using #index in Lists

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["First", "Second", "Third"])

    item_labels: list[QLabel] = new(
        bind="_items",
        format="[{#index}] {#self}"
    )
    # Creates: "[0] First", "[1] Second", "[2] Third"
```

### Using #key and #value in Dicts

```python
@widget
class ConfigView(Widget):
    _settings: Variable[dict[str, int]] = new({
        "timeout": 30,
        "retries": 3,
    })

    setting_labels: list[QLabel] = new(
        bind="_settings",
        format="{#key} = {#value}"
    )
    # Creates: "timeout = 30", "retries = 3"
```

## Common Patterns

### Computed Properties

Create derived state by combining multiple Variables:

```python
@widget
class ShoppingCart(Widget):
    _quantity: Variable[int] = new(1)
    _price: Variable[float] = new(9.99)

    total_label: QLabel = new(bind="Total: ${_quantity * _price:.2f}")
```

### Validation Messages

Show error messages based on state:

```python
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")

    error_label: QLabel = new(
        bind="{'Username required' if len(_username) == 0 else ''}"
    )
```

### List Statistics

Display aggregate information about lists:

```python
@widget
class TaskManager(Widget):
    _tasks: Variable[list[str]] = new(["Task 1", "Task 2"])

    count_label: QLabel = new(bind="Tasks: {len(_tasks)}")
    empty_label: QLabel = new(bind="{'No tasks' if len(_tasks) == 0 else ''}")
```

### Dynamic Formatting

Change display format based on values:

```python
@widget
class Temperature(Widget):
    _temp: Variable[float] = new(20.5)

    temp_label: QLabel = new(
        bind="{_temp:.1f}°C ({'Cold' if _temp < 18 else 'Warm'})"
    )
```

## Performance Considerations

Bindings are efficient but keep these in mind:

1. **Expression complexity**: Complex expressions in format strings are re-evaluated on every Variable change. For expensive computations, consider computing once and storing in a Variable.

2. **Multiple bindings to same Variable**: Multiple widgets can bind to the same Variable with no performance penalty. Each widget updates independently.

3. **List bindings**: When a list Variable changes (append, remove, etc.), only the affected widgets are updated. Unchanged items remain intact.

4. **Two-way bindings**: Only create circular dependencies if you ensure proper event handling. QtPie doesn't automatically prevent update loops.

## Summary

| Feature | Syntax | Example |
|---------|--------|---------|
| Manual binding | `bind(var).to(widget)` | `bind(self._name).to(self._label)` |
| Declarative binding | `new(bind="var")` | `label: QLabel = new(bind="_name")` |
| Format string | `new(bind="{expr}")` | `new(bind="Count: {_count}")` |
| List binding | `new(bind="list_var")` | `labels: list[QLabel] = new(bind="_items")` |
| List format | `new(bind="var", format="...")` | `new(bind="_items", format="#{#index}: {#self}")` |
| Dict binding | `new(bind="dict_var")` | `labels: list[QLabel] = new(bind="_config")` |
| Two-way disable | `bind(var).to(widget, two_way=False)` | Prevents widget → Variable updates |

Key concepts:
- Bindings are reactive and update automatically
- Format strings support full Python expressions
- Type conversion is automatic
- List and dict bindings create repeating widgets
- Special placeholders (`#self`, `#index`, etc.) provide context
