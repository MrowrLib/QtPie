# Lists and Dictionaries

QtPie provides reactive list and dictionary bindings that automatically sync collections with UI widgets. Changes to the data automatically create, update, or remove widgets.

## Variable[list[T], W] - List with Widget Type

Declare a list Variable with a widget type to create a repeater:

```python
from PySide6.QtWidgets import QLabel, QLineEdit, QSpinBox
from qtpie import Widget, Variable, new, widget

@widget
class TodoList(Widget):
    # Creates a WidgetRepeater with one QLineEdit per item
    _items: Variable[list[str], QLineEdit] = new(["Buy milk", "Walk dog"])

    def __setup__(self) -> None:
        # Access the repeater
        print(self._items.widget.widget_count())  # 2
```

The `Variable[list[T], W]` syntax automatically creates a `WidgetRepeater[T]` that manages a collection of `W` widgets.

## WidgetRepeater Basics

A `WidgetRepeater` creates one widget per list item and keeps them synchronized:

```python
@widget
class NumberList(Widget):
    _numbers: Variable[list[int], QLabel] = new([1, 2, 3])

w = NumberList()

# Access the repeater
repeater = w._numbers.widget

# Check widget count
print(repeater.widget_count())  # 3

# Access specific widgets
print(repeater.widget_at(0).text())  # "1"
print(repeater.widget_at(1).text())  # "2"
```

### List-Like Interface

`WidgetRepeater` provides a list-like interface for accessing widgets:

```python
@widget
class Items(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b", "c"])

w = Items()

# Access by index (positive or negative)
print(w._items.widget[0].text())   # "a"
print(w._items.widget[-1].text())  # "c"

# Length
print(len(w._items.widget))  # 3

# Iteration
for label in w._items.widget:
    print(label.text())  # "a", "b", "c"
```

## Reactive Synchronization

Changes to the list automatically update the widgets:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str], QLineEdit] = new(["Task 1"])

w = TodoList()
print(w._items.widget.widget_count())  # 1

# Append - creates new widget
w._items.observable.append("Task 2")
print(w._items.widget.widget_count())  # 2

# Insert at position
w._items.observable.insert(1, "Task 1.5")
print(w._items.widget.widget_count())  # 3
print(w._items.widget[1].text())  # "Task 1.5"

# Remove - removes widget
w._items.observable.remove("Task 1.5")
print(w._items.widget.widget_count())  # 2

# Replace - updates widget
w._items.observable[0] = "Updated Task"
print(w._items.widget[0].text())  # "Updated Task"

# Clear - removes all widgets
w._items.observable.clear()
print(w._items.widget.widget_count())  # 0
```

## Two-Way Binding

For editable widgets, changes sync back to the list:

```python
@widget
class NameList(Widget):
    _names: Variable[list[str], QLineEdit] = new(["Alice", "Bob"])

w = NameList()

# Edit widget - updates list
edit = w._names.widget[0]
edit.setText("Charlie")
print(w._names.observable[0])  # "Charlie"

# Change list - updates widget
w._names.observable[1] = "Diana"
print(w._names.widget[1].text())  # "Diana"
```

Works with various widget types:

```python
@widget
class Settings(Widget):
    # Numbers with spinboxes
    _numbers: Variable[list[int], QSpinBox] = new([10, 20, 30])

w = Settings()
spin = w._numbers.widget[0]
spin.setValue(99)
print(w._numbers.observable[0])  # 99
```

## Binding Complex Objects

Bind lists of dataclass instances using format strings:

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str
    age: int

@widget
class DogList(Widget):
    _dogs: Variable[list[Dog], QLabel] = new([
        Dog("Rover", 3),
        Dog("Snoopy", 5)
    ])(bind="{name}")

w = DogList()
print(w._dogs.widget[0].text())  # "Rover"
print(w._dogs.widget[1].text())  # "Snoopy"
```

### Format Strings for Objects

Combine multiple properties in format strings:

```python
@widget
class DogList(Widget):
    _dogs: Variable[list[Dog], QLabel] = new([
        Dog("Rover", 3),
        Dog("Snoopy", 5)
    ])(bind="{name} is {age} years old")

w = DogList()
print(w._dogs.widget[0].text())  # "Rover is 3 years old"
print(w._dogs.widget[1].text())  # "Snoopy is 5 years old"
```

### Editable Object Properties

Use format strings with editable widgets for two-way binding to specific properties:

```python
@widget
class DogEditor(Widget):
    _dogs: Variable[list[Dog], QLineEdit] = new([
        Dog("Rover", 3)
    ])(bind="{name}")

w = DogEditor()

# Initial value
print(w._dogs.widget[0].text())  # "Rover"

# Edit widget - updates object's name property
w._dogs.widget[0].setText("Max")
print(w._dogs.observable[0].name)  # "Max"
```

## Special Placeholders

Format strings support special placeholders for list bindings:

| Placeholder | Description |
|-------------|-------------|
| `{#self}` | The item value itself (default for primitives) |
| `{#index}` | The item's index in the list |

### Using #self

Explicitly reference the item value:

```python
@widget
class Numbers(Widget):
    _nums: Variable[list[int], QLabel] = new([10, 20, 30])(bind="{#self}")

w = Numbers()
print(w._nums.widget[0].text())  # "10"
```

### Using #index

Display item indices:

```python
@widget
class IndexedList(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b", "c"])(
        bind="{#index}"
    )

w = IndexedList()
print(w._items.widget[0].text())  # "0"
print(w._items.widget[1].text())  # "1"
print(w._items.widget[2].text())  # "2"
```

### Combining Placeholders

Combine multiple placeholders:

```python
@widget
class IndexedList(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b", "c"])(
        bind="Index {#index}: {#self}"
    )

w = IndexedList()
print(w._items.widget[0].text())  # "Index 0: a"
print(w._items.widget[1].text())  # "Index 1: b"
```

For objects:

```python
@widget
class DogList(Widget):
    _dogs: Variable[list[Dog], QLabel] = new([
        Dog("Rover", 3),
        Dog("Snoopy", 5)
    ])(bind="[{#index}] {name} ({age})")

w = DogList()
print(w._dogs.widget[0].text())  # "[0] Rover (3)"
print(w._dogs.widget[1].text())  # "[1] Snoopy (5)"
```

## list[QWidget] with bind=

Alternative syntax using `list[QWidget]` type hint with explicit `bind=`:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])

    # Create repeater by binding list[QLabel] to the Variable
    labels: list[QLabel] = new(bind="_items")

w = TodoList()

# labels is a WidgetRepeater
print(len(w.labels))  # 2
print(w.labels[0].text())  # "Buy milk"

# Changes to _items update labels
w._items.append("Read book")
print(len(w.labels))  # 3
```

This syntax is useful when you want to separate data storage from display.

### Format with list[QWidget]

Use the `format=` parameter with `list[QWidget]` bindings:

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class DogList(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])

    # Format how each dog displays
    labels: list[QLabel] = new(
        bind="_dogs",
        format="{name} is {age} years old"
    )

w = DogList()
print(w.labels[0].text())  # "Fido is 3 years old"
print(w.labels[1].text())  # "Rex is 5 years old"
```

### Callable Format

Pass a function for complex formatting:

```python
@widget
class DogList(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])

    labels: list[QLabel] = new(
        bind="_dogs",
        format=lambda d: f"{d.name.upper()} - {d.age}"
    )

w = DogList()
print(w.labels[0].text())  # "FIDO - 3"
```

## Widget Constructor Arguments

Apply constructor arguments to all widgets in the repeater:

```python
@widget
class StyledList(Widget):
    _items: Variable[list[str], QLineEdit] = new(["a", "b"])(
        maxLength=5,
        styleSheet="color: blue;"
    )

w = StyledList()

# All widgets get the kwargs
print(w._items.widget[0].maxLength())  # 5
print(w._items.widget[1].maxLength())  # 5

# Even newly added widgets
w._items.observable.append("c")
print(w._items.widget[2].maxLength())  # 5
```

With `list[QWidget]` syntax:

```python
@widget
class StyledList(Widget):
    _items: Variable[list[str]] = new(["a", "b"])

    labels: list[QLabel] = new(
        bind="_items",
        styleSheet="color: red;"  # or stylesheet=
    )

w = StyledList()
print(w.labels[0].styleSheet())  # "color: red;"
```

## Dictionary Bindings

Bind dictionaries using `Variable[dict[K, V]]` with `list[QWidget]`:

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({
        "Alice": 100,
        "Bob": 85
    })

    labels: list[QLabel] = new(
        bind="_scores",
        format="{#key}: {#value} points"
    )

w = ScoreBoard()

# Access via DictWidgetRepeater
print(len(w.labels))  # 2
print(w.labels.widget_for_key("Alice").text())  # "Alice: 100 points"
```

The result is a `DictWidgetRepeater` that manages widgets keyed by dictionary keys.

### Dict Special Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{#key}` | The dictionary key |
| `{#value}` | The dictionary value (alias: `{#self}`) |

```python
@widget
class Stats(Widget):
    _data: Variable[dict[str, int]] = new({"wins": 10, "losses": 5})

    labels: list[QLabel] = new(
        bind="_data",
        format="{#key}={#value}"
    )

w = Stats()
print(w.labels.widget_for_key("wins").text())  # "wins=10"
```

### Dict with Complex Values

Bind dictionaries with complex value types:

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class DogRegistry(Widget):
    _dogs: Variable[dict[str, Dog]] = new({
        "Fido": Dog("Fido", 3),
        "Rex": Dog("Rex", 5)
    })

    labels: list[QLabel] = new(
        bind="_dogs",
        format="{#key}: {name} is {age} years old"
    )

w = DogRegistry()
fido_label = w.labels.widget_for_key("Fido")
print(fido_label.text())  # "Fido: Fido is 3 years old"
```

Note: `{name}` and `{age}` reference properties of the dictionary values (Dog instances).

### Dict Reactive Updates

Dictionary changes automatically update widgets:

```python
@widget
class Items(Widget):
    _items: Variable[dict[str, int]] = new({"a": 1})

    labels: list[QLabel] = new(bind="_items", format="{#key}={#value}")

w = Items()
print(w.labels.widget_count())  # 1

# Add entry - creates widget
w._items["b"] = 2
print(w.labels.widget_count())  # 2
print(w.labels.widget_for_key("b").text())  # "b=2"

# Remove entry - removes widget
del w._items["a"]
print(w.labels.widget_count())  # 1
```

## Layout Integration

Repeaters integrate into parent layouts automatically:

```python
@widget
class MyWidget(Widget):
    header: QLabel = new("Header")
    _items: Variable[list[str], QLabel] = new(["a", "b"])
    footer: QLabel = new("Footer")

w = MyWidget()
layout = w.layout()

# Layout contains: header, repeater, footer
print(layout.count())  # 3
print(layout.itemAt(0).widget())  # header
print(layout.itemAt(1).widget())  # repeater (WidgetRepeater)
print(layout.itemAt(2).widget())  # footer
```

### Exclude from Layout

Exclude a repeater from the parent layout with `layout=False`:

```python
@widget
class MyWidget(Widget):
    header: QLabel = new("Header")

    _items: Variable[list[str], QLabel] = new(["a", "b"])
    labels: list[QLabel] = new(bind="_items", layout=False)

    footer: QLabel = new("Footer")

w = MyWidget()

# Layout only has header and footer
print(w.layout().count())  # 2

# But repeater still exists
print(len(w.labels))  # 2
```

## Validation Error Lists

Bind to validation error messages to display validation feedback:

```python
@widget
class LoginForm(Widget):
    username: Variable[str] = new("")
    password: Variable[str] = new("")

    username_input: QLineEdit = new(bind="username")
    password_input: QLineEdit = new(bind="password")

    # Show errors for username field
    username_errors: list[QLabel] = new(bind="username.validation_error_messages")

    def __setup__(self) -> None:
        self.username.add_validator("required",
            lambda v: "Username required" if not v else None)
        self.username.add_validator("length",
            lambda v: "Min 3 chars" if len(v) < 3 else None)

form = LoginForm()

# Initially invalid (empty)
print(len(form.username_errors))  # 2 (both validators fail)

# Enter text
form.username.value = "ab"
print(len(form.username_errors))  # 1 (only length validator fails)

# Valid
form.username.value = "alice"
print(len(form.username_errors))  # 0
```

### Widget-Level Validation Errors

Bind to all validation errors across the entire widget:

```python
@widget
class RegistrationForm(Widget):
    username: Variable[str] = new("")
    email: Variable[str] = new("")

    # Aggregated errors from all fields
    errors: list[QLabel] = new(bind="validation_error_messages")

    # Or via view_model
    errors2: list[QLabel] = new(bind="view_model.validation_error_messages")

    def __setup__(self) -> None:
        self.username.add_validator("req1",
            lambda v: "Username required" if not v else None)
        self.email.add_validator("req2",
            lambda v: "Email required" if not v else None)

form = RegistrationForm()
print(len(form.errors))  # 2 (both fields invalid)

form.username.value = "alice"
print(len(form.errors))  # 1 (only email invalid)
```

## Modifying Widgets in __setup__

Access and configure repeater widgets in `__setup__`:

```python
@widget
class CustomList(Widget):
    _items: Variable[list[str], QLabel] = new(["first", "second"])
    labels: list[QLabel] = new(bind="_items")

    def __setup__(self) -> None:
        # Customize individual widgets
        self.labels[0].setStyleSheet("color: red;")
        self.labels[1].setStyleSheet("color: blue;")

        # Or iterate
        for i, label in enumerate(self.labels):
            label.setToolTip(f"Item {i}")
```

## Common Patterns

### Todo List with Delete Buttons

```python
@dataclass
class TodoItem:
    text: str
    done: bool = False

@widget
class TodoList(Widget):
    _todos: Variable[list[TodoItem]] = new([
        TodoItem("Buy milk"),
        TodoItem("Walk dog")
    ])

    items: list[QLabel] = new(
        bind="_todos",
        format="{'✓' if done else '○'} {text}"
    )

    def add_todo(self, text: str) -> None:
        self._todos.append(TodoItem(text))

    def remove_todo(self, index: int) -> None:
        del self._todos[index]
```

### Dynamic Form Fields

```python
@widget
class DynamicForm(Widget):
    _fields: Variable[list[str]] = new(["Name", "Email"])

    inputs: list[QLineEdit] = new(
        bind="_fields",
        placeholderText="Enter value..."
    )

    def add_field(self, name: str) -> None:
        self._fields.append(name)

    def get_values(self) -> dict[str, str]:
        return {
            self._fields[i]: self.inputs[i].text()
            for i in range(len(self._fields))
        }
```

### Leaderboard

```python
@dataclass
class Player:
    name: str
    score: int

@widget
class Leaderboard(Widget):
    _players: Variable[list[Player]] = new([])

    rows: list[QLabel] = new(
        bind="_players",
        format="[{#index + 1}] {name}: {score} points"
    )

    def update_scores(self, scores: dict[str, int]) -> None:
        players = [Player(name, score) for name, score in scores.items()]
        players.sort(key=lambda p: p.score, reverse=True)
        self._players.observable.clear()
        for player in players:
            self._players.observable.append(player)
```

## Error Handling

### Missing bind= Parameter

`list[QWidget]` fields require `bind=`:

```python
@widget
class BadWidget(Widget):
    labels: list[QLabel] = new()  # Error: requires bind=

# Raises: ValueError: list[QWidget] field 'labels' requires bind=
```

### Invalid Bind Path

The bind path must resolve to a valid attribute:

```python
@widget
class BadWidget(Widget):
    labels: list[QLabel] = new(bind="nonexistent")

# Raises: ValueError: Could not resolve bind path 'nonexistent'
```

### Non-List Binding

Can't bind `list[QWidget]` to non-list values:

```python
@widget
class BadWidget(Widget):
    name: Variable[str] = new("hello")
    labels: list[QLabel] = new(bind="name")

# Raises: TypeError: list[QWidget] bind expected list or dict, got str
```

## Performance Notes

- Widget creation is lazy - widgets are created only when items are added
- Granular operations (insert, remove, replace) only affect specific widgets, not the entire list
- Index updates after insert/remove are efficient - existing widgets remain bound correctly
- For large lists (100+ items), consider virtualizing with custom solutions or limiting visible items
