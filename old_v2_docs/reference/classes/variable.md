# Variable

`Variable[T]` provides reactive state management for QtPie widgets. Variables wrap underlying observables from the `observant` library and automatically select the appropriate observable type based on your type annotation.

## Basic Usage

### Single Type Generic: Variable[T]

```python
from qtpie import Widget, Variable, new, widget

@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _name: Variable[str] = new("User")

    def increment(self):
        self._count += 1  # Reactive update
```

### Type + Widget Generic: Variable[T, W]

Creates both reactive state and an auto-bound widget:

```python
from PySide6.QtWidgets import QLineEdit, QLabel
from qtpie import Widget, Variable, new, widget

@widget
class Form(Widget):
    # Creates Variable[str] + QLineEdit, automatically bound
    _username: Variable[str, QLineEdit] = new("")

    # Can chain widget configuration
    _password: Variable[str, QLineEdit] = new("")(
        echoMode=QLineEdit.EchoMode.Password
    )

    # Display-only binding
    _status: Variable[str, QLabel] = new("Ready")
```

## Type Selection

Variable automatically chooses the right observable wrapper based on your type annotation:

| Type Annotation | Observable Type | Usage |
|----------------|----------------|-------|
| `Variable[str]`, `Variable[int]`, etc. | `Observable[T]` | Primitives |
| `Variable[list[T]]` | `ObservableList[T]` | Lists with granular callbacks |
| `Variable[dict[K, V]]` | `ObservableDict[K, V]` | Dicts with granular callbacks |
| `Variable[MyClass]` | `ObservableProxy[MyClass]` | Complex objects with reactive fields |

### Primitives

```python
@widget
class Primitives(Widget):
    _name: Variable[str] = new("Alice")
    _age: Variable[int] = new(30)
    _score: Variable[float] = new(98.5)
    _active: Variable[bool] = new(True)
```

### Lists

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])

    def add_item(self, text: str):
        self._items.append(text)  # Direct list method
        # OR: self._items.observable.append(text)
```

### Dicts

```python
@widget
class Scoreboard(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})

    def update_score(self, name: str, score: int):
        self._scores[name] = score  # Direct dict access
        # OR: self._scores.observable[name] = score
```

### Complex Objects

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

@widget
class PersonEditor(Widget):
    _person: Variable[Person] = new(Person("Alice", 30))

    def update_name(self, name: str):
        # Direct field access (reactive)
        self._person.name = name
        # OR: self._person.observable.name.set(name)
```

## Properties

### .value

Get or set the current value:

```python
# Get value
current = self._count.value  # int

# Set value (triggers change notifications)
self._count.value = 42

# For lists/dicts, replaces entire collection
self._items.value = ["new", "list"]
```

For complex objects (`ObservableProxy`), `.value` returns the unwrapped object:

```python
person_obj = self._person.value  # Person instance
print(person_obj.name)
```

### .widget

Access the bound widget (only for `Variable[T, W]`):

```python
@widget
class Form(Widget):
    _name: Variable[str, QLineEdit] = new("")

    def focus_name(self):
        self._name.widget.setFocus()  # QLineEdit methods
        self._name.widget.setPlaceholderText("Enter name")
```

Returns `None` for `Variable[T]` without a widget type.

### .observable

Access the underlying observable wrapper for advanced operations:

```python
from observant import Observable, ObservableList

# Primitives → Observable[T]
name_obs: Observable[str] = self._name.observable
name_obs.on_change(lambda v: print(f"Changed to: {v}"))

# Lists → ObservableList[T]
items_obs: ObservableList[str] = self._items.observable
items_obs.on_insert(lambda idx, item: print(f"Inserted {item} at {idx}"))
items_obs.on_remove(lambda idx, item: print(f"Removed {item} from {idx}"))

# Dicts → ObservableDict[K, V]
scores_obs: ObservableDict[str, int] = self._scores.observable
scores_obs.on_set(lambda key, val: print(f"{key} = {val}"))

# Complex objects → ObservableProxy[T]
person_obs: ObservableProxy[Person] = self._person.observable
person_obs.name.on_change(lambda v: print(f"Name changed to {v}"))
```

### .is_dirty

Check if the value has changed from its initial value:

```python
@widget
class Editor(Widget):
    _content: Variable[str] = new("")

    def check_unsaved_changes(self):
        # .is_dirty is an Observable[bool] - use .get() to read
        if self._content.is_dirty.get():
            print("You have unsaved changes!")

        # Can bind to widgets
        self._save_button.setEnabled(self._content.is_dirty.get())

    def save(self):
        # Save logic here...
        self._content.reset_dirty()  # Mark as clean
```

Works with all variable types:

```python
# List changes
self._items.append("new")
assert self._items.is_dirty.get() == True

# Dict changes
self._scores["Alice"] = 200
assert self._scores.is_dirty.get() == True

# Object field changes
self._person.age = 31
assert self._person.is_dirty.get() == True
```

## Methods

### .on_change()

Register a callback for value changes:

```python
@widget
class Example(Widget):
    _name: Variable[str] = new("")

    def __setup__(self):
        # Primitives: callback receives new value
        self._name.on_change(lambda v: print(f"Name is now: {v}"))

        # Lists: callback receives no args (use .value to inspect)
        self._items.on_change(lambda: print(f"Items: {self._items.value}"))

        # Can also register on .observable for granular callbacks
        self._items.observable.on_insert(lambda idx, item: ...)
```

### .reset_dirty()

Mark the current value as clean (resets dirty tracking):

```python
def save(self):
    save_to_database(self._content.value)
    self._content.reset_dirty()  # Now is_dirty will be False
```

### .add_validator()

Add validation rules (see [Validation](../../features/validation.md)):

```python
def __setup__(self):
    self._email.add_validator(
        "format",
        lambda v: None if "@" in v else "Invalid email"
    )
```

## Operators

### Augmented Assignment

All standard augmented assignment operators work:

```python
@widget
class Calculator(Widget):
    _total: Variable[int] = new(0)
    _multiplier: Variable[float] = new(1.0)

    def add(self, n: int):
        self._total += n  # Reactive update

    def subtract(self, n: int):
        self._total -= n

    def multiply(self, n: int):
        self._total *= n

    def divide(self, n: float):
        self._multiplier /= n

    def floor_divide(self, n: int):
        self._total //= n

    def modulo(self, n: int):
        self._total %= n
```

All operators trigger change notifications and dirty tracking.

### Type Coercion

Variables can be coerced to Python primitives:

```python
@widget
class Coercion(Widget):
    _count: Variable[int] = new(42)
    _ratio: Variable[float] = new(3.14)
    _enabled: Variable[bool] = new(True)

    def demo(self):
        # int()
        x = int(self._count)  # 42

        # float()
        y = float(self._ratio)  # 3.14

        # str()
        s = str(self._count)  # "42"

        # bool()
        if self._enabled:  # Coerces to bool
            print("Enabled!")
```

Note: These return the current value - they don't maintain reactivity.

## List/Dict Methods

When `Variable[list[T]]` or `Variable[dict[K, V]]` is used, standard collection methods are available:

### List Methods

```python
@widget
class ListOps(Widget):
    _items: Variable[list[str]] = new(["a", "b", "c"])

    def demo(self):
        # Append
        self._items.append("d")

        # Extend
        self._items.extend(["e", "f"])

        # Insert
        self._items.insert(0, "first")

        # Remove
        self._items.remove("b")

        # Pop
        last = self._items.pop()  # Remove and return last item
        item = self._items.pop(0)  # Remove and return at index

        # Clear
        self._items.clear()

        # Length
        count = len(self._items)

        # Iteration
        for item in self._items:
            print(item)

        # Membership
        if "a" in self._items:
            print("Found!")

        # Indexing
        first = self._items[0]
        self._items[0] = "new value"
        del self._items[0]
```

### Dict Methods

```python
@widget
class DictOps(Widget):
    _data: Variable[dict[str, int]] = new({"x": 1, "y": 2})

    def demo(self):
        # Indexing
        value = self._data["x"]
        self._data["z"] = 3
        del self._data["y"]

        # Get with default
        value = self._data.get("missing", 0)

        # Update
        self._data.update({"a": 10, "b": 20})

        # Keys/values/items
        keys = self._data.keys()  # list[str]
        values = self._data.values()  # list[int]
        items = self._data.items()  # list[tuple[str, int]]

        # Clear
        self._data.clear()

        # Length
        count = len(self._data)

        # Iteration (over keys)
        for key in self._data:
            print(key, self._data[key])

        # Membership
        if "x" in self._data:
            print("Found!")
```

All mutations trigger change notifications.

## Direct Field Access (ObservableProxy)

For `Variable[T]` where `T` is a complex object, you can access fields directly:

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str
    age: int

@widget
class DogEditor(Widget):
    _dog: Variable[Dog] = new(Dog("Max", 3))

    def demo(self):
        # Direct field access (reactive!)
        print(self._dog.name)  # "Max"
        self._dog.name = "Buddy"  # Triggers change

        # This is equivalent to:
        print(self._dog.observable.name.get())
        self._dog.observable.name.set("Buddy")

        # But direct access is cleaner
```

Field access returns the unwrapped value. Use `.observable.field` if you need the `Observable` instance.

## Validation

Variables support validation with reactive error tracking:

```python
@widget
class ValidatedForm(Widget):
    _email: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self):
        # Add validators
        self._email.add_validator(
            "required",
            lambda v: None if v else "Email required"
        )
        self._email.add_validator(
            "format",
            lambda v: None if "@" in v else "Invalid email"
        )
        self._age.add_validator(
            "range",
            lambda v: None if 0 < v < 120 else "Age must be 1-119"
        )

    def check_validity(self):
        # Check if valid
        if self._email.is_valid.get():
            print("Email is valid")

        # Get errors by validator name
        errors = self._email.validation_errors.get()
        # {"required": ["Email required"], "format": ["Invalid email"]}

        # Get flat list of error messages
        messages = self._email.validation_error_messages.get()
        # ["Email required", "Invalid email"]
```

Validation properties return `Observable` instances that can be bound to widgets:

```python
# Disable submit button when form is invalid
self._submit.setEnabled(self._email.is_valid.get())

# Display errors
self._error_label.setText(", ".join(self._email.validation_error_messages.get()))
```

## Type Safety

Variable provides full type safety with pyright:

```python
# Type inference works correctly
_count: Variable[int] = new(42)
reveal_type(self._count.value)  # int

# Widget type is inferred
_name: Variable[str, QLineEdit] = new("")
reveal_type(self._name.widget)  # QLineEdit | None

# List/dict item types are preserved
_items: Variable[list[str]] = new([])
item: str = self._items[0]  # Typed correctly

# ObservableProxy field access is typed
_person: Variable[Person] = new(Person("Alice", 30))
reveal_type(self._person.name)  # str
```

## Advanced Examples

### Multiple Variables with Change Tracking

```python
@widget
class Form(Widget):
    _first_name: Variable[str] = new("")
    _last_name: Variable[str] = new("")
    _full_name: Variable[str] = new("")

    def __setup__(self):
        # Update full name when parts change
        def update_full_name(_):
            first = self._first_name.value
            last = self._last_name.value
            self._full_name.value = f"{first} {last}".strip()

        self._first_name.on_change(update_full_name)
        self._last_name.on_change(update_full_name)
```

### Variable with Complex Validation

```python
@widget
class PasswordForm(Widget):
    _password: Variable[str, QLineEdit] = new("")
    _confirm: Variable[str, QLineEdit] = new("")

    def __setup__(self):
        # Password validators
        self._password.add_validator(
            "length",
            lambda v: None if len(v) >= 8 else "Min 8 characters"
        )
        self._password.add_validator(
            "uppercase",
            lambda v: None if any(c.isupper() for c in v) else "Need uppercase"
        )

        # Confirmation validator (cross-field)
        self._confirm.add_validator(
            "match",
            lambda v: None if v == self._password.value else "Passwords don't match"
        )

        # Re-validate confirm when password changes
        self._password.on_change(lambda _: self._confirm.observable.validate())
```

### Working with Nested Observables

```python
from dataclasses import dataclass

@dataclass
class Address:
    street: str
    city: str

@dataclass
class Person:
    name: str
    address: Address

@widget
class NestedEditor(Widget):
    _person: Variable[Person] = new(
        Person("Alice", Address("123 Main St", "Springfield"))
    )

    def update_city(self, city: str):
        # Access nested fields reactively
        self._person.address.city = city

        # Or use observable directly
        self._person.observable.address.city.set(city)
```

## See Also

- [Observable](./observable.md) - Underlying primitive from observant library
- [ObservableList](./observable-list.md) - List wrapper with granular callbacks
- [ObservableDict](./observable-dict.md) - Dict wrapper with granular callbacks
- [ObservableProxy](./observable-proxy.md) - Object wrapper with reactive fields
- [Validation](../../features/validation.md) - Validation system details
- [Dirty Tracking](../../features/dirty-tracking.md) - Change tracking details
