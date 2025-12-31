# @action

The `@action` decorator transforms a class into a Qt action with automatic configuration and signal handling.

## Basic Usage

```python
from qtpie import action
from qtpy.QtGui import QAction

@action
class SaveAction(QAction):
    pass
```

This creates an action with:
- Auto-generated text ("Save" - derived from class name)
- Automatic signal connection for `on_triggered()` and `on_toggled()` methods
- Dataclass-like field initialization

## With or Without Parentheses

Both forms work:

```python
@action
class SaveAction(QAction):
    pass

@action()
class SaveAction(QAction):
    pass
```

Use parentheses when you need to pass parameters.

## Parameters

### `text` - Action Text

Sets the action's text (shown in menus and toolbars).

```python
@action(text="&New File")
class NewAction(QAction):
    pass
```

**Positional shorthand:**

```python
@action("&Open")  # Same as text="&Open"
class OpenAction(QAction):
    pass
```

**Auto-generation from class name:**

If `text` is not provided, it's derived from the class name:

```python
@action
class SaveAction(QAction):
    pass
# Text: "Save" (strips "Action" suffix)

@action
class Quit(QAction):
    pass
# Text: "Quit" (no suffix to strip)
```

The decorator removes the `Action` suffix if present, otherwise uses the full class name.

**Ampersand for mnemonics:**

Use `&` to create keyboard mnemonics (underlined shortcuts in menus):

```python
@action("&File")  # Alt+F in menu
@action("&New")   # Alt+N in menu
@action("E&xit")  # Alt+X in menu
```

### `shortcut` - Keyboard Shortcut

Sets a keyboard shortcut for the action.

**String format:**

```python
@action("&New", shortcut="Ctrl+N")
class NewAction(QAction):
    pass

@action("&Bold", shortcut="Ctrl+B")
class BoldAction(QAction):
    pass
```

**Standard key sequences:**

Use `QKeySequence.StandardKey` for platform-specific shortcuts:

```python
from qtpy.QtGui import QKeySequence

@action("&Save", shortcut=QKeySequence.StandardKey.Save)
class SaveAction(QAction):
    pass
# Ctrl+S on Windows/Linux, Cmd+S on macOS
```

**QKeySequence objects:**

```python
@action("&Copy", shortcut=QKeySequence("Ctrl+C"))
class CopyAction(QAction):
    pass
```

### `tooltip` - Tooltip and Status Tip

Sets both the tooltip (hover text) and status tip (status bar text).

```python
@action("&New", tooltip="Create a new file")
class NewAction(QAction):
    pass
```

This sets:
- `toolTip()` - Shown on hover
- `statusTip()` - Shown in status bar

### `icon` - Action Icon

Sets the action's icon. Accepts three formats:

**String path:**

```python
@action("&Save", icon="icons/save.png")
class SaveAction(QAction):
    pass
```

**QIcon object:**

```python
from qtpy.QtGui import QIcon

custom_icon = QIcon("icons/custom.png")

@action("&Custom", icon=custom_icon)
class CustomAction(QAction):
    pass
```

**Standard pixmap:**

Use Qt's built-in icons via `QStyle.StandardPixmap`:

```python
from qtpy.QtWidgets import QStyle

@action("&Info", icon=QStyle.StandardPixmap.SP_MessageBoxInformation)
class InfoAction(QAction):
    pass
```

Common standard pixmaps:
- `SP_MessageBoxInformation`
- `SP_MessageBoxWarning`
- `SP_MessageBoxCritical`
- `SP_DialogSaveButton`
- `SP_DialogOpenButton`
- `SP_DialogCloseButton`

### `checkable` - Toggle Actions

Makes the action checkable (on/off toggle).

```python
@action("&Bold", checkable=True)
class BoldAction(QAction):
    pass

# Later...
action = BoldAction()
action.setChecked(True)
```

Checkable actions emit the `toggled` signal (see [Signal Auto-Connection](#signal-auto-connection)).

## Signal Auto-Connection

The `@action` decorator automatically connects signals to specially-named methods.

### `on_triggered()` - Triggered Signal

Define `on_triggered()` to handle action activation:

```python
@action("&Test")
class TestAction(QAction):
    def on_triggered(self) -> None:
        print("Action triggered!")

# When action is activated (clicked, keyboard shortcut, etc.)
# on_triggered() is called automatically
```

### `on_toggled()` - Toggled Signal

For checkable actions, define `on_toggled()` to handle state changes:

```python
@action("&Bold", checkable=True)
class BoldAction(QAction):
    def on_toggled(self, checked: bool) -> None:
        print(f"Bold is now: {'on' if checked else 'off'}")

# When action is toggled, on_toggled() receives the new state
```

## Lifecycle Hooks

### `setup()`

Called after action initialization:

```python
@action("&Custom")
class CustomAction(QAction):
    def setup(self) -> None:
        # Called after action is fully initialized
        # Customize action behavior here
        pass
```

This is the only lifecycle hook available for `@action`.

## Data Fields

Mix action configuration with data fields:

```python
from dataclasses import field

@action("&Save")
class SaveAction(QAction):
    count: int = 0
    name: str = "default"

    def on_triggered(self) -> None:
        self.count += 1
        print(f"Saved {self.count} times")
```

**Constructor arguments:**

Pass data via keyword arguments:

```python
@action("&Test")
class TestAction(QAction):
    count: int = 0
    name: str = "default"

# Later...
action = TestAction(count=42, name="custom")
```

**Default factories:**

Use `field(default_factory=...)` for mutable defaults:

```python
@action("&Items")
class ItemsAction(QAction):
    items: list[str] = field(default_factory=list)

    def on_triggered(self) -> None:
        self.items.append("new")
```

## Using with @menu

Actions are commonly used with `@menu` decorated menus:

```python
from qtpie import menu, action, make
from qtpy.QtWidgets import QMenu

@action("&New", shortcut="Ctrl+N")
class NewAction(QAction):
    def on_triggered(self) -> None:
        print("New file")

@action("&Open", shortcut="Ctrl+O")
class OpenAction(QAction):
    def on_triggered(self) -> None:
        print("Open file")

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    open_file: OpenAction = make(OpenAction)
```

See the [@menu reference](menu.md) for more details.

## Child Actions

Actions can contain other actions as fields with signal connections:

```python
from qtpie import make

@action("&Parent")
class ParentAction(QAction):
    child: QAction = make(QAction, "Child", triggered="on_child_triggered")

    def on_child_triggered(self) -> None:
        print("Child triggered!")
```

Signal connections work with method names or callables:

```python
@action("&Parent")
class ParentAction(QAction):
    child: QAction = make(
        QAction,
        "Child",
        triggered=lambda: print("Child clicked!")
    )
```

## Complete Examples

### Simple Action with Signal

```python
@action("&Save", shortcut="Ctrl+S", tooltip="Save the current file")
class SaveAction(QAction):
    def on_triggered(self) -> None:
        print("Saving file...")
```

### Checkable Action

```python
@action("&Bold", shortcut="Ctrl+B", checkable=True)
class BoldAction(QAction):
    def on_toggled(self, checked: bool) -> None:
        if checked:
            print("Text is now bold")
        else:
            print("Text is now normal")
```

### Action with Icon and Data

```python
from qtpy.QtWidgets import QStyle

@action(
    "&Info",
    shortcut="F1",
    tooltip="Show information",
    icon=QStyle.StandardPixmap.SP_MessageBoxInformation
)
class InfoAction(QAction):
    show_count: int = 0

    def on_triggered(self) -> None:
        self.show_count += 1
        print(f"Info shown {self.show_count} times")
```

### Full-Featured Action

```python
@action(
    text="&Bold",
    shortcut="Ctrl+B",
    tooltip="Toggle bold formatting",
    checkable=True
)
class BoldAction(QAction):
    # Track usage
    toggle_count: int = 0

    def setup(self) -> None:
        # Initialize to unchecked
        self.setChecked(False)

    def on_toggled(self, checked: bool) -> None:
        self.toggle_count += 1
        status = "enabled" if checked else "disabled"
        print(f"Bold {status} (toggled {self.toggle_count} times)")
```

## What's Next?

- Learn about [@menu](menu.md) - Create menus with actions
- Explore [@window](window.md) - Add menu bars to windows
- See [make()](../factories/make.md) - Create and configure widget instances
