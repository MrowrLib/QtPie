# Window Feature Usage Patterns

Documentation extracted from `test_window.py` demonstrating QtPie `Window` class usage conventions.

---

## Basic Window Declaration

Windows require the `@window` decorator and extend `Window`. Widgets are declared as class attributes using `new()`.

```python
@window
class MainWindow(Window):
    label: QLabel = new("Hello")
    button: QPushButton = new("Click")
```

---

## Window Title

Set window title via `title=` (alias) or `windowTitle=` parameter.

```python
@window(title="My Window")
class MainWindow(Window):
    label: QLabel = new("Hello")
```

---

## Layout Types

Windows default to vertical layout. Specify via `layout=` parameter.

```python
# Vertical (default)
@window
class MainWindow(Window): ...

# Horizontal
@window(layout="horizontal")
class MainWindow(Window): ...

# Form (with label= on fields)
@window(layout="form")
class MainWindow(Window):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")

# Grid (with grid= positions)
@window(layout="grid")
class MainWindow(Window):
    a: QLabel = new("A", grid=(0, 0))
    b: QLabel = new("B", grid=(0, 1))
```

---

## Layout Margins

Apply margins as integer (all sides) or tuple (left, top, right, bottom).

```python
@window(margins=10)  # All sides
class MainWindow(Window): ...

@window(margins=(1, 2, 3, 4))  # Left, top, right, bottom
class MainWindow(Window): ...
```

---

## Central Widget

Name a field `central_widget` (or `_central_widget`) to use it directly as the central widget.

```python
@window
class MainWindow(Window):
    central_widget: QLabel = new("I AM THE CENTRAL WIDGET")
```

---

## Object Name and CSS Classes

Windows get their class name as `objectName` by default. Override with `name=` and add CSS classes with `classes=`.

```python
@window(name="my-main-window", classes=["dark-theme", "main-window"])
class MainWindow(Window):
    label: QLabel = new("Hello")
```

---

## Window Icon

Set window icon via `icon=` parameter (supports QIcon, QPixmap, string path, or StandardPixmap).

```python
from qtpy.QtWidgets import QStyle

@window(icon=QStyle.StandardPixmap.SP_ComputerIcon)
class MainWindow(Window):
    label: QLabel = new("Hello")
```

---

## Menu Bar Integration

Menus (decorated with `@menu`) are automatically added to the menu bar.

```python
@menu(text="&File")
class FileMenu(Menu):
    action_exit: QAction = new("E&xit", triggered="on_exit")

    def on_exit(self) -> None:
        print("Exit!")

@window
class MainWindow(Window):
    file_menu: FileMenu = new()
    label: QLabel = new("Content")
```

---

## Signal Connections

Connect signals to methods by name or lambda.

```python
@window
class MainWindow(Window):
    btn: QPushButton = new("Click", clicked="on_clicked")

    def on_clicked(self) -> None:
        self.was_clicked = True
```

---

## Variable Fields (Reactive State)

`Variable[T]` creates reactive state. Not added to layout (data only).

```python
@window
class MainWindow(Window):
    _count: Variable[int] = new(0)
    label: QLabel = new("Hello")
```

---

## Variable with Widget (`Variable[T, W]`)

`Variable[T, W]` creates reactive state with an auto-bound widget.

```python
@window
class MainWindow(Window):
    name: Variable[str, QLineEdit] = new("Initial")
```

Widget kwargs are chained after the value:

```python
name: Variable[str, QLineEdit] = new("")(placeholderText="Enter name")
```

---

## Binding Expressions

Use `bind=` with format strings containing Python expressions.

```python
@window
class MainWindow(Window):
    _name: Variable[str] = new("hello")
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)

    # String methods
    upper_label: QLabel = new(bind="{_name.upper()}")

    # Math expressions
    sum_label: QLabel = new(bind="{_x + _y}")

    # Mixed text and expressions
    label: QLabel = new(bind="x={_x}, y={_y}, sum={_x + _y}")

    # Format specs
    _price: Variable[float] = new(19.99)
    price_label: QLabel = new(bind="${_price:.2f}")
```

---

## Binding Placeholders

Special placeholders in binding expressions:

| Placeholder | Meaning |
|-------------|---------|
| `{#self}` | Variable's value |
| `{#var}` | Alias for Variable's value |
| `{#widget}` | Parent widget instance |
| `{#window}` | Parent window instance (alias for #widget in Window) |
| `{#index}` | Item index (in list repeaters) |
| `{#key}` | Dict key (in dict repeaters) |
| `{#value}` | Dict value (in dict repeaters) |

```python
@window(title="Test Window")
class MainWindow(Window):
    label: QLabel = new(bind="Title: {#window.windowTitle()}")
    my_var: Variable[str, QLabel] = new("hello")(bind="{#self.upper()}")
```

---

## Property Bindings (`visible=`, `enabled=`)

Control visibility and enabled state reactively.

```python
@window
class MainWindow(Window):
    _show_label: Variable[bool] = new(True)
    label: QLabel = new("Hello", visible="_show_label")

    _count: Variable[int] = new(5)
    label2: QLabel = new("Visible when > 3", visible="{_count > 3}")
```

---

## Reactive Window Properties

Decorator kwargs can reference Variables for reactive updates.

```python
@window(title="{_title}")
class MainWindow(Window):
    _title: Variable[str] = new("Initial Title")
```

---

## Window with Record Type (`Window[T]`)

`Window[T]` creates a typed record with reactive field access.

```python
@dataclass
class Dog:
    name: str
    age: int

@window(record=Dog("Fido", "Lab"))
class DogWindow(Window[Dog]):
    pass

# Access via w.record.name, w.record.age
```

---

## Record Auto-Binding

Fields with same name as record properties auto-bind.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@window
class PersonWindow(Window[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age
```

---

## List Repeater (`Variable[list[T], W]`)

Creates one widget per list item.

```python
@window
class MainWindow(Window):
    numbers: Variable[list[int], QLabel] = new([1, 2, 3])(bind="{#self}")
```

With index and object properties:

```python
items: Variable[list[str], QLabel] = new(["x", "y"])(bind="Item {#index}: {#self}")

# With dataclass objects
items: Variable[list[Item], QLabel] = new([Item("Apple", 5)])(bind="{name}: {count}")
```

---

## Dict Repeater (`Variable[dict[K, V], W]`)

Creates one widget per dict entry.

```python
@window
class MainWindow(Window):
    scores: Variable[dict[str, int], QLabel] = new({"Alice": 100})(bind="{#key}: {#value}")
```

---

## List Widget Binding (`list[QWidget]`)

Alternative syntax for list repeaters.

```python
@window
class MainWindow(Window):
    _items: Variable[list[str]] = new(["one", "two"])
    labels: list[QLabel] = new(bind="_items", format="Value: {#self}")
```

---

## Exclude from Layout

Use `layout=False` to create a widget without adding it to the layout.

```python
@window
class MainWindow(Window):
    visible: QLabel = new("Visible")
    hidden: QLabel = new("Hidden", layout=False)
```

---

## __setup__ Hook

Override `__setup__` for post-initialization logic.

```python
@window
class MainWindow(Window):
    label: QLabel = new("Hello")

    def __setup__(self) -> None:
        # Widgets and menus are ready here
        print(self.label.text())
```

---

## Dirty Tracking

Track when fields change from initial values.

```python
@window
class MainWindow(Window):
    _name: Variable[str] = new("")

# w.is_dirty - Observable[bool]
# w.dirty_fields - set of changed field names
# w.reset_dirty() - mark all as clean
```

Lifecycle hook:

```python
def on_dirty_changed(self, is_dirty: bool) -> None:
    self.save_btn.setEnabled(is_dirty)
```

---

## Validation

Add validators to fields.

```python
@window
class MainWindow(Window):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

# w.is_valid - bool
# w.validation_errors - {field: {validator: [errors]}}
# w.validation_error_messages - flat list of all error messages
```

Lifecycle hook:

```python
def on_valid_changed(self, is_valid: bool) -> None:
    self.submit_btn.setEnabled(is_valid)
```

---

## Programmatic Binding

Use `bind()` function in `__setup__` for programmatic bindings.

```python
from qtpie import bind

@window
class MainWindow(Window):
    _name: Variable[str] = new("Hello")
    label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self.label)
```

---

## Instance Methods in Bindings

Call instance methods in binding expressions.

```python
@window
class MainWindow(Window):
    label: QLabel = new(bind="{compute_value()}")

    _name: Variable[str] = new("Hi")
    label2: QLabel = new(bind="{repeat_text(_name, 3)}")

    def compute_value(self) -> str:
        return "Computed!"

    def repeat_text(self, text: str, times: int) -> str:
        return text * times
```
