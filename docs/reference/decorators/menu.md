# @menu

The `@menu` decorator transforms a class into a Qt menu with automatic action and submenu management.

## Basic Usage

```python
from qtpie import menu
from qtpy.QtWidgets import QMenu

@menu
class FileMenu(QMenu):
    pass
```

This creates a menu with:
- Auto-generated title ("File" - derived from class name)
- Automatic action/submenu registration
- Dataclass-like field initialization

## With or Without Parentheses

Both forms work:

```python
@menu
class FileMenu(QMenu):
    pass

@menu()
class FileMenu(QMenu):
    pass
```

Use parentheses when you need to pass parameters.

## Parameters

### `text` - Menu Title

Sets the menu's title (shown in menu bars or parent menus).

```python
@menu(text="&File")
class FileMenu(QMenu):
    pass
```

**Positional shorthand:**

```python
@menu("&File")  # Same as text="&File"
class FileMenu(QMenu):
    pass
```

**Auto-generation from class name:**

If `text` is not provided, the title is derived from the class name:

```python
@menu
class FileMenu(QMenu):
    pass
# Title: "File" (strips "Menu" suffix)

@menu
class Tools(QMenu):
    pass
# Title: "Tools" (no suffix to strip)
```

The decorator removes the `Menu` suffix if present, otherwise uses the full class name.

## Auto-Adding Actions

`QAction` fields are automatically added to the menu in declaration order.

### Using `@action` Decorated Classes

```python
from qtpie import menu, action, make
from qtpy.QtGui import QAction

@action("&New")
class NewAction(QAction):
    pass

@action("&Open")
class OpenAction(QAction):
    pass

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open_file: OpenAction = make(OpenAction)

# Actions appear in menu as: New, Open
```

### Using Plain QAction

```python
from dataclasses import field

@menu("&Edit")
class EditMenu(QMenu):
    undo: QAction = field(default_factory=lambda: QAction("&Undo"))
    redo: QAction = field(default_factory=lambda: QAction("&Redo"))
```

### Signal Connections

Connect action signals using `make()`:

```python
@menu("&File")
class FileMenu(QMenu):
    save: QAction = make(QAction, "&Save", triggered="on_save")

    def on_save(self) -> None:
        print("Save triggered!")

# Or with a lambda
@menu("&File")
class FileMenu(QMenu):
    exit_app: QAction = make(QAction, "E&xit", triggered=lambda: app.quit())
```

See the [make() reference](../factories/make.md) for more signal connection options.

## Submenus

`QMenu` fields are automatically added as submenus.

```python
@menu("&Recent Files")
class RecentMenu(QMenu):
    pass

@menu("&File")
class FileMenu(QMenu):
    recent: RecentMenu = make(RecentMenu)

# The "Recent Files" submenu appears in the File menu
```

### Mixed Actions and Submenus

```python
@action("&New")
class NewAction(QAction):
    pass

@menu("&Recent")
class RecentMenu(QMenu):
    pass

@action("E&xit")
class ExitAction(QAction):
    pass

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    recent: RecentMenu = make(RecentMenu)
    exit_app: ExitAction = make(ExitAction)

# Menu structure:
# File
#   New
#   Recent >
#   Exit
```

## Separators

Use `separator()` to add visual dividers between menu items.

```python
from qtpie import separator

@action("&New")
class NewAction(QAction):
    pass

@action("&Open")
class OpenAction(QAction):
    pass

@action("E&xit")
class ExitAction(QAction):
    pass

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open_file: OpenAction = make(OpenAction)
    sep1: QAction = separator()
    exit_app: ExitAction = make(ExitAction)

# Menu structure:
# File
#   New
#   Open
#   ─────────
#   Exit
```

**Multiple separators:**

```python
@menu("&Edit")
class EditMenu(QMenu):
    undo: UndoAction = make(UndoAction)
    redo: RedoAction = make(RedoAction)
    sep1: QAction = separator()
    cut: CutAction = make(CutAction)
    copy: CopyAction = make(CopyAction)
    paste: PasteAction = make(PasteAction)
    sep2: QAction = separator()
    select_all: SelectAllAction = make(SelectAllAction)
```

The `separator()` function creates a field that the `@menu` decorator processes to add a separator action. The actual `QAction` (from `addSeparator()`) is stored on the instance and accessible via the field name.

See the [separator() reference](../factories/separator.md) for more details.

## Private Fields

Fields starting with `_` are not added to the menu:

```python
@action("&Public")
class PublicAction(QAction):
    pass

@action("&Private")
class PrivateAction(QAction):
    pass

@menu("&Test")
class TestMenu(QMenu):
    public: PublicAction = make(PublicAction)
    _private: PrivateAction = make(PrivateAction)

# Only "Public" appears in the menu
# _private still exists as an attribute but is not added
```

## Non-Widget Fields

Mix menu items with data fields:

```python
@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    save: SaveAction = make(SaveAction)

    # Data fields
    recent_files: list[str] = field(default_factory=list)
    max_recent: int = 10

# Only QAction and QMenu fields are added to the menu
```

## Lifecycle Hooks

### `setup()`

Called after menu initialization:

```python
@menu("&View")
class ViewMenu(QMenu):
    zoom_in: QAction = make(QAction, "Zoom &In")
    zoom_out: QAction = make(QAction, "Zoom &Out")

    def setup(self) -> None:
        # Called after menu is initialized
        # Customize menu behavior here
        pass
```

This is the only lifecycle hook available for `@menu`. It's called after all actions and submenus have been added.

## Constructor Arguments

Pass data via keyword arguments:

```python
@menu("&File")
class FileMenu(QMenu):
    recent_files: list[str] = field(default_factory=list)

# Later...
menu = FileMenu(recent_files=["file1.txt", "file2.txt"])
```

## Complete Example

A full File menu with actions, submenus, and separators:

```python
from qtpie import menu, action, make, separator
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

@action("&New")
class NewAction(QAction):
    pass

@action("&Open...")
class OpenAction(QAction):
    pass

@menu("&Recent Files")
class RecentMenu(QMenu):
    def setup(self) -> None:
        # Dynamically populate recent files
        self.addAction("file1.txt")
        self.addAction("file2.txt")

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
    recent: RecentMenu = make(RecentMenu)
    sep1: QAction = separator()
    save: SaveAction = make(SaveAction, triggered="on_save")
    sep2: QAction = separator()
    exit_app: ExitAction = make(ExitAction, triggered="on_exit")

    def on_new(self) -> None:
        print("New file")

    def on_open(self) -> None:
        print("Open file")

    def on_save(self) -> None:
        print("Save file")

    def on_exit(self) -> None:
        app.quit()
```

## What's Next?

- Learn about [@action](action.md) - Create reusable menu actions
- Explore [@window](window.md) - Add menus to windows
- See [separator()](../factories/separator.md) - Menu separators in detail
