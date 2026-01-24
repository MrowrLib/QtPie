# Dialog Feature Documentation

This document describes QtPie's declarative dialog system based on patterns extracted from `test_dialog.py`.

## Basic Dialog Creation

Dialogs extend `Dialog` and require the `@dialog` decorator. At minimum, a dialog needs at least one `DialogButton`.

```python
@dialog
class MyDialog(Dialog):
    ok: DialogButton
```

### Dialog with Title

```python
@dialog(title="My Title")
class MyDialog(Dialog):
    ok: DialogButton
```

### Dialog with Content

Regular Qt widgets are added using `new()`. The layout defaults to vertical (`QVBoxLayout`).

```python
@dialog
class MyDialog(Dialog):
    label: QLabel = new("Test content")
    ok: DialogButton
```

## DialogButton Types

Button field names determine the button type. Supported types: `ok`, `cancel`, `yes`, `no`, `save`, `discard`, `apply`, `help`, `reset`.

```python
@dialog
class ConfirmDialog(Dialog):
    ok: DialogButton
    cancel: DialogButton
```

### Custom Button Labels

Override the default label with `new()`:

```python
@dialog
class SaveDialog(Dialog):
    ok: DialogButton = new("Save Changes")
    cancel: DialogButton = new("Discard")
```

### Underscore-Prefixed Button Names

Buttons can use underscore prefixes for Python convention (e.g., `_ok` instead of `ok`):

```python
@dialog
class MyDialog(Dialog):
    _ok: DialogButton
    _cancel: DialogButton
```

## Button Bindings

### Enabled Binding

Bind button enabled state to a reactive Variable:

```python
@dialog
class ValidatedDialog(Dialog):
    _valid: Variable[bool] = new(False)
    ok: DialogButton = new(enabled="{_valid}")
    cancel: DialogButton
```

### Click Handler

Connect button clicks to methods:

```python
@dialog
class ActionDialog(Dialog):
    apply: DialogButton = new(clicked="on_apply")
    cancel: DialogButton

    def on_apply(self) -> None:
        print("Applied!")
```

## Dialog with Record Type

Use `Dialog[T]` to bind dialog fields to a dataclass. Fields with matching names auto-bind.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@dialog
class PersonDialog(Dialog[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QSpinBox = new()    # Auto-binds to record.age
    ok: DialogButton
```

Set the record before showing:

```python
d = PersonDialog()
d.record = Person("Alice", 30)  # Widgets populate automatically
```

Two-way binding works - editing widgets updates the record:

```python
d.name.setText("Bob")
# d.record.name is now "Bob"
```

## Showing Dialogs

### Instance Method

```python
d = MyDialog()
result = d.show_dialog()
```

### Class Method

Creates instance automatically:

```python
result = MyDialog.show_dialog()
```

### Class Method with Record

Pass record when calling on class:

```python
result = PersonDialog.show_dialog(Person("Alice", 30))
```

## DialogResult

The `show_dialog()` method returns a `DialogResult` with these properties:

```python
result = dialog.show_dialog()
result.accepted    # True if user accepted (ok/save/yes)
result.rejected    # True if user cancelled/closed
result.button      # ButtonInfo with .name and .text
result.record      # The record (for Dialog[T])
```

## Accept/Reject Hooks

Override `on_accept()` or `on_reject()` to control dialog closing. Return `False` to prevent closing.

```python
@dialog
class ConfirmDialog(Dialog):
    ok: DialogButton
    cancel: DialogButton

    def on_accept(self) -> bool:
        if not self.validate():
            return False  # Prevent close
        return True
```

## Validation Integration

Positive buttons (ok, save, yes) auto-bind to the dialog's `is_valid` state:

```python
@dialog
class ValidatedDialog(Dialog):
    _name: Variable[str] = new("")
    ok: DialogButton  # Auto-disabled when invalid
    cancel: DialogButton

# Add validators after creation
d.add_validator("_name", "required", lambda v: "Required" if not v else None)
# ok button is disabled until _name has a value
```

## Custom DialogButtons Class

Create reusable button configurations with `@buttons` and `DialogButtons`:

```python
@buttons
class SaveCancelButtons(DialogButtons):
    ok: DialogButton = new("Save")
    cancel: DialogButton = new("Cancel")

@dialog
class MyDialog(Dialog):
    content: QLabel = new("Content here")
    my_buttons: SaveCancelButtons = new()
```

This allows explicit positioning of the button box in the layout.

## Dialog Icon

### Icon from Path

```python
@dialog(title="My Dialog", icon=":/icons/app.png")
class MyDialog(Dialog):
    ok: DialogButton
```

### Icon from QIcon or QPixmap

```python
@dialog(title="My Dialog", icon=my_qicon)
class MyDialog(Dialog):
    ok: DialogButton
```

### Inherit from Active Window

By default, dialogs inherit the icon from the active window. Opt out with `icon=False`:

```python
@dialog(title="No Icon", icon=False)
class MyDialog(Dialog):
    ok: DialogButton
```

## Button Box Layout Position

Buttons declared inline with content are collected and placed at the end:

```python
@dialog
class MyDialog(Dialog):
    label1: QLabel = new("First")
    ok: DialogButton              # Collected
    label2: QLabel = new("Second")
    cancel: DialogButton          # Collected
# Layout: label1, label2, [ok, cancel button box]
```

Using a custom `DialogButtons` class gives explicit control over position:

```python
@dialog
class MyDialog(Dialog):
    header: QLabel = new("Header")
    my_buttons: SaveCancelButtons = new()  # Positioned here
    footer: QLabel = new("Footer")
```
