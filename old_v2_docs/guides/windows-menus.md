# Windows & Menus

This guide covers building application windows with menu bars using QtPie's declarative patterns.

## Basic Window

Windows are defined using the `@window` decorator on a class inheriting from `Window`:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Window, new, window

@window(title="My Application")
class MainWindow(Window):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me")
```

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
- `minimumWidth`, `minimumHeight`: Minimum dimensions
- `stylesheet` or `styleSheet`: CSS styling
- `name`: Object name (defaults to class name)
- `classes`: CSS class names as a list

### Reactive Window Properties

Window properties can be reactive:

```python
@window(title="{_filename} - MyEditor")
class EditorWindow(Window):
    _filename: Variable[str] = new("untitled.txt")

    def open_file(self, path: str) -> None:
        self._filename.value = path  # Title updates automatically
```

## Creating Menus

Menus are created with the `@menu` decorator and the `Menu` base class:

```python
from PySide6.QtGui import QAction
from qtpie import Menu, menu, new

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New", shortcut="Ctrl+N")
    open_action: QAction = new("&Open", shortcut="Ctrl+O")
    save_action: QAction = new("&Save", shortcut="Ctrl+S")
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_exit(self) -> None:
        if parent := self.parent():
            parent.close()
```

!!! important
    Menus must inherit from `Menu`, not `QMenu`. The `Menu` class provides Variable bindings, separators, sections, and other QtPie features.

### Adding Menus to Windows

Menu fields in `Window` classes are automatically added to the menu bar:

```python
@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()  # Added to menu bar
    edit_menu: EditMenu = new()  # Added to menu bar
    content: QLabel = new("Content area")
```

Menus appear in declaration order. Non-menu widget fields go to the central widget layout.

## Separators

Use the `Separator` marker to add visual separators between actions:

```python
from qtpie import Menu, Separator, menu, new

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
    ____: Separator                       # Visual separator
    save_action: QAction = new("&Save")
    _____: Separator                      # Another separator
    exit_action: QAction = new("E&xit")
```

The separator field name is arbitrary but must be unique. Convention: use underscores.

## Sections

Use the `Section` marker to add labeled section headers:

```python
from qtpie import Menu, Section, Separator, menu, new

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    ____: Separator

    ___recent___: Section                 # Section with text "Recent"
    file1: QAction = new("file1.txt")
    file2: QAction = new("file2.txt")
```

Section text is derived from the field name (`___recent___` → "Recent") or can be set explicitly:

```python
___projects___: Section = new("Recent Projects")
```

## Passing State to Menus

Menus can receive state from their parent Window through Variable bindings. This is the recommended pattern for connecting menu actions to window state.

### Required Bindings

Declare a `Variable[T]` without a default value to create a required binding:

```python
@menu(text="&File")
class FileMenu(Menu):
    # Required - must be provided by parent Window
    is_dirty: Variable[bool]

    save_action: QAction = new("&Save", enabled="{is_dirty}")
```

The parent Window provides the binding when creating the menu:

```python
@window(title="Editor")
class EditorWindow(Window):
    _is_dirty: Variable[bool] = new(False)

    # Provide binding: FileMenu.is_dirty bound to EditorWindow._is_dirty
    file_menu: FileMenu = new(is_dirty="_is_dirty")
```

If you forget to provide a required binding, QtPie raises a clear error with instructions.

### Two-Way Bindings

Variable bindings are two-way. Changes on either side are reflected on both:

```python
@menu(text="&File")
class FileMenu(Menu):
    is_dirty: Variable[bool]
    save: QAction = new("&Save", enabled="{is_dirty}", triggered="on_save")

    def on_save(self) -> None:
        # Changes here update the Window's variable
        self.is_dirty.value = False

@window(title="Editor")
class EditorWindow(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new(is_dirty="_is_dirty")

    def make_edit(self) -> None:
        # Changes here update the Menu's variable
        self._is_dirty.value = True
```

### Optional Bindings

Variables with default values are optional - the parent can override them or use the default:

```python
@menu(text="&View")
class ViewMenu(Menu):
    # Optional - has default, can be overridden
    word_wrap: Variable[bool] = new(True)

    word_wrap_action: QAction = new(
        "Word Wrap", checkable=True, checked="word_wrap"
    )

@window(title="Editor")
class EditorWindow(Window):
    _word_wrap: Variable[bool] = new(False)

    # Override the default
    view_menu: ViewMenu = new(word_wrap="_word_wrap")

    # Or use the default
    # view_menu: ViewMenu = new()
```

## Checkable Actions

Create toggle actions with two-way Variable binding:

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(True)
    _line_numbers: Variable[bool] = new(True)

    word_wrap: QAction = new(
        "Word Wrap", checkable=True, checked="_word_wrap"
    )
    line_numbers: QAction = new(
        "Line Numbers", checkable=True, checked="_line_numbers"
    )
```

The Variable and action stay in sync:

- Changing the Variable updates the action's checked state
- Toggling the action updates the Variable

### Handling Toggle Events

Use `toggled=` to handle toggle events:

```python
bold: QAction = new("Bold", checkable=True, toggled="on_bold")

def on_bold(self, checked: bool) -> bool | None:
    """Called when action is toggled.

    Return False to refuse the toggle (reverts action).
    Return None (or don't return) to accept.
    """
    if not self.can_apply_bold():
        return False  # Refuse
    self.apply_bold(checked)
    return None  # Accept
```

## Dynamic Action Lists

Create actions dynamically from a list:

```python
@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[str]] = new([])

    tile: QAction = new("&Tile")
    cascade: QAction = new("&Cascade")
    ____: Separator

    # Dynamic actions - one per item in _windows
    window_actions: list[QAction] = new(
        bind="_windows",
        format="{#self}",           # Use item as action text
        triggered="on_select"       # Handler receives the item
    )

    def on_select(self, window_name: str) -> None:
        print(f"Selected: {window_name}")
```

Actions sync automatically when the list changes:

```python
menu._windows.append("Settings")  # Adds new action
menu._windows.remove("Main")      # Removes action
```

### Format Placeholders

- `{#self}` - The item itself (for primitives like `str`)
- `{#index}` - Item's index in the list
- `{property}` - Property access on the item

```python
from dataclasses import dataclass

@dataclass
class Document:
    title: str
    path: str

@menu(text="&File")
class FileMenu(Menu):
    _recent: Variable[list[Document]] = new([])

    ___recent___: Section
    recent_actions: list[QAction] = new(
        bind="_recent",
        format="{title}",           # Property access
        triggered="open_document"
    )

    def open_document(self, doc: Document) -> None:
        print(f"Opening: {doc.path}")
```

## The #parent Placeholder

As an escape hatch, you can access the parent Window's variables directly:

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("&Save", enabled="{#parent._is_dirty}")

@window(title="Editor")
class EditorWindow(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new()  # No explicit binding needed
```

!!! tip "Prefer Variable Bindings"
    Variable bindings make dependencies explicit and menus reusable across different windows. Use `#parent` only for menus tightly coupled to a specific window.

## Menu with Record Type

For menus with multiple related state values, use `Menu[T]`:

```python
from dataclasses import dataclass

@dataclass
class EditState:
    can_undo: bool = False
    can_redo: bool = False
    selection_active: bool = False

@menu(text="&Edit", record=EditState())
class EditMenu(Menu[EditState]):
    undo: QAction = new("&Undo", enabled="{record.can_undo}")
    redo: QAction = new("&Redo", enabled="{record.can_redo}")
    ____: Separator
    cut: QAction = new("Cu&t", enabled="{record.selection_active}")
    copy: QAction = new("&Copy", enabled="{record.selection_active}")
```

Access via `self.record`:

```python
def on_text_selected(self) -> None:
    self.record.selection_active = True  # Enables Cut/Copy
```

## Complete Example

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QAction
from qtpie import Menu, Section, Separator, Variable, Window, menu, new, window

@dataclass
class Document:
    title: str
    path: str

# ═══════════════════════════════════════════════════════════════
# File Menu
# ═══════════════════════════════════════════════════════════════

@menu(text="&File")
class FileMenu(Menu):
    # Required bindings from Window
    is_dirty: Variable[bool]
    recent_files: Variable[list[Document]]

    # Callbacks
    on_new_doc: Variable[Callable[[], None]]
    on_save_doc: Variable[Callable[[], None]]

    new_action: QAction = new("&New", shortcut="Ctrl+N", triggered="do_new")
    open_action: QAction = new("&Open", shortcut="Ctrl+O")
    ____: Separator
    save_action: QAction = new("&Save", shortcut="Ctrl+S",
                                enabled="{is_dirty}", triggered="do_save")
    _____: Separator

    ___recent___: Section
    recent_actions: list[QAction] = new(
        bind="recent_files",
        format="{title}",
        triggered="open_recent"
    )

    ______: Separator
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def do_new(self) -> None:
        self.on_new_doc.value()

    def do_save(self) -> None:
        self.on_save_doc.value()

    def open_recent(self, doc: Document) -> None:
        print(f"Opening: {doc.path}")

    def on_exit(self) -> None:
        if parent := self.parent():
            parent.close()

# ═══════════════════════════════════════════════════════════════
# Edit Menu
# ═══════════════════════════════════════════════════════════════

@menu(text="&Edit")
class EditMenu(Menu):
    can_undo: Variable[bool]
    can_redo: Variable[bool]

    undo: QAction = new("&Undo", shortcut="Ctrl+Z", enabled="{can_undo}")
    redo: QAction = new("&Redo", shortcut="Ctrl+Y", enabled="{can_redo}")
    ____: Separator
    cut: QAction = new("Cu&t", shortcut="Ctrl+X")
    copy: QAction = new("&Copy", shortcut="Ctrl+C")
    paste: QAction = new("&Paste", shortcut="Ctrl+V")

# ═══════════════════════════════════════════════════════════════
# View Menu
# ═══════════════════════════════════════════════════════════════

@menu(text="&View")
class ViewMenu(Menu):
    # Optional bindings with defaults
    word_wrap: Variable[bool] = new(True)
    line_numbers: Variable[bool] = new(True)

    word_wrap_action: QAction = new(
        "Word Wrap", checkable=True, checked="word_wrap"
    )
    line_numbers_action: QAction = new(
        "Line Numbers", checkable=True, checked="line_numbers"
    )

# ═══════════════════════════════════════════════════════════════
# Main Window
# ═══════════════════════════════════════════════════════════════

@window(title="{_filename} - Text Editor", minimumWidth=800, minimumHeight=600)
class EditorWindow(Window):
    # State
    _filename: Variable[str] = new("untitled.txt")
    _is_dirty: Variable[bool] = new(False)
    _can_undo: Variable[bool] = new(False)
    _can_redo: Variable[bool] = new(False)
    _recent: Variable[list[Document]] = new([
        Document("readme.txt", "/docs/readme.txt"),
        Document("config.yml", "/config/config.yml"),
    ])
    _word_wrap: Variable[bool] = new(True)

    # Menus with bindings
    file_menu: FileMenu = new(
        is_dirty="_is_dirty",
        recent_files="_recent",
        on_new_doc="new_document",
        on_save_doc="save_document",
    )
    edit_menu: EditMenu = new(
        can_undo="_can_undo",
        can_redo="_can_redo",
    )
    view_menu: ViewMenu = new(
        word_wrap="_word_wrap",
    )

    # Central widget
    editor: QTextEdit = new()

    def __setup__(self) -> None:
        self.editor.textChanged.connect(self.on_text_changed)

    def on_text_changed(self) -> None:
        self._is_dirty.value = True
        self._can_undo.value = self.editor.document().isUndoAvailable()
        self._can_redo.value = self.editor.document().isRedoAvailable()

    def new_document(self) -> None:
        self.editor.clear()
        self._filename.value = "untitled.txt"
        self._is_dirty.value = False

    def save_document(self) -> None:
        print(f"Saving: {self._filename.value}")
        self._is_dirty.value = False
```

## Submenus

Create submenus by nesting Menu fields:

```python
@menu(text="Recent")
class RecentMenu(Menu):
    file1: QAction = new("document1.txt")
    file2: QAction = new("document2.txt")
    ____: Separator
    clear: QAction = new("Clear Recent")

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    recent: RecentMenu = new()  # Submenu
    ____: Separator
    exit_action: QAction = new("E&xit")
```

## Key Differences from Widget

| Feature | Widget | Window |
|---------|--------|--------|
| Base class | `QWidget` | `QMainWindow` |
| Menu fields | Go to layout | Go to menu bar |
| Widget fields | Go to layout | Go to central widget |
| Layout target | The widget | The central widget |

All other features (Variables, bindings, validation, dirty tracking) work identically.

## See Also

- [@menu decorator](../reference/decorators/menu.md) - Complete menu reference
- [@window decorator](../reference/decorators/window.md) - Window decorator reference
- [Variables](../state/variables.md) - Variable system documentation
- [Bindings](../state/bindings.md) - Data binding details
