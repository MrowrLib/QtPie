# separator()

Create visual separators between menu items in `@menu` decorated classes.

## Overview

The `separator()` factory function adds horizontal dividing lines between menu items to group related actions. It creates a `QAction` separator that the `@menu` decorator automatically processes and adds to the menu.

```python
from qtpie import menu, action, make, separator
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open_file: OpenAction = make(OpenAction)
    sep1: QAction = separator()  # Visual divider
    exit_app: ExitAction = make(ExitAction)
```

## Basic Usage

### Simple Separator

Add a separator between action groups:

```python
from qtpie import menu, action, make, separator
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

@action("&New")
class NewAction(QAction):
    pass

@action("E&xit")
class ExitAction(QAction):
    pass

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    sep1: QAction = separator()
    exit_app: ExitAction = make(ExitAction)
```

The separator appears as a horizontal line between "New" and "Exit" menu items.

### Multiple Separators

Create multiple logical groups in a single menu:

```python
@action("&Undo")
class UndoAction(QAction):
    pass

@action("Cu&t")
class CutAction(QAction):
    pass

@action("Select &All")
class SelectAllAction(QAction):
    pass

@menu("&Edit")
class EditMenu(QMenu):
    undo: UndoAction = make(UndoAction)
    sep1: QAction = separator()
    cut: CutAction = make(CutAction)
    sep2: QAction = separator()
    select_all: SelectAllAction = make(SelectAllAction)
```

This creates three distinct groups: undo operations, editing operations, and selection operations.

## Advanced Usage

### Separators with Submenus

Separators work alongside submenus:

```python
@menu("&Recent")
class RecentMenu(QMenu):
    pass

@action("E&xit")
class ExitAction(QAction):
    pass

@menu("&File")
class FileMenu(QMenu):
    recent: RecentMenu = make(RecentMenu)
    sep1: QAction = separator()
    exit_app: ExitAction = make(ExitAction)
```

The separator visually separates the "Recent" submenu from the "Exit" action.

### Accessing Separator Instances

The separator `QAction` is stored on the menu instance and can be accessed:

```python
@menu("&Test")
class TestMenu(QMenu):
    sep1: QAction = separator()

menu = TestMenu()
assert menu.sep1.isSeparator()  # True
```

This is useful for dynamic menu manipulation or testing.

## How It Works

### Type Signature

```python
def separator() -> QAction: ...
```

At type-check time, `separator()` returns a `QAction`. At runtime, it returns a dataclass field with special metadata that the `@menu` decorator recognizes.

### Processing by @menu

When the `@menu` decorator initializes a menu:

1. It scans all fields for separator metadata
2. For each separator field, it calls `menu.addSeparator()`
3. The returned `QAction` separator is stored on the instance

This happens automatically - you just declare the separator field.

## Important Notes

### Field Naming

**Do NOT use underscore prefix for separators:**

```python
# WRONG - underscore fields are ignored by @menu
_sep1: QAction = separator()

# CORRECT - public field name
sep1: QAction = separator()
```

The `@menu` decorator skips all fields starting with `_`, so underscore-prefixed separators won't be added to the menu.

### Menu-Only Feature

Separators only work in `@menu` decorated classes:

```python
# WORKS - in @menu class
@menu("&File")
class FileMenu(QMenu):
    sep1: QAction = separator()

# DOESN'T WORK - not a menu
@widget
class MyWidget(QWidget):
    sep1: QAction = separator()  # Won't create a separator
```

### Declaration Order Matters

Separators appear in the menu at the position they're declared:

```python
@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)      # First
    sep1: QAction = separator()           # Second (separator)
    exit_app: ExitAction = make(ExitAction)  # Third
```

## Common Patterns

### Grouping Related Actions

Use separators to create logical groups:

```python
@menu("&Edit")
class EditMenu(QMenu):
    # Undo/Redo group
    undo: UndoAction = make(UndoAction)
    redo: RedoAction = make(RedoAction)

    sep1: QAction = separator()

    # Clipboard group
    cut: CutAction = make(CutAction)
    copy: CopyAction = make(CopyAction)
    paste: PasteAction = make(PasteAction)

    sep2: QAction = separator()

    # Selection group
    select_all: SelectAllAction = make(SelectAllAction)
```

### Separating Exit Actions

Common pattern: separate destructive or exit actions:

```python
@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open_file: OpenAction = make(OpenAction)
    save: SaveAction = make(SaveAction)

    sep1: QAction = separator()

    exit_app: ExitAction = make(ExitAction)  # Isolated
```

## See Also

- [@menu](../decorators/menu.md) - Menu decorator that processes separators
- [make()](make.md) - Factory for creating menu actions
- [@action](../decorators/action.md) - Decorator for creating menu actions
- [Windows & Menus Guide](../../guides/windows-menus.md) - Complete menu building guide
