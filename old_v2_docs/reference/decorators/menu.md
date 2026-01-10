# @menu

Decorator for creating declarative `Menu` subclasses with automatic action management, Variable bindings, separators, sections, and dynamic action lists.

## Signature

```python
@menu
class FileMenu(Menu): ...

@menu(text="&File")
class FileMenu(Menu): ...

@menu(text="&File", name="file-menu", record=SomeRecord())
class FileMenu(Menu[SomeRecord]): ...
```

## Parameters

**`text`** (keyword)
:   Menu title text. Supports keyboard mnemonics with `&` (e.g., `"&File"`). If omitted, derived from class name (strips `"Menu"` suffix if present).

**`name`** (keyword)
:   Object name for CSS/QSS styling. Defaults to class name.

**`classes`** (keyword)
:   List of CSS class names for styling.

**`record`** (keyword)
:   Initial record value for `Menu[T]` record types.

## The Menu Base Class

Menus must inherit from `Menu`, not `QMenu`:

```python
from qtpie import Menu, menu, new

@menu(text="&File")
class FileMenu(Menu):  # Not QMenu!
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
```

`Menu` is a QtPie-enhanced `QMenu` that provides:

- Automatic action addition in declaration order
- Variable binding support
- Separator and Section markers
- Dynamic action lists (ActionRepeater)
- Checkable action two-way binding

## Automatic Title

If no `text` parameter is provided, the menu title is derived from the class name:

```python
@menu
class FileMenu(Menu):  # Title: "File"
    pass

@menu
class Edit(Menu):  # Title: "Edit" (no suffix to strip)
    pass
```

## Actions

Actions are declared as `QAction` fields with `new()`:

```python
from PySide6.QtGui import QAction

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New", shortcut="Ctrl+N")
    open_action: QAction = new("&Open", shortcut="Ctrl+O")
    save_action: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")

    def on_save(self) -> None:
        print("Save triggered")
```

### Action Options

- `text` (positional): Action text with mnemonics
- `shortcut`: Keyboard shortcut (e.g., `"Ctrl+S"`)
- `triggered`: Signal connection (method name or callable)
- `enabled`: Enable/disable (can be binding expression)
- `visible`: Show/hide (can be binding expression)
- `checkable`: Whether action can be toggled
- `checked`: Initial checked state or Variable binding
- `toggled`: Handler for toggle state changes
- `toolTip`: Tooltip text

## Separators

Use the `Separator` marker class to add visual separators:

```python
from qtpie import Menu, Separator, menu, new

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
    ____: Separator                       # Separator here
    save_action: QAction = new("&Save")
    _____: Separator                      # Another separator
    exit_action: QAction = new("E&xit")
```

Separator field names are arbitrary but must be unique. Convention: use underscores (`____`, `_____`, etc.).

## Sections

Use the `Section` marker class to add labeled section headers:

```python
from qtpie import Menu, Section, Separator, menu, new

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    ____: Separator

    ___recent___: Section                 # Text: "Recent"
    file1: QAction = new("file1.txt")
    file2: QAction = new("file2.txt")

    ___projects___: Section = new("Recent Projects")  # Explicit text
    project1: QAction = new("My Project")
```

Section naming:

- Format: `___text___` (leading and trailing triple underscores)
- Text extracted from name: `___recent___` → "Recent"
- Snake case converted: `___recent_files___` → "Recent Files"
- Override with `= new("Explicit Text")`

## Variables and Bindings

Menus support the same Variable system as widgets:

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)

    word_wrap: QAction = new(
        "Word Wrap",
        checkable=True,
        checked="_word_wrap"  # Two-way binding!
    )
```

### Required Bindings

Bare `Variable[T]` declarations (no `= new()`) are **required bindings** that must be provided by the parent Window:

```python
@menu(text="&File")
class FileMenu(Menu):
    is_dirty: Variable[bool]  # Required!
    save: QAction = new("&Save", enabled="{is_dirty}")

@window(title="App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new(is_dirty="_is_dirty")  # Provide binding
```

### Expression Bindings

Action properties can use expression bindings:

```python
@menu(text="&Edit")
class EditMenu(Menu):
    can_undo: Variable[bool]
    can_redo: Variable[bool]

    undo: QAction = new("&Undo", enabled="{can_undo}")
    redo: QAction = new("&Redo", enabled="{can_redo}")
```

## Checkable Actions

Create toggle actions with two-way Variable binding:

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)

    word_wrap: QAction = new(
        "Word Wrap",
        checkable=True,
        checked="_word_wrap"  # Two-way binding
    )
```

Changes to the Variable update the action's checked state, and toggling the action updates the Variable.

### Toggle Handler

Handle toggle events with `toggled=`:

```python
@menu(text="&View")
class ViewMenu(Menu):
    bold: QAction = new(
        "Bold",
        checkable=True,
        toggled="on_bold"
    )

    def on_bold(self, checked: bool) -> bool | None:
        """Handler receives checked state.

        Return False to refuse the toggle (reverts action).
        Return None (or nothing) to accept.
        """
        if not self.can_toggle():
            return False  # Refuse
        return None  # Accept
```

## Dynamic Action Lists

Create actions dynamically from a list using `list[QAction]`:

```python
@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[str]] = new(["Win1", "Win2"])

    tile: QAction = new("&Tile")
    cascade: QAction = new("&Cascade")
    ____: Separator

    window_actions: list[QAction] = new(
        bind="_windows",
        format="{#self}",           # Format for action text
        triggered="on_select"       # Handler receives the item
    )

    def on_select(self, window_name: str) -> None:
        print(f"Selected: {window_name}")
```

Dynamic actions sync automatically when the list changes (append, remove, etc.).

### Format Placeholders

- `{#self}` - The item itself
- `{#index}` - Item's index in the list
- `{property}` - Property access on the item

```python
@dataclass
class WindowInfo:
    title: str
    path: str

@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[WindowInfo]] = new([])
    window_actions: list[QAction] = new(
        bind="_windows",
        format="{#index}: {title}"  # "0: Main Window"
    )
```

## Menu[T] Record Support

Menus can use the `Menu[T]` pattern for record binding:

```python
from dataclasses import dataclass

@dataclass
class EditState:
    can_undo: bool = False
    can_redo: bool = False

@menu(text="&Edit", record=EditState())
class EditMenu(Menu[EditState]):
    undo: QAction = new("&Undo", enabled="{record.can_undo}")
    redo: QAction = new("&Redo", enabled="{record.can_redo}")
```

Access via `self.record`:

```python
def enable_undo(self) -> None:
    self.record.can_undo = True  # Reactive!
```

## The #parent Placeholder

Access the parent Window's variables with `#parent`:

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("&Save", enabled="{#parent._is_dirty}")

@window(title="App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new()  # No explicit binding needed
```

!!! tip "Prefer Variable Bindings"
    Variable bindings (`is_dirty="_is_dirty"`) make dependencies explicit and menus reusable. Use `#parent` as an escape hatch for tightly-coupled menus.

## Window Integration

Menu fields in `Window` classes are automatically added to the menu bar:

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")

@menu(text="&Edit")
class EditMenu(Menu):
    undo: QAction = new("&Undo")

@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()  # Added to menu bar
    edit_menu: EditMenu = new()  # Added to menu bar
```

Menus appear in declaration order.

## The `__setup__` Hook

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")

    def __setup__(self) -> None:
        # Actions are ready
        print(f"Menu has {len(self.actions())} actions")
        self.setToolTipsVisible(True)
```

## Complete Example

```python
from dataclasses import dataclass
from PySide6.QtGui import QAction
from qtpie import Menu, Section, Separator, Variable, Window, menu, new, window

@dataclass
class WindowInfo:
    title: str
    widget: QWidget

@menu(text="&File")
class FileMenu(Menu):
    # Required bindings from Window
    is_dirty: Variable[bool]
    recent_files: Variable[list[str]]

    new_action: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
    open_action: QAction = new("&Open", shortcut="Ctrl+O")
    ____: Separator
    save_action: QAction = new("&Save", shortcut="Ctrl+S", enabled="{is_dirty}")
    _____: Separator

    ___recent___: Section
    recent_actions: list[QAction] = new(
        bind="recent_files",
        format="{#self}",
        triggered="open_recent"
    )

    ______: Separator
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        print("New document")

    def open_recent(self, filename: str) -> None:
        print(f"Opening: {filename}")

    def on_exit(self) -> None:
        if parent := self.parent():
            parent.close()

@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(True)
    _line_numbers: Variable[bool] = new(True)

    word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")
    line_numbers: QAction = new("Line Numbers", checkable=True, checked="_line_numbers")

@window(title="My Editor")
class EditorWindow(Window):
    _is_dirty: Variable[bool] = new(False)
    _recent: Variable[list[str]] = new(["file1.txt", "file2.txt"])

    file_menu: FileMenu = new(is_dirty="_is_dirty", recent_files="_recent")
    view_menu: ViewMenu = new()
```

## See Also

- [Windows & Menus guide](../../guides/windows-menus.md) - Complete guide with examples
- [@window decorator](./window.md) - Window decorator reference
- [new() factory](../factories/new.md) - The `new()` factory
- [Variables](../../state/variables.md) - Variable system documentation
