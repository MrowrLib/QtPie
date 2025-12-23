# Undo & Redo

QtPie provides built-in undo/redo functionality for `Widget[T]` model fields through [Observant](https://mrowrlib.github.io/observant.py/)'s [ObservableProxy](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/) ([PyPI](https://pypi.org/project/observant/)).

## Enable Undo

Add `undo=True` to the `@widget` decorator:

```python
from dataclasses import dataclass
from qtpie import Widget, make, widget
from qtpy.QtWidgets import QLineEdit, QWidget

@dataclass
class User:
    name: str = ""

@widget(undo=True)
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
```

Now every change to `name` is tracked in an undo history.

## Configuration

Control undo behavior with additional parameters:

```python
@widget(
    undo=True,
    undo_max=50,              # Keep max 50 undo steps (default: unlimited)
    undo_debounce_ms=500      # Wait 500ms before recording (useful for text)
)
class TextEditor(QWidget, Widget[Document]):
    content: QLineEdit = make(QLineEdit)
```

### Parameters

- **`undo`** - Enable/disable undo tracking (default: `False`)
- **`undo_max`** - Maximum history depth (default: unlimited)
- **`undo_debounce_ms`** - Debounce time in milliseconds before recording a change

The debounce is particularly useful for text input - without it, every keystroke creates a separate undo step. With `undo_debounce_ms=500`, typing rapidly only creates one undo step per 500ms pause.

## Undo & Redo

Use the `undo()` and `redo()` methods:

```python
@widget(undo=True)
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        # Make some changes
        self.name.setText("Alice")

        # Undo the change
        self.undo("name")  # name is now ""

        # Redo the change
        self.redo("name")  # name is "Alice" again
```

## Check Availability

Before calling undo/redo, check if the operation is available:

```python
if self.can_undo("name"):
    self.undo("name")

if self.can_redo("name"):
    self.redo("name")
```

This is essential for enabling/disabling undo/redo buttons.

## Example: Text Editor with Undo Buttons

Here's a complete text editor with undo/redo buttons:

```python
from dataclasses import dataclass
from qtpie import Widget, make, widget
from qtpy.QtWidgets import QLineEdit, QPushButton, QWidget

@dataclass
class Document:
    content: str = ""

@widget(undo=True, undo_debounce_ms=500)
class TextEditor(QWidget, Widget[Document]):
    content: QLineEdit = make(QLineEdit)
    undo_btn: QPushButton = make(QPushButton, "Undo", clicked="do_undo")
    redo_btn: QPushButton = make(QPushButton, "Redo", clicked="do_redo")

    def setup_bindings(self) -> None:
        # Update button states whenever content changes
        self.model_observable_proxy.observable(str, "content").on_change(self.update_buttons)
        self.update_buttons()

    def update_buttons(self, _value: str | None = None) -> None:
        """Enable/disable buttons based on undo/redo availability."""
        self.undo_btn.setEnabled(self.can_undo("content"))
        self.redo_btn.setEnabled(self.can_redo("content"))

    def do_undo(self) -> None:
        if self.can_undo("content"):
            self.undo("content")

    def do_redo(self) -> None:
        if self.can_redo("content"):
            self.redo("content")
```

## How It Works

1. **Undo enabled** - `@widget(undo=True)` creates the proxy with undo tracking
2. **Changes tracked** - Each field change is recorded as a history entry
3. **Debouncing** - Rapid changes within `undo_debounce_ms` are grouped
4. **Per-field** - Each field has its own independent undo/redo stack
5. **Max depth** - Old entries are discarded when `undo_max` is exceeded

## Multiple Fields

Each field maintains its own undo history:

```python
from dataclasses import dataclass
from qtpie import Widget, make, widget
from qtpy.QtWidgets import QLineEdit, QSpinBox, QWidget

@dataclass
class User:
    name: str = ""
    age: int = 0

@widget(undo=True)
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

    def setup(self) -> None:
        # Make changes to both fields
        self.name.setText("Alice")
        self.age.setValue(30)

        # Undo only affects the specified field
        self.undo("name")  # name reverts, age stays 30
        self.undo("age")   # age reverts, name stays reverted
```

## API Reference

### Widget[T] Methods

- **`undo(field: str)`** - Undo the last change to a field
- **`redo(field: str)`** - Redo the last undone change
- **`can_undo(field: str) -> bool`** - Check if undo is available
- **`can_redo(field: str) -> bool`** - Check if redo is available

### Decorator Parameters

- **`undo: bool`** - Enable undo/redo (default: `False`)
- **`undo_max: int | None`** - Max history depth (default: `None` = unlimited)
- **`undo_debounce_ms: int | None`** - Debounce time in milliseconds (default: `None`)

## See Also

- [Model Widgets](model-widgets.md) - Understanding `Widget[T]`
- [Dirty Tracking](dirty.md) - Detect unsaved changes
- [Validation](validation.md) - Validate field values
- [@widget decorator](../reference/decorators/widget.md) - Full decorator API
- [Observant Integration](../guides/observant.md) - Understanding the reactive layer
