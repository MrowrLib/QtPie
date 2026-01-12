# QtPie - Context for Claude

## What Is This?

**QtPie** is a declarative UI library for Qt/PySide6 in Python. Think React/Vue patterns but for desktop apps. Or other GUI frameworks. And with the 'Conventions over Configuration' culture of Ruby on Rails.

## Project Structure

This is **v2** - a complete rewrite of QtPie.

- `lib/qtpie/` - The v2 QtPie library (active development)
- `lib/observant/` - The v2 observant library (reactive primitives)
- `v1/` - The original v1 codebase (reference only, uses `qtpy` for Qt abstraction)
- `tests/` - All tests for v2

### Observant Library

The `observant` library provides reactive primitives. Originally a separate project at `C:/Code/mrowr/MrowrLib/observant.py`, we're rewriting it here in `lib/observant/`:

- `Observable[T]` - Single reactive value
- `ObservableList[T]` - Reactive list with granular callbacks (on_insert, on_remove, etc.)
- `ObservableDict[K, V]` - Reactive dictionary with granular callbacks
- `ObservableProxy[T]` - Wraps any object, making its fields reactive

### Key Differences from v1

- v2 has `observant` integrated in the same repo
- v2 has much better typing and pyright strict compliance

We use `qtpy` for Qt abstraction so it works with PySide6 or PyQt6.

## Running Things

**Run tests frequently!**

```bash
# Run all tests
uv run pytest tests/ -v

# Type check
uv run pyright lib/qtpie/ tests/qtpie/

# Lint
uv run ruff check lib/qtpie/ tests/

# Format
uv run ruff format lib/qtpie/ tests/
```

---

## ⚠️ CRITICAL: BEFORE ANNOUNCING ANY FEATURE AS DONE ⚠️

**YOU MUST RUN ALL THREE CHECKS ON THE ENTIRE PROJECT BEFORE SAYING A FEATURE IS COMPLETE:**

```bash
# 1. Ruff (linting) - ENTIRE PROJECT
uv run ruff check lib/qtpie/ tests/

# 2. Pyright (type checking) - ENTIRE PROJECT
uv run pyright lib/qtpie/ tests/qtpie/

# 3. Pytest (tests) - ENTIRE PROJECT
uv run python -m pytest tests/ -v
```

**ALL THREE MUST PASS WITH ZERO ERRORS BEFORE YOU ANNOUNCE COMPLETION.**

- Do NOT run checks on just the files you modified
- Do NOT skip ruff because "pyright passed"
- Do NOT skip any of these checks for any reason
- Do NOT announce a feature as done until all three pass

If ANY check fails, fix it FIRST, then re-run ALL checks again.

---

## Design Principles

1. **Declarative over imperative** - define what, not how
2. **Type safety** - pyright strict, no `Any` leakage, no ignore comments
3. **Zero magic strings** - signals connected by method reference when possible
4. **Dataclass patterns** - `@dataclass_transform()` for IDE support
5. **Test-driven** - write tests first, then implement
6. **Minimal API surface** - few things that compose well

---

## Code Style - No Unnecessary Bullshit

**Don't add imports or code that isn't actually needed.**

- **NO `from __future__ import annotations`** - Python 3.13+ doesn't need it. Only use if you have actual forward references (rare).
- **NO unnecessary imports** - Don't import things "just in case"
- **NO cargo-cult patterns** - If you can't explain why something is needed, don't add it
- **NO defensive coding against impossible cases** - Trust the type system
- **NO premature abstractions** - Write concrete code first
- Only use `if TYPE_CHECKING` when it super makes sense to use it

When in doubt, leave it out. Simpler is better.

---

## ⚠️ Pyright Ignores Policy - CRITICAL ⚠️

**This library MUST be perfectly typed. End users should NEVER need pyright ignores.**

### In `lib/` (Library Code)

- **INLINE ignores only** - when absolutely necessary, use targeted inline comments
- **NEVER add file-header ignores** (like `# pyright: reportSomething=false`) blindly
- Every ignore must be justified and as narrow as possible
- The goal is ZERO ignores - each one is technical debt

```python
# GOOD - narrow, targeted, explained
value = some_call()  # pyright: ignore[reportUnknownMemberType] - Qt returns Any here

# BAD - never do this in lib/
# pyright: reportPrivateUsage=false  ← NO! Not at file header!
```

### In `tests/` (Test Code)

- **File-header ignores are OK** - tests often need relaxed typing
- Prefer header-level over inline to keep test code clean
- Common test file headers:

```python
# pyright: reportPrivateUsage=false
# pyright: reportMissingTypeArgument=false
```

### For End Users - ABSOLUTE RULE

**It is NEVER acceptable to ship library code that requires end users to add pyright ignores.**

- Users importing `qtpie` must get perfect type inference
- All public APIs must be fully typed with no `Any` leakage
- If a user needs `# type: ignore` to use our library, WE FAILED
- This is non-negotiable - we ship production-grade typed code

---

## Widget Examples

### Basic Widget

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget
class HelloWorld(Widget):
    _label: QLabel = new("Hello, World!")
    _button: QPushButton = new("Click Me")
```

### Widget with Reactive State (Variable)

```python
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton
from qtpie import Widget, Variable, new, widget

@widget
class Counter(Widget):
    # Variable[T] creates reactive state
    _count: Variable[int] = new(0)

    # Variable[T, W] creates reactive state + auto-bound widget
    _name: Variable[str, QLineEdit] = new("Enter name")

    # Regular widgets
    _label: QLabel = new("Count: 0")
    _increment: QPushButton = new("Increment", clicked="on_increment")

    def on_increment(self):
        self._count += 1  # Triggers reactive updates
```

### Widget with Record Type (Widget[T])

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit
from qtpie import Widget, new, widget

@dataclass
class Person:
    name: str = ""
    age: int = 0

# Option 1: Use record= decorator parameter (preferred - full pyright support)
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    # self.record.name and self.record.age autocomplete perfectly!
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age

# Option 2: Set record in __setup__ (for types without defaults)
@widget
class PersonEditor2(Widget[Person]):
    name: QLineEdit = new()
    age: QLineEdit = new()

    def __setup__(self) -> None:
        self.record = Person("Bob", 25)
```

**Key points about `Widget[T]`:**
- `self.record` is an `ObservableProxy[T]` - field access/assignment is reactive
- `self.record_state` gives access to `.is_dirty`, `.value`, `.observable`
- Fields named same as record properties auto-bind (e.g., `name: QLineEdit` binds to `record.name`)
- Use `record=` decorator param to avoid pyright errors about overriding the `record` property

### List Binding with WidgetRepeater

```python
from PySide6.QtWidgets import QLabel
from qtpie import Widget, Variable, new, widget

@widget
class TodoList(Widget):
    # Source data
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])

    # list[QWidget] bound to a Variable creates a WidgetRepeater
    # One QLabel per item, auto-synced when list changes
    _labels: list[QLabel] = new(bind="_items")

    def add_item(self, text: str):
        self._items.append(text)  # Automatically creates new QLabel
```

### List with Custom Format

```python
@widget
class NumberList(Widget):
    _numbers: Variable[list[int]] = new([1, 2, 3])

    # format= customizes how items are displayed
    _labels: list[QLabel] = new(
        bind="_numbers",
        format="Item #{#index}: {#self}"  # "Item #0: 1", "Item #1: 2", etc.
    )
```

### Dict Binding

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})

    # Dict binding with key/value placeholders
    _labels: list[QLabel] = new(
        bind="_scores",
        format="{#key}: {#value} points"  # "Alice: 100 points"
    )
```

### Variable with Widget Type (Inline)

```python
@widget
class InlineWidgets(Widget):
    # Variable[T, W] - creates T observable + W widget, auto-bound
    _username: Variable[str, QLineEdit] = new("")(placeholderText="Username")
    _password: Variable[str, QLineEdit] = new("")(placeholderText="Password", echoMode=QLineEdit.EchoMode.Password)

    # Access the widget via .widget property
    def focus_username(self):
        self._username.widget.setFocus()
```

### Object Name and CSS Classes

```python
@widget(name="main-window", classes=["dark-theme"])
class StyledWidget(Widget):
    # objectName defaults to field name, or explicit name=
    _title: QLabel = new("Title", name="page-title", classes=["header"])
    _content: QLabel = new("Content")  # objectName = "_content"

    # Widget class objectName defaults to class name
    # So #StyledWidget works in QSS (if name= not set)
```

### Signal Connections

```python
@widget
class ButtonExample(Widget):
    # Connect signal to method by name
    _save: QPushButton = new("Save", clicked="on_save")

    # Or connect to lambda
    _cancel: QPushButton = new("Cancel", clicked=lambda: print("Cancelled"))

    def on_save(self):
        print("Saved!")
```

### The `new()` Function

`new()` is the factory for creating fields:

```python
# Positional args go to widget constructor
_button: QPushButton = new("Button Text")

# Keyword args: some are QtPie special, rest go to constructor
_field: QLineEdit = new(
    bind="_some_var",       # QtPie: bind to variable
    name="my-field",        # QtPie: set objectName
    classes=["input"],      # QtPie: set CSS classes
    clicked="on_click",     # QtPie: signal connection
    placeholderText="...",  # Qt: passed to constructor
)

# For Variable[T, W], chain calls:
_name: Variable[str, QLineEdit] = new("default")(placeholderText="Name...")
#                                     ^          ^
#                                     |          Widget kwargs
#                                     Variable default value
```

### Layout Types

```python
@widget(layout="vertical")   # Default - QVBoxLayout
class VBox(Widget): ...

@widget(layout="horizontal") # QHBoxLayout
class HBox(Widget): ...

@widget(layout="form")       # QFormLayout - use label= on fields
class Form(Widget):
    _name: QLineEdit = new(label="Name:")
    _email: QLineEdit = new(label="Email:")

@widget(layout="grid")       # QGridLayout - use grid= on fields
class Grid(Widget):
    _a: QLabel = new("A", grid=(0, 0))
    _b: QLabel = new("B", grid=(0, 1))
    _c: QLabel = new("C", grid=(1, 0, 1, 2))  # row, col, rowspan, colspan
```

### Entrypoint

```python
from qtpie import entrypoint

@entrypoint
@widget
class MyApp(Widget):
    _label: QLabel = new("Hello!")

# Just run: python my_app.py
# The @entrypoint decorator handles QApplication setup
```

---

## Format String Bindings (Complex Expressions)

The `bind=` parameter supports complex Python expressions in format strings:

### Basic Expressions

```python
@widget
class Example(Widget):
    _name: Variable[str] = new("hello")
    _count: Variable[int] = new(42)

    # Function calls
    _len_label: QLabel = new(bind="Length: {len(_name)}")

    # String methods
    _upper_label: QLabel = new(bind="Upper: {_name.upper()}")

    # Math expressions
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _math_label: QLabel = new(bind="Sum: {_x + _y}, Product: {_x * _y}")

    # Complex math with parentheses
    _z: Variable[int] = new(5)
    _complex: QLabel = new(bind="Result: {(_x + _y) * _z}")

    # Format specs (Python format string syntax)
    _price: Variable[float] = new(19.99)
    _price_label: QLabel = new(bind="Price: ${_price:.2f}")

    # Instance methods
    def compute(self) -> str:
        return "computed value"

    _computed: QLabel = new(bind="Value: {compute()}")

    # Methods with parameters
    def repeat(self, s: str, n: int) -> str:
        return s * n

    _repeated: QLabel = new(bind="{repeat(_name, 3)}")
```

### Special Placeholders

| Placeholder | Description                                                      |
| ----------- | ---------------------------------------------------------------- |
| `{#self}`   | Variable's value (in `Variable[T,W]` context) or Widget instance |
| `{#var}`    | Explicit reference to Variable's value                           |
| `{#widget}` | Explicit reference to parent Widget instance                     |
| `{#index}`  | Item index (in list/dict repeaters)                              |
| `{#key}`    | Dict key (in dict repeaters)                                     |
| `{#value}`  | Dict value (in dict repeaters)                                   |

### Variable[T, W] with bind=

```python
@widget
class Example(Widget):
    # #self refers to the Variable's value ("Hello"), not the widget
    _name: Variable[str, QLabel] = new("Hello")(bind="Value: {#self}")

    # Use expressions on #self
    _upper: Variable[str, QLabel] = new("hello")(bind="Upper: {#self.upper()}")
    _len: Variable[str, QLabel] = new("hello")(bind="Length: {len(#self)}")

    # #var is explicit alias for Variable's value
    _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")

    # #widget refers to parent widget (for accessing widget attributes)
    title: str = "MyWidget"
    _with_title: Variable[str, QLabel] = new("x")(bind="Title: {#widget.title}")

    # Combine them all
    _combo: Variable[int, QLabel] = new(5)(
        bind="{#widget.title}: value={#self}, doubled={#var * 2}"
    )
```

### List Repeater Placeholders

```python
@widget
class ListExample(Widget):
    _numbers: Variable[list[int], QLabel] = new([1, 2, 3])(
        bind="Index {#index}: value is {#self}"
        # Output: "Index 0: value is 1", "Index 1: value is 2", etc.
    )

    # With complex objects
    _dogs: Variable[list[Dog], QLabel] = new([Dog("Fido", 3)])(
        bind="{name} is {age} years old"  # Direct property access
    )
```

### Dict Repeater Placeholders

```python
@widget
class DictExample(Widget):
    _scores: Variable[dict[str, int], QLabel] = new({"Alice": 100})(
        bind="{#key} scored {#value} points"
    )

    # #self and #value are aliases for dict values
    _dogs: Variable[dict[str, Dog], QLabel] = new({"Fido": Dog("Fido", 3)})(
        bind="{#key}: {#self.name} is {age} years old"
    )
```

### Reactivity

All format bindings are reactive - when any referenced Variable changes, the expression is re-evaluated and the widget updates automatically:

```python
@widget
class ReactiveExample(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _sum: QLabel = new(bind="Sum: {_x + _y}")  # Shows "Sum: 30"

    def update_x(self):
        self._x.value = 50  # _sum automatically updates to "Sum: 70"
```

---

## Window Examples

`Window` is like `Widget` but for `QMainWindow`. Menus are auto-added to the menu bar.

### Basic Window

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Window, new, window

@window(title="My App")
class MainWindow(Window):
    label: QLabel = new("Hello!")
    button: QPushButton = new("Click")
```

### Window with Menus

```python
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from qtpie import Window, new, window, menu

@menu("&File")
class FileMenu(QMenu):
    action_new: QAction = new("&New", triggered="on_new")
    action_exit: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        print("New!")

    def on_exit(self) -> None:
        print("Exit!")

@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()  # Auto-added to menu bar
    label: QLabel = new("Content")
```

### Window with Record Type

```python
@dataclass
class AppState:
    username: str = ""
    dark_mode: bool = False

@window(title="Settings", record=AppState("admin", True))
class SettingsWindow(Window[AppState]):
    username: QLineEdit = new()  # Auto-binds to record.username
```

---

## Property Bindings (visible=, enabled=)

Control widget visibility and enabled state reactively:

```python
@widget
class ConditionalUI(Widget):
    _show_advanced: Variable[bool] = new(False)
    _has_input: Variable[bool] = new(False)

    # Simple variable binding
    advanced_panel: QWidget = new(visible="_show_advanced")

    # Expression binding
    submit_btn: QPushButton = new("Submit", enabled="{len(_name) > 0}")

    # With Variable
    _name: Variable[str] = new("")
    name_error: QLabel = new("Name required!", visible="{len(_name) == 0}")
```

---

## Dirty Tracking

Track whether fields have changed from their initial values:

```python
@widget
class DirtyExample(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def check_dirty(self):
        # Check if any field changed
        if self.is_dirty.get():
            print(f"Changed fields: {self.dirty_fields}")

        # Reset all to clean
        self.reset_dirty()

    # Optional lifecycle hook - fires on state transitions only
    def on_dirty_changed(self, is_dirty: bool) -> None:
        self.save_btn.setEnabled(is_dirty)
```

---

## Validation

Add validators to fields and check validity:

```python
@widget
class ValidatedForm(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)
    _errors: QLabel = new(bind="{', '.join(validation_error_messages)}")

    def __setup__(self) -> None:
        # Add named validators (can be replaced/removed by name)
        self.add_validator("_name", "required", lambda v: None if v else "Name required")
        self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Min 3 chars")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

    def on_submit(self):
        if self.is_valid:
            print("Form is valid!")
        else:
            # Structured: {field: {validator: [errors]}}
            print(self.validation_errors)
            # Flat list of all error messages
            print(self.validation_error_messages)

    # Optional lifecycle hook
    def on_valid_changed(self, is_valid: bool) -> None:
        self.submit_btn.setEnabled(is_valid)
```

---

## Reactive Decorator Properties

Decorator kwargs can reference Variables for reactive properties:

```python
@widget(windowTitle="{_title}")  # Reactive!
class DynamicTitle(Widget):
    _title: Variable[str] = new("Initial Title")

    def update_title(self):
        self._title.value = "New Title"  # Window title updates automatically

@window(title="{_app_name} - {_filename}")
class EditorWindow(Window):
    _app_name: Variable[str] = new("MyEditor")
    _filename: Variable[str] = new("untitled.txt")
```

---

## Translations (i18n)

QtPie provides a declarative translation system using `t()` for marking translatable strings.

### Basic Usage

```python
from qtpie import Widget, new, t, widget

@widget
class MyWidget(Widget):
    # Mark strings for translation with t()
    label: QLabel = new(t("Hello"))
    button: QPushButton = new(t("Click Me"))
```

### With @entrypoint

```python
from qtpie import Widget, entrypoint, new, t, widget

@entrypoint(
    translations="translations.yml",  # Path to YAML file
    language="fr",                    # Language code
    watch_translations=True,          # Hot-reload in dev
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))  # Shows "Bonjour" when language="fr"
```

### Runtime Language Switching

```python
from qtpie import set_language

def change_to_french(self) -> None:
    set_language("fr")  # Automatically retranslates all t() widgets
```

### Translation YAML Format

```yaml
# translations.yml

# Global translations (available to all widgets)
:global:
    Hello:
        en: Hello
        fr: Bonjour
        de: Hallo

    # Disambiguation - same source, different meanings
    "Open|menu":
        en: Open
        fr: Ouvrir

    "Open|status":
        en: Open
        fr: Ouvert

    # Plurals - use %n for count
    "%n file(s)":
        en:
            - "%n file"
            - "%n files"
        fr:
            - "%n fichier"
            - "%n fichiers"

    # Translator notes
    Submit:
        :note: Button for form submission
        en: Submit
        fr: Soumettre

# Widget-specific translations (context = class name)
MainWindow:
    Title:
        en: My Application
        fr: Mon Application
```

### Disambiguation

When the same source text has different meanings:

```python
@widget
class MyWidget(Widget):
    # Use context= to disambiguate
    menu_open: QAction = new(t("Open", context="menu"))    # "Ouvrir"
    status_open: QLabel = new(t("Open", context="status")) # "Ouvert"
```

### Plurals

```python
# In code - call t() with count
label.setText(t("%n file(s)")(5))  # "5 files" or "5 fichiers"
```

### CLI Commands

```bash
# Compile YAML to Qt .ts files
uv run qtpie tr compile translations.yml -o ./i18n/

# Also generate .qm binary files (requires lrelease)
uv run qtpie tr compile translations.yml -o ./i18n/ --qm

# Compile specific languages only
uv run qtpie tr compile translations.yml -o ./i18n/ --lang fr --lang de

# List all translations
uv run qtpie tr list translations.yml
```

### Key Functions

| Function                 | Description                         |
| ------------------------ | ----------------------------------- |
| `t("text")`              | Mark string for translation         |
| `t("text", context="x")` | Mark with disambiguation            |
| `t("%n item(s)")(n)`     | Plural with count                   |
| `set_language("fr")`     | Change language (auto-retranslates) |

### Architecture

- `t()` returns a `Translatable` marker (lazy resolution)
- Translation context defaults to widget class name
- Falls back to `:global:` (`@default`) if no widget-specific translation
- In-memory store for dev (hot-reload), QTranslator for production (.qm files)
- Widgets using `t()` are registered for automatic retranslation

---

## Key Architecture Notes

### Class Hierarchy
- `Widget` → `QWidget` with declarative features
- `Window` → `QMainWindow` with declarative features (menus auto-added to menu bar)
- Both support `[T]` type parameter for record types

### Config Objects
- `Widget` uses `_QtPieConfig` (stored in `cls._qtpie_config`)
- `Window` uses `WindowConfig` (dataclass, stored in `cls._qtpie_config`)
- Instance state in `self._qtpie` (`QtPieState`)

### Descriptor Pattern
- `_RecordDescriptor` handles `self.record` access for `Widget[T]`/`Window[T]`
- `_VariableDescriptor` handles `Variable[T]` field access
- Both use lazy initialization

### The `new()` Factory
- Returns `NewField` instance at class definition time
- Processed by `new_fields()` in `__init_subclass__`
- Converted to proper descriptors or widget instances

### Signal Auto-Connect
- `clicked="method_name"` → connects to `self.method_name`
- `clicked=lambda: ...` → connects directly
- Happens in wrapped `__init__` after widget creation

## Issue Tracking

This project uses **bd (beads)** for issue tracking.
Run `bd prime` for workflow context, or install hooks (`bd hooks install`) for auto-injection.

**Quick reference:**
- `bd ready` - Find unblocked work
- `bd create "Title" --type task --priority 2` - Create issue
- `bd close <id>` - Complete work
- `bd sync` - Sync with git (run at session end)

For full workflow details: `bd prime`