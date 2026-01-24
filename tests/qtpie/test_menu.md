# QtPie Menu System Usage Patterns

This document captures conventions and usage patterns for the QtPie `@menu` decorator and `Menu` base class.

---

## Basic Menu Declaration

Menus inherit from `Menu` and use the `@menu` decorator. The menu title is derived from the class name (`FileMenu` -> `"File"`).

```python
@menu
class FileMenu(Menu):
    pass
```

### Explicit Title with Mnemonics

Use `text=` for explicit titles with keyboard mnemonics (`&`).

```python
@menu(text="&File")
class MyMenu(Menu):
    pass
```

### Object Name

The `name=` parameter sets the Qt `objectName`.

```python
@menu(name="file-menu")
class FileMenu(Menu):
    pass
```

---

## QAction Fields

Actions are declared as class attributes with `new()` factory.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
```

### Keyboard Shortcuts

```python
new_action: QAction = new("&New", shortcut="Ctrl+N")
```

### Signal Handlers

Connect `triggered` to a method by name or lambda.

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("&Save", triggered="on_save")

    def on_save(self) -> None:
        print("Saved!")
```

---

## Separators

Use `Separator` type annotation with underscore-named fields.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    ____: Separator  # Creates visual separator
    exit_action: QAction = new("E&xit")
```

Multiple separators use unique names: `_1: Separator`, `_2: Separator`, etc.

---

## Sections

Sections are labeled groups. Use triple underscores around the name: `___name___`.

```python
@menu(text="&File")
class FileMenu(Menu):
    ___recent___: Section  # Displays as "Recent"
    file1: QAction = new("file1.txt")
```

### Snake Case Conversion

`___recent_files___` becomes `"Recent Files"`.

### Explicit Section Text

```python
___recent___: Section = new("Recent Files")
```

---

## Checkable Actions

Toggle actions with `checkable=True`.

```python
@menu(text="&View")
class ViewMenu(Menu):
    word_wrap: QAction = new("Word Wrap", checkable=True, checked=True)
```

### Two-Way Binding to Variable

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)
    word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")
```

### Toggle Handler

```python
word_wrap: QAction = new("Word Wrap", checkable=True, toggled="on_toggle")

def on_toggle(self, checked: bool) -> None:
    print(f"Wrap: {checked}")
```

---

## Variables in Menus

Menus support `Variable[T]` for reactive state.

```python
@menu(text="&View")
class ViewMenu(Menu):
    _dark_mode: Variable[bool] = new(False)  # Optional (has default)
```

### Required Bindings

Bare `Variable[T]` (no `= new()`) is a required binding that must be provided by parent.

```python
@menu(text="&File")
class FileMenu(Menu):
    doc_dirty: Variable[bool]  # Required from parent
    save: QAction = new("&Save", enabled="{doc_dirty}")
```

---

## Window Integration

Menus are auto-added to `Window` menu bars.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")

@window(title="Test App")
class App(Window):
    file_menu: FileMenu = new()  # Added to menu bar
```

### Passing Bindings to Menu

```python
@window(title="App")
class App(Window):
    _doc_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new(doc_dirty="_doc_dirty")  # Binds required Variable
```

### Parent Placeholder

Use `{#parent._variable}` to access parent window variables directly.

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("Save", enabled="{#parent._is_dirty}")
```

---

## Dynamic Action Lists (ActionRepeater)

Bind `list[QAction]` to a `Variable[list[T]]` for dynamic menus.

```python
@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[str]] = new(["Win1", "Win2"])
    window_actions: list[QAction] = new(bind="_windows")
```

### Format Placeholders

- `{#self}` - item value
- `{#index}` - item index

```python
window_actions: list[QAction] = new(bind="_windows", format="Open {#self}")
window_actions: list[QAction] = new(bind="_windows", format="{#index}: {#self}")
```

### Triggered Handler with Item

```python
window_actions: list[QAction] = new(bind="_windows", triggered="on_window_select")

def on_window_select(self, item: str) -> None:
    print(f"Selected: {item}")
```

---

## Menu[T] Record Support

Menus can have a typed record like widgets.

```python
@dataclass
class EditState:
    can_undo: bool = False

@menu(text="&Edit", record=EditState())
class EditMenu(Menu[EditState]):
    undo: QAction = new("Undo", enabled="{record.can_undo}")
```

---

## Signal-to-Signal Connections

Action signals can emit custom signals.

```python
from qtpy.QtCore import Signal

@menu(text="&File")
class FileMenu(Menu):
    file_requested = Signal()
    new_action: QAction = new("&New", triggered="file_requested")
```

### Expression-Based Signal Handlers

Use `{expression}` syntax for inline signal calls.

```python
@menu(text="&File")
class FileMenu(Menu):
    custom_signal = Signal(int)
    action: QAction = new("Action", triggered="{custom_signal(123)}")
```

---

## Dirty Tracking

Menus track variable changes with `is_dirty`, `dirty_fields`, and `reset_dirty()`.

```python
@menu(text="&File")
class FileMenu(Menu):
    _count: Variable[int] = new(0)

# Usage:
m._count.value = 42
m.is_dirty.get()      # True
m.dirty_fields        # {"_count"}
m.reset_dirty()       # Clears dirty state
```

### Lifecycle Hook

```python
def on_dirty_changed(self, is_dirty: bool) -> None:
    self.save_btn.setEnabled(is_dirty)
```

---

## Validation

Add validators with `add_validator(field, name, fn)`.

```python
@menu(text="&File")
class FileMenu(Menu):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
```

### Validation Properties

- `is_valid` - Observable[bool] aggregate validity
- `validation_errors` - `{field: {validator: [messages]}}`
- `validation_error_messages` - Observable[list[str]] flat list

### Lifecycle Hook

```python
def on_valid_changed(self, is_valid: bool) -> None:
    self.submit_btn.setEnabled(is_valid)
```

---

## The `ref()` Helper

Use `ref()` for reactive text that combines literals with expressions.

```python
from qtpie import ref

@menu(text="&Dog")
class DogMenu(Menu):
    dog: Variable[Dog]
    dog_action: QAction = new(text=ref("Dog name: {dog.name}"))
```

---

## Setup Lifecycle

The `__setup__` method runs after menu initialization, when all actions are ready.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")

    def __setup__(self) -> None:
        # Actions are available here
        self.new_action.setEnabled(False)
```
