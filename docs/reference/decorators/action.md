# @action

Decorator for creating declarative `QAction` subclasses with automatic configuration and signal connections.

## Signature

```python
@action(
    text: str | None = None,
    *,
    shortcut: str | QKeySequence | QKeySequence.StandardKey | None = None,
    tooltip: str | None = None,
    icon: QIcon | QStyle.StandardPixmap | None = None,
    checkable: bool = False
) -> type[QAction]
```

## Parameters

**`text`** (positional or keyword)
- Action text
- Supports keyboard mnemonics with `&` (e.g., `"&Save"`)
- Default: Derived from class name (strips `"Action"` suffix if present)

**`shortcut`**
- Keyboard shortcut
- Can be a string (e.g., `"Ctrl+S"`), `QKeySequence`, or `QKeySequence.StandardKey`
- Default: No shortcut

**`tooltip`**
- Tooltip text (shown on hover)
- Also sets the action's status tip
- Default: No tooltip

**`icon`**
- Action icon
- Can be a `QIcon` or `QStyle.StandardPixmap`
- Default: No icon

**`checkable`**
- Whether the action can be toggled on/off
- Default: `False`

## Behavior

### Automatic Text

If no `text` parameter is provided, the action text is derived from the class name:

```python
@action
class SaveAction(QAction):  # Text: "Save"
    pass

@action
class Undo(QAction):  # Text: "Undo" (no suffix to strip)
    pass
```

### Automatic Signal Connections

Methods with specific names are automatically connected to their corresponding signals:

- `on_triggered()` → `triggered` signal
- `on_toggled(checked: bool)` → `toggled` signal (for checkable actions)

```python
@action("Bold", checkable=True)
class BoldAction(QAction):
    def on_triggered(self) -> None:
        print("Bold triggered")

    def on_toggled(self, checked: bool) -> None:
        print(f"Bold is now {'on' if checked else 'off'}")
```

### Initialization Order

1. `QAction.__init__()` called
2. Text, shortcut, tooltip, icon, checkable properties set
3. Auto signal connections established
4. `__setup__()` hook called (if defined)

## Usage in Menus

Actions are typically used as fields in `@menu` classes:

```python
@menu("&File")
class FileMenu(QMenu):
    save: SaveAction = new()  # Uses declarative action class
    exit: QAction = new("E&xit")  # Or inline with new()
```

## Examples

### Basic Action

```python
@action("&Save")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Save triggered")
```

### Action with Text from Class Name

```python
@action
class SaveAction(QAction):  # Text: "Save"
    pass

@action
class Undo(QAction):  # Text: "Undo"
    pass
```

### Action with Shortcut

```python
@action("&Save", shortcut="Ctrl+S")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Save")
```

Shortcut variants:

```python
# String format
@action("Save", shortcut="Ctrl+S")
class Save1(QAction):
    pass

# QKeySequence
from PySide6.QtGui import QKeySequence

@action("Save", shortcut=QKeySequence("Ctrl+S"))
class Save2(QAction):
    pass

# Standard key
@action("Save", shortcut=QKeySequence.StandardKey.Save)
class Save3(QAction):
    pass
```

### Checkable Action

```python
@action("Word Wrap", checkable=True)
class WordWrapAction(QAction):
    def on_toggled(self, checked: bool) -> None:
        print(f"Word wrap: {checked}")
```

### Action with Tooltip

```python
@action("&Find", shortcut="Ctrl+F", tooltip="Find text in document")
class FindAction(QAction):
    pass
```

The tooltip also sets the status tip (shown in status bar).

### Action with Icon

```python
from PySide6.QtWidgets import QStyle

@action("Save", icon=QStyle.StandardPixmap.SP_DialogSaveButton)
class SaveAction(QAction):
    pass
```

### Action with `__setup__` Hook

```python
@action("Save", shortcut="Ctrl+S")
class SaveAction(QAction):
    def __setup__(self) -> None:
        # Action properties are ready
        print(f"Action created: {self.text()}")
        print(f"Shortcut: {self.shortcut().toString()}")
```

### Complete Action Example

```python
from PySide6.QtGui import QKeySequence

@action(
    text="&Save Document",
    shortcut=QKeySequence.StandardKey.Save,
    tooltip="Save the current document",
    checkable=False
)
class SaveAction(QAction):
    def on_triggered(self) -> None:
        # Save logic here
        print("Saving document...")

    def __setup__(self) -> None:
        # Additional setup if needed
        self.setEnabled(False)  # Initially disabled
```

### Using Actions in Menus

```python
@action("&New", shortcut="Ctrl+N")
class NewAction(QAction):
    def on_triggered(self) -> None:
        print("New document")

@action("&Save", shortcut="Ctrl+S")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Save document")

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = new()
    save: SaveAction = new()
    sep: QAction = separator()
    exit: QAction = new("E&xit", triggered="on_exit")

    def on_exit(self) -> None:
        self.parent().close()
```

## Signal Connections

### Auto-connected Methods

Define these methods to automatically connect to signals:

```python
@action("Save")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        # Called when action is triggered
        pass
```

For checkable actions:

```python
@action("Bold", checkable=True)
class BoldAction(QAction):
    def on_triggered(self) -> None:
        # Called when action is triggered (any toggle)
        pass

    def on_toggled(self, checked: bool) -> None:
        # Called when action state changes
        print(f"Bold is {'on' if checked else 'off'}")
```

### Manual Connections

You can also connect signals manually in `__setup__`:

```python
@action("Save")
class SaveAction(QAction):
    def __setup__(self) -> None:
        self.triggered.connect(self.on_save)

    def on_save(self) -> None:
        print("Manual connection")
```

## Keyboard Mnemonics

Use `&` before a letter to create keyboard mnemonics:

```python
@action("&Save")  # Alt+S when in menu
class SaveAction(QAction):
    pass
```

## Comparison with Inline Actions

Declarative action classes:

```python
@action("&Save", shortcut="Ctrl+S")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Save")

# Usage
@menu("&File")
class FileMenu(QMenu):
    save: SaveAction = new()
```

Inline with `new()`:

```python
@menu("&File")
class FileMenu(QMenu):
    save: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")

    def on_save(self) -> None:
        print("Save")
```

Use declarative classes when:
- The action has complex logic
- The action is reused across multiple menus
- You want to test the action in isolation

Use inline `new()` when:
- The action is simple and menu-specific
- The handler is a one-liner or lambda

## Standard Icons

Qt provides standard icons via `QStyle.StandardPixmap`:

```python
from PySide6.QtWidgets import QStyle

# Common standard pixmaps
@action("Save", icon=QStyle.StandardPixmap.SP_DialogSaveButton)
class SaveAction(QAction):
    pass

@action("Open", icon=QStyle.StandardPixmap.SP_DialogOpenButton)
class OpenAction(QAction):
    pass

@action("Help", icon=QStyle.StandardPixmap.SP_DialogHelpButton)
class HelpAction(QAction):
    pass
```

## See Also

- [Windows & Menus guide](../../guides/windows-menus.md)
- [@menu decorator](./menu.md)
- [new() factory](../factories/new.md)
- [QAction documentation](https://doc.qt.io/qt-6/qaction.html)
