# List Bindings

Bind a list of widgets to a `Variable[list[T]]`. When the list changes, widgets are automatically added or removed.

## Basic Usage

```python
from qtpie import Widget, Variable, new, widget

@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])
    _labels: list[QLabel] = new(bind="_items")
```

This creates one `QLabel` per item. When `_items` changes, the labels update automatically.

## Automatic Synchronization

### Adding Items

```python
def add_item(self, text: str) -> None:
    self._items.append(text)  # New label appears!
```

### Removing Items

```python
def remove_item(self, text: str) -> None:
    self._items.remove(text)  # Label disappears!
```

### Clearing

```python
def clear_all(self) -> None:
    self._items.clear()  # All labels removed
```

### Full Example

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new([])
    _labels: list[QLabel] = new(bind="_items")

    _input: QLineEdit = new(placeholderText="New item")
    _add_btn: QPushButton = new("Add", clicked="add_item")
    _clear_btn: QPushButton = new("Clear All", clicked="clear_all")

    def add_item(self) -> None:
        if text := self._input.text():
            self._items.append(text)
            self._input.clear()

    def clear_all(self) -> None:
        self._items.clear()
```

## Format Expressions

Customize how items are displayed:

```python
@widget
class NumberedList(Widget):
    _items: Variable[list[str]] = new(["First", "Second", "Third"])

    _labels: list[QLabel] = new(
        bind="_items",
        format="#{#index + 1}: {#self}"
    )
    # "1: First", "2: Second", "3: Third"
```

### Special Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{#self}` | Current item value |
| `{#index}` | Item index (0-based) |

### Complex Objects

```python
from dataclasses import dataclass

@dataclass
class Task:
    title: str
    done: bool = False

@widget
class TaskList(Widget):
    _tasks: Variable[list[Task]] = new([
        Task("Buy milk"),
        Task("Walk dog", done=True)
    ])

    _labels: list[QLabel] = new(
        bind="_tasks",
        format="{'✓' if done else '☐'} {title}"
    )
```

## Widget Configuration

Pass properties to all generated widgets:

```python
@widget
class StyledList(Widget):
    _items: Variable[list[str]] = new(["Error 1", "Error 2"])

    _labels: list[QLabel] = new(
        bind="_items",
        styleSheet="color: red; font-weight: bold;"
    )
```

## Validation Error Display

A common pattern: display validation errors as a list of labels:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _email: Variable[str] = new("")

    # All validation errors
    _errors: list[QLabel] = new(
        bind="validation_error_messages",
        styleSheet="color: red;"
    )

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Name required")
        self.add_validator("_email", "email",
            lambda v: None if "@" in v else "Invalid email")
```

### Per-Field Errors

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    # Errors for just this field
    _name_errors: list[QLabel] = new(bind="_name.validation_error_messages")

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Name required")
        self.add_validator("_name", "min_len",
            lambda v: None if len(v) >= 3 else "Min 3 characters")
```

## Accessing Widgets

Access individual widgets using list operations:

```python
@widget
class ColoredList(Widget):
    _items: Variable[list[str]] = new(["Red", "Green", "Blue"])
    _labels: list[QLabel] = new(bind="_items")

    def __setup__(self) -> None:
        # Access by index
        self._labels[0].setStyleSheet("color: red;")
        self._labels[1].setStyleSheet("color: green;")
        self._labels[2].setStyleSheet("color: blue;")

        # Iterate
        for label in self._labels:
            label.setFont(QFont("Arial", 14))

        # Length
        print(f"{len(self._labels)} items")
```

## Layout Control

### Default: In Parent Layout

By default, list widgets are added to the parent's layout.

### Exclude from Layout

Use `layout=False` to manage positioning yourself:

```python
@widget
class CustomLayout(Widget):
    _header: QLabel = new("Header")
    _items: Variable[list[str]] = new(["A", "B", "C"])
    _labels: list[QLabel] = new(bind="_items", layout=False)
    _footer: QLabel = new("Footer")

    def __setup__(self) -> None:
        # Manually add labels to a custom layout
        horizontal = QHBoxLayout()
        for label in self._labels:
            horizontal.addWidget(label)
        # Add horizontal to parent...
```

## Dict Bindings

For dictionaries, use `#key` and `#value`:

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})

    _labels: list[QLabel] = new(
        bind="_scores",
        format="{#key}: {#value} points"
    )
    # "Alice: 100 points", "Bob: 85 points"
```

## See Also

- [Bindings](bindings.md) - Content binding overview
- [Format Expressions](format-expressions.md) - Expression syntax
- [Validation](../data/validation.md) - Form validation
- [Variables](variables.md) - List Variables
