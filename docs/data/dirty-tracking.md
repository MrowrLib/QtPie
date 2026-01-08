# Dirty Tracking

QtPie automatically tracks whether `Variable` fields have changed from their initial values. This is essential for features like "Save" buttons that should only be enabled when there are unsaved changes, or warning users about unsaved data before closing a window.

## Overview

The dirty tracking system provides:

- Automatic tracking of all `Variable` field changes
- Per-field tracking to identify which specific fields changed
- The ability to reset dirty state (e.g., after saving)
- Lifecycle hooks that fire on dirty state transitions
- Access through the auto-generated `view_model` property

## The `view_model` Property

Every `Widget` has a `view_model` property that provides access to:

- All `Variable` fields (but not other widget fields)
- Dirty tracking state and methods
- Validation state (see [Validation](validation.md))

```python
from qtpie import Widget, Variable, new, widget

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

w = MyWidget()

# Access Variables through view_model
print(w.view_model._name.value)  # ""
print(w.view_model._count.value)  # 0

# Variables are the same instance
assert w.view_model._name is w._name  # True
```

**Key points:**
- `view_model` contains only `Variable` fields, not regular widgets
- The `Variable` instances are the same whether accessed via `view_model` or directly
- Changes through `view_model` are reflected on the widget, and vice versa

## Basic Dirty Tracking

### Checking Dirty State

Use `view_model.is_dirty` to check if any field has changed:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

w = MyWidget()
print(w.view_model.is_dirty)  # False

w._name.value = "changed"
print(w.view_model.is_dirty)  # True
```

### Identifying Changed Fields

Use `view_model.dirty_fields` to get a set of field names that have changed:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)
    _active: Variable[bool] = new(False)

w = MyWidget()
w._name.value = "Alice"
w._count.value = 42

print(w.view_model.dirty_fields)  # {"_name", "_count"}
print(w.view_model.is_dirty)      # True
```

**Key points:**
- `dirty_fields` is a set of field names (strings)
- Only fields that have changed are included
- Empty set means no fields are dirty

### Resetting Dirty State

Use `view_model.reset_dirty()` to mark all fields as clean:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

w = MyWidget()
w._name.value = "changed"
w._count.value = 42

print(w.view_model.is_dirty)      # True
print(w.view_model.dirty_fields)  # {"_name", "_count"}

w.view_model.reset_dirty()

print(w.view_model.is_dirty)      # False
print(w.view_model.dirty_fields)  # set()
```

**After reset:**
- `is_dirty` becomes `False`
- `dirty_fields` becomes empty
- The field values remain unchanged - only the dirty tracking state is reset
- Future changes will make the widget dirty again

## Lifecycle Hook: `on_dirty_changed`

The `on_dirty_changed` hook fires when the widget's dirty state transitions between clean and dirty:

```python
from qtpy.QtWidgets import QPushButton

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _save_button: QPushButton = new("Save")

    def __setup__(self) -> None:
        self._save_button.setEnabled(False)

    def on_dirty_changed(self, is_dirty: bool) -> None:
        # Enable save button only when there are unsaved changes
        self._save_button.setEnabled(is_dirty)
        print(f"Widget is {'dirty' if is_dirty else 'clean'}")
```

**Key points:**
- The hook receives a single `bool` parameter: `is_dirty`
- It fires ONLY on state transitions (clean → dirty or dirty → clean)
- It does NOT fire on every field change, only when overall state changes
- The hook is optional - widgets work fine without it

**Example of when it fires:**

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    def on_dirty_changed(self, is_dirty: bool) -> None:
        print(f"Dirty: {is_dirty}")

w = MyWidget()
# Initially clean, but hook doesn't fire (no transition yet)

w._name.value = "first"
# Prints: "Dirty: True" (transition: clean → dirty)

w._name.value = "second"
# No output (still dirty, no transition)

w._count.value = 42
# No output (still dirty, no transition)

w.view_model.reset_dirty()
# Prints: "Dirty: False" (transition: dirty → clean)

w._name.value = "third"
# Prints: "Dirty: True" (transition: clean → dirty)
```

## Practical Examples

### Save Button

Enable a save button only when there are unsaved changes:

```python
from qtpy.QtWidgets import QLineEdit, QPushButton, QLabel

@widget
class DocumentEditor(Widget):
    _title: Variable[str, QLineEdit] = new("")
    _content: Variable[str, QLineEdit] = new("")
    _save_btn: QPushButton = new("Save", clicked="on_save")
    _status: QLabel = new("No changes")

    def __setup__(self) -> None:
        self._save_btn.setEnabled(False)

    def on_dirty_changed(self, is_dirty: bool) -> None:
        self._save_btn.setEnabled(is_dirty)
        if is_dirty:
            self._status.setText(f"Unsaved changes in: {', '.join(self.view_model.dirty_fields)}")
        else:
            self._status.setText("All changes saved")

    def on_save(self) -> None:
        if self.view_model.is_dirty:
            # Save logic here
            print(f"Saving: {self._title.value}")
            print(f"Changed fields: {self.view_model.dirty_fields}")

            # Mark as saved
            self.view_model.reset_dirty()
```

### Unsaved Changes Warning

Warn users before closing a window with unsaved changes:

```python
from qtpy.QtWidgets import QMessageBox
from qtpy.QtCore import QEvent

@widget
class MyEditor(Widget):
    _content: Variable[str] = new("")

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.Close:
            if self.view_model.is_dirty:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Close anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return True
        return super().eventFilter(obj, event)
```

### Form with Save/Discard

Track which specific fields changed and offer to discard changes:

```python
from qtpy.QtWidgets import QLineEdit, QPushButton

@widget
class PersonForm(Widget):
    _name: Variable[str, QLineEdit] = new("")
    _email: Variable[str, QLineEdit] = new("")
    _age: Variable[str, QLineEdit] = new("")
    _save_btn: QPushButton = new("Save", clicked="on_save")
    _discard_btn: QPushButton = new("Discard", clicked="on_discard")

    def __setup__(self) -> None:
        self._save_btn.setEnabled(False)
        self._discard_btn.setEnabled(False)

    def on_dirty_changed(self, is_dirty: bool) -> None:
        self._save_btn.setEnabled(is_dirty)
        self._discard_btn.setEnabled(is_dirty)

    def on_save(self) -> None:
        if self.view_model.is_dirty:
            changed = self.view_model.dirty_fields
            print(f"Saving changes to: {changed}")
            # Perform save...
            self.view_model.reset_dirty()

    def on_discard(self) -> None:
        if self.view_model.is_dirty:
            # Reset to original values
            self._name.value = ""
            self._email.value = ""
            self._age.value = ""
            self.view_model.reset_dirty()
```

### Combining Dirty Tracking with Validation

Enable a save button only when form is both dirty AND valid:

```python
from qtpy.QtWidgets import QLineEdit, QPushButton

@widget
class ValidatedForm(Widget):
    _name: Variable[str, QLineEdit] = new("", validate="validate_name")
    _email: Variable[str, QLineEdit] = new("", validate="validate_email")
    _save_btn: QPushButton = new("Save", clicked="on_save")

    def validate_name(self, value: str) -> str | None:
        return None if value else "Name required"

    def validate_email(self, value: str) -> str | None:
        return None if "@" in value else "Invalid email"

    def __setup__(self) -> None:
        self._update_save_button()

    def on_dirty_changed(self, is_dirty: bool) -> None:
        self._update_save_button()

    def on_valid_changed(self, is_valid: bool) -> None:
        self._update_save_button()

    def _update_save_button(self) -> None:
        # Enable only when dirty AND valid
        self._save_btn.setEnabled(self.view_model.is_dirty and self.is_valid)

    def on_save(self) -> None:
        if self.view_model.is_dirty and self.is_valid:
            print("Saving valid changes")
            self.view_model.reset_dirty()
```

## Working Through `view_model`

You can make changes through the `view_model` - they work exactly the same way:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

w = MyWidget()

# Change through view_model
w.view_model._name.value = "Alice"

# Change is reflected on widget
print(w._name.value)  # "Alice"

# Dirty state is tracked
print(w.view_model.is_dirty)  # True

# Works the other way too
w._name.value = "Bob"
print(w.view_model._name.value)  # "Bob"
```

## Initial State Behavior

Widgets start in a clean state:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("initial value")
    _count: Variable[int] = new(42)

w = MyWidget()

# Initial state is clean
print(w.view_model.is_dirty)      # False
print(w.view_model.dirty_fields)  # set()

# Any change makes it dirty
w._name.value = "new value"
print(w.view_model.is_dirty)      # True
```

**Note:** The initial values of fields are considered the "clean" state. Changing a field to a different value makes it dirty, even if you later change it back to the initial value (the system tracks state changes, not value equality).

## Reset and Continue

After resetting dirty state, the current values become the new "clean" baseline:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

w = MyWidget()

w._name.value = "first"
print(w.view_model.is_dirty)  # True

w.view_model.reset_dirty()
print(w.view_model.is_dirty)  # False

# Now "first" is the clean state
w._name.value = "second"
print(w.view_model.is_dirty)  # True
print(w.view_model.dirty_fields)  # {"_name"}
```

## Summary

**Key APIs:**
- `view_model` - Auto-generated property containing all `Variable` fields
- `view_model.is_dirty` - Boolean property, `True` when any field changed
- `view_model.dirty_fields` - Set of field names that changed
- `view_model.reset_dirty()` - Mark all fields as clean
- `on_dirty_changed(is_dirty)` - Lifecycle hook for state transitions

**Common patterns:**
- Enable/disable save buttons based on `is_dirty`
- Warn about unsaved changes before closing windows
- Display which specific fields changed using `dirty_fields`
- Combine with validation: enable save only when dirty AND valid
- Reset after successful save operation

**Best practices:**
- Use `on_dirty_changed` to update UI state reactively
- Call `reset_dirty()` after saving to mark form as clean
- Combine dirty tracking with validation for robust forms
- Check `dirty_fields` to show users exactly what changed
