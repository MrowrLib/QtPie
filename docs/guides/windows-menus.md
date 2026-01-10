# Windows & Menus

`Window` extends `QMainWindow` with declarative features. Use it when you need a menu bar, status bar, or main window functionality.

## Basic Window

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Window, new, window

@window(title="My App")
class MainWindow(Window):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me")
```

The `@window` decorator is required. Child widgets are placed in a central widget with automatic layout.

## Window Properties

```python
@window(
    title="My Application",
    minimumWidth=800,
    minimumHeight=600
)
class MainWindow(Window):
    ...
```

### Property Aliases

| Alias | Qt Property |
|-------|-------------|
| `title` | `windowTitle` |
| `stylesheet` | `styleSheet` |

## Layouts

### Default: Vertical

```python
@window
class MainWindow(Window):
    a: QLabel = new("First")
    b: QLabel = new("Second")
```

### Horizontal

```python
@window(layout="horizontal")
class MainWindow(Window):
    left: QLabel = new("Left")
    right: QLabel = new("Right")
```

### Form Layout

```python
@window(layout="form")
class MainWindow(Window):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")
```

### Grid Layout

```python
@window(layout="grid")
class MainWindow(Window):
    a: QLabel = new("A", grid=(0, 0))
    b: QLabel = new("B", grid=(0, 1))
    c: QLabel = new("C", grid=(1, 0))
    d: QLabel = new("D", grid=(1, 1))
```

### Layout Margins

```python
# All sides
@window(margins=10)
class MainWindow(Window):
    ...

# Individual: (left, top, right, bottom)
@window(margins=(5, 10, 5, 10))
class MainWindow(Window):
    ...
```

## Explicit Central Widget

Name a field `central_widget` to use it directly as the central widget:

```python
@window
class MainWindow(Window):
    central_widget: QLabel = new("I AM THE CENTRAL WIDGET")
```

## Menu Bar

Menu fields are automatically added to the menu bar:

```python
from qtpie import Menu, menu

@menu(text="&File")
class FileMenu(Menu):
    open_action: QAction = new("&Open", triggered="on_open")
    save_action: QAction = new("&Save", triggered="on_save")

    def on_open(self) -> None:
        print("Open!")

    def on_save(self) -> None:
        print("Save!")

@window(title="Editor")
class MainWindow(Window):
    file_menu: FileMenu = new()  # Automatically in menu bar
    content: QTextEdit = new()   # Goes to central widget
```

See [Menus](#menus) below for more details.

## Reactive State

Windows support all reactive features:

### Variables

```python
@window(title="Counter")
class MainWindow(Window):
    _count: Variable[int] = new(0)
    label: QLabel = new(bind="Count: {_count}")
    button: QPushButton = new("+1", clicked="increment")

    def increment(self) -> None:
        self._count += 1
```

### Auto-Binding

Widgets auto-bind to same-named Variables:

```python
@window
class MainWindow(Window):
    _name: Variable[str] = new("Initial")
    name: QLineEdit = new()  # Auto-binds to _name (two-way)
```

### Property Bindings

```python
@window
class MainWindow(Window):
    _show_panel: Variable[bool] = new(True)
    panel: QLabel = new("Panel", visible="_show_panel")

    _count: Variable[int] = new(0)
    warning: QLabel = new("Low!", visible="{_count < 5}")
```

### Reactive Window Title

```python
@window(title="{_name.upper()}")
class MainWindow(Window):
    _name: Variable[str] = new("hello")
    # Window title updates when _name changes!
```

## Record Types

Bind a dataclass to your window:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@window(title="Person Editor", record=Person("Alice", 30))
class PersonWindow(Window[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age
```

## Validation

```python
@window
class MainWindow(Window):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")
```

Or use the `validate=` parameter:

```python
_name: Variable[str] = new("", validate=lambda v: None if v else "Required")
```

## Dirty Tracking

```python
@window
class MainWindow(Window):
    _name: Variable[str] = new("")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        print(f"Has changes: {is_dirty}")
```

---

# Menus

The `@menu` decorator creates declarative menus with QAction fields.

## Basic Menu

```python
from qtpy.QtGui import QAction
from qtpie import Menu, menu

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New", triggered="on_new")
    open_action: QAction = new("&Open", triggered="on_open")
    save_action: QAction = new("&Save", triggered="on_save")

    def on_new(self) -> None:
        print("New file")

    def on_open(self) -> None:
        print("Open file")

    def on_save(self) -> None:
        print("Save file")
```

## Menu Separators

Use `Separator` type annotation:

```python
from qtpie.menu import Separator

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
    ___: Separator  # Separator line
    quit_action: QAction = new("&Quit")
```

## Menu Sections

Use `Section` for labeled groups:

```python
from qtpie.menu import Section

@menu(text="&Edit")
class EditMenu(Menu):
    ___clipboard___: Section  # Shows as "Clipboard"
    cut_action: QAction = new("Cu&t")
    copy_action: QAction = new("&Copy")
    paste_action: QAction = new("&Paste")

    ___: Separator

    ___selection___: Section  # Shows as "Selection"
    select_all: QAction = new("Select &All")
```

## Adding Menus to Window

Menu fields are automatically added to the menu bar:

```python
@window(title="Editor")
class MainWindow(Window):
    file_menu: FileMenu = new()
    edit_menu: EditMenu = new()
    # Menu bar shows: File | Edit
```

## Menu with Record Type

```python
@dataclass
class Document:
    title: str = ""
    modified: bool = False

@menu(text="&File")
class FileMenu(Menu[Document]):
    save_action: QAction = new(enabled="{record.modified}")
```

## See Also

- [Widgets](../basics/widgets.md) - Widget fundamentals
- [Bindings](../state/bindings.md) - Data binding
- [Validation](../data/validation.md) - Form validation
- [App Guide](app.md) - Full application setup
