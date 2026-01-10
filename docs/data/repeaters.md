# Widget Repeaters

A `WidgetRepeater` automatically creates one widget per item in a list or dict. When items are added or removed, widgets are created or destroyed automatically.

## How It Works

When you bind a list type to a Variable, QtPie creates a WidgetRepeater that:

1. Creates one widget per item
2. Syncs widgets when the list changes (add, remove, update)
3. Integrates into the parent layout
4. Supports two-way binding for primitives

## Two Syntaxes

### Inline Widget Type

```python
@widget
class App(Widget):
    _names: Variable[list[str], QLineEdit] = new(["Alice", "Bob"])
```

The widget type (`QLineEdit`) is part of the Variable declaration.

### Standalone Binding

```python
@widget
class App(Widget):
    _names: Variable[list[str]] = new(["Alice", "Bob"])
    _inputs: list[QLineEdit] = new(bind="_names")
```

The data and widget are separate fields.

### When to Use Each

| Use Case | Recommended |
|----------|-------------|
| Simple, self-contained lists | Inline: `Variable[list[T], W]` |
| Shared data across widgets | Standalone: `list[W]` with `bind=` |
| Custom widget configuration | Either works |
| Complex format expressions | Standalone with `format=` |

## Synchronization

### All List Operations Work

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str], QLabel] = new([])

    def add(self, text: str) -> None:
        self._items.append(text)  # Widget appears

    def remove(self, text: str) -> None:
        self._items.remove(text)  # Widget disappears

    def insert(self, pos: int, text: str) -> None:
        self._items.insert(pos, text)  # Widget inserted at position

    def update(self, index: int, text: str) -> None:
        self._items[index] = text  # Widget updates

    def clear(self) -> None:
        self._items.clear()  # All widgets removed
```

### Layout Integration

Repeaters integrate into the parent layout:

```python
@widget
class App(Widget):
    _header: QLabel = new("Items:")
    _items: Variable[list[str], QLabel] = new(["A", "B"])
    _footer: QLabel = new("End")
```

Layout order: header, item A, item B, footer.

## Two-Way Binding

### Primitives

For primitive types (str, int, bool), binding is two-way:

```python
@widget
class Editor(Widget):
    _names: Variable[list[str], QLineEdit] = new(["Alice", "Bob"])

editor = Editor()

# List → Widget
assert editor._names.widget.widget_at(0).text() == "Alice"

# Widget → List
editor._names.widget.widget_at(0).setText("Charlie")
assert editor._names[0] == "Charlie"
```

### Complex Objects

For objects, use format expressions to bind properties:

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str
    age: int

@widget
class DogList(Widget):
    # Single property - two-way binding
    _dogs: Variable[list[Dog], QLineEdit] = new(
        [Dog("Rover", 3)]
    )(bind="{name}")

dog_list = DogList()

# Editing widget updates the object
dog_list._dogs.widget.widget_at(0).setText("Max")
assert dog_list._dogs[0].name == "Max"
```

Multiple properties are display-only:

```python
@widget
class DogDisplay(Widget):
    _dogs: Variable[list[Dog], QLabel] = new(
        [Dog("Rover", 3)]
    )(bind="{name} is {age} years old")
    # Shows: "Rover is 3 years old" (read-only)
```

## Accessing Widgets

### By Index

```python
@widget
class App(Widget):
    _items: Variable[list[str], QLabel] = new(["A", "B", "C"])

app = App()
repeater = app._items.widget

# Access by index
first = repeater.widget_at(0)
last = repeater.widget_at(-1)

# Widget count
count = repeater.widget_count()
```

### For Dict Binding

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
    _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}")

board = ScoreBoard()

# Access by key
alice_label = board._labels.widget_for_key("Alice")
```

## Widget Configuration

Kwargs are applied to all widgets, including newly created ones:

```python
@widget
class App(Widget):
    _items: Variable[list[str], QLineEdit] = new(
        ["A", "B"]
    )(maxLength=10, placeholderText="Enter item")

app = App()

# All widgets have maxLength=10
app._items.append("C")  # New widget also has maxLength=10
```

## Index Management

After insert/remove, widgets stay bound to the correct items:

```python
@widget
class App(Widget):
    _items: Variable[list[str], QLabel] = new(["A", "C"])

app = App()
app._items.insert(1, "B")  # Now ["A", "B", "C"]

# Widget at index 2 shows "C"
assert app._items.widget.widget_at(2).text() == "C"
```

## Dict Binding

Use `{#key}` and `{#value}` placeholders:

```python
@dataclass
class Player:
    name: str
    score: int

@widget
class Leaderboard(Widget):
    _players: Variable[dict[str, Player]] = new({
        "p1": Player("Alice", 100),
        "p2": Player("Bob", 85)
    })

    _labels: list[QLabel] = new(
        bind="_players",
        format="{#key}: {name} - {score} points"
    )
```

## Sorting

Control the order of repeated widgets with the `sort=` parameter.

### Sort Modes

| Mode | Description |
|------|-------------|
| `sort=False` | Preserve source order (default) |
| `sort=True` | Use Python's default `sorted()` |
| `sort=callable` | Custom sort key function |
| `sort="method_name"` | Method on parent widget as sort key |

### Using a Method Name

The method name resolves to a method on the parent widget:

```python
from dataclasses import dataclass

@dataclass
class Dog:
    name: str
    age: int

@widget
class DogList(Widget):
    _dogs: Variable[list[Dog]] = new([
        Dog("Zara", 3),
        Dog("Buddy", 5),
        Dog("Ace", 1)
    ])

    # Sort alphabetically by name
    _labels: list[QLabel] = new(
        bind="_dogs",
        format="{name} ({age})",
        sort="sort_by_name"
    )
    # Renders: "Ace (1)", "Buddy (5)", "Zara (3)"

    def sort_by_name(self, dog: Dog) -> str:
        return dog.name
```

### Numeric Sorting

```python
@widget
class DogList(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Zara", 3), Dog("Ace", 1)])
    _labels: list[QLabel] = new(
        bind="_dogs",
        format="{name}",
        sort="sort_by_age"
    )
    # Renders: "Ace", "Zara" (sorted by age: 1, 3)

    def sort_by_age(self, dog: Dog) -> int:
        return dog.age
```

### Reverse Sorting

```python
def sort_by_age_desc(self, dog: Dog) -> int:
    return -dog.age  # Negate for reverse numeric sort
```

### Dict Sorting

For dicts, the sort key receives the dict key:

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({
        "Zara": 100, "Ace": 90, "Buddy": 85
    })

    _labels: list[QLabel] = new(
        bind="_scores",
        format="{#key}: {#value}",
        sort="sort_by_key"
    )
    # Renders: "Ace: 90", "Buddy: 85", "Zara: 100"

    def sort_by_key(self, key: str) -> str:
        return key
```

### Lambda Sorting

For inline sort expressions:

```python
_labels: list[QLabel] = new(
    bind="_dogs",
    format="{name}",
    sort=lambda dog: dog.name.lower()
)
```

### Default Sorting

With `sort=True`, uses Python's default comparison:

```python
@widget
class NumberList(Widget):
    _nums: Variable[list[int]] = new([3, 1, 4, 1, 5])
    _labels: list[QLabel] = new(bind="_nums", sort=True)
    # Renders: "1", "1", "3", "4", "5"
```

## Signal Connections

Connect child widget signals to parent handlers using special placeholders. This enables interactive lists like todo apps.

### Signal Placeholders

| Placeholder | Type | Description |
|-------------|------|-------------|
| `#index` | `int` | Current index of the item in the list |
| `#value` | `T` | The actual item from the list/dict |
| `#widget` | `QWidget` | The child widget instance |
| `#args` | spread | The signal's own arguments |

### Basic Example: Delete by Index

```python
@widget
class TodoRow(Widget):
    item: Variable[str]
    _label: QLabel = new(bind="{item}")
    _delete: QPushButton = new("×", clicked="on_delete")

    on_delete: signal = new()  # Signal to parent

@widget
class TodoApp(Widget):
    _items: Variable[list[str]] = new(["Task 1", "Task 2"])
    _rows: list[TodoRow] = new(
        bind="_items",
        on_delete="handle_delete(#index)"  # #index passes item position
    )

    def handle_delete(self, index: int) -> None:
        del self._items[index]  # Widget at that position is removed
```

### Using #value for the Item

```python
@widget
class ProductPicker(Widget):
    _products: Variable[list[Product]] = new([...])
    _cards: list[ProductCard] = new(
        bind="_products",
        clicked="on_select(#value)"  # Pass the actual Product
    )

    def on_select(self, product: Product) -> None:
        self.selected = product
```

### Using #widget for the Child Widget

```python
@widget
class App(Widget):
    _items: Variable[list[str]] = new(["A", "B", "C"])
    _rows: list[RowWidget] = new(
        bind="_items",
        on_click="handle_click(#widget)"
    )

    def handle_click(self, widget: RowWidget) -> None:
        widget.setStyleSheet("background: yellow;")
```

### Using #args for Signal Arguments

When the child widget's signal carries arguments:

```python
@widget
class EditRow(Widget):
    value: Variable[str]
    _input: QLineEdit = new(bind="value", textChanged="on_change")

    on_change: signal = new()  # Emits the new text

@widget
class App(Widget):
    _items: Variable[list[str]] = new(["a", "b"])
    _rows: list[EditRow] = new(
        bind="_items",
        on_change="handle_change(#index, #args)"  # #args spreads signal args
    )

    def handle_change(self, index: int, new_text: str) -> None:
        self._items[index] = new_text
```

### Combining Multiple Placeholders

```python
_rows: list[ItemRow] = new(
    bind="_items",
    on_edit="handle_edit(#index, #value, #widget)"
)

def handle_edit(self, index: int, item: Item, widget: ItemRow) -> None:
    # Full context available
    pass
```

### Handler Formats

| Format | Behavior |
|--------|----------|
| `"handler"` | Signal's own args passed through |
| `"handler()"` | No args passed |
| `"handler(#index)"` | Index passed |
| `"handler(#index, #args)"` | Index + signal args |
| `lambda: ...` | Direct callable (no placeholders) |

### Dynamic Index Updates

After list modifications, `#index` reflects the item's current position:

```python
def handle_delete(self, index: int) -> None:
    del self._items[index]
    # Remaining items' indices update automatically
    # Widget for item at [2] becomes [1] after [0] is deleted
```

## See Also

- [List Bindings](../state/list-bindings.md) - Basic list binding
- [Format Expressions](../state/format-expressions.md) - Expression syntax
- [Variables](../state/variables.md) - List Variables
