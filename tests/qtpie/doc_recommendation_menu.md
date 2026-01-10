# Menu Documentation Proposal

## Priority: HIGH

Menus are a core feature for desktop applications and a key differentiator for QtPie. The `@menu` decorator and `Menu` class provide declarative menu creation with full reactive state support, making menu management significantly simpler than plain Qt.

---

## Files to Add/Update

### New Files to Create

1. **`docs/reference/decorators/menu.md`** (already in nav)
   - Reference documentation for `@menu` decorator
   - All decorator parameters and their effects

2. **`docs/reference/classes/menu.md`** (add to nav)
   - Reference documentation for `Menu` class
   - API surface, properties, methods

### Files to Update

1. **`docs/guides/windows-menus.md`** (already exists per nav)
   - Add comprehensive menu examples
   - Show menu + window integration patterns
   - Cover common use cases (File, Edit, View menus)

2. **`docs/index.md`**
   - Add menu example to "Key Features" section
   - Show menu as part of declarative UI story

3. **`docs/why-qtpie.md`**
   - Add before/after comparison for menus
   - Highlight declarative menu creation vs imperative Qt

---

## Suggested Nav Location

### In `mkdocs.yml`

```yaml
nav:
  # ... existing ...
  - Reference:
      - Decorators:
          - "@widget": reference/decorators/widget.md
          - "@window": reference/decorators/window.md
          - "@menu": reference/decorators/menu.md  # Already present
          - "@slot": reference/decorators/slot.md
          - "@entrypoint": reference/decorators/entrypoint.md
      - Factories:
          - "new()": reference/factories/new.md
      - Classes:
          - Widget: reference/classes/widget.md
          - Window: reference/classes/window.md
          - Menu: reference/classes/menu.md  # ADD THIS
          - Variable: reference/classes/variable.md
```

---

## Content Outline

### 1. `docs/reference/decorators/menu.md`

**Purpose:** Complete reference for `@menu` decorator

**Sections:**

- **Overview**
  - What is `@menu`?
  - When to use it
  - Basic syntax

- **Parameters**
  - `text=` - Menu title (with & for mnemonics)
  - `name=` - objectName for styling
  - `record=` - Bind dataclass for Menu[T]
  - Default behaviors (title from class name)

- **Field Types Supported**
  - `QAction` - Standard actions
  - `Separator` - Menu separators
  - `Section` - Section headers
  - `Variable[T]` - Reactive state
  - `Variable[T] = new(default)` - Optional state
  - `list[QAction]` - ActionRepeater for dynamic actions
  - Nested `Menu` subclasses (submenus)

- **Signal Connections**
  - `triggered="method_name"` pattern
  - Lambda handlers
  - Auto-connection behavior

- **Auto-Integration with Window**
  - How menus are automatically added to menu bar
  - Declaration order preservation

- **Examples**
  - Minimal menu
  - File menu with actions
  - View menu with checkable actions
  - Window menu with dynamic list
  - Nested submenu

---

### 2. `docs/reference/classes/menu.md`

**Purpose:** Complete reference for `Menu` class

**Sections:**

- **Overview**
  - Inherits from `QMenu`
  - Provides reactive state management
  - Works with `@menu` decorator

- **Type Parameters**
  - `Menu[T]` - Bind to record type
  - `self.record` property
  - `self.record_state` property

- **Properties**
  - `is_dirty: Observable[bool]` - Dirty tracking
  - `dirty_fields: set[str]` - Which fields changed
  - `is_valid: Observable[bool]` - Validation state
  - `validation_errors: dict` - Structured errors
  - `validation_error_messages: list[str]` - Flat error list

- **Methods**
  - `add_validator(field, name, func)` - Add validation rule
  - `remove_validator(field, name)` - Remove validation rule
  - `reset_dirty()` - Reset dirty tracking
  - `__setup__()` - Lifecycle hook for initialization

- **Lifecycle Hooks**
  - `on_dirty_changed(is_dirty: bool)` - Fires on dirty state changes
  - `on_valid_changed(is_valid: bool)` - Fires on validation state changes

- **Variable Bindings**
  - Required bindings (`Variable[T]` without default)
  - Optional bindings (`Variable[T] = new(default)`)
  - Binding from parent Window via `new(var="_parent_var")`

- **Examples**
  - Basic menu with state
  - Menu with validation
  - Menu[T] with record type
  - Menu with required bindings

---

### 3. `docs/guides/windows-menus.md`

**Purpose:** Practical guide for creating windows with menus

**Sections:**

- **Introduction**
  - Why menus matter in desktop apps
  - QtPie's declarative approach

- **Basic Window with Menu**
  - Simple File menu example
  - Action connections
  - Code walkthrough

- **Common Menu Patterns**
  - **File Menu** - New, Open, Save, Exit
  - **Edit Menu** - Undo, Redo, Cut, Copy, Paste
  - **View Menu** - Checkable actions (Word Wrap, Status Bar)
  - **Window Menu** - Dynamic list of open windows
  - **Help Menu** - About, Documentation

- **Checkable Actions**
  - Two-way binding with Variable[bool]
  - Toggle state management
  - Use case: preferences/settings

- **Dynamic Menus (ActionRepeater)**
  - Recent files list
  - Open windows list
  - Format strings with `{#self}`, `{#index}`
  - Handler receives the item

- **Section Headers and Separators**
  - Using `Separator` annotation
  - Using `Section` annotation
  - Naming conventions for sections

- **Menus with State**
  - Sharing state between menu and window
  - Required bindings pattern
  - `{#parent}` escape hatch

- **Enabled/Visible Actions**
  - Reactive `enabled=` bindings
  - Example: Save only when dirty
  - Example: Undo only when history available

- **Submenus**
  - Nested Menu classes
  - Example: File → Recent Files submenu

- **Menu Validation and Dirty Tracking**
  - When to use validation in menus
  - Tracking menu-specific state changes

- **Complete Example**
  - Full text editor with File, Edit, View, Help menus
  - Integration with Window
  - State management

---

### 4. Update `docs/index.md`

**Add to "Key Features" section:**

```markdown
### Declarative Menus

Create menus with actions, sections, and dynamic lists using the same declarative pattern:

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New", triggered="on_new")
    open_action: QAction = new("&Open", triggered="on_open")
    ____: Separator
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        # Handle new file
        pass

@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()  # Auto-added to menu bar
```
```

---

### 5. Update `docs/why-qtpie.md`

**Add new section after "The Solution":**

```markdown
## Menu Example

### Plain Qt Menus

```python
from PySide6.QtWidgets import QMainWindow, QMenu
from PySide6.QtGui import QAction

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Create menu bar
        menubar = self.menuBar()

        # Create File menu
        file_menu = QMenu("&File", self)
        menubar.addMenu(file_menu)

        # Create actions
        new_action = QAction("&New", self)
        new_action.triggered.connect(self.on_new)
        file_menu.addAction(new_action)

        open_action = QAction("&Open", self)
        open_action.triggered.connect(self.on_open)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # More menus...

    def on_new(self) -> None:
        pass

    def on_open(self) -> None:
        pass
```

**Problems:**
- Manual menu creation and population
- Manual action creation and adding
- Manual signal connections
- Verbose and error-prone
- Hard to maintain action order
- Separators break the flow

### QtPie Menus

```python
from qtpie import Window, Menu, window, menu, new
from PySide6.QtGui import QAction

@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New", triggered="on_new")
    open_action: QAction = new("&Open", triggered="on_open")
    ____: Separator
    exit_action: QAction = new("E&xit", triggered="close")

    def on_new(self) -> None:
        pass

    def on_open(self) -> None:
        pass

@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()  # Auto-added to menu bar
```

**Benefits:**
- Declarative action definition
- Clear visual structure
- Automatic menu bar integration
- Type-safe action references
- Separators as fields preserve order
- Signal connections in action definition
```

**Update feature comparison table:**

Add row:
```markdown
| Menus | Manual QMenu/QAction | Declarative `@menu` |
```

---

## Code Examples Needed

### Basic Examples

1. **Minimal menu**
   ```python
   @menu(text="&File")
   class FileMenu(Menu):
       new_action: QAction = new("&New")
   ```

2. **Menu with actions and handlers**
   ```python
   @menu(text="&File")
   class FileMenu(Menu):
       new_action: QAction = new("&New", triggered="on_new")

       def on_new(self) -> None:
           print("New file")
   ```

3. **Menu with separator**
   ```python
   @menu(text="&File")
   class FileMenu(Menu):
       new_action: QAction = new("&New")
       ____: Separator
       exit_action: QAction = new("E&xit")
   ```

4. **Menu with section header**
   ```python
   @menu(text="&File")
   class FileMenu(Menu):
       ___recent___: Section
       file1: QAction = new("file1.txt")
       file2: QAction = new("file2.txt")
   ```

### Intermediate Examples

5. **Checkable action with Variable binding**
   ```python
   @menu(text="&View")
   class ViewMenu(Menu):
       _word_wrap: Variable[bool] = new(False)
       word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")
   ```

6. **ActionRepeater (dynamic actions)**
   ```python
   @menu(text="&Window")
   class WindowMenu(Menu):
       _windows: Variable[list[str]] = new(["Main", "Settings"])
       window_actions: list[QAction] = new(
           bind="_windows",
           format="Open {#self}",
           triggered="on_switch_window"
       )

       def on_switch_window(self, window_name: str) -> None:
           print(f"Switching to {window_name}")
   ```

7. **Menu with enabled binding**
   ```python
   @menu(text="&Edit")
   class EditMenu(Menu):
       _can_undo: Variable[bool] = new(False)
       undo: QAction = new("Undo", enabled="{_can_undo}")
   ```

### Advanced Examples

8. **Menu with required binding from Window**
   ```python
   @menu(text="&File")
   class FileMenu(Menu):
       is_dirty: Variable[bool]  # Required binding
       save: QAction = new("&Save", enabled="{is_dirty}")

   @window(title="Editor")
   class EditorWindow(Window):
       _is_dirty: Variable[bool] = new(False)
       file_menu: FileMenu = new(is_dirty="_is_dirty")
   ```

9. **Menu[T] with record type**
   ```python
   @dataclass
   class EditState:
       can_undo: bool = False
       can_redo: bool = False

   @menu(text="&Edit", record=EditState())
   class EditMenu(Menu[EditState]):
       undo: QAction = new("Undo", enabled="{record.can_undo}")
       redo: QAction = new("Redo", enabled="{record.can_redo}")
   ```

10. **Complete application with multiple menus**
    ```python
    @menu(text="&File")
    class FileMenu(Menu):
        new_action: QAction = new("&New", triggered="on_new")
        open_action: QAction = new("&Open", triggered="on_open")
        ____: Separator
        exit_action: QAction = new("E&xit", triggered="on_exit")

        def on_new(self) -> None:
            pass

        def on_open(self) -> None:
            pass

        def on_exit(self) -> None:
            pass

    @menu(text="&Edit")
    class EditMenu(Menu):
        _can_undo: Variable[bool] = new(False)
        undo: QAction = new("Undo", enabled="{_can_undo}")
        redo: QAction = new("Redo")

    @menu(text="&View")
    class ViewMenu(Menu):
        _word_wrap: Variable[bool] = new(False)
        word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")

    @window(title="Text Editor")
    class MainWindow(Window):
        file_menu: FileMenu = new()
        edit_menu: EditMenu = new()
        view_menu: ViewMenu = new()
        _content: QTextEdit = new()
    ```

---

## Cross-References

### Links to Include

**In menu docs:**
- Link to `@window` decorator (menus integrate with windows)
- Link to `Window` class (parent container)
- Link to `Variable` class (reactive state)
- Link to `new()` factory (field creation)
- Link to bindings guide (format expressions)
- Link to validation guide (menu validation)
- Link to dirty tracking guide (menu dirty state)
- Link to signals guide (action connections)

**From other docs to menu:**
- `docs/guides/windows-menus.md` → link to `@menu` reference
- `docs/reference/decorators/window.md` → link to menu integration
- `docs/reference/classes/window.md` → link to menu fields
- `docs/state/bindings.md` → include menu binding examples
- `docs/basics/signals.md` → include action signal examples

### Related Features

- **Window** - Menus are children of Windows
- **Variable** - Menus use Variables for reactive state
- **Bindings** - Menus support all binding features
- **Validation** - Menus support validation like Widgets
- **Dirty Tracking** - Menus track state changes
- **Signals** - Actions connect to methods/lambdas
- **Record Types** - Menu[T] pattern like Widget[T]

---

## Key Documentation Points

### Must Cover

1. **Automatic menu bar integration** - Menus declared as Window fields are auto-added
2. **Declaration order matters** - Fields appear in menu in declaration order
3. **Separator and Section patterns** - Field name ignored, just the annotation matters
4. **ActionRepeater** - Dynamic lists of actions from Variables
5. **Checkable actions** - Two-way binding with Variable[bool]
6. **Required bindings** - Menu fields that must be provided by parent
7. **`{#parent}` escape hatch** - Access parent Window variables
8. **Menu[T] pattern** - Record-bound menus for complex state
9. **Signal connections** - `triggered="method"` vs lambda vs no connection
10. **Handler signatures** - ActionRepeater handlers receive the item

### Common Pitfalls

1. **Forgetting & for mnemonics** - `"&File"` not `"File"`
2. **Wrong separator syntax** - Use `____: Separator` not `Separator()`
3. **Section naming** - Must start/end with `___` for auto-naming
4. **Required bindings** - Must provide when instantiating menu
5. **ActionRepeater handler** - Must accept the item parameter

### Design Philosophy Notes

- Menus use same patterns as Widgets (Variables, bindings, validation, etc.)
- Declarative field order = visual menu order
- Type annotations drive behavior (QAction, Separator, Section, list[QAction])
- Convention over configuration (title from class name, etc.)

---

## Additional Resources to Link

- PySide6 QMenu documentation (external)
- PySide6 QAction documentation (external)
- Keyboard shortcuts/mnemonics explanation (external or in-doc)
- Menu design best practices (external or in-doc)

---

## Testing Examples

For `docs/guides/testing.md`, include menu testing patterns:

```python
def test_menu_action_triggers_handler():
    """Test that menu actions trigger their handlers"""

    @menu(text="File")
    class FileMenu(Menu):
        triggered = False
        new_action: QAction = new("New", triggered="on_new")

        def on_new(self) -> None:
            self.triggered = True

    m = FileMenu()
    m.new_action.trigger()
    assert m.triggered is True

def test_action_repeater_updates():
    """Test that ActionRepeater updates with list changes"""

    @menu(text="Window")
    class WindowMenu(Menu):
        _windows: Variable[list[str]] = new(["Win1"])
        window_actions: list[QAction] = new(bind="_windows")

    m = WindowMenu()
    assert len(m.actions()) == 1

    m._windows.append("Win2")
    assert len(m.actions()) == 2
```

---

## Summary

The menu feature is **high priority** because:

1. **Core desktop app feature** - Most desktop apps need menus
2. **Major QtPie differentiator** - Declarative menus vs imperative Qt is a big win
3. **Feature complete** - Menus have all the bells and whistles (Variables, validation, dirty tracking, bindings)
4. **Well tested** - test_menu.md shows comprehensive test coverage
5. **User-facing impact** - Developers will use this immediately

The documentation should:
- **Emphasize simplicity** - Show how easy declarative menus are vs Qt
- **Show integration** - Menus + Windows work seamlessly together
- **Cover common patterns** - File, Edit, View menus are standard
- **Include complete examples** - Full app examples help developers
- **Reference existing patterns** - Link to Variable, bindings, validation docs
