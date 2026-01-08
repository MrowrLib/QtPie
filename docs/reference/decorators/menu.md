# @menu

Decorator for creating declarative `QMenu` subclasses with automatic action and submenu management.

## Signature

```python
@menu(text: str | None = None) -> type[QMenu]
```

## Parameters

**`text`** (positional or keyword)
- Menu title text
- Supports keyboard mnemonics with `&` (e.g., `"&File"`)
- Default: Derived from class name (strips `"Menu"` suffix if present)

## Behavior

### Automatic Title

If no `text` parameter is provided, the menu title is derived from the class name:

```python
@menu
class FileMenu(QMenu):  # Title: "File"
    pass

@menu
class Edit(QMenu):  # Title: "Edit" (no suffix to strip)
    pass
```

### Automatic Action Addition

All `QAction` fields are automatically added to the menu via `addAction()` in declaration order:

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")     # Added first
    open_action: QAction = new("&Open")   # Added second
    exit_action: QAction = new("E&xit")   # Added third
```

Fields starting with underscore (`_`) are NOT added to the menu (useful for private state or helper actions).

### Automatic Submenu Addition

All `QMenu` fields are automatically added as submenus via `addMenu()`:

```python
@menu
class RecentMenu(QMenu):
    file1: QAction = new("file1.txt")
    file2: QAction = new("file2.txt")

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")
    recent: RecentMenu = new()  # Submenu added here
```

### Initialization Order

1. `QMenu.__init__()` called with title
2. All field descriptors initialized
3. Actions added to menu in order
4. Submenus added to menu in order
5. `__setup__()` hook called (if defined)

## Usage in Windows

`QMenu` fields in `Window` classes are automatically added to the menu bar:

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")

@menu("&Edit")
class EditMenu(QMenu):
    undo: QAction = new("&Undo")

@window
class MainWindow(Window):
    file_menu: FileMenu = new()  # Added to menu bar
    edit_menu: EditMenu = new()  # Added to menu bar
```

## Examples

### Basic Menu

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", shortcut="Ctrl+N")
    open_action: QAction = new("&Open", shortcut="Ctrl+O")
    exit_action: QAction = new("E&xit")
```

### Menu with Title from Class Name

```python
@menu
class FileMenu(QMenu):  # Title: "File"
    pass

@menu
class Edit(QMenu):  # Title: "Edit"
    pass
```

### Menu with Separators

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

### Menu with Signal Connections

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", triggered="on_new")
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        print("New file")

    def on_exit(self) -> None:
        # Access parent window
        window = self.parent()
        if window:
            window.close()
```

### Menu with Submenus

```python
@menu
class RecentMenu(QMenu):  # Title: "Recent"
    file1: QAction = new("document1.txt")
    file2: QAction = new("document2.txt")
    clear: QAction = separator()
    clear_action: QAction = new("Clear Recent")

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")
    recent: RecentMenu = new()  # Submenu
    sep: QAction = separator()
    exit_action: QAction = new("E&xit")
```

### Menu with Private Actions

```python
@menu("&Edit")
class EditMenu(QMenu):
    undo: QAction = new("&Undo")       # Added to menu
    redo: QAction = new("&Redo")       # Added to menu
    _helper: QAction = new("Helper")   # NOT added (underscore prefix)

    def __setup__(self) -> None:
        # Can still use _helper programmatically
        self._helper.triggered.connect(self.on_helper)

    def on_helper(self) -> None:
        print("Helper action")
```

### Menu with Action Configuration

```python
@menu("&Edit")
class EditMenu(QMenu):
    # With shortcut
    undo: QAction = new("&Undo", shortcut="Ctrl+Z", triggered="on_undo")

    # Checkable action
    word_wrap: QAction = new("Word Wrap", checkable=True)

    # With tooltip (also sets status tip)
    find: QAction = new("&Find", shortcut="Ctrl+F", tooltip="Find text")

    def on_undo(self) -> None:
        print("Undo")
```

### Menu with `__setup__` Hook

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")
    recent_menu: RecentMenu = new()

    def __setup__(self) -> None:
        # Actions and submenus are ready
        print(f"Menu has {len(self.actions())} actions")

        # Can perform additional configuration
        self.setToolTipsVisible(True)
```

### Complete Example in Window

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
    open_action: QAction = new("&Open", shortcut="Ctrl+O", triggered="on_open")
    sep1: QAction = separator()
    save_action: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")
    save_as_action: QAction = new("Save &As...", triggered="on_save_as")
    sep2: QAction = separator()
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        window = self.parent()
        if hasattr(window, 'new_document'):
            window.new_document()

    def on_open(self) -> None:
        print("Open file dialog")

    def on_save(self) -> None:
        print("Save file")

    def on_save_as(self) -> None:
        print("Save as dialog")

    def on_exit(self) -> None:
        self.parent().close()

@menu("&Edit")
class EditMenu(QMenu):
    undo: QAction = new("&Undo", shortcut="Ctrl+Z")
    redo: QAction = new("&Redo", shortcut="Ctrl+Y")
    sep: QAction = separator()
    cut: QAction = new("Cu&t", shortcut="Ctrl+X")
    copy: QAction = new("&Copy", shortcut="Ctrl+C")
    paste: QAction = new("&Paste", shortcut="Ctrl+V")

@window(title="Text Editor")
class EditorWindow(Window):
    file_menu: FileMenu = new()
    edit_menu: EditMenu = new()

    editor: QTextEdit = new()

    def new_document(self) -> None:
        self.editor.clear()
```

## Action Declaration

Actions are created with `new()` and support:

- `text`: Action text with keyboard mnemonics
- `shortcut`: Keyboard shortcut (e.g., `"Ctrl+S"`)
- `triggered`: Signal connection (method name or callable)
- `checkable`: Whether action can be toggled
- `tooltip`: Tooltip text (also sets status tip)
- `icon`: Action icon

See [@action decorator](./action.md) for declarative action classes.

## Separators

Use `separator()` to create visual separators between menu items:

```python
from qtpie import separator

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")
    sep: QAction = separator()  # Creates separator action
    exit_action: QAction = new("E&xit")
```

## Keyboard Mnemonics

Use `&` before a letter to create keyboard mnemonics:

```python
@menu("&File")  # Alt+F activates menu
class FileMenu(QMenu):
    new_action: QAction = new("&New")   # N key in menu
    open_action: QAction = new("&Open")  # O key in menu
```

## See Also

- [Windows & Menus guide](../../guides/windows-menus.md)
- [@window decorator](./window.md)
- [@action decorator](./action.md)
- [new() factory](../factories/new.md)
- [separator() factory](../factories/separator.md)
