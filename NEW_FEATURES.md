# QtPie v2 New Features

This document covers the new features in QtPie v2, specifically **Variable Bindings** (dependency injection for widgets) and the **New Menu System** (`@menu` and `Menu`).

---

## Table of Contents

1. [Variable Bindings](#variable-bindings)
   - [Overview](#overview)
   - [Required vs Optional Bindings](#required-vs-optional-bindings)
   - [Direct Variable Bindings (Two-Way)](#direct-variable-bindings-two-way)
   - [Expression Bindings (One-Way Computed)](#expression-bindings-one-way-computed)
   - [Literal Value Bindings](#literal-value-bindings)
   - [Nested Widget Bindings (Pass-Through)](#nested-widget-bindings-pass-through)
   - [Window Support](#window-support)
2. [New Menu System](#new-menu-system)
   - [Overview](#menu-overview)
   - [@menu Decorator](#newmenu-decorator)
   - [Menu Base Class](#menu-base-class)
   - [QAction Fields](#qaction-fields)
   - [Separators](#separators)
   - [Sections](#sections)
   - [Dynamic Action Lists (ActionRepeater)](#dynamic-action-lists-actionrepeater)
   - [Checkable Actions](#checkable-actions)
   - [Menu with Record Type (Menu[T])](#menu-with-record-type-menut)
   - [Variable Bindings in Menus](#variable-bindings-in-menus)
   - [Window Integration](#window-integration)
   - [The #parent Placeholder](#the-parent-placeholder)

---

## Variable Bindings

### Overview

Variable bindings enable **React-style dependency injection** in QtPie. Instead of child widgets reaching UP to their parent via `#parent`, parents can now pass state DOWN to children via Variable bindings.

**The Core Pattern:**
- Bare `Variable[T]` = **required** binding (must be provided by parent)
- `Variable[T] = new(default)` = **optional** binding (can be overridden by parent)
- `child: ChildWidget = new(var_name="_parent_var")` creates a reactive binding

This is similar to React props, but with QtPie vocabulary.

### Required vs Optional Bindings

#### Required Bindings (Bare Variable)

When a widget declares a `Variable[T]` without a default value, it's a **required binding**. The parent MUST provide a value or binding.

```python
from PySide6.QtWidgets import QLabel
from qtpie import Widget, Variable, new, widget

@widget
class CounterDisplay(Widget):
    # REQUIRED - must be provided by parent
    count: Variable[int]

    _label: QLabel = new(bind="Count: {count}")
```

If a parent tries to use this widget without providing the binding, a clear error is raised:

```python
@widget
class Parent(Widget):
    # ERROR: TypeError: CounterDisplay requires binding for 'count'
    display: CounterDisplay = new()
```

The error message includes the fix:
```
CounterDisplay requires binding for 'count'. Use: display: CounterDisplay = new(count="_parent_var")
```

#### Optional Bindings (Variable with Default)

When a widget declares a `Variable[T] = new(default)`, it has a default value and binding is optional.

```python
@widget
class CounterDisplay(Widget):
    # OPTIONAL - has default, parent can override
    count: Variable[int] = new(0)
    prefix: Variable[str] = new("Count: ")

    _label: QLabel = new(bind="{prefix}{count}")
```

Parents can use this widget with or without providing bindings:

```python
@widget
class Parent(Widget):
    _my_count: Variable[int] = new(42)

    # Uses default count=0
    display1: CounterDisplay = new()

    # Overrides count with parent's variable
    display2: CounterDisplay = new(count="_my_count")

    # Overrides both count and prefix
    display3: CounterDisplay = new(count="_my_count", prefix="Total: ")
```

### Direct Variable Bindings (Two-Way)

Direct variable bindings create a **two-way reactive connection** between parent and child Variables. Changes to either side are reflected on both.

**Syntax:** `child_var="_parent_var"` (string starting with `_`)

```python
@widget
class Child(Widget):
    count: Variable[int]  # Required
    _label: QLabel = new(bind="Count: {count}")

@widget
class Parent(Widget):
    _my_count: Variable[int] = new(0)

    # Two-way binding: Parent._my_count <-> Child.count
    child: Child = new(count="_my_count")

# Usage:
parent = Parent()

# Initial sync
assert parent.child.count.value == 0

# Parent changes -> child updates
parent._my_count.value = 42
assert parent.child.count.value == 42

# Child changes -> parent updates (two-way!)
parent.child.count.value = 100
assert parent._my_count.value == 100
```

**How it works:**

Under the hood, the child's Variable shares the parent's Observable. This means:
- No data copying - both point to the same reactive source
- Changes propagate instantly in both directions
- UI bindings on both sides update automatically

### Expression Bindings (One-Way Computed)

Expression bindings create a **one-way computed** value from parent Variables. The child's Variable is derived from an expression.

**Syntax:** `child_var="{expression}"` (string containing `{` and `}`)

```python
@widget
class ActionButton(Widget):
    enabled: Variable[bool]
    label_text: Variable[str]
    _button: QPushButton = new(bind="{label_text}", enabled="{enabled}")

@widget
class Parent(Widget):
    _items: Variable[list[str]] = new([])
    _name: Variable[str] = new("")

    # Expression bindings - computed one-way
    action: ActionButton = new(
        enabled="{len(_items) > 0}",           # True when list is non-empty
        label_text="{_name.upper() if _name else 'UNNAMED'}"
    )

# Usage:
parent = Parent()
assert parent.action.enabled.value == False  # Empty list

parent._items.append("item1")
assert parent.action.enabled.value == True   # Now has items

parent._name.value = "hello"
assert parent.action.label_text.value == "HELLO"
```

**Supported expressions:**
- Variable references: `{_count}`, `{_name}`
- Attribute access: `{_name.upper()}`
- Function calls: `{len(_items)}`
- Math operations: `{_x + _y}`, `{_count * 2}`
- Comparisons: `{_count > 0}`, `{len(_name) >= 3}`
- Ternary: `{_name if _name else 'default'}`
- Complex: `{(_x + _y) * _z}`

### Literal Value Bindings

When you pass a non-binding value, it's set as the Variable's initial value without creating a reactive connection.

**Syntax:** Value that doesn't match binding patterns

```python
@widget
class Child(Widget):
    message: Variable[str]
    count: Variable[int]

@widget
class Parent(Widget):
    # Literal values - not reactive, just set defaults
    child: Child = new(
        message="Hello World",  # String literal (no leading _)
        count=42                 # Non-string literal
    )

# Usage:
parent = Parent()
assert parent.child.message.value == "Hello World"
assert parent.child.count.value == 42
```

**Detection rules:**
- Starts with `_` → Direct variable binding
- Contains `{` and `}` → Expression binding
- Is a simple identifier that exists as a Variable on parent → Direct binding
- Otherwise → Literal value

### Nested Widget Bindings (Pass-Through)

Bindings can flow through multiple levels of the widget hierarchy. A child can receive a binding and pass it down to grandchildren.

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]  # Required
    _label: QLabel = new(bind="Theme: {theme}")

@widget
class Child(Widget):
    theme: Variable[str]  # Required, will pass to grandchild
    grandchild: GrandChild = new(theme="theme")  # Pass our theme down

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")

# Usage:
parent = Parent()

# Binding flows through: Parent._theme -> Child.theme -> GrandChild.theme
assert parent.child.grandchild.theme.value == "dark"

# Parent change propagates all the way down
parent._theme.value = "light"
assert parent.child.theme.value == "light"
assert parent.child.grandchild.theme.value == "light"
```

**Deep nesting (6+ levels) is fully supported:**

```python
@widget
class Level6(Widget):
    value: Variable[int]
    _label: QLabel = new(bind="Value: {value}")

@widget
class Level5(Widget):
    value: Variable[int]
    child: Level6 = new(value="value")

@widget
class Level4(Widget):
    value: Variable[int]
    child: Level5 = new(value="value")

@widget
class Level3(Widget):
    value: Variable[int]
    child: Level4 = new(value="value")

@widget
class Level2(Widget):
    value: Variable[int]
    child: Level3 = new(value="value")

@widget
class Level1(Widget):
    _value: Variable[int] = new(100)
    child: Level2 = new(value="_value")

# Works correctly at all depths
```

### Window Support

Variable bindings work the same way in Windows:

```python
from qtpie import Window, window

@widget
class StatusBar(Widget):
    message: Variable[str]  # Required
    _label: QLabel = new(bind="{message}")

@window(title="My App")
class App(Window):
    _status: Variable[str] = new("Ready")
    status_bar: StatusBar = new(message="_status")

# Usage:
app = App()
assert app.status_bar.message.value == "Ready"

app._status.value = "Loading..."
assert app.status_bar.message.value == "Loading..."
```

---

## New Menu System

### Menu Overview

The new menu system (`@menu` and `Menu`) provides declarative menus with full Variable support. It's built on the same Variable binding foundation as widgets.

Key features:
- Declarative QAction definition
- `Separator` and `Section` markers
- Dynamic action lists via `ActionRepeater`
- Checkable actions with two-way binding
- Menu[T] record support
- Variable bindings from parent Window

### @menu Decorator

The `@menu` decorator creates a menu class, similar to how `@widget` creates a widget.

```python
from qtpie import Menu, newmenu

# Bare decorator - title derived from class name
@menu
class FileMenu(Menu):
    pass  # Title: "File"

# With explicit text (supports mnemonics)
@menu(text="&File")
class FileMenu(Menu):
    pass  # Title: "&File"

# With additional options
@menu(text="&Edit", name="edit-menu", classes=["main-menu"])
class EditMenu(Menu):
    pass
```

**Decorator options:**
- `text`: Menu title (e.g., `"&File"` for mnemonic)
- `name`: Object name for CSS/QSS styling
- `classes`: CSS classes
- `record`: Default record instance for Menu[T]

### Menu Base Class

`Menu` extends `QMenu` with QtPie features:

```python
from qtpie import Menu

class Menu[T = None](QMenu):
    """QMenu with QtPie declarative features."""

    def __setup__(self) -> None:
        """Override for custom setup after menu initialization."""
        pass
```

### QAction Fields

Declare actions as typed fields:

```python
from PySide6.QtGui import QAction
from qtpie import Menu, new, newmenu

@menu(text="&File")
class FileMenu(Menu):
    # Basic action
    new_action: QAction = new("&New")

    # Action with shortcut
    save_action: QAction = new("&Save", shortcut="Ctrl+S")

    # Action with triggered handler (method name)
    exit_action: QAction = new("E&xit", triggered="on_exit")

    # Action with tooltip
    open_action: QAction = new("&Open", toolTip="Open a file")

    def on_exit(self) -> None:
        print("Exiting!")
```

**Supported kwargs:**
- `shortcut`: Keyboard shortcut (e.g., `"Ctrl+S"`)
- `toolTip`: Tooltip text
- `enabled`: Enable/disable (can be binding)
- `visible`: Show/hide (can be binding)
- `checkable`: Make action checkable
- `checked`: Initial checked state or binding
- `triggered`: Handler for triggered signal
- `toggled`: Handler for toggled signal

### Separators

Use the `Separator` marker class to add visual separators:

```python
from qtpie import Menu, Separator, new, newmenu

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")
    ____: Separator                       # <-- Separator here
    save_action: QAction = new("&Save")
    save_as_action: QAction = new("Save &As")
    _____: Separator                      # <-- Another separator
    exit_action: QAction = new("E&xit")
```

**Separator naming:**
- The name doesn't matter (just underscores for style)
- Convention: `____`, `_____`, `______`, etc.
- Each must be unique (different number of underscores)

### Sections

Use the `Section` marker class to add labeled section headers:

```python
from qtpie import Menu, Section, Separator, new, newmenu

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    ____: Separator

    # Section with text derived from name: "Recent" from "___recent___"
    ___recent___: Section
    file1: QAction = new("file1.txt")
    file2: QAction = new("file2.txt")

    # Section with explicit text
    ___projects___: Section = new("Recent Projects")
    project1: QAction = new("My Project")

    # Section with reactive binding
    ___dynamic___: Section = new(bind="_section_title")
```

**Section naming:**
- Format: `___text___` (leading and trailing underscores)
- Text is extracted: `___recent___` → "Recent"
- Snake case converts: `___recent_files___` → "Recent Files"

### Dynamic Action Lists (ActionRepeater)

Create actions dynamically from a list using `list[QAction]`:

```python
from dataclasses import dataclass

@dataclass
class WindowInfo:
    title: str
    widget: QWidget

@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[WindowInfo]] = new([])

    tile: QAction = new("&Tile")
    cascade: QAction = new("&Cascade")
    ____: Separator

    # Dynamic actions - one per item in _windows
    window_actions: list[QAction] = new(
        bind="_windows",           # Bind to the Variable
        format="{title}",          # Format for action text
        triggered="on_select"      # Handler receives the item
    )

    def on_select(self, info: WindowInfo) -> None:
        """Handler receives the list item, not the action."""
        info.widget.raise_()
```

**ActionRepeater features:**
- Automatically syncs with `ObservableList` changes
- Uses granular callbacks (insert, remove, replace, clear)
- Format string supports: `{#self}`, `{#index}`, `{property}`
- Handler receives the list item, not the QAction

**Format placeholders:**
- `{#self}` - The item itself (for primitives like `str`)
- `{#index}` - Item's index in the list
- `{property}` - Property access on the item

```python
# For list[str]
_files: Variable[list[str]] = new([])
file_actions: list[QAction] = new(bind="_files", format="{#self}")

# For list[WindowInfo]
_windows: Variable[list[WindowInfo]] = new([])
window_actions: list[QAction] = new(bind="_windows", format="{#index}: {title}")
```

### Checkable Actions

Create toggle actions with two-way binding to Variables:

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)
    _line_numbers: Variable[bool] = new(True)

    # Checkable with two-way binding to Variable
    word_wrap: QAction = new(
        "Word Wrap",
        checkable=True,
        checked="_word_wrap"   # Two-way binding!
    )

    line_numbers: QAction = new(
        "Line Numbers",
        checkable=True,
        checked="_line_numbers"
    )

# Usage:
menu = ViewMenu()

# Variable controls action
menu._word_wrap.value = True
assert menu.word_wrap.isChecked() == True

# Action controls Variable
menu.word_wrap.setChecked(False)
assert menu._word_wrap.value == False
```

**With toggled handler:**

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

        Return False to refuse/revert the toggle.
        Return None (or nothing) to accept.
        """
        if not self.can_toggle():
            return False  # Refuse - action reverts
        return None  # Accept
```

### Menu with Record Type (Menu[T])

Menus support the same `[T]` record type pattern as widgets:

```python
from dataclasses import dataclass

@dataclass
class EditState:
    can_undo: bool = False
    can_redo: bool = False
    clipboard_has_content: bool = False

@menu(text="&Edit", record=EditState())
class EditMenu(Menu[EditState]):
    # Bind action properties to record fields
    undo: QAction = new("&Undo", enabled="{record.can_undo}")
    redo: QAction = new("&Redo", enabled="{record.can_redo}")
    ____: Separator
    paste: QAction = new("&Paste", enabled="{record.clipboard_has_content}")

# Usage:
menu = EditMenu()
assert menu.undo.isEnabled() == False

menu.record.can_undo = True  # Reactive!
assert menu.undo.isEnabled() == True
```

### Variable Bindings in Menus

Menus support the same Variable binding pattern as widgets:

```python
@menu(text="&File")
class FileMenu(Menu):
    # Required bindings - must be provided by parent Window
    is_dirty: Variable[bool]
    recent_files: Variable[list[str]]

    # Optional bindings - has defaults
    file_limit: Variable[int] = new(10)

    new_action: QAction = new("&New")
    save_action: QAction = new("&Save", enabled="{is_dirty}")
    ____: Separator

    ___recent___: Section
    recent_actions: list[QAction] = new(
        bind="recent_files",
        format="{#self}",
        triggered="open_recent"
    )

@window(title="Editor")
class EditorWindow(Window):
    _is_dirty: Variable[bool] = new(False)
    _recent: Variable[list[str]] = new([])

    # Provide bindings to menu
    file_menu: FileMenu = new(
        is_dirty="_is_dirty",
        recent_files="_recent"
    )
```

### Window Integration

Menus declared as fields on a Window are automatically added to the menu bar:

```python
@window(title="My Editor")
class EditorWindow(Window):
    _is_dirty: Variable[bool] = new(False)
    _can_undo: Variable[bool] = new(False)

    # Menus auto-added to menu bar in declaration order
    file_menu: FileMenu = new(is_dirty="_is_dirty")
    edit_menu: EditMenu = new(can_undo="_can_undo")
    view_menu: ViewMenu = new()
    help_menu: HelpMenu = new()

    editor: QTextEdit = new()
```

The menu bar order matches the field declaration order.

### The #parent Placeholder

The `#parent` placeholder provides access to the parent window from within menu expressions. This is an escape hatch for cases where bindings aren't practical.

```python
@menu(text="&File")
class FileMenu(Menu):
    # Access parent window's variable via #parent
    save: QAction = new(
        "&Save",
        enabled="{#parent._is_dirty}"
    )

    close: QAction = new(
        "&Close",
        enabled="{#parent._can_close}"
    )

@window(title="App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    _can_close: Variable[bool] = new(True)

    # No bindings needed - menu uses #parent
    file_menu: FileMenu = new()
```

**When to use `#parent` vs bindings:**

| Approach | Pros | Cons |
|----------|------|------|
| **Variable Bindings** | Explicit dependencies, reusable menus | More verbose |
| **#parent** | Quick and easy | Menu is coupled to parent structure |

**Recommendation:** Prefer Variable bindings for reusable components. Use `#parent` for quick prototyping or when the menu is tightly coupled to a specific window.

---

## Complete Example

Here's a complete example combining Variable bindings and the new menu system:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QTextEdit, QLabel
from PySide6.QtGui import QAction
from qtpie import (
    Widget, Window, Menu, Variable,
    new, widget, window, newmenu,
    Separator, Section
)

# ═══════════════════════════════════════════════════════════════
# Reusable Status Bar Widget
# ═══════════════════════════════════════════════════════════════

@widget
class StatusBar(Widget):
    # Required bindings
    message: Variable[str]
    is_modified: Variable[bool]

    _message_label: QLabel = new(bind="{message}")
    _modified_label: QLabel = new(bind="{'*' if is_modified else ''}")

# ═══════════════════════════════════════════════════════════════
# File Menu with Variable Bindings
# ═══════════════════════════════════════════════════════════════

@menu(text="&File")
class FileMenu(Menu):
    # Required bindings from parent
    is_dirty: Variable[bool]
    recent_files: Variable[list[str]]

    # Callbacks from parent
    on_new: Variable[Callable[[], None]] = new(lambda: None)
    on_save: Variable[Callable[[], None]] = new(lambda: None)

    new_action: QAction = new("&New", shortcut="Ctrl+N", triggered="do_new")
    open_action: QAction = new("&Open", shortcut="Ctrl+O")
    ____: Separator
    save_action: QAction = new("&Save", shortcut="Ctrl+S",
                                enabled="{is_dirty}", triggered="do_save")
    _____: Separator

    ___recent___: Section
    recent_actions: list[QAction] = new(
        bind="recent_files",
        format="{#self}",
        triggered="open_recent"
    )

    ______: Separator
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def do_new(self) -> None:
        self.on_new.value()

    def do_save(self) -> None:
        self.on_save.value()

    def open_recent(self, filename: str) -> None:
        print(f"Opening: {filename}")

    def on_exit(self) -> None:
        if parent := self.parent():
            parent.close()

# ═══════════════════════════════════════════════════════════════
# View Menu with Checkable Actions
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

@window(title="QtPie Editor")
class EditorWindow(Window):
    # Application state
    _is_dirty: Variable[bool] = new(False)
    _status_message: Variable[str] = new("Ready")
    _recent_files: Variable[list[str]] = new([
        "document1.txt",
        "document2.txt"
    ])
    _word_wrap: Variable[bool] = new(True)
    _line_numbers: Variable[bool] = new(True)

    # Menus with bindings
    file_menu: FileMenu = new(
        is_dirty="_is_dirty",
        recent_files="_recent_files",
        on_new="new_document",
        on_save="save_document"
    )

    view_menu: ViewMenu = new(
        word_wrap="_word_wrap",
        line_numbers="_line_numbers"
    )

    # Main editor
    editor: QTextEdit = new()

    # Status bar with bindings
    status_bar: StatusBar = new(
        message="_status_message",
        is_modified="_is_dirty"
    )

    def new_document(self) -> None:
        self.editor.clear()
        self._is_dirty.value = False
        self._status_message.value = "New document"

    def save_document(self) -> None:
        # Save logic here...
        self._is_dirty.value = False
        self._status_message.value = "Saved"

# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from qtpie import entrypoint

    @entrypoint
    @window(title="QtPie Editor")
    class App(EditorWindow):
        pass
```

---

## Summary of Binding Syntax

| Syntax | Type | Description |
|--------|------|-------------|
| `var="_parent_var"` | Direct (two-way) | Share Observable with parent |
| `var="{expression}"` | Expression (one-way) | Computed from parent Variables |
| `var="literal"` | Literal | Set as initial value (no underscore, no braces) |
| `var=42` | Literal | Non-string literal value |

## Summary of Menu Syntax

| Syntax | Description |
|--------|-------------|
| `action: QAction = new("Text")` | Basic action |
| `action: QAction = new("Text", triggered="method")` | Action with handler |
| `action: QAction = new("Text", enabled="{_var}")` | Action with binding |
| `____: Separator` | Visual separator |
| `___name___: Section` | Section header ("Name") |
| `___name___: Section = new("Text")` | Section with explicit text |
| `actions: list[QAction] = new(bind="_var")` | Dynamic action list |
| `action: QAction = new(checkable=True, checked="_var")` | Checkable with binding |
