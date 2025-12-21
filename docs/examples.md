# Example Gallery

A collection of example applications showcasing QtPie features.

---

## Counter - The Hero Example

The canonical counter example demonstrating reactive state and automatic UI updates.

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entry_point
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1  # That's it. Label updates automatically.
```

**What it demonstrates:**
- `state()` for reactive state management
- Format string binding with `bind="Count: {count}"`
- Signal connections via `clicked="increment"`
- Automatic UI updates when state changes

**Run it:** Save the code and run with `python counter.py`

---

## Hello World - Three Ways

QtPie offers multiple approaches for different needs.

### Function Entry Point

The simplest possible QtPie app - a function that returns a widget.

```python
from qtpie import entry_point
from qtpy.QtWidgets import QLabel

@entry_point
def main():
    return QLabel("Hello, World!")
```

### Widget Class Entry Point

For apps that need interactivity and state.

```python
from qtpie import entry_point, make, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entry_point
@widget
class MyWidget(QWidget):
    text: QLabel = make(QLabel, "Hello, World!")
    button: QPushButton = make(QPushButton, "Click Me", clicked="on_click")

    def on_click(self) -> None:
        self.text.setText("Button Clicked!")
```

### App Class Entry Point

For apps that need full control over initialization.

```python
from typing import override
from qtpie import App, entry_point
from qtpy.QtWidgets import QLabel

@entry_point
class MyApp(App):
    @override
    def create_window(self):
        return QLabel("Hello from App!")
```

**What it demonstrates:**
- Three different entry point patterns
- Choose the right level of complexity for your needs
- All three use `@entry_point` to handle app lifecycle

---

## Form with Data Binding

A form that automatically binds input fields to a model.

```python
from dataclasses import dataclass
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QLineEdit, QSlider, QWidget
from qtpie import Widget, entry_point, make, widget

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@entry_point
@widget(layout="form")
class DogEditor(QWidget, Widget[Dog]):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    age: QSlider = make(
        QSlider,
        Qt.Orientation.Horizontal,
        form_label="Age",
        minimum=0,
        maximum=20
    )
    info: QLabel = make(QLabel, bind="Name: {name}, Age: {age}")
```

**What it demonstrates:**
- `Widget[Dog]` for model-based widgets
- Automatic two-way binding to model fields
- `layout="form"` for form-style layouts
- `form_label` parameter for field labels
- Format binding with multiple variables: `bind="Name: {name}, Age: {age}"`

**How it works:**
- Fields named `name` and `age` auto-bind to `model.name` and `model.age`
- Changing the widgets updates the model automatically
- The info label watches both fields and updates when either changes

---

## Form with Validation

Real-time validation with visual feedback.

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QLabel, QLineEdit, QWidget
from qtpie import Widget, entry_point, make, widget

@dataclass
class User:
    name: str = ""
    email: str = ""

@entry_point
@widget(layout="form")
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    email: QLineEdit = make(QLineEdit, form_label="Email")
    name_error: QLabel = make(QLabel, bind="{validation_for('name')}")
    email_error: QLabel = make(QLabel, bind="{validation_for('email')}")
    valid_status: QLabel = make(QLabel, bind="Valid: {is_valid()}")

    def setup(self) -> None:
        # Add validation rules
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)

        # Style error labels
        self.name_error.setStyleSheet("color: red;")
        self.email_error.setStyleSheet("color: red;")
```

**What it demonstrates:**
- `add_validator()` for field validation
- `validation_for(field)` to get errors for one field
- `is_valid()` to check overall form validity
- Binding validation state to labels
- Custom setup in `setup()` lifecycle hook

**How validation works:**
- Validators are functions that return `None` (valid) or error message (invalid)
- `validation_for()` returns a list of error messages for a field
- `is_valid()` returns `True` only when all fields pass validation
- All validation results are reactive - UI updates automatically

---

## Window with Menus

A main window with a menu bar.

```python
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMainWindow, QMenu, QTextEdit
from qtpie import action, make, menu, separator, window

@action("&New")
class NewAction(QAction):
    pass

@action("&Open")
class OpenAction(QAction):
    pass

@action("&Save")
class SaveAction(QAction):
    pass

@action("E&xit")
class ExitAction(QAction):
    pass

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction, triggered="on_new")
    open_file: OpenAction = make(OpenAction, triggered="on_open")
    save: SaveAction = make(SaveAction, triggered="on_save")
    sep1: QAction = separator()
    exit_app: ExitAction = make(ExitAction, triggered="on_exit")

    def on_new(self) -> None:
        print("New file")

    def on_open(self) -> None:
        print("Open file")

    def on_save(self) -> None:
        print("Save file")

    def on_exit(self) -> None:
        self.parent().close()

@window(title="Text Editor", size=(800, 600))
class EditorWindow(QMainWindow):
    file_menu: FileMenu = make(FileMenu)
    central_widget: QTextEdit = make(QTextEdit)
```

**What it demonstrates:**
- `@window` decorator for QMainWindow
- `@menu` decorator for QMenu with auto-title from class name
- `@action` decorator for QAction with text
- `separator()` for menu separators
- Auto-adding menus to menu bar
- Auto-adding actions to menus
- `central_widget` field auto-set as central widget
- Signal connections for menu actions

**How menus work:**
- QMenu fields in a window are automatically added to the menu bar
- QAction fields in a menu are automatically added to the menu
- Separators are inserted in declaration order
- "Menu" suffix is stripped from class name for auto-title

---

## Counter with Up/Down Buttons

A counter with increment and decrement.

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@entry_point
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    up: QPushButton = make(QPushButton, "+", clicked="increment")
    down: QPushButton = make(QPushButton, "-", clicked="decrement")
    reset: QPushButton = make(QPushButton, "Reset", clicked="reset")

    def increment(self) -> None:
        self.count += 1

    def decrement(self) -> None:
        self.count -= 1

    def reset(self) -> None:
        self.count = 0
```

**What it demonstrates:**
- Multiple buttons controlling the same state
- Simple state manipulation with `+=`, `-=`, and `=`
- All connected widgets update automatically

---

## Format String Expressions

Advanced format string bindings with expressions.

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox, QWidget

@entry_point
@widget(layout="form")
class Calculator(QWidget):
    price: float = state(10.0)
    quantity: int = state(1)
    discount: float = state(0.0)

    price_input: QSpinBox = make(
        QSpinBox,
        form_label="Price",
        bind="price",
        maximum=10000
    )
    qty_input: QSpinBox = make(
        QSpinBox,
        form_label="Quantity",
        bind="quantity",
        minimum=1,
        maximum=100
    )
    discount_input: QSpinBox = make(
        QSpinBox,
        form_label="Discount %",
        bind="discount",
        maximum=100
    )

    subtotal: QLabel = make(QLabel, bind="Subtotal: ${price * quantity:.2f}")
    discount_amount: QLabel = make(
        QLabel,
        bind="Discount: -${price * quantity * discount / 100:.2f}"
    )
    total: QLabel = make(
        QLabel,
        bind="Total: ${price * quantity * (1 - discount / 100):.2f}"
    )
```

**What it demonstrates:**
- Math expressions in format strings: `{price * quantity}`
- Format specifiers: `{price:.2f}` for decimal precision
- Multiple variables in one expression
- Complex calculations update automatically

---

## Nested State Binding

Binding to nested object properties.

```python
from dataclasses import dataclass
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox, QWidget

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@entry_point
@widget(layout="form")
class DogEditor(QWidget):
    dog: Dog = state(Dog(name="Buddy", age=3))

    name_edit: QLineEdit = make(QLineEdit, form_label="Name", bind="dog.name")
    age_spin: QSpinBox = make(QSpinBox, form_label="Age", bind="dog.age")
    greeting: QLabel = make(QLabel, bind="Hello, {dog.name}!")
    info: QLabel = make(QLabel, bind="{dog.name} is {dog.age} years old")
```

**What it demonstrates:**
- `state(Dog(...))` for complex object state
- Nested property binding: `bind="dog.name"`
- Format strings with nested paths: `{dog.name}`
- Two-way binding to nested properties

---

## Form with Dirty Tracking

Track unsaved changes in a form.

```python
from dataclasses import dataclass
from qtpie import Widget, entry_point, make, widget
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QWidget

@dataclass
class User:
    name: str = ""
    email: str = ""

@entry_point
@widget(layout="form")
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    email: QLineEdit = make(QLineEdit, form_label="Email")

    dirty_status: QLabel = make(
        QLabel,
        bind="{'Unsaved changes!' if is_dirty() else 'All saved'}"
    )
    save_button: QPushButton = make(
        QPushButton,
        "Save",
        clicked="on_save",
        bind_prop={"enabled": "is_dirty()"}
    )

    def on_save(self) -> None:
        # Save changes
        print(f"Saving: {self.proxy.name}, {self.proxy.email}")
        # Mark as clean
        self.reset_dirty()
```

**What it demonstrates:**
- `is_dirty()` to check if any field has changed
- `reset_dirty()` to mark all fields as clean
- `bind_prop` to bind widget properties (button enabled state)
- Ternary expressions in bindings
- Conditional UI based on state

---

## Text Editor with Undo/Redo

A text editor with undo and redo buttons.

```python
from qtpie import Widget, entry_point, make, widget
from qtpy.QtWidgets import QLineEdit, QPushButton, QWidget

@entry_point
@widget(undo=True)  # Enable undo/redo tracking
class Editor(QWidget):
    text: str = ""

    text_edit: QLineEdit = make(QLineEdit, bind="text")
    undo_btn: QPushButton = make(
        QPushButton,
        "Undo",
        clicked="do_undo",
        bind_prop={"enabled": "can_undo('text')"}
    )
    redo_btn: QPushButton = make(
        QPushButton,
        "Redo",
        clicked="do_redo",
        bind_prop={"enabled": "can_redo('text')"}
    )

    def do_undo(self) -> None:
        self.undo("text")

    def do_redo(self) -> None:
        self.redo("text")
```

**What it demonstrates:**
- `@widget(undo=True)` to enable undo/redo
- `undo(field)` and `redo(field)` methods
- `can_undo(field)` and `can_redo(field)` for button states
- Property binding to disable buttons when undo/redo unavailable

**Undo options:**
- `undo=True` - enable with defaults
- `undo_max=50` - max history depth (default: 20)
- `undo_debounce_ms=500` - debounce rapid changes (default: 300ms)

---

## Multiple State Fields

A form with multiple independent state fields.

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox, QWidget

@entry_point
@widget(layout="form")
class UserForm(QWidget):
    # Independent state fields
    first_name: str = state("John")
    last_name: str = state("Doe")
    age: int = state(0)
    active: bool = state(False)

    # Input widgets
    first_edit: QLineEdit = make(QLineEdit, form_label="First", bind="first_name")
    last_edit: QLineEdit = make(QLineEdit, form_label="Last", bind="last_name")
    age_spin: QSpinBox = make(QSpinBox, form_label="Age", bind="age")

    # Display widget
    full_name: QLabel = make(QLabel, bind="{first_name} {last_name}")
```

**What it demonstrates:**
- Multiple `state()` fields in one widget
- Each state field is independent
- Format binding can reference multiple state fields
- All state changes trigger automatic UI updates

---

## See Also

- **[Getting Started](start/hello-world.md)** - Build your first QtPie app
- **[Reactive State](data/state.md)** - Deep dive into `state()`
- **[Format Expressions](data/format.md)** - All format binding features
- **[Model Widgets](data/model-widgets.md)** - `Widget[T]` pattern
- **[Validation](data/validation.md)** - Form validation in detail
- **[Windows & Menus](guides/windows-menus.md)** - Building desktop apps
