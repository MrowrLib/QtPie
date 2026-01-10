# Widget Class

Base class for declarative Qt widgets with reactive state management.

## Overview

`Widget` is QtPie's foundational class for building reactive UI components. It extends `QWidget` with:

- Automatic layout management for child widgets
- Reactive state via `Variable` fields
- Lifecycle hooks for initialization
- Record binding for data models
- Validation and dirty tracking
- Async event handling

## Basic Usage

```python
from qtpy.QtWidgets import QLabel, QPushButton
from qtpie import Widget, new, widget

@widget
class HelloWidget(Widget):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me", clicked="on_click")

    def on_click(self) -> None:
        print("Button clicked!")
```

The `@widget` decorator is required and handles initialization. Without it, the class will raise a `TypeError` on instantiation.

## Type Parameter: Widget[T]

Widgets can be parameterized with a record type to enable automatic data binding:

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QLineEdit, QSpinBox
from qtpie import Widget, new, widget

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QSpinBox = new()    # Auto-binds to record.age
```

When using `Widget[T]`:
- Fields with matching names auto-bind to record properties
- The `record` property provides reactive access to the model
- Changes to the record automatically update bound widgets
- Changes to widgets automatically update the record

## Lifecycle Hook: __setup__

The `__setup__` method is called after the widget is fully initialized but before bindings are applied:

```python
@widget
class MyWidget(Widget):
    label: QLabel = new("")

    def __setup__(self) -> None:
        # Called after __init__, before bindings
        self.label.setText("Initialized!")
        print("Widget is ready")
```

Use `__setup__` for:
- Setting initial values for the record
- Registering validators
- Performing one-time setup tasks
- Accessing widget instances that need configuration

**Note:** `__setup__` runs before auto-bindings are applied, so you can safely initialize record values here.

## Properties

### view_model

Access all `Variable` fields in the widget:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def check_changes(self) -> None:
        if self.view_model.is_dirty:
            print(f"Changed fields: {self.view_model.dirty_fields}")
```

The `view_model` property provides:
- `is_dirty` - Whether any field has changed
- `dirty_fields` - Set of field names that changed
- `reset_dirty()` - Reset all dirty flags

### record (Widget[T] only)

Access the record model for data binding:

```python
@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()

    def update_name(self) -> None:
        # Read from record
        current = self.record.name

        # Write to record (reactive)
        self.record.name = "New Name"
```

The `record` property is an `ObservableProxy[T]` that makes field access reactive. Changes to `record.field` trigger updates to bound widgets.

### record_state (Widget[T] only)

Access the underlying `RecordVariable` wrapper:

```python
@widget
class PersonEditor(Widget[Person]):
    def check_record(self) -> None:
        # Access the RecordVariable wrapper
        state = self.record_state

        # Check if record has changed
        if state.is_dirty.get():
            print("Record modified")

        # Access the observable
        state.observable.name.on_change(lambda n: print(f"Name: {n}"))
```

Use `record_state` to:
- Check dirty state: `record_state.is_dirty.get()`
- Access the raw value: `record_state.value`
- Subscribe to changes: `record_state.observable.field.on_change(...)`

## Validation

### add_validator

Add a named validator to a field:

```python
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_username", "required", lambda v: None if v else "Username required")
        self.add_validator("_password", "min_length", lambda v: None if len(v) >= 8 else "Min 8 chars")
```

Validator function signature:
- Takes the field value as input
- Returns `None` if valid
- Returns error message string (or list of strings) if invalid

Named validators can be replaced or removed by name.

### is_valid

Check if all fields pass validation:

```python
@widget
class MyForm(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

    def on_submit(self) -> None:
        if self.is_valid:
            print("Form is valid!")
        else:
            print("Form has errors")
```

Returns `True` only when all fields with validators are valid. Widgets without validators are always considered valid.

### validation_errors

Get structured validation errors:

```python
@widget
class MyForm(Widget):
    def show_errors(self) -> None:
        # Format: {field_name: {validator_name: [error_messages]}}
        errors = self.validation_errors
        # Example: {"_name": {"required": ["Name required"]}}

        for field, validators in errors.items():
            for validator_name, messages in validators.items():
                print(f"{field}.{validator_name}: {messages}")
```

### validation_error_messages

Get a flat list of all error messages:

```python
@widget
class MyForm(Widget):
    _errors: QLabel = new("")

    def update_errors(self) -> None:
        # Simple list of all error strings
        messages = self.validation_error_messages
        # Example: ["Username required", "Min 8 chars"]

        self._errors.setText(", ".join(messages))
```

## Lifecycle Hooks

### on_valid_changed

Called when validation state transitions between valid and invalid:

```python
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _submit: QPushButton = new("Login")

    def __setup__(self) -> None:
        self.add_validator("_username", "required", lambda v: None if v else "Required")

    def on_valid_changed(self, is_valid: bool) -> None:
        # Enable submit button only when valid
        self._submit.setEnabled(is_valid)
```

Key points:
- Fires only on state transitions (invalid to valid, or vice versa)
- Does not fire on every field change
- Optional - widgets work fine without it

### on_dirty_changed

Called when dirty state transitions:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _save: QPushButton = new("Save")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        # Enable save button only when changes exist
        self._save.setEnabled(is_dirty)
```

Similar to `on_valid_changed`, this hook fires only on state transitions between clean and dirty.

### on_close (async)

Async hook called when the widget is closing:

```python
@widget
class MyWidget(Widget):
    async def on_close(self) -> None:
        # Perform async cleanup
        await self.save_data()
        print("Widget closing...")
```

Use `on_close` for:
- Async cleanup operations
- Saving state before close
- Confirming user actions

The close event is automatically accepted after this completes.

## Complete Example

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QLineEdit, QSpinBox, QPushButton, QLabel
from qtpie import Widget, Variable, new, widget

@dataclass
class Person:
    name: str = ""
    age: int = 0
    email: str = ""

@widget(layout="form", record=Person())
class PersonForm(Widget[Person]):
    # Fields auto-bind to record by name
    name: QLineEdit = new(label="Name:")
    age: QSpinBox = new(label="Age:")
    email: QLineEdit = new(label="Email:")

    # Additional widgets
    _errors: QLabel = new("")
    _save: QPushButton = new("Save", clicked="on_save")

    def __setup__(self) -> None:
        # Register validators
        self.add_validator("name", "required", lambda v: None if v else "Name required")
        self.add_validator("email", "email", self._validate_email)
        self.add_validator("age", "positive", lambda v: None if v > 0 else "Age must be positive")

        # Initial state
        self._save.setEnabled(False)

    def _validate_email(self, email: str) -> str | None:
        if not email:
            return "Email required"
        if "@" not in email:
            return "Invalid email"
        return None

    def on_valid_changed(self, is_valid: bool) -> None:
        self._save.setEnabled(is_valid)
        if not is_valid:
            self._errors.setText(", ".join(self.validation_error_messages))
        else:
            self._errors.setText("")

    def on_save(self) -> None:
        if self.is_valid:
            print(f"Saving: {self.record.name}, {self.record.age}, {self.record.email}")
```

## See Also

- [@widget decorator](../decorators/widget.md) - Decorator configuration options
- [Variable class](variable.md) - Reactive state management
- [Records guide](../../data/records.md) - Working with data models
- [Validation guide](../../data/validation.md) - Complete validation examples
- [Dirty Tracking guide](../../data/dirty-tracking.md) - Change detection
