# Windows & Menus

QtPie makes creating application windows with menu bars completely declarative. Use `@window` for main windows, `@menu` for menu bars, and `@action` for menu items.

## Creating a Window

The `@window` decorator transforms a class into a `QMainWindow`:

```python
from qtpie import window, make
from qtpy.QtWidgets import QMainWindow, QTextEdit

@window(title="My App", size=(800, 600))
class MainWindow(QMainWindow):
    central_widget: QTextEdit = make(QTextEdit)
```

### Window Parameters

```python
@window(
    title="Text Editor",       # Window title
    size=(1024, 768),          # Width x height in pixels
    center=True,               # Center on screen
    icon="app.png",            # Path to icon file
    name="EditorWindow",       # Object name for QSS
    classes=["dark", "modern"] # CSS-like classes for styling
)
class EditorWindow(QMainWindow):
    ...
```

### Central Widget

Any field named `central_widget` is automatically set as the window's central widget:

```python
@window(title="Editor")
class EditorWindow(QMainWindow):
    central_widget: QTextEdit = make(QTextEdit)
    # Automatically calls self.setCentralWidget(self.central_widget)
```

### Auto-Naming

If you don't specify `title` or `name`, QtPie derives them from your class name:

```python
@window  # title="Editor", objectName="Editor"
class EditorWindow(QMainWindow):
    ...

@window  # title="Main", objectName="Main"
class MainWindow(QMainWindow):
    ...
```

The "Window" suffix is automatically stripped.

## Creating Menus

The `@menu` decorator transforms a class into a `QMenu`. Menus automatically add their actions and submenus in declaration order.

### Basic Menu

```python
from qtpie import menu, action, make
from qtpy.QtWidgets import QMenu
from qtpy.QtGui import QAction

@action("&New", shortcut="Ctrl+N")
class NewAction(QAction):
    def on_triggered(self) -> None:
        print("New file")

@action("E&xit", shortcut="Ctrl+Q")
class ExitAction(QAction):
    def on_triggered(self) -> None:
        print("Exit")

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    exit_app: ExitAction = make(ExitAction)
```

### Auto-Adding to Menu Bar

When you add a `QMenu` field to a `@window`, it's automatically added to the menu bar:

```python
from dataclasses import field

@window(title="My App")
class MainWindow(QMainWindow):
    file_menu: FileMenu = make(FileMenu)
    edit_menu: QMenu = field(default_factory=lambda: QMenu("&Edit"))
    # Both menus appear in the menu bar automatically
```

### Submenus

Menu fields can contain other menus as submenus:

```python
@menu("&Recent Files")
class RecentMenu(QMenu):
    pass

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    recent: RecentMenu = make(RecentMenu)  # Appears as submenu
    exit_app: ExitAction = make(ExitAction)
```

### Menu Separators

Use `separator()` to add visual separators between menu items:

```python
from qtpie import separator

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open_file: OpenAction = make(OpenAction)
    sep1: QAction = separator()  # Visual separator
    exit_app: ExitAction = make(ExitAction)
```

### Auto-Naming Menus

Like windows, menus auto-derive their title from the class name:

```python
@menu  # title="File"
class FileMenu(QMenu):
    ...

@menu  # title="Edit"
class EditMenu(QMenu):
    ...
```

The "Menu" suffix is automatically stripped.

## Creating Actions

The `@action` decorator transforms a class into a `QAction`. Actions represent menu items, toolbar buttons, and keyboard shortcuts.

### Basic Action

```python
from qtpie import action
from qtpy.QtGui import QAction

@action("&New File", shortcut="Ctrl+N", tooltip="Create a new file")
class NewAction(QAction):
    def on_triggered(self) -> None:
        print("Creating new file...")
```

### Action Parameters

```python
@action(
    text="&Save",                      # Menu text (& for keyboard shortcut)
    shortcut="Ctrl+S",                # Keyboard shortcut
    tooltip="Save the current file",  # Tooltip and status bar text
    icon="save.png",                  # Icon path, QIcon, or StandardPixmap
    checkable=True                    # Make it a toggle action
)
class SaveAction(QAction):
    ...
```

### Text as Positional Argument

You can pass the action text as the first argument:

```python
@action("&Open", shortcut="Ctrl+O")
class OpenAction(QAction):
    ...
```

### Auto-Connect Signals

Define `on_triggered()` or `on_toggled()` methods to handle action signals:

```python
@action("&Bold", shortcut="Ctrl+B", checkable=True)
class BoldAction(QAction):
    def on_toggled(self, checked: bool) -> None:
        print(f"Bold formatting: {checked}")

@action("&Save", shortcut="Ctrl+S")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Saving...")
```

These methods are automatically connected to the `triggered` and `toggled` signals.

### Action Icons

Icons can be specified three ways:

```python
# 1. Path to image file
@action("&Open", icon="icons/open.png")
class OpenAction(QAction):
    ...

# 2. QIcon object
from qtpy.QtGui import QIcon
icon = QIcon("path/to/icon.png")

@action("&Open", icon=icon)
class OpenAction(QAction):
    ...

# 3. Standard system icon
from qtpy.QtWidgets import QStyle

@action("&Info", icon=QStyle.StandardPixmap.SP_MessageBoxInformation)
class InfoAction(QAction):
    ...
```

### Checkable Actions

Use `checkable=True` for toggle actions (like Bold, Italic, etc.):

```python
@action("Show &Toolbar", checkable=True)
class ToolbarToggleAction(QAction):
    def on_toggled(self, checked: bool) -> None:
        toolbar.setVisible(checked)
```

### Keyboard Shortcuts

Shortcuts can be strings or Qt constants:

```python
# String shortcuts
@action("&New", shortcut="Ctrl+N")
@action("&Find", shortcut="Ctrl+F")
@action("&Quit", shortcut="Ctrl+Q")

# Standard Qt shortcuts
from qtpy.QtGui import QKeySequence

@action("&Save", shortcut=QKeySequence.StandardKey.Save)
@action("&Copy", shortcut=QKeySequence.StandardKey.Copy)
```

### Auto-Naming Actions

Actions auto-derive their text from the class name:

```python
@action  # text="Save"
class SaveAction(QAction):
    ...

@action  # text="Copy"
class CopyAction(QAction):
    ...
```

The "Action" suffix is automatically stripped.

## Complete Example

Here's a complete application with window, menus, and actions:

```python
from qtpie import window, menu, action, make, separator, entry_point
from qtpy.QtWidgets import QMainWindow, QMenu, QTextEdit
from qtpy.QtGui import QAction

# Define actions
@action("&New", shortcut="Ctrl+N", tooltip="Create a new file")
class NewAction(QAction):
    def on_triggered(self) -> None:
        print("New file")

@action("&Open", shortcut="Ctrl+O", tooltip="Open a file")
class OpenAction(QAction):
    def on_triggered(self) -> None:
        print("Open file")

@action("&Save", shortcut="Ctrl+S", tooltip="Save the file")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Save file")

@action("E&xit", shortcut="Ctrl+Q", tooltip="Exit application")
class ExitAction(QAction):
    def on_triggered(self) -> None:
        print("Exit")

@action("&Undo", shortcut="Ctrl+Z")
class UndoAction(QAction):
    def on_triggered(self) -> None:
        print("Undo")

@action("&Redo", shortcut="Ctrl+Y")
class RedoAction(QAction):
    def on_triggered(self) -> None:
        print("Redo")

# Define menus
@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open_file: OpenAction = make(OpenAction)
    save: SaveAction = make(SaveAction)
    sep1: QAction = separator()
    exit_app: ExitAction = make(ExitAction)

@menu("&Edit")
class EditMenu(QMenu):
    undo: UndoAction = make(UndoAction)
    redo: RedoAction = make(RedoAction)

# Define window
@entry_point
@window(title="Text Editor", size=(1024, 768), center=True)
class EditorWindow(QMainWindow):
    file_menu: FileMenu = make(FileMenu)
    edit_menu: EditMenu = make(EditMenu)
    central_widget: QTextEdit = make(QTextEdit)

    def setup(self) -> None:
        self.statusBar().showMessage("Ready")
```

## Connecting Actions to Methods

You can connect actions to methods using `make()`:

```python
@menu("&File")
class FileMenu(QMenu):
    save: QAction = make(QAction, "&Save", triggered="on_save")

    def on_save(self) -> None:
        print("Saving from menu method...")
```

Or use lambdas:

```python
@menu("&File")
class FileMenu(QMenu):
    save: QAction = make(
        QAction,
        "&Save",
        triggered=lambda: print("Saving...")
    )
```

## Lifecycle Hooks

All three decorators support lifecycle hooks:

### Window Hooks

```python
@window(title="My App")
class MainWindow(QMainWindow):
    def setup(self) -> None:
        """Called after all fields are initialized"""
        pass

    def setup_values(self) -> None:
        """Called after setup()"""
        pass

    def setup_bindings(self) -> None:
        """Called after setup_values()"""
        pass

    def setup_styles(self) -> None:
        """Called after setup_bindings()"""
        pass

    def setup_events(self) -> None:
        """Called after setup_styles()"""
        pass

    def setup_signals(self) -> None:
        """Called after setup_events()"""
        pass
```

### Menu and Action Hooks

Menus and actions support `setup()`:

```python
@menu("&File")
class FileMenu(QMenu):
    def setup(self) -> None:
        """Called after menu initialization"""
        pass

@action("&Save")
class SaveAction(QAction):
    def setup(self) -> None:
        """Called after action initialization"""
        pass
```

## Private Fields

Fields starting with `_` are not automatically added to menus or menu bars:

```python
@window(title="App")
class MainWindow(QMainWindow):
    file_menu: FileMenu = make(FileMenu)      # Added to menu bar
    _debug_menu: QMenu = make(QMenu, "Debug") # NOT added to menu bar

@menu("&File")
class FileMenu(QMenu):
    save: SaveAction = make(SaveAction)     # Added to menu
    _internal: QAction = make(QAction)      # NOT added to menu
```

## See Also

- [Widgets](../basics/widgets.md) - Using the `@widget` decorator
- [Styling](../basics/styling.md) - CSS classes and styling
- [@entry_point](../reference/decorators/entry-point.md) - Application entry points
- [make()](../reference/factories/make.md) - Creating widget instances
- [separator()](../reference/factories/separator.md) - Menu separators
