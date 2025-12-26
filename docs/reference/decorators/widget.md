# @widget

The `@widget` decorator transforms a Python class into a Qt widget with automatic layout management, signal connections, and optional data binding.

## Basic Usage

### Without Parentheses

For default settings, use `@widget` without parentheses:

```python
from qtpy.QtWidgets import QWidget, QLabel
from qtpie import widget, make

@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello World")
```

### With Parentheses

To customize behavior, use `@widget()` with parameters:

```python
@widget(layout="horizontal", name="MyCustomWidget", classes=["card", "shadow"])
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")
```

## Parameters

### layout

**Type:** `Literal["vertical", "horizontal", "form", "grid", "none"]`
**Default:** `"vertical"`

Controls the automatic layout type:

- `"vertical"` - Creates a `QVBoxLayout`, stacking widgets vertically
- `"horizontal"` - Creates a `QHBoxLayout`, arranging widgets horizontally
- `"form"` - Creates a `QFormLayout` for label-field pairs (see [Form Layouts](../../guides/forms.md))
- `"grid"` - Creates a `QGridLayout` for grid-based layouts (see [Grid Layouts](../../guides/grids.md))
- `"none"` - No automatic layout (manage layout manually)

**Examples:**

```python
@widget(layout="horizontal")
class Toolbar(QWidget):
    button1: QPushButton = make(QPushButton, "Save")
    button2: QPushButton = make(QPushButton, "Load")
    # Buttons will be arranged horizontally
```

```python
@widget(layout="none")
class CustomWidget(QWidget):
    def setup(self) -> None:
        # Manually manage layout
        layout = QVBoxLayout(self)
        # ... custom layout code
```

### name

**Type:** `str | None`
**Default:** `None` (auto-derived from class name)

Sets the widget's `objectName` for QSS/CSS styling. If not provided, the name is auto-generated from the class name (with "Widget" suffix removed if present).

**Examples:**

```python
@widget(name="MainEditor")
class EditorWidget(QWidget):
    pass

# objectName will be "MainEditor"
```

```python
@widget()
class EditorWidget(QWidget):
    pass

# objectName will be "Editor" (auto-stripped "Widget" suffix)
```

```python
@widget()
class Editor(QWidget):
    pass

# objectName will be "Editor"
```

### classes

**Type:** `list[str] | None`
**Default:** `None`

Sets CSS-like class names on the widget as a Qt property. Used for styling with QSS selectors.

**Example:**

```python
@widget(classes=["card", "shadow"])
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Styled")

# Can now style with QSS:
# QWidget[class~="card"] { background: white; padding: 10px; }
# QWidget[class~="shadow"] { border: 1px solid #ccc; }
```

See [Styling Guide](../../basics/styling.md) for more details.

### auto_bind

**Type:** `bool`
**Default:** `True`

Controls automatic binding of widget fields to model properties by matching field names. Only applies to `Widget[T]` model widgets.

When `True`, widget fields with names matching model properties are automatically bound bidirectionally. When `False`, only explicit `bind=` bindings work.

**Example with auto_bind=True (default):**

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QLineEdit, QSpinBox

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget()  # auto_bind=True by default
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # Auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # Auto-binds to model.age

editor = PersonEditor()
editor.name.setText("Alice")
print(editor.record.name)  # "Alice" - auto-synced!
```

**Example with auto_bind=False:**

```python
@widget(auto_bind=False)
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # NOT auto-bound
    age: QSpinBox = make(QSpinBox, bind="age")  # Explicit bind still works

editor = PersonEditor()
editor.name.setText("Bob")
print(editor.record.name)  # "" - no auto-binding
editor.age.setValue(30)
print(editor.record.age)   # 30 - explicit bind works
```

See [Record Widgets](../../data/record-widgets.md) for more details.

### undo

**Type:** `bool`
**Default:** `False`

Enables undo/redo functionality for `Widget[T]` model widgets. When enabled, creates an undo history for all model field changes.

**Example:**

```python
@widget(undo=True)
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)

editor = PersonEditor()
editor.name.setText("Alice")
editor.name.setText("Bob")

editor.undo("name")  # Reverts to "Alice"
editor.redo("name")  # Restores "Bob"
```

See [Undo & Redo](../../data/undo.md) for complete API.

### undo_max

**Type:** `int | None`
**Default:** `None` (unlimited)

Sets the maximum number of undo steps to store per field. Only applies when `undo=True`.

**Example:**

```python
@widget(undo=True, undo_max=50)
class TextEditor(QWidget, Widget[Document]):
    content: QTextEdit = make(QTextEdit)
    # Only last 50 changes are kept in history
```

### undo_debounce_ms

**Type:** `int | None`
**Default:** `None` (no debouncing)

Debounce time in milliseconds for recording undo snapshots. Useful for text input to avoid recording every keystroke. Only applies when `undo=True`.

**Example:**

```python
@widget(undo=True, undo_debounce_ms=500)
class TextEditor(QWidget, Widget[Document]):
    content: QTextEdit = make(QTextEdit)
    # Undo snapshot only recorded 500ms after user stops typing
```

## Lifecycle Hook

Override `setup()` to customize initialization after fields are ready:

```python
@widget()
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Initial")

    def setup(self) -> None:
        # Widget fields are accessible here
        self.label.setText("Modified in setup")
```

## Async closeEvent

The `@widget` decorator automatically wraps async `closeEvent` methods with `qasync.asyncClose`, allowing cleanup operations to complete before the widget is destroyed:

```python
import asyncio

@widget
class MyWidget(QWidget):
    async def closeEvent(self, event: QCloseEvent) -> None:
        # Async cleanup - runs to completion before window closes
        await self.save_data_async()
        await self.disconnect_services()
        event.accept()
```

Without this automatic wrapping, an async `closeEvent` would not wait for the coroutine to complete, potentially causing data loss or incomplete cleanup.

**Requirements:** Requires `qasync` to be installed. If qasync is not available, async closeEvent methods are not wrapped.

## Widget Field Behavior

### Automatic Layout Addition

Widget fields (subclasses of `QWidget`) are automatically added to the layout in declaration order:

```python
@widget()
class MyWidget(QWidget):
    first: QLabel = make(QLabel, "First")
    second: QPushButton = make(QPushButton, "Second")
    third: QLabel = make(QLabel, "Third")
    # Layout order: first → second → third
```

### Field Naming Conventions

QtPie uses underscore conventions to control field behavior:

| Field | Layout | objectName | Auto-bind |
|-------|--------|------------|-----------|
| `foo` | ✅ Added | `foo` | to `foo` |
| `_foo` | ✅ Added | `_foo` | to `foo` (strips `_`) |
| `_foo_` | ❌ Excluded | `_foo_` | ❌ None |

**Private fields (`_foo`)** are included in the layout but auto-bind with the underscore stripped. Useful for encapsulation while keeping widgets in the layout:

```python
@widget()
class MyWidget(QWidget, Widget[Person]):
    _name: QLineEdit = make(QLineEdit)  # Added to layout, binds to record.name
    _age: QSpinBox = make(QSpinBox)      # Added to layout, binds to record.age
```

**Excluded fields (`_foo_`)** start AND end with `_`. They are NOT added to the layout and do not auto-bind:

```python
@widget()
class MyWidget(QWidget):
    visible: QLabel = make(QLabel, "Visible")
    _internal_: QLabel = make(QLabel, "Internal")
    # Only 'visible' is added to layout
```

### Non-Widget Fields

Non-widget fields (int, str, etc.) are never added to the layout:

```python
@widget()
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")
    counter: int = 0
    name: str = "test"
    # Only 'label' is added to layout
```

## Complete Example

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox, QLabel, QPushButton
from qtpie import widget, make, Widget

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(
    layout="vertical",
    name="PersonEditor",
    classes=["form", "card"],
    undo=True,
    undo_max=50,
)
class PersonEditor(QWidget, Widget[Person]):
    # Model (auto-created if not specified)
    record: Person = make(Person, name="Alice", age=30)

    # Form fields (auto-bind to model.name and model.age)
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox, minimum=0, maximum=120)

    # Display with format binding
    info: QLabel = make(QLabel, bind="Name: {name}, Age: {age}")

    # Buttons
    save_btn: QPushButton = make(QPushButton, "Save", clicked="save")
    undo_btn: QPushButton = make(QPushButton, "Undo", clicked=lambda: self.undo("name"))

    def setup(self) -> None:
        print(f"Editing: {self.record.name}")
        if self.layout():
            self.layout().setSpacing(10)

    def save(self) -> None:
        print(f"Saving {self.record.name}, age {self.record.age}")

# Usage
editor = PersonEditor()
editor.name.setText("Bob")  # Auto-syncs to model.name
print(editor.record.name)     # "Bob"
```

## See Also

- [Widgets](../../basics/widgets.md) - Basic widget usage guide
- [Layouts](../../basics/layouts.md) - Layout types and customization
- [Record Widgets](../../data/record-widgets.md) - Working with `Widget[T]`
- [Data Binding](../../reference/bindings/bind.md) - Manual binding reference
- [make()](../../reference/factories/make.md) - Widget factory function
