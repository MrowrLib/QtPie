# Variables

Variables are QtPie's reactive state primitives. They hold values that automatically trigger UI updates when changed. Variables come in two forms: `Variable[T]` for standalone reactive state, and `Variable[T, W]` for reactive state with an automatically bound widget.

## Variable[T] - Basic Reactive State

The simplest form creates reactive state that you can observe and update.

### Creating Variables

Use `new()` with a default value:

```python
from qtpie import Widget, Variable, new, widget

@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _name: Variable[str] = new("hello")
    _price: Variable[float] = new(9.99)
    _enabled: Variable[bool] = new(True)
```

For lists and dicts, `new()` with no arguments creates an empty collection:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new()  # Empty list
    _scores: Variable[dict[str, int]] = new()  # Empty dict
```

Or provide defaults:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(default=["Buy milk", "Walk dog"])
    _scores: Variable[dict[str, int]] = new(default={"Alice": 100, "Bob": 85})
```

### Reading and Writing Values

Access the value through the `.value` property:

```python
@widget
class Example(Widget):
    _count: Variable[int] = new(0)

    def increment(self) -> None:
        current = self._count.value
        self._count.value = current + 1
```

### Direct Assignment

You can also assign directly to the Variable field (the descriptor handles it):

```python
@widget
class Example(Widget):
    _count: Variable[int] = new(0)

    def reset(self) -> None:
        self._count = 0  # Same as self._count.value = 0
```

Note: Pyright may flag this as an error since it doesn't understand descriptors. The code works correctly at runtime.

### Augmented Assignment Operators

Variables support all standard augmented assignment operators:

```python
@widget
class Calculator(Widget):
    _total: Variable[int] = new(0)
    _multiplier: Variable[float] = new(1.0)

    def operate(self) -> None:
        self._total += 10     # Add
        self._total -= 5      # Subtract
        self._total *= 2      # Multiply
        self._total //= 3     # Floor divide
        self._total %= 7      # Modulo

        self._multiplier /= 2  # True divide
```

All augmented assignments trigger change callbacks, just like `.value` assignment.

### Observing Changes

Variables expose an `.observable` property for registering callbacks. For primitive types (int, str, float, bool), the observable is an `Observable[T]` that passes the new value to callbacks:

```python
from qtpie import Widget, Variable, new, widget

@widget
class Example(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self._name.observable.on_change(self._on_name_changed)

    def _on_name_changed(self, new_name: str) -> None:
        print(f"Name changed to: {new_name}")
```

### Variables are Per-Instance

Each widget instance gets its own Variable with independent state:

```python
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)

a = Counter()
b = Counter()

a._count.value = 10
b._count.value = 20

print(a._count.value)  # 10
print(b._count.value)  # 20
```

## Variable[list[T]] - Observable Lists

When the type parameter is a list, Variable wraps an `ObservableList` that tracks insertions, removals, and other list operations:

```python
@widget
class TodoApp(Widget):
    _items: Variable[list[str]] = new()

    def add_item(self, text: str) -> None:
        # Append triggers reactivity
        self._items.observable.append(text)

    def clear(self) -> None:
        # Replace entire list
        self._items.value = []
```

List changes trigger the `on_change` callback:

```python
@widget
class TodoApp(Widget):
    _items: Variable[list[str]] = new()

    def __setup__(self) -> None:
        self._items.on_change(self._update_count)

    def _update_count(self) -> None:
        print(f"Item count: {len(self._items.value)}")
```

Modifying the list marks it as dirty (see Dirty Tracking section).

## Variable[dict[K, V]] - Observable Dicts

Dictionary variables work similarly to lists:

```python
@widget
class Config(Widget):
    _settings: Variable[dict[str, str]] = new()

    def update_setting(self, key: str, value: str) -> None:
        self._settings.observable[key] = value

    def clear_settings(self) -> None:
        self._settings.value = {}
```

## Variable[MyClass] - Observable Proxies

For custom classes (dataclasses, plain classes), Variable wraps an `ObservableProxy` that makes field access reactive:

```python
from dataclasses import dataclass
from qtpie import Widget, Variable, new, widget

@dataclass
class Person:
    name: str
    age: int

@widget
class PersonEditor(Widget):
    _person: Variable[Person] = new(default=Person("Alice", 30))

    def __setup__(self) -> None:
        # Access fields through .observable
        self._person.observable.name.on_change(self._on_name_changed)

    def update_name(self) -> None:
        # Set fields through .observable
        self._person.observable.name.set("Bob")

    def _on_name_changed(self, new_name: str) -> None:
        print(f"Name changed to: {new_name}")
```

### Direct Field Access via Proxy

For `Variable[MyClass]`, you can access fields directly on the Variable itself (not just through `.observable`). This provides convenient dot notation:

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class DogEditor(Widget):
    _dog: Variable[Dog] = new(Dog("Fido", 3))

    def rename(self) -> None:
        # Direct field access - read
        old_name = self._dog.name

        # Direct field access - write (reactive!)
        self._dog.name = "Max"
        self._dog.age = 4

    def show_info(self) -> None:
        print(f"{self._dog.name} is {self._dog.age} years old")
```

This works through proxy forwarding: when you access `self._dog.name`, it forwards to `self._dog.observable.name.get()`. When you assign `self._dog.name = "Max"`, it forwards to `self._dog.observable.name.set("Max")`.

**Important**: Variable's own attributes (`.value`, `.widget`, `.observable`, `.is_dirty`) always take precedence. If your class has a field named `value`, access it through `.observable.value.get()` instead of `.value`.

You can also replace the entire object:

```python
def reset(self) -> None:
    self._dog.value = Dog("Buddy", 1)
    # Or via descriptor:
    self._dog = Dog("Buddy", 1)
```

Both approaches trigger reactivity and update any bound widgets.

## Variable[T, W] - Variables with Widgets

The most powerful form creates both reactive state AND an automatically bound widget:

```python
from PySide6.QtWidgets import QLineEdit, QLabel, QSpinBox
from qtpie import Widget, Variable, new, widget

@widget
class LoginForm(Widget):
    # Variable[str, QLineEdit] creates a str variable + QLineEdit widget
    _username: Variable[str, QLineEdit] = new("")
    _password: Variable[str, QLineEdit] = new("")

    # Variable[int, QSpinBox] creates an int variable + QSpinBox widget
    _age: Variable[int, QSpinBox] = new(0)
```

### The .widget Property

Access the created widget via `.widget`:

```python
@widget
class Form(Widget):
    _name: Variable[str, QLineEdit] = new("")

    def focus_name(self) -> None:
        self._name.widget.setFocus()

    def configure_widget(self) -> None:
        self._name.widget.setPlaceholderText("Enter your name...")
```

For `Variable[T]` (no widget type), `.widget` is `None`.

### Automatic Two-Way Binding

The widget is automatically bound to the Variable's value:

```python
@widget
class Example(Widget):
    _name: Variable[str, QLineEdit] = new("hello")

# On creation:
print(widget._name.widget.text())  # "hello"

# Variable → Widget
widget._name.value = "world"
print(widget._name.widget.text())  # "world"

# Widget → Variable
widget._name.widget.setText("updated")
print(widget._name.value)  # "updated"
```

### Configuring Widget Creation

Use the callable chain syntax to pass constructor arguments to the widget:

```python
from PySide6.QtWidgets import QLineEdit, QSpinBox
from qtpie import Widget, Variable, new, widget

@widget
class Form(Widget):
    # new(value)(widget_kwargs)
    _username: Variable[str, QLineEdit] = new("")(
        placeholderText="Username",
        maxLength=50
    )

    _password: Variable[str, QLineEdit] = new("")(
        placeholderText="Password",
        echoMode=QLineEdit.EchoMode.Password
    )

    _age: Variable[int, QSpinBox] = new(18)(
        minimum=0,
        maximum=120
    )
```

Invalid widget kwargs raise a `TypeError` with a helpful message showing:
- The widget type (e.g., `QLineEdit`)
- The field name (e.g., `_username`)
- The invalid kwarg name

### Layout Order

`Variable[T, W]` widgets appear in layout order with other widgets:

```python
@widget
class Form(Widget):
    _label1: QLabel = new("First")                      # Position 0
    _name: Variable[str, QLabel] = new("Second")        # Position 1
    _label2: QLabel = new("Third")                      # Position 2
    _age: Variable[str, QLabel] = new("Fourth")         # Position 3
```

The widgets created from `Variable[T, W]` are placed in the layout in declaration order, interleaved with regular widget fields.

## Variable[T, Widget[T]] - Custom Widget Binding

You can bind a Variable to a custom `Widget[T]` subclass. This creates a powerful pattern for reusable editors:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit, QSpinBox
from qtpie import Widget, Variable, new, widget

@dataclass
class Dog:
    name: str
    age: int

@widget(layout="form")
class DogEditor(Widget[Dog]):
    _name: QLineEdit = new(label="Dog's Name")
    _age: QSpinBox = new(label="Dog's Age")

@widget
class DogOwner(Widget):
    # Variable[Dog, DogEditor] creates a DogEditor bound to the Dog
    dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))
```

The Variable and the Widget's `.record` share the same underlying `ObservableProxy`, so changes in either place update both:

```python
# Change via Variable
widget.dog.observable.name.set("Buddy")
print(widget.dog.widget._name.text())  # "Buddy"

# Change via Widget's record
widget.dog.widget.record.name = "Rex"
print(widget.dog.observable.name.get())  # "Rex"

# Change via Widget's QLineEdit
widget.dog.widget._name.setText("Max")
print(widget.dog.observable.name.get())  # "Max"
```

Or use direct field access:

```python
# All of these are equivalent and reactive:
widget.dog.name = "Buddy"
widget.dog.observable.name.set("Buddy")
widget.dog.widget.record.name = "Buddy"
```

### Variable[list[T], Widget[T]] - Repeating Editors

When you bind a list to a `Widget[T]`, QtPie creates a `WidgetRepeater` with one widget per item:

```python
@widget
class DogKennel(Widget):
    dogs: Variable[list[Dog], DogEditor] = new([
        Dog("Fido", 3),
        Dog("Rex", 5),
    ])

# widget.dogs.widget is a WidgetRepeater
repeater = widget.dogs.widget
print(repeater.widget_count())  # 2

editor0 = repeater.widget_at(0)  # DogEditor for Fido
editor1 = repeater.widget_at(1)  # DogEditor for Rex

print(editor0._name.text())  # "Fido"
print(editor1._name.text())  # "Rex"
```

The repeater automatically updates when you modify the list:

```python
# Add a dog
widget.dogs.append(Dog("Buddy", 2))
print(repeater.widget_count())  # 3

# Remove a dog
widget.dogs.remove(Dog("Fido", 3))
print(repeater.widget_count())  # 2
```

Editing in one widget updates the underlying list item:

```python
editor = repeater.widget_at(0)
editor._name.setText("Spot")
print(widget.dogs[0].name)  # "Spot"
```

## Type Conversion in Bindings

When binding Variables to widgets, QtPie automatically converts types:

```python
from PySide6.QtWidgets import QLabel
from qtpie import Widget, Variable, new, widget, bind

@widget
class Display(Widget):
    _count: Variable[int] = new(42)
    _price: Variable[float] = new(19.99)

    _count_label: QLabel = new("")
    _price_label: QLabel = new("")

    def __setup__(self) -> None:
        # int → str conversion
        bind(self._count).to(self._count_label)
        # float → str conversion
        bind(self._price).to(self._price_label)

# count_label.text() == "42"
# price_label.text() == "19.99"
```

Custom classes use their `__str__` method:

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
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._person).to(self._label)

# label.text() == "Alice (30)"
```

## Dirty Tracking

Every Variable tracks whether its value has changed from the initial value:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    def check_dirty(self) -> None:
        if self._name.is_dirty.get():
            print("Name has been modified")
```

For lists and dicts, any modification marks the Variable as dirty:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new()

    def test(self) -> None:
        print(self._items.is_dirty.get())  # False

        self._items.observable.append("Buy milk")
        print(self._items.is_dirty.get())  # True
```

For custom classes (proxies), field changes mark the Variable as dirty:

```python
@widget
class PersonEditor(Widget):
    _person: Variable[Person] = new(default=Person("Alice", 30))

    def test(self) -> None:
        print(self._person.is_dirty.get())  # False

        self._person.observable.name.set("Bob")
        print(self._person.is_dirty.get())  # True
```

## Summary

| Form | Purpose | Example |
|------|---------|---------|
| `Variable[T]` | Reactive state only | `_count: Variable[int] = new(0)` |
| `Variable[list[T]]` | Observable list | `_items: Variable[list[str]] = new()` |
| `Variable[dict[K,V]]` | Observable dict | `_data: Variable[dict[str,int]] = new()` |
| `Variable[MyClass]` | Observable proxy | `_person: Variable[Person] = new(...)` |
| `Variable[T, W]` | State + widget | `_name: Variable[str, QLineEdit] = new("")` |
| `Variable[T, Widget[T]]` | State + custom widget | `dog: Variable[Dog, DogEditor] = new(...)` |
| `Variable[list[T], Widget[T]]` | List + repeating widgets | `dogs: Variable[list[Dog], DogEditor] = new([...])` |

Key operations:
- Read: `var.value` or direct field access (`var.name` for proxies)
- Write: `var.value = x` or `var = x` or `var.name = x`
- Augmented: `var += 1`, `var *= 2`, etc.
- Observe: `var.observable.on_change(callback)`
- Widget access: `var.widget` (for `Variable[T, W]`)
- Dirty check: `var.is_dirty.get()`
