# Key Concepts

QtPie transforms Qt development from imperative to declarative. This page explains the core building blocks you'll use in every QtPie application.

---

## Decorators

Decorators turn regular Python classes into Qt components with minimal boilerplate.

### @widget

The foundation of QtPie. Transforms a class into a Qt widget with automatic layout and initialization.

```python
from qtpie import widget, make
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@widget(layout="vertical")
class CounterWidget(QWidget):
    label: QLabel = make(QLabel, "Count: 0")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")
    count: int = 0

    def increment(self) -> None:
        self.count += 1
        self.label.setText(f"Count: {self.count}")
```

**What it does:**
- Automatically creates a layout (`vertical`, `horizontal`, `form`, `grid`, or `none`)
- Adds widget fields to the layout in declaration order
- Connects signals to methods
- Calls lifecycle hooks at the right time
- Supports CSS-like classes for styling

**Key parameters:**
- `layout` - Layout type (default: `"vertical"`)
- `name` - Object name for styling (default: auto-generated from class name)
- `classes` - List of CSS classes for styling
- `auto_bind` - Auto-bind Widget[T] fields to model properties (default: `True`)
- `undo` - Enable undo/redo for model fields (default: `False`)

[Full @widget reference →](../reference/decorators/widget.md)

### @window

Turns a class into a QMainWindow with automatic menu bar and central widget setup.

```python
from qtpie import window, make
from qtpy.QtWidgets import QMainWindow, QTextEdit

@window(title="Text Editor", size=(800, 600), center=True)
class EditorWindow(QMainWindow):
    editor: QTextEdit = make(QTextEdit)

    def setup(self) -> None:
        self.statusBar().showMessage("Ready")
```

**What it does:**
- Sets window title, size, and icon
- Auto-adds QMenu fields to the menu bar
- Can center the window on screen
- Supports `central_widget` field for main content

[Full @window reference →](../reference/decorators/window.md)

### @menu

Creates a QMenu with automatic action and submenu population.

```python
from qtpie import menu, action, make
from qtpy.QtWidgets import QMenu
from qtpy.QtGui import QAction

@action("&New", shortcut="Ctrl+N")
class NewAction(QAction):
    def on_triggered(self) -> None:
        print("New file!")

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open: QAction = make(QAction, "&Open", shortcut="Ctrl+O")
```

**What it does:**
- Sets menu title (auto-generated from class name if not provided)
- Auto-adds QAction and QMenu fields in declaration order
- Supports separator() for menu dividers

[Full @menu reference →](../reference/decorators/menu.md)

### @action

Creates a QAction with automatic signal connections.

```python
from qtpie import action
from qtpy.QtGui import QAction

@action("&Save", shortcut="Ctrl+S", tooltip="Save the current file")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Saving...")
```

**What it does:**
- Sets text, shortcut, tooltip, and icon
- Auto-connects `triggered` signal to `on_triggered()` method
- Auto-connects `toggled` signal to `on_toggled()` method (for checkable actions)

[Full @action reference →](../reference/decorators/action.md)

### @entry_point

Marks the application entry point. Automatically creates the QApplication and event loop when the script is run directly.

```python
from qtpie import entry_point, widget, make
from qtpy.QtWidgets import QWidget, QLabel

@entry_point(dark_mode=True, title="Hello App", size=(400, 200))
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Hello, QtPie!")
```

**What it does:**
- Auto-runs when `__name__ == "__main__"`
- Creates QApplication instance
- Shows the window
- Starts the event loop
- Supports dark/light mode, window config

[Full @entry_point reference →](../reference/decorators/entry-point.md)

---

## Factories

Factory functions create instances with declarative syntax, avoiding verbose `field(default_factory=...)` boilerplate.

### make()

The primary factory for creating widget instances with type safety.

```python
from qtpie import make
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton

# Basic widget creation
label: QLabel = make(QLabel, "Hello World")

# With properties
edit: QLineEdit = make(QLineEdit, placeholderText="Enter name")

# With signal connections
button: QPushButton = make(QPushButton, "Click", clicked="on_click")

# With lambda
button2: QPushButton = make(QPushButton, "Go", clicked=lambda: print("Go!"))
```

**Key features:**
- Positional args passed to constructor
- Keyword args can be properties (passed to constructor) or signals (connected)
- `form_label` - Label for form layouts
- `grid` - Position in grid layouts as `(row, col)` or `(row, col, rowspan, colspan)`
- `bind` - Data binding path (see Data Binding section)
- `bind_prop` - Explicit property to bind to

[Full make() reference →](../reference/factories/make.md)

### make_later()

Declares a field that will be initialized in `setup()`.

```python
from qtpie import widget, make, make_later
from qtpy.QtWidgets import QWidget, QLabel

@widget
class MyWidget(QWidget):
    label: QLabel = make_later()  # Set in setup()

    def setup(self) -> None:
        # Now we can reference other fields or self
        self.label = QLabel(f"Widget ID: {id(self)}")
```

[Full make_later() reference →](../reference/factories/make-later.md)

### state()

Creates reactive state fields that automatically update bound widgets when assigned.

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@widget
class Counter(QWidget):
    count: int = state(0)  # Reactive state
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1  # Label updates automatically!
```

**Type syntax:**
- Inferred from default: `count: int = state(0)`
- Explicit type (for optionals): `dog: Dog | None = state[Dog | None]()`
- Pre-initialized: `config: Config = state(Config(debug=True))`

**How it works:**
- Backed by `ObservableProxy` from the `observant` library
- Assignment triggers change notifications
- Bound widgets update automatically

[Full state() reference →](../reference/factories/state.md)

### spacer()

Creates flexible space in box layouts (like `addStretch`).

```python
from qtpie import widget, make, spacer
from qtpy.QtWidgets import QWidget, QPushButton, QSpacerItem

@widget(layout="vertical")
class MyWidget(QWidget):
    top_button: QPushButton = make(QPushButton, "Top")
    space: QSpacerItem = spacer()  # Push everything to top
    bottom_button: QPushButton = make(QPushButton, "Bottom")
```

[Full spacer() reference →](../reference/factories/stretch.md)

### separator()

Creates menu separators.

```python
from qtpie import menu, action, make, separator
from qtpy.QtWidgets import QMenu
from qtpy.QtGui import QAction

@menu
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open: OpenAction = make(OpenAction)
    sep1: QAction = separator()  # Visual divider
    exit: ExitAction = make(ExitAction)
```

[Full separator() reference →](../reference/factories/separator.md)

---

## Widget[T] - Model Binding

The `Widget[T]` base class enables automatic model binding. When you inherit from `Widget[Person]`, QtPie automatically:

1. Creates a `model` instance of type `Person`
2. Creates an `ObservableProxy` wrapper as `self.proxy`
3. Auto-binds widget fields to model properties by matching names

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # Auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # Auto-binds to model.age
```

**What you get:**
- `self.model` - The Person instance
- `self.proxy` - ObservableProxy wrapping the model
- Two-way data binding between widgets and model
- Validation, dirty tracking, undo/redo support

**Manual model creation:**
```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make(Person, name="Alice", age=30)
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
```

**Disable auto-binding:**
```python
@widget(auto_bind=False)
class PersonEditor(QWidget, Widget[Person]):
    # Now you must explicitly bind with bind="name", bind="age"
    name: QLineEdit = make(QLineEdit, bind="name")
```

[Full Widget[T] reference →](../reference/bindings/widget-base.md) | [Model Widgets guide →](../data/model-widgets.md)

---

## Lifecycle Hooks

QtPie calls these methods at specific points during widget initialization. Override them to customize behavior:

```python
@widget
class MyWidget(QWidget):
    def setup(self) -> None:
        """Called after all fields are initialized."""
        print("Widget ready!")

    def setup_values(self) -> None:
        """Called after setup(). Initialize field values here."""
        pass

    def setup_bindings(self) -> None:
        """Called after setup_values(). Set up data bindings."""
        pass

    def setup_layout(self, layout: QLayout) -> None:
        """Called after bindings (if widget has a layout). Customize layout."""
        layout.setSpacing(10)

    def setup_styles(self) -> None:
        """Called after layout. Apply styles."""
        pass

    def setup_events(self) -> None:
        """Called after styles. Set up event handlers."""
        pass

    def setup_signals(self) -> None:
        """Called after events. Connect additional signals."""
        pass
```

**Execution order:**
1. `__init__()` - Fields initialized
2. `setup()` - First hook
3. `setup_values()` - Initialize values
4. `setup_bindings()` - Manual bindings
5. Widget[T] model/proxy creation
6. Data bindings processed
7. Widget[T] auto-bindings
8. `setup_layout()` - Layout customization
9. `setup_styles()` - Styling
10. `setup_events()` - Event handlers
11. `setup_signals()` - Signal connections

**Common use cases:**
- `setup()` - Create proxies, initialize state
- `setup_values()` - Set initial widget values
- `setup_bindings()` - Manual bind() calls
- `setup_layout()` - Adjust spacing, margins
- `setup_styles()` - Apply stylesheets

---

## Data Binding

QtPie supports powerful declarative data binding with multiple forms.

### Simple state binding

Bind to a reactive state field:

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="count")
    # When count changes, label updates
```

### Format string binding

Embed expressions in format strings:

```python
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    # Updates to "Count: 5" when count = 5
```

### Expression binding

Use Python expressions:

```python
@widget
class Calculator(QWidget):
    x: int = state(5)
    y: int = state(3)
    result: QLabel = make(QLabel, bind="Result: {x + y}")
    # Shows "Result: 8"
```

### Method calls in bindings

```python
@dataclass
class Person:
    name: str = ""

@widget
class PersonView(QWidget, Widget[Person]):
    label: QLabel = make(QLabel, bind="{name.upper()}")
    # Shows "ALICE" when name = "alice"
```

### Format specs

```python
@widget
class PriceDisplay(QWidget):
    price: float = state(99.99)
    label: QLabel = make(QLabel, bind="Price: ${price:.2f}")
    # Shows "Price: $99.99"
```

### Nested paths (Widget[T] models)

```python
@dataclass
class Address:
    city: str = ""

@dataclass
class Person:
    name: str = ""
    address: Address | None = None

@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # Auto-binds to model.name
    city: QLineEdit = make(QLineEdit, bind="address.city")  # Nested
```

### Optional chaining

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    # Safe even when address is None
    city: QLineEdit = make(QLineEdit, bind="address?.city")
```

**What properties are bound?**
QtPie uses a binding registry to determine the default property for each widget type:
- `QLabel` → `text`
- `QLineEdit` → `text`
- `QSpinBox` → `value`
- `QCheckBox` → `checked`
- etc.

Override with `bind_prop`:
```python
label: QLabel = make(QLabel, bind="status", bind_prop="toolTip")
```

[Format expressions guide →](../data/format.md) | [Full bind() reference →](../reference/bindings/bind.md)

---

## Next Steps

Now that you understand the core concepts, explore:

- **[Widgets](../basics/widgets.md)** - Deep dive into @widget
- **[Layouts](../basics/layouts.md)** - Vertical, horizontal, form, grid layouts
- **[Reactive State](../data/state.md)** - Master state() and format expressions
- **[Model Widgets](../data/model-widgets.md)** - Build forms with Widget[T]
- **[Styling](../basics/styling.md)** - CSS classes and SCSS support
