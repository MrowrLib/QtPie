# Window Class

Base class for declarative main windows with menu bar support.

## Overview

`Window` extends `QMainWindow` with QtPie's declarative features. Like `Widget`, it provides:

- Automatic layout management for child widgets
- Reactive state via `Variable` fields
- Lifecycle hooks and validation
- Record binding for data models

Additionally, `Window` provides:

- Automatic menu bar population from `QMenu` fields
- Central widget management
- Support for `Widget[T]` record binding

## Basic Usage

```python
from qtpy.QtWidgets import QLabel, QPushButton
from qtpie import Window, new, window

@window(title="My App")
class MainWindow(Window):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me")
```

The `@window` decorator is required and handles initialization. Without it, the class will raise a `TypeError` on instantiation.

## Automatic Menu Bar

`QMenu` fields are automatically added to the window's menu bar:

```python
from qtpy.QtWidgets import QMenu, QLabel
from qtpy.QtGui import QAction
from qtpie import Window, new, window, menu

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", shortcut="Ctrl+N")
    open_action: QAction = new("&Open", shortcut="Ctrl+O")
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_exit(self) -> None:
        self.parent().close()

@window(title="Editor")
class EditorWindow(Window):
    file_menu: FileMenu = new()  # Auto-added to menu bar
    content: QLabel = new("Document content...")
```

Menus are added to the menu bar in declaration order. Fields starting with `_` are not added to the menu bar.

## Central Widget

### Automatic Central Widget

By default, `Window` creates a central widget with a layout containing all non-menu `QWidget` fields:

```python
@window(title="Dashboard", layout="vertical")
class Dashboard(Window):
    file_menu: FileMenu = new()  # Added to menu bar
    header: QLabel = new("Dashboard")  # Added to central widget
    content: QLabel = new("Content")   # Added to central widget
    footer: QLabel = new("Footer")     # Added to central widget
```

The central widget is created with the specified layout (default is `"vertical"`).

### Explicit Central Widget

Use a field named `central_widget` to provide your own central widget:

```python
@window(title="My App")
class MyWindow(Window):
    file_menu: FileMenu = new()
    central_widget: QLabel = new("I AM THE CENTRAL WIDGET")
```

When `central_widget` is defined, no automatic container is created. The specified widget becomes the window's central widget directly.

## Type Parameter: Window[T]

Windows can be parameterized with a record type, just like `Widget[T]`:

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QLineEdit, QSpinBox
from qtpie import Window, new, window

@dataclass
class Document:
    title: str = ""
    word_count: int = 0

@window(title="Document Editor", record=Document())
class DocumentWindow(Window[Document]):
    title: QLineEdit = new()       # Auto-binds to record.title
    word_count: QSpinBox = new()   # Auto-binds to record.word_count
```

The record system works identically to `Widget[T]`:
- Fields with matching names auto-bind to record properties
- The `record` property provides reactive access
- Changes propagate automatically between widgets and the record

## Properties

`Window` shares the same properties as `Widget`:

### view_model

Access all `Variable` fields:

```python
@window
class MyWindow(Window):
    _title: Variable[str] = new("")

    def check_dirty(self) -> None:
        if self.view_model.is_dirty:
            print("Window has unsaved changes")
```

### record (Window[T] only)

Access the record model:

```python
@window
class DocumentWindow(Window[Document]):
    def update_title(self) -> None:
        self.record.title = "New Document"
```

### record_state (Window[T] only)

Access the underlying `RecordVariable`:

```python
@window
class DocumentWindow(Window[Document]):
    def check_record(self) -> None:
        if self.record_state.is_dirty.get():
            print("Document modified")
```

## Validation

Windows support the same validation API as `Widget`:

```python
@window
class LoginWindow(Window):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_username", "required", lambda v: None if v else "Username required")
        self.add_validator("_password", "min_length", lambda v: None if len(v) >= 8 else "Min 8 chars")

    def on_login(self) -> None:
        if self.is_valid:
            print("Logging in...")
        else:
            print(self.validation_error_messages)
```

All validation methods are identical to `Widget`:
- `add_validator(field, name, fn)`
- `is_valid`
- `validation_errors`
- `validation_error_messages`

## Lifecycle Hooks

### __setup__

Called after initialization, before bindings:

```python
@window
class MyWindow(Window):
    label: QLabel = new("")

    def __setup__(self) -> None:
        self.label.setText("Window initialized!")
```

### on_valid_changed

Called when validation state transitions:

```python
@window
class FormWindow(Window):
    _name: Variable[str] = new("")
    _save: QPushButton = new("Save")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

    def on_valid_changed(self, is_valid: bool) -> None:
        self._save.setEnabled(is_valid)
```

### on_dirty_changed

Called when dirty state transitions:

```python
@window
class EditorWindow(Window):
    _content: Variable[str] = new("")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        # Update window title to show unsaved changes
        if is_dirty:
            self.setWindowTitle(f"{self.windowTitle()}*")
```

### on_close (async)

Async hook called when the window is closing:

```python
@window
class MainWindow(Window):
    async def on_close(self) -> None:
        # Save state before closing
        await self.save_document()
        print("Window closing...")
```

## Complete Example

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QMenu, QLineEdit, QTextEdit, QPushButton, QLabel
from qtpy.QtGui import QAction
from qtpie import Window, Variable, new, window, menu

@dataclass
class Document:
    filename: str = "untitled.txt"
    content: str = ""

@menu("&File")
class FileMenu(QMenu):
    new_doc: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
    open_doc: QAction = new("&Open", shortcut="Ctrl+O", triggered="on_open")
    sep1: QAction = separator()
    save: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")
    sep2: QAction = separator()
    exit_app: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        parent = self.parent()
        if isinstance(parent, DocumentWindow):
            parent.record.filename = "untitled.txt"
            parent.record.content = ""

    def on_open(self) -> None:
        print("Open file dialog...")

    def on_save(self) -> None:
        parent = self.parent()
        if isinstance(parent, DocumentWindow):
            print(f"Saving {parent.record.filename}...")

    def on_exit(self) -> None:
        self.parent().close()

@window(title="Text Editor", layout="form", record=Document())
class DocumentWindow(Window[Document]):
    # Menu bar
    file_menu: FileMenu = new()

    # Central widget fields
    filename: QLineEdit = new(label="Filename:")
    content: QTextEdit = new()

    # Status bar
    _status: QLabel = new("")
    _save_btn: QPushButton = new("Save", clicked="on_save")

    def __setup__(self) -> None:
        # Validators
        self.add_validator("filename", "required", lambda v: None if v else "Filename required")

        # Initial state
        self._save_btn.setEnabled(False)
        self.update_title()

    def update_title(self) -> None:
        dirty = "*" if self.view_model.is_dirty else ""
        self.setWindowTitle(f"{self.record.filename}{dirty} - Text Editor")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        self._save_btn.setEnabled(is_dirty)
        self.update_title()

    def on_valid_changed(self, is_valid: bool) -> None:
        if not is_valid:
            self._status.setText(", ".join(self.validation_error_messages))
        else:
            self._status.setText("")

    def on_save(self) -> None:
        if self.is_valid:
            print(f"Saving {self.record.filename}")
            self.view_model.reset_dirty()

    async def on_close(self) -> None:
        if self.view_model.is_dirty:
            # In real app, show confirmation dialog
            print("Unsaved changes!")
```

## Key Differences from Widget

| Feature | Widget | Window |
|---------|--------|--------|
| Base class | `QWidget` | `QMainWindow` |
| Menu support | No | Yes - auto-added to menu bar |
| Central widget | IS the widget | Created automatically or explicit |
| Typical use | Components, forms | Main application windows |

## See Also

- [@window decorator](../decorators/window.md) - Decorator configuration options
- [Widget class](widget.md) - Base widget class
- [Windows and Menus guide](../../guides/windows-menus.md) - Complete examples
- [@menu decorator](../decorators/menu.md) - Menu creation
- [separator() function](../factories/separator.md) - Menu separators
