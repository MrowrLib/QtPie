# Windows & Menus

The `Window` class and `@window` decorator provide declarative patterns for building application windows with menu bars. `Window` inherits from `QMainWindow` and automatically manages central widgets, layouts, and menu integration.

## Basic Window

Windows are defined using the `@window` decorator on a class inheriting from `Window`:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Window, new, window

@window
class MainWindow(Window):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me")
```

The `@window` decorator is required. Attempting to instantiate a `Window` subclass without the decorator raises a `TypeError`.

### Window Properties

Set window properties via decorator parameters:

```python
@window(
    title="My Application",
    minimumWidth=800,
    minimumHeight=600
)
class MainWindow(Window):
    label: QLabel = new("Content")
```

Common window properties:
- `title` or `windowTitle`: Window title text
- `minimumWidth`, `minimumHeight`: Minimum window dimensions
- `stylesheet` or `styleSheet`: CSS styling
- `name`: Object name (defaults to class name)
- `classes`: CSS class names as a list

```python
@window(
    title="Editor",
    stylesheet="background: #f0f0f0;",
    classes=["main-window", "dark-theme"]
)
class EditorWindow(Window):
    pass
```

### Reactive Window Properties

Window properties can be reactive by referencing Variables in format strings:

```python
@window(title="{_filename} - MyEditor")
class EditorWindow(Window):
    _filename: Variable[str] = new("untitled.txt")

    def open_file(self, path: str) -> None:
        self._filename.value = path  # Window title updates automatically
```

Expressions work too:

```python
@window(title="{_app_name.upper()} - Editor")
class EditorWindow(Window):
    _app_name: Variable[str] = new("MyApp")
```

## Central Widget Layout

By default, `Window` creates a central widget with a vertical layout and adds all non-menu widget fields to it.

### Layout Types

Specify layout type with the `layout=` parameter:

```python
@window(layout="horizontal")  # QHBoxLayout
class HorizontalWindow(Window):
    left: QLabel = new("Left")
    right: QLabel = new("Right")
```

Available layouts:
- `"vertical"` (default): `QVBoxLayout`
- `"horizontal"`: `QHBoxLayout`
- `"form"`: `QFormLayout` (use `label=` on fields)
- `"grid"`: `QGridLayout` (use `grid=` on fields)
- `None`: No layout (manual control)

### Form Layout

```python
@window(layout="form")
class SettingsWindow(Window):
    username: QLineEdit = new(label="Username:")
    password: QLineEdit = new(label="Password:")
    email: QLineEdit = new(label="Email:")
```

### Grid Layout

```python
@window(layout="grid")
class CalculatorWindow(Window):
    display: QLabel = new("0", grid=(0, 0, 1, 4))  # row, col, rowspan, colspan
    btn7: QPushButton = new("7", grid=(1, 0))
    btn8: QPushButton = new("8", grid=(1, 1))
    btn9: QPushButton = new("9", grid=(1, 2))
```

### Layout Margins

Control layout margins:

```python
@window(margins=10)  # All sides
class Window1(Window):
    pass

@window(margins=(5, 10, 5, 10))  # left, top, right, bottom
class Window2(Window):
    pass
```

### Excluding from Layout

Exclude specific widgets from the layout:

```python
@window
class MainWindow(Window):
    visible: QLabel = new("In layout")
    hidden: QLabel = new("Not in layout", layout=False)
```

The `hidden` widget exists as an attribute but isn't added to the central widget's layout.

## Explicit Central Widget

Use `central_widget` as a field name to set the central widget directly:

```python
@window
class MainWindow(Window):
    central_widget: MyCustomWidget = new()
```

When `central_widget` is defined, no automatic layout container is created, and other widget fields are not added to any layout (though they still exist as attributes).

### Variable as Central Widget

```python
@window
class MainWindow(Window):
    central_widget: Variable[str, QLabel] = new("Hello")(bind="{#self.upper()}")
```

The Variable's widget becomes the central widget.

## Menus and Menu Bar

`QMenu` fields are automatically added to the window's menu bar in declaration order.

### Basic Menu

Use the `@menu` decorator to create menus:

```python
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from qtpie import Window, menu, new, window

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
    open_action: QAction = new("&Open", shortcut="Ctrl+O", triggered="on_open")
    sep1: QAction = separator()
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        print("New file")

    def on_open(self) -> None:
        print("Open file")

    def on_exit(self) -> None:
        print("Exit")

@window
class MainWindow(Window):
    file_menu: FileMenu = new()
    label: QLabel = new("Content area")
```

Menus go to the menu bar, widgets go to the central widget layout.

### Multiple Menus

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")

@menu("&Edit")
class EditMenu(QMenu):
    undo_action: QAction = new("&Undo")
    redo_action: QAction = new("&Redo")

@menu("&Help")
class HelpMenu(QMenu):
    about_action: QAction = new("&About")

@window
class MainWindow(Window):
    file_menu: FileMenu = new()
    edit_menu: EditMenu = new()
    help_menu: HelpMenu = new()
```

Menus appear in the order they're declared.

### Submenus

Nest `QMenu` fields to create submenus:

```python
@menu
class RecentMenu(QMenu):
    file1: QAction = new("file1.txt")
    file2: QAction = new("file2.txt")

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")
    recent: RecentMenu = new()  # Submenu
```

### Menu Separators

Use `separator()` to add separators:

```python
from qtpie import separator

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
    sep1: QAction = separator()  # Visual separator
    save_action: QAction = new("&Save")
    sep2: QAction = separator()
    exit_action: QAction = new("E&xit")
```

### Menu Actions

Actions in menus support standard QAction features:

```python
@menu("&Edit")
class EditMenu(QMenu):
    # With shortcut
    undo: QAction = new("&Undo", shortcut="Ctrl+Z", triggered="on_undo")

    # Checkable action
    word_wrap: QAction = new("Word Wrap", checkable=True)

    # With tooltip (also sets status tip)
    find: QAction = new("&Find", shortcut="Ctrl+F", tooltip="Find text in document")

    def on_undo(self) -> None:
        print("Undo")
```

Fields starting with underscore (`_`) are not added to the menu (useful for private state).

## Window with Record Type

Windows can be parameterized with a record type (`Window[T]`) to bind fields to a data structure:

```python
from dataclasses import dataclass

@dataclass
class AppSettings:
    theme: str = "light"
    auto_save: bool = True
    font_size: int = 12

@window(record=AppSettings())
class SettingsWindow(Window[AppSettings]):
    theme: QLineEdit = new()  # Auto-binds to record.theme
    auto_save: QCheckBox = new()  # Auto-binds to record.auto_save
    font_size: QSpinBox = new()  # Auto-binds to record.font_size
```

The `record=` decorator parameter sets the initial record value. Fields with matching names automatically bind to record properties.

Access the record via `self.record`:

```python
@window(record=AppSettings())
class SettingsWindow(Window[AppSettings]):
    def apply_settings(self) -> None:
        print(f"Theme: {self.record.theme}")
        print(f"Auto-save: {self.record.auto_save}")
```

The record supports dirty tracking:

```python
def check_unsaved_changes(self) -> bool:
    if self.record_state.is_dirty.get():
        print("Unsaved changes detected!")
        return True
    return False
```

## Variables in Windows

Windows support all Variable features from `Widget`:

```python
@window
class CounterWindow(Window):
    _count: Variable[int] = new(0)
    _name: Variable[str, QLineEdit] = new("")

    label: QLabel = new(bind="Count: {_count}, Name: {_name}")
    increment: QPushButton = new("Increment", clicked="on_increment")

    def on_increment(self) -> None:
        self._count += 1
```

All binding expressions, format strings, property bindings (`visible=`, `enabled=`), and repeaters work identically to `Widget`.

Use `#window` placeholder in bindings to reference the window instance:

```python
@window(title="My App")
class MainWindow(Window):
    label: QLabel = new(bind="Title: {#window.windowTitle()}")
```

(`#window` is an alias for `#widget`)

## Signal Connections

Connect widget signals declaratively:

```python
@window
class MainWindow(Window):
    save_btn: QPushButton = new("Save", clicked="on_save")
    input: QLineEdit = new(textChanged="on_text_changed")

    def on_save(self) -> None:
        print("Save clicked")

    def on_text_changed(self, text: str) -> None:
        print(f"Text changed: {text}")
```

Or use lambdas:

```python
@window
class MainWindow(Window):
    button: QPushButton = new("Click", clicked=lambda: print("Clicked!"))
```

## Lifecycle Hooks

### `__setup__` Hook

Called after window initialization, after menus are added to the menu bar:

```python
@window
class MainWindow(Window):
    _count: Variable[int] = new(0)
    label: QLabel = new("")

    def __setup__(self) -> None:
        # Widgets are ready, menus are in menu bar
        self.label.setText(f"Count: {self._count.value}")

        # Can access menu bar
        print(f"Menu count: {len(self.menuBar().actions())}")
```

### Dirty Tracking Hooks

`on_dirty_changed` fires when the window's dirty state transitions:

```python
@window
class EditorWindow(Window):
    _content: Variable[str] = new("")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        # Update window title or save button state
        title = "Editor" + (" *" if is_dirty else "")
        self.setWindowTitle(title)
```

Access dirty state:

```python
def check_dirty(self) -> None:
    if self.view_model.is_dirty:
        print(f"Modified fields: {self.view_model.dirty_fields}")

    # Reset dirty state
    self.view_model.reset_dirty()
```

### Validation Hooks

`on_valid_changed` fires when validation state transitions:

```python
@window
class FormWindow(Window):
    _name: Variable[str] = new("")
    _email: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_email", "format", lambda v: None if "@" in v else "Invalid email")

    def on_valid_changed(self, is_valid: bool) -> None:
        self.submit_btn.setEnabled(is_valid)
```

Access validation state:

```python
def submit(self) -> None:
    if not self.is_valid:
        print(self.validation_error_messages)  # Flat list of errors
        print(self.validation_errors)  # Nested dict: {field: {validator: [errors]}}
        return
    # Process form...
```

## Complete Example

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit, QTextEdit, QPushButton, QLabel
from PySide6.QtGui import QAction
from qtpie import Window, Variable, menu, new, separator, window

@dataclass
class Document:
    filename: str = "untitled.txt"
    content: str = ""

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
    open_action: QAction = new("&Open", shortcut="Ctrl+O", triggered="on_open")
    sep1: QAction = separator()
    save_action: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")
    sep2: QAction = separator()
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        # Access parent window via Qt parent mechanism
        window = self.parent()
        if window:
            window.new_document()

    def on_open(self) -> None:
        print("Open dialog")

    def on_save(self) -> None:
        window = self.parent()
        if window:
            window.save_document()

    def on_exit(self) -> None:
        self.parent().close()

@menu("&Edit")
class EditMenu(QMenu):
    undo: QAction = new("&Undo", shortcut="Ctrl+Z")
    redo: QAction = new("&Redo", shortcut="Ctrl+Y")

@window(
    title="{filename} - Text Editor",
    minimumWidth=800,
    minimumHeight=600,
    record=Document()
)
class EditorWindow(Window[Document]):
    # Menus
    file_menu: FileMenu = new()
    edit_menu: EditMenu = new()

    # Status bar
    status: QLabel = new(bind="Lines: {len(content.split('\\n'))}")

    # Central widget (the text editor)
    central_widget: QTextEdit = new()

    def __setup__(self) -> None:
        # Bind text editor to record
        from qtpie import bind
        bind(self.record_state.content).to(self.central_widget)

        # Validators
        self.add_validator("content", "not_empty", lambda v: None if v.strip() else "Document is empty")

        # Add status bar
        self.statusBar().addWidget(self.status)

    def new_document(self) -> None:
        if self.record_state.is_dirty.get():
            # Prompt to save...
            pass
        self.record.filename = "untitled.txt"
        self.record.content = ""
        self.record_state.reset_dirty()

    def save_document(self) -> None:
        # Save logic...
        print(f"Saving {self.record.filename}")
        self.record_state.reset_dirty()

    def on_dirty_changed(self, is_dirty: bool) -> None:
        # Update window title with dirty indicator
        title_base = f"{self.record.filename} - Text Editor"
        self.setWindowTitle(title_base + (" *" if is_dirty else ""))
```

## Key Differences from Widget

1. `Window` uses `QMainWindow` instead of `QWidget`
2. QMenu fields auto-add to menu bar
3. Non-menu widget fields go to central widget layout (unless `central_widget` is defined)
4. Default layout is on the central widget, not the window itself
5. `__setup__` is called after menu bar setup

All other features (Variables, bindings, validation, dirty tracking) work identically to `Widget`.
