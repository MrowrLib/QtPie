# Widgets

Widgets are the building blocks of QtPie applications. The `Widget` class provides a declarative way to define Qt widgets with automatic layout, reactive state, and signal connections.

## The @widget Decorator

Every QtPie widget must be decorated with `@widget`. This decorator processes field definitions and sets up the reactive system.

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget
class MyWidget(Widget):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me")
```

**Important:** Attempting to instantiate a `Widget` subclass without the `@widget` decorator will raise a `TypeError`.

```python
# This will raise TypeError: "MyWidget must be decorated with @widget"
class MyWidget(Widget):
    label: QLabel = new("Hello")

widget = MyWidget()  # Error!
```

## The new() Factory

The `new()` function is used to declare fields in your widget. It creates instances of Qt widgets, Variables, or any other objects at runtime.

### Basic Widget Creation

```python
@widget
class Example(Widget):
    # Positional args go to the widget constructor
    label: QLabel = new("Label text")
    button: QPushButton = new("Button text")
```

### Constructor Arguments

You can pass both positional and keyword arguments through `new()`:

```python
from PySide6.QtWidgets import QLineEdit

@widget
class LoginForm(Widget):
    username: QLineEdit = new(placeholderText="Enter username")
    password: QLineEdit = new(echoMode=QLineEdit.EchoMode.Password)
```

### Non-Widget Fields

The `new()` factory works with any class, not just Qt widgets:

```python
class Config:
    def __init__(self, name: str = "default"):
        self.name = name

@widget
class MyWidget(Widget):
    config: Config = new(name="custom")
    label: QLabel = new("Hello")

widget = MyWidget()
assert widget.config.name == "custom"
```

## Widget Properties with new()

You can set Qt widget properties declaratively using keyword arguments in `new()`. These become `setXxx()` calls on the widget:

```python
@widget
class StyledWidget(Widget):
    label: QLabel = new(
        "Hello",
        toolTip="This is a label",
        styleSheet="color: red;",
        enabled=False,
        visible=True
    )
```

### Property Aliases

Some properties have convenient aliases:

- `title` → `windowTitle` (calls `setWindowTitle()`)
- `stylesheet` → `styleSheet` (calls `setStyleSheet()`)

```python
@widget
class Example(Widget):
    # Both of these work:
    label1: QLabel = new("Hello", title="My Label")
    label2: QLabel = new("World", windowTitle="My Label")

    # Both of these work:
    label3: QLabel = new("Red", stylesheet="color: red;")
    label4: QLabel = new("Blue", styleSheet="color: blue;")
```

## Decorator Properties

The `@widget` decorator accepts keyword arguments that become `setXxx()` calls on the widget itself:

```python
@widget(windowTitle="My Application", minimumWidth=400, minimumHeight=300)
class MainWidget(Widget):
    label: QLabel = new("Content")

widget = MainWidget()
assert widget.windowTitle() == "My Application"
assert widget.minimumWidth() == 400
assert widget.minimumHeight() == 300
```

### The title Alias

The `title` parameter is an alias for `windowTitle`:

```python
@widget(title="My Window")
class MyWidget(Widget):
    label: QLabel = new("Hello")

widget = MyWidget()
assert widget.windowTitle() == "My Window"
```

### The stylesheet Alias

The `stylesheet` parameter is an alias for `styleSheet`:

```python
@widget(stylesheet="background: yellow;")
class MyWidget(Widget):
    label: QLabel = new("Hello")

widget = MyWidget()
assert widget.styleSheet() == "background: yellow;"
```

### Multiple Properties

You can set multiple properties at once:

```python
@widget(
    windowTitle="Calculator",
    toolTip="A simple calculator",
    minimumWidth=300,
    minimumHeight=200,
    styleSheet="background-color: white;"
)
class Calculator(Widget):
    display: QLabel = new("0")
```

### Invalid Properties

If you specify a property that doesn't exist, you'll get an `AttributeError`:

```python
@widget(notARealProperty="value")
class MyWidget(Widget):
    label: QLabel = new("Hello")

# Raises AttributeError: "setNotARealProperty" with reference to "notARealProperty"
widget = MyWidget()
```

## Signal Connections

Signals can be connected declaratively using keyword arguments in `new()`:

### Connect to Methods by Name

```python
@widget
class Counter(Widget):
    button: QPushButton = new("Increment", clicked="on_button_clicked")
    count: int = 0

    def on_button_clicked(self):
        self.count += 1
        print(f"Count: {self.count}")
```

If the method doesn't exist, you'll get an `AttributeError` during widget initialization:

```python
@widget
class BadWidget(Widget):
    button: QPushButton = new("Click", clicked="nonexistent_method")

# Raises AttributeError with "nonexistent_method" in the message
widget = BadWidget()
```

### Connect to Callables

```python
def handle_click():
    print("Button clicked!")

@widget
class Example(Widget):
    button: QPushButton = new("Click", clicked=handle_click)
```

### Connect to Lambdas

```python
@widget
class Example(Widget):
    button: QPushButton = new("Click", clicked=lambda: print("Clicked!"))
```

### Multiple Signals

You can connect multiple signals on the same widget:

```python
@widget
class Example(Widget):
    button: QPushButton = new(
        "Click",
        pressed=lambda: print("Pressed!"),
        released=lambda: print("Released!"),
        clicked=lambda: print("Clicked!")
    )
```

## Variable Fields

QtPie supports reactive state through `Variable` fields. Variables are not Qt widgets and won't be added to the layout.

```python
from qtpie import Variable

@widget
class Counter(Widget):
    count: Variable[int] = new(0)
    label: QLabel = new("Count: 0")

    def increment(self):
        self.count += 1  # Direct assignment works
```

Variables are reactive and can trigger UI updates automatically. See the [Variables documentation](../reactive/variables.md) for details.

## The __setup__ Hook

The `__setup__()` method is called after the widget is fully initialized and its layout is ready. Use this for:

- Connecting signals manually
- Initializing state based on widget properties
- Performing setup that requires the widget hierarchy to be complete

```python
@widget
class Example(Widget):
    label: QLabel = new("Initial")
    button: QPushButton = new("Click")

    def __setup__(self):
        # Layout is ready
        assert self.layout() is not None

        # Child widgets are accessible
        assert self.label.text() == "Initial"

        # Can perform additional setup
        self.button.clicked.connect(self.on_click)

    def on_click(self):
        self.label.setText("Clicked!")
```

The `__setup__()` hook is called after `__init__()` completes, ensuring all fields are initialized.

## Field Definition Order

Widgets are added to the layout in the order they're defined in the class:

```python
@widget
class OrderedWidget(Widget):
    first: QLabel = new("First")
    second: QLabel = new("Second")
    third: QLabel = new("Third")

widget = OrderedWidget()
layout = widget.layout()
assert layout.itemAt(0).widget() == widget.first
assert layout.itemAt(1).widget() == widget.second
assert layout.itemAt(2).widget() == widget.third
```

This makes the UI structure predictable and easy to reason about.

## WidgetBase for Custom Widgets

For advanced use cases where you need to add QtPie functionality to existing Qt widgets (like `QListView`, `QTableView`, etc.), you can use the `WidgetBase` mixin:

```python
from PySide6.QtWidgets import QListView
from qtpie import WidgetBase, Variable, new

class MyListView(QListView, WidgetBase):
    items: Variable[list[str]] = new([])

    def __setup__(self):
        # Called after Qt widget initialization
        self.items.value = ["one", "two", "three"]
```

`WidgetBase` provides:
- Automatic processing of `new()` fields
- The `__setup__()` lifecycle hook
- Support for `Variable` fields

This is primarily intended for cases where you're extending an existing Qt widget class directly rather than composing them in a `Widget` container.

## Common Patterns

### Composition Over Inheritance

Prefer composing widgets rather than inheriting from specific Qt widget types:

```python
# Good - composition
@widget
class UserCard(Widget):
    name_label: QLabel = new()
    email_label: QLabel = new()
    avatar: QLabel = new()

# Avoid - inheritance (unless using WidgetBase for a specific Qt widget)
class UserCard(QLabel):  # Don't do this with Widget
    ...
```

### Organizing Complex Widgets

For complex UIs, break them into smaller widget components:

```python
@widget
class HeaderBar(Widget):
    logo: QLabel = new()
    title: QLabel = new()
    user_menu: QPushButton = new()

@widget
class SidePanel(Widget):
    nav_list: QListWidget = new()
    settings_btn: QPushButton = new()

@widget
class MainApp(Widget):
    header: HeaderBar = new()
    sidebar: SidePanel = new()
    content: QLabel = new()
```

### Composable Widgets with Variable Bindings

Build reusable widgets by declaring what state they need. Parent widgets provide bindings when creating children—similar to React props.

```python
from qtpie import Variable

@widget
class CounterDisplay(Widget):
    # Required binding - must be provided by parent
    count: Variable[int]

    _label: QLabel = new(bind="Count: {count}")

@widget
class App(Widget):
    _my_count: Variable[int] = new(0)

    # Pass state down: CounterDisplay.count binds to App._my_count
    display: CounterDisplay = new(count="_my_count")
    increment: QPushButton = new("+", clicked="on_inc")

    def on_inc(self) -> None:
        self._my_count += 1  # CounterDisplay updates automatically
```

#### Required vs Optional Bindings

- **Required**: Bare `Variable[T]` (no `= new()`) must be provided by parent
- **Optional**: `Variable[T] = new(default)` has a default, can be overridden

```python
@widget
class StatusBar(Widget):
    message: Variable[str]                   # Required
    show_icon: Variable[bool] = new(True)    # Optional with default

@widget
class App(Widget):
    _status: Variable[str] = new("Ready")

    # Must provide 'message', 'show_icon' is optional
    status_bar: StatusBar = new(message="_status")

    # Or override the default
    # status_bar: StatusBar = new(message="_status", show_icon=False)
```

If you forget a required binding, QtPie raises a clear error with instructions.

#### Two-Way Synchronization

Variable bindings are two-way. Changes on either side are synchronized:

```python
@widget
class Editor(Widget):
    content: Variable[str]

@widget
class App(Widget):
    _text: Variable[str] = new("")
    editor: Editor = new(content="_text")

    def reset(self) -> None:
        self._text.value = ""  # Editor.content also becomes ""
```

#### Nested Bindings

State flows down through multiple levels:

```python
@widget
class ThemeLabel(Widget):
    theme: Variable[str]
    _label: QLabel = new(bind="Theme: {theme}")

@widget
class ThemedPanel(Widget):
    theme: Variable[str]  # Required, passed down to child
    label: ThemeLabel = new(theme="theme")

@widget
class App(Widget):
    _theme: Variable[str] = new("dark")
    panel: ThemedPanel = new(theme="_theme")

    def toggle(self) -> None:
        self._theme.value = "light" if self._theme.value == "dark" else "dark"
        # ThemeLabel updates automatically through the chain!
```

### Private vs Public Fields

Use naming conventions to indicate field visibility:

```python
@widget
class Example(Widget):
    # Public - part of the widget's interface
    submit_button: QPushButton = new("Submit")

    # Private - internal implementation detail
    _internal_state: Variable[int] = new(0)
    _helper_label: QLabel = new()
```

## Summary

- Every QtPie widget must use the `@widget` decorator
- Use `new()` to declare widget fields and pass constructor arguments
- Set widget properties via keyword arguments in `new()` or the decorator
- Connect signals declaratively using keyword arguments
- Use `__setup__()` for initialization after the widget hierarchy is ready
- Fields are added to the layout in definition order
- Variables provide reactive state but aren't added to layouts
- Use `WidgetBase` when extending existing Qt widget classes directly
