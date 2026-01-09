# Widgets

Widgets are the building blocks of QtPie applications. The `Widget` class provides a declarative way to define Qt widgets with automatic layout, reactive state, and signal connections.

QtPie widgets are **composable**: child widgets declare their interface (Variables and Signals), parents provide bindings. State flows down, events flow up. See [Composable Widgets](#composable-widgets) for the full pattern.

## The @widget Decorator

Every QtPie widget must be decorated with `@widget`. This decorator processes field definitions and sets up the reactive system.

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello, World!")
    _button: QPushButton = new("Click Me")
```

**Important:** Attempting to instantiate a `Widget` subclass without the `@widget` decorator will raise a `TypeError`.

```python
# This will raise TypeError: "MyWidget must be decorated with @widget"
class MyWidget(Widget):
    _label: QLabel = new("Hello")

widget = MyWidget()  # Error!
```

## The new() Factory

The `new()` function is used to declare fields in your widget. It creates instances of Qt widgets, Variables, or any other objects at runtime.

### Basic Widget Creation

```python
@widget
class Example(Widget):
    # Positional args go to the widget constructor
    _label: QLabel = new("Label text")
    _button: QPushButton = new("Button text")
```

### Constructor Arguments

You can pass both positional and keyword arguments through `new()`:

```python
from PySide6.QtWidgets import QLineEdit

@widget
class LoginForm(Widget):
    _username: Variable[str, QLineEdit] = new("")(placeholderText="Enter username")
    _password: Variable[str, QLineEdit] = new("")(echoMode=QLineEdit.EchoMode.Password)
    _login_btn: QPushButton = new("Login", clicked="_on_login")

    def _on_login(self):
        print(f"Logging in as {self._username.value}")
```

For `Variable[T, W]`, the first call sets the Variable's default, and the chained call configures the widget.

### Binding to Child Widgets

When creating child widgets, pass Variable and Signal bindings via `new()`:

```python
from PySide6.QtCore import Signal

@widget
class Slider(Widget):
    value: Variable[int]          # Required - parent provides
    on_change = Signal(int)       # Parent handles
    _slider: QSlider = new(valueChanged="on_change")

@widget
class App(Widget):
    _volume: Variable[int] = new(50)
    _slider: Slider = new(value="_volume", on_change="_on_volume_change")
    _label: QLabel = new(bind="Volume: {_volume}")

    def _on_volume_change(self, val: int):
        self._volume.value = val
```

The string `"_volume"` binds the child's `value` interface to the parent's `_volume` Variable. Same pattern for Signals.

### Non-Widget Fields

The `new()` factory works with any class, not just Qt widgets:

```python
class Config:
    def __init__(self, name: str = "default"):
        self.name = name

@widget
class MyWidget(Widget):
    _config: Config = new(name="custom")
    _label: QLabel = new("Hello")

w = MyWidget()
assert w._config.name == "custom"
```

## Widget Properties with new()

You can set Qt widget properties declaratively using keyword arguments in `new()`. These become `setXxx()` calls on the widget:

```python
@widget
class StyledWidget(Widget):
    _label: QLabel = new(
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
    _result: Variable[str] = new("0")
    _display: QLabel = new(bind="{_result}")
```

### Reactive Decorator Properties

Decorator properties can reference Variables for reactive updates:

```python
@widget(windowTitle="{_filename} - Editor")
class Editor(Widget):
    _filename: Variable[str] = new("untitled.txt")
    _content: QTextEdit = new()

    def open_file(self, path: str):
        self._filename.value = path  # Window title updates automatically
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

Signals can be connected declaratively using keyword arguments in `new()`. The handler can be a method name, a callable, or a Signal to emit.

### Connect to Methods by Name

```python
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("Increment", clicked="_on_increment")

    def _on_increment(self):
        self._count += 1
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
    _button: QPushButton = new(
        "Click",
        pressed=lambda: print("Pressed!"),
        released=lambda: print("Released!"),
        clicked=lambda: print("Clicked!")
    )
```

### Connect to a Signal

When the handler string refers to a Signal on your widget, the signals are connected directly. This is useful for forwarding events to parent widgets:

```python
from PySide6.QtCore import Signal

@widget
class IncrementButton(Widget):
    on_click = Signal()  # Interface - parent connects to this
    _button: QPushButton = new("+", clicked="on_click")  # Emits signal
```

The parent can then connect to `on_click`:

```python
@widget
class App(Widget):
    _count: Variable[int] = new(0)
    _btn: IncrementButton = new(on_click="_increment")

    def _increment(self):
        self._count += 1
```

## Variable Fields

QtPie supports reactive state through `Variable` fields. Variables are not Qt widgets and won't be added to the layout.

```python
from qtpie import Variable

@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("+", clicked="_increment")

    def _increment(self):
        self._count += 1  # Label updates automatically
```

### Required vs Optional Variables

Variables with `= new(default)` have a default value. Variables without a default are required - the parent must provide them:

```python
@widget
class ProgressBar(Widget):
    progress: Variable[int]                    # Required - parent must provide
    show_percent: Variable[bool] = new(True)   # Optional - has default
    _label: QLabel = new(bind="{progress}%", visible="show_percent")

@widget
class App(Widget):
    _progress: Variable[int] = new(0)
    _bar: ProgressBar = new(progress="_progress")  # Binds _progress to child's progress
```

Variables are reactive and can trigger UI updates automatically. See the [Variables documentation](../reactive/variables.md) for details.

## Validation

Add validators to Variables using the `validate=` parameter:

```python
@widget
class SignupForm(Widget):
    _email: Variable[str, QLineEdit] = new("")(
        placeholderText="Email",
        validate=lambda v: None if "@" in v else "Invalid email"
    )
    _password: Variable[str, QLineEdit] = new("")(
        placeholderText="Password",
        validate="validate_password"
    )
    _errors: list[QLabel] = new(bind="validation_error_messages", stylesheet="color: red;")
    _submit: QPushButton = new("Sign Up", enabled="{is_valid}", clicked="_on_submit")

    def validate_password(self, value: str) -> str | None:
        if len(value) < 8:
            return "Password must be at least 8 characters"
        return None

    def _on_submit(self):
        print(f"Signing up {self._email.value}")
```

Validators return `None` if valid, or an error message string. Use `is_valid` and `validation_error_messages` to bind UI state reactively. See the [Validation documentation](../data/validation.md) for details.

## The __setup__ Hook

The `__setup__()` method is called after the widget is fully initialized and its layout is ready. Use this for:

- Setting initial focus or state
- Loading data from external sources
- Performing setup that requires the widget hierarchy to be complete

```python
@widget
class SearchForm(Widget):
    _query: Variable[str, QLineEdit] = new("")(placeholderText="Search...")
    _results: QLabel = new(bind="Results for: {_query}")
    _search_btn: QPushButton = new("Search", clicked="_on_search")

    def __setup__(self):
        # Layout is ready, all fields exist
        self._query.widget.setFocus()
        self._query.widget.selectAll()

    def _on_search(self):
        print(f"Searching for: {self._query.value}")
```

The `__setup__()` hook is called after `__init__()` completes, ensuring all fields are initialized.

## Field Definition Order

Widgets are added to the layout in the order they're defined in the class:

```python
@widget
class OrderedWidget(Widget):
    _first: QLabel = new("First")
    _second: QLabel = new("Second")
    _third: QLabel = new("Third")

w = OrderedWidget()
layout = w.layout()
assert layout.itemAt(0).widget() == w._first
assert layout.itemAt(1).widget() == w._second
assert layout.itemAt(2).widget() == w._third
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
    name: Variable[str]   # Parent provides user data
    email: Variable[str]
    _name_label: QLabel = new(bind="{name}")
    _email_label: QLabel = new(bind="{email}")

# Avoid - inheritance (unless using WidgetBase for a specific Qt widget)
class UserCard(QLabel):  # Don't do this with Widget
    ...
```

### Organizing Complex Widgets

For complex UIs, break them into smaller widget components. Each component declares its interface:

```python
from PySide6.QtCore import Signal

@widget
class HeaderBar(Widget):
    title: Variable[str]           # Parent provides
    on_menu_click = Signal()       # Parent handles
    _logo: QLabel = new("🏠")
    _title: QLabel = new(bind="{title}")
    _menu_btn: QPushButton = new("☰", clicked="on_menu_click")

@widget
class SidePanel(Widget):
    on_navigate = Signal(str)      # Emits page name
    _home_btn: QPushButton = new("Home", clicked=lambda: self.on_navigate.emit("home"))
    _settings_btn: QPushButton = new("Settings", clicked=lambda: self.on_navigate.emit("settings"))

@widget
class MainApp(Widget):
    _page: Variable[str] = new("home")
    _header: HeaderBar = new(title="_page", on_menu_click="_toggle_sidebar")
    _sidebar: SidePanel = new(on_navigate="_navigate")
    _content: QLabel = new(bind="Current page: {_page}")

    def _toggle_sidebar(self):
        self._sidebar.setVisible(not self._sidebar.isVisible())

    def _navigate(self, page: str):
        self._page.value = page
```

### Composable Widgets

Build reusable widgets by declaring their interface: required Variables for state and Signals for events. Parents provide bindings when creating children.

```python
from PySide6.QtCore import Signal

@widget
class CounterDisplay(Widget):
    # Interface - parent provides these
    count: Variable[int]
    on_increment = Signal()

    # Internal
    _label: QLabel = new(bind="Count: {count}")
    _button: QPushButton = new("+", clicked="on_increment")

@entrypoint
@widget
class App(Widget):
    # Example: state in parent, passed to child
    _count: Variable[int] = new(0)

    _display: CounterDisplay = new(
        count="_count",
        on_increment="_on_increment"
    )

    def _on_increment(self) -> None:
        self._count += 1
```

State flows down via Variable bindings. Events flow up via Signals. The child doesn't know where `count` comes from or what happens on increment.

#### Interface vs Internal

- **No underscore**: Interface (required Variables, Signals) - what parents connect to
- **Underscore**: Internal implementation (state, widgets, handlers)

#### Required vs Optional Bindings

```python
@widget
class StatusBar(Widget):
    message: Variable[str]                   # Required - no default
    show_icon: Variable[bool] = new(True)    # Optional - has default
```

If you forget a required binding, QtPie raises a clear error.

#### Nested Bindings

State flows through multiple levels:

```python
@widget
class ThemeLabel(Widget):
    theme: Variable[str]
    _label: QLabel = new(bind="Theme: {theme}")

@widget
class ThemedPanel(Widget):
    theme: Variable[str]
    _label: ThemeLabel = new(theme="theme")  # Pass through

@widget
class App(Widget):
    _theme: Variable[str] = new("dark")
    _panel: ThemedPanel = new(theme="_theme")
```

Changing `App._theme` updates `ThemeLabel` automatically through the chain.

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
- Connect signals to methods (`clicked="_on_click"`) or forward to Signals (`clicked="on_click"`)
- Variables without defaults are required - parents provide them via `new(var_name="_parent_var")`
- Use `__setup__()` for initialization after the widget hierarchy is ready
- Fields are added to the layout in definition order
- Use underscore prefix for internal fields, no underscore for interface (Variables, Signals)
- Use `WidgetBase` when extending existing Qt widget classes directly
