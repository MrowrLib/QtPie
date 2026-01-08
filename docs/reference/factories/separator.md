# separator()

Factory function for creating menu separators.

## Overview

The `separator()` function creates visual separators between menu items. When used in a `@menu` decorated class, it adds a separator action to the menu at that position.

## Basic Usage

Use `separator()` to visually group related menu actions:

```python
from qtpy.QtWidgets import QMenu
from qtpy.QtGui import QAction
from qtpie import menu, new, separator

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
    sep1: QAction = separator()  # Visual separator
    save_action: QAction = new("&Save")
    exit_action: QAction = new("E&xit")
```

This creates a menu structure with a separator between "Open" and "Save":

```
File
├── New
├── Open
├── ─────────  (separator)
├── Save
└── Exit
```

## Multiple Separators

You can use multiple separators to create logical groups:

```python
@menu("&Edit")
class EditMenu(QMenu):
    undo: QAction = new("&Undo")
    redo: QAction = new("&Redo")
    sep1: QAction = separator()
    cut: QAction = new("Cu&t")
    copy: QAction = new("&Copy")
    paste: QAction = new("&Paste")
    sep2: QAction = separator()
    preferences: QAction = new("&Preferences")
```

This creates three logical groups:
1. Undo/Redo operations
2. Clipboard operations
3. Settings

## Field Naming

The field name for a separator can be anything, but common conventions include:

```python
sep: QAction = separator()         # Single separator
sep1: QAction = separator()        # Multiple separators
sep2: QAction = separator()
_separator: QAction = separator()  # Private field (still added to menu)
```

Note: Unlike other menu fields, separators starting with `_` are still added to the menu (this is an implementation detail).

## Return Type

`separator()` returns a `NewField` marker that the `@menu` decorator recognizes. The marker is configured to:

- Create a `QAction` instance
- Mark it as a separator via the `_separator` flag
- Add it to the menu at the appropriate position

## Common Patterns

### Grouping by Function

```python
@menu("&Tools")
class ToolsMenu(QMenu):
    # Code tools
    format_code: QAction = new("&Format Code")
    refactor: QAction = new("&Refactor")

    sep1: QAction = separator()

    # Build tools
    build: QAction = new("&Build")
    test: QAction = new("&Test")

    sep2: QAction = separator()

    # Options
    options: QAction = new("&Options")
```

### Standard Application Menu

```python
@menu("&File")
class FileMenu(QMenu):
    new_file: QAction = new("&New", shortcut="Ctrl+N")
    open_file: QAction = new("&Open", shortcut="Ctrl+O")

    sep1: QAction = separator()

    save: QAction = new("&Save", shortcut="Ctrl+S")
    save_as: QAction = new("Save &As...", shortcut="Ctrl+Shift+S")

    sep2: QAction = separator()

    exit: QAction = new("E&xit", shortcut="Alt+F4", triggered="on_exit")

    def on_exit(self) -> None:
        self.parent().close()
```

## See Also

- [@menu decorator](../decorators/menu.md) - Menu class decorator
- [new() function](new.md) - Widget and action factory
- [Windows and Menus guide](../../guides/windows-menus.md) - Complete menu examples
