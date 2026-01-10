# Dirty Tracking

QtPie automatically tracks whether widget Variables have changed from their initial values. This enables save buttons, unsaved change warnings, and reset functionality.

## Basic Usage

### Checking Dirty State

```python
from qtpie import Widget, Variable, new, widget

@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

form = Form()
form._name.value = "Alice"
form._age.value = 30

# Check if any field changed
if form.view_model.is_dirty:
    print("Has unsaved changes")

# Check which fields changed
print(form.view_model.dirty_fields)  # {"_name", "_age"}
```

### Resetting Dirty State

After saving, reset to mark all fields as clean:

```python
def save(self) -> None:
    save_to_database(self._name.value, self._age.value)
    self.view_model.reset_dirty()  # Now clean
```

`reset_dirty()` treats current values as the new baseline - it doesn't revert values.

## Reactive Bindings

Use `is_dirty` in property bindings:

### Save Button

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    _save_btn: QPushButton = new(
        "Save",
        enabled="{view_model.is_dirty}",
        clicked="save"
    )

    def save(self) -> None:
        # Save logic...
        self.view_model.reset_dirty()
```

### Unsaved Changes Warning

```python
@widget
class Editor(Widget):
    _content: Variable[str] = new("")

    _warning: QLabel = new(
        "You have unsaved changes",
        visible="{view_model.is_dirty}"
    )
```

## on_dirty_changed Hook

React to dirty state transitions:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def on_dirty_changed(self, is_dirty: bool) -> None:
        if is_dirty:
            print("Form has unsaved changes")
        else:
            print("Form is clean")
```

The hook fires only on **transitions** (clean → dirty or dirty → clean), not on every field change.

```python
form = Form()
form._name.value = "first"   # clean → dirty (hook fires with True)
form._name.value = "second"  # dirty → dirty (hook does NOT fire)
form._age.value = 25         # dirty → dirty (hook does NOT fire)
```

## Record Dirty Tracking

With `Widget[T]`, both Variables and record fields are tracked:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    _notes: Variable[str] = new("")  # Variable
    name: QLineEdit = new()          # Record field
    age: QSpinBox = new()            # Record field

editor = PersonEditor()
editor._notes.value = "Some notes"
editor.record.name = "Alice"
editor.record.age = 30

# dirty_fields includes both
print(editor.view_model.dirty_fields)
# {"_notes", "record.name", "record.age"}
```

Record fields appear with the `record.` prefix in `dirty_fields`.

## Combining with Validation

Common pattern: enable save only when valid AND dirty:

```python
@widget
class ValidatedForm(Widget):
    _name: Variable[str] = new("")
    _email: Variable[str] = new("")

    _save_btn: QPushButton = new(
        "Save",
        enabled="{view_model.is_valid and view_model.is_dirty}",
        clicked="save"
    )

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Name required")
        self.add_validator("_email", "email",
            lambda v: None if "@" in v else "Invalid email")

    def save(self) -> None:
        # Only called when valid AND dirty
        save_to_database(self._name.value, self._email.value)
        self.view_model.reset_dirty()
```

## Common Patterns

### Save and Reset

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    _save_btn: QPushButton = new(
        "Save",
        enabled="{view_model.is_dirty}",
        clicked="save"
    )

    def save(self) -> None:
        save_to_database(self._name.value)
        self.view_model.reset_dirty()
```

### Check Specific Fields

```python
def check_changes(self) -> None:
    dirty = self.view_model.dirty_fields

    if "_name" in dirty:
        print("Name was changed")

    if "_email" in dirty:
        print("Email was changed")
```

### Prevent Close with Unsaved Changes

```python
@window(title="Editor")
class EditorWindow(Window):
    _content: Variable[str] = new("")

    def closeEvent(self, event) -> None:
        if self.view_model.is_dirty:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Close anyway?"
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        event.accept()
```

## API Reference

| Property/Method | Description |
|-----------------|-------------|
| `view_model.is_dirty` | `bool` - True if any field changed |
| `view_model.dirty_fields` | `set[str]` - Names of changed fields |
| `view_model.reset_dirty()` | Reset all fields to clean state |
| `on_dirty_changed(is_dirty)` | Hook for state transitions |

## See Also

- [Validation](validation.md) - Form validation
- [Records](records.md) - Widget[T] with record types
- [View Model](view-model.md) - view_model properties
- [Property Bindings](../state/property-bindings.md) - Using in enabled=/visible=
