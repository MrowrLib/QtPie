# Validation

Real-time validation for `Widget[T]` forms using the observant library.

## Overview

When you use `Widget[T]`, you get built-in validation capabilities through the underlying `ObservableProxy`. Add validation rules to fields and get real-time feedback as users edit.

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QWidget, QLineEdit, QLabel
from qtpie import widget, make, Widget

@dataclass
class User:
    name: str = ""
    email: str = ""

@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)
    error_label: QLabel = make(QLabel)

    def setup(self) -> None:
        # Add validation rules
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("email", self._validate_email)

        # React to validation changes
        self.is_valid().on_change(lambda valid: self.error_label.setText(
            "" if valid else "Please fix errors"
        ))

    def _validate_email(self, value: str) -> str | None:
        if not value:
            return "Email required"
        if "@" not in value:
            return "Invalid email format"
        return None
```

## Core Methods

### `add_validator(field, validator)`

Add a validation rule to a specific field.

**Parameters:**
- `field: str` - The model field name
- `validator: Callable[[Any], str | None]` - Validation function that returns:
  - `None` if valid
  - Error message string if invalid

```python
# Simple validator
self.add_validator("name", lambda v: "Required" if not v else None)

# Multiple validators for one field
self.add_validator("age", lambda v: "Required" if v == 0 else None)
self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)

# Complex validator
def validate_password(value: str) -> str | None:
    if len(value) < 8:
        return "Password must be at least 8 characters"
    if not any(c.isupper() for c in value):
        return "Password must contain uppercase letter"
    return None

self.add_validator("password", validate_password)
```

### `is_valid()`

Get an observable that tracks overall validity.

**Returns:** `IObservable[bool]` - True when all fields pass validation

```python
# Enable/disable submit button based on validity
self.is_valid().on_change(lambda valid: self.submit_btn.setEnabled(valid))

# Check current validity
if self.is_valid().get():
    print("Form is valid!")
```

### `validation_for(field)`

Get validation errors for a specific field.

**Parameters:**
- `field: str` - The field name

**Returns:** `IObservable[list[str]]` - List of error messages (empty if valid)

```python
# Show errors for one field
def show_name_errors() -> None:
    errors = self.validation_for("name").get()
    if errors:
        self.name_error_label.setText(errors[0])
    else:
        self.name_error_label.setText("")

self.validation_for("name").on_change(show_name_errors)
```

### `validation_errors()`

Get all validation errors across all fields.

**Returns:** `IObservableDict[str, list[str]]` - Dict mapping field names to error lists

```python
# Display all errors
errors_dict = self.validation_errors().get()
for field, messages in errors_dict.items():
    print(f"{field}: {', '.join(messages)}")

# Check specific field from the dict
name_errors = self.validation_errors().get("name", [])
if name_errors:
    print(f"Name errors: {name_errors}")
```

## Complete Example: Registration Form

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox, QLabel, QPushButton
from qtpie import widget, make, Widget

@dataclass
class User:
    name: str = ""
    age: int = 0
    email: str = ""

@widget
class RegistrationForm(QWidget, Widget[User]):
    # Input fields (auto-bind to model)
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
    email: QLineEdit = make(QLineEdit)

    # Error displays
    name_error: QLabel = make(QLabel, classes=["error"])
    age_error: QLabel = make(QLabel, classes=["error"])
    email_error: QLabel = make(QLabel, classes=["error"])

    # Submit button
    submit: QPushButton = make(QPushButton, "Submit", clicked="on_submit")

    def setup(self) -> None:
        # Add validation rules
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)
        self.add_validator("email", self._validate_email)

        # Show field-specific errors in real-time
        self.validation_for("name").on_change(self._update_name_error)
        self.validation_for("age").on_change(self._update_age_error)
        self.validation_for("email").on_change(self._update_email_error)

        # Enable/disable submit based on overall validity
        self.is_valid().on_change(lambda valid: self.submit.setEnabled(valid))

        # Initially disable submit
        self.submit.setEnabled(False)

    def _validate_email(self, value: str) -> str | None:
        if not value:
            return "Email required"
        if "@" not in value:
            return "Invalid email format"
        return None

    def _update_name_error(self) -> None:
        errors = self.validation_for("name").get()
        self.name_error.setText(errors[0] if errors else "")

    def _update_age_error(self) -> None:
        errors = self.validation_for("age").get()
        self.age_error.setText(errors[0] if errors else "")

    def _update_email_error(self) -> None:
        errors = self.validation_for("email").get()
        self.email_error.setText(errors[0] if errors else "")

    def on_submit(self) -> None:
        # Double-check validity (should always be true if button is enabled)
        if self.is_valid().get():
            print(f"Submitting: {self.model.name}, {self.model.age}, {self.model.email}")
            # Save back to model
            self.save_to(self.model)
        else:
            print("Form has errors - should not reach here!")
```

## Validation Timing

Validators run automatically when:
- Field value changes (via widget or direct proxy assignment)
- You call `is_valid().get()`, `validation_for(field).get()`, or `validation_errors().get()`

The validation is **reactive** - observables update automatically when values change.

## Multiple Validators

You can add multiple validators to the same field:

```python
# All validators must pass for the field to be valid
self.add_validator("password", lambda v: "Required" if not v else None)
self.add_validator("password", lambda v: "Min 8 chars" if len(v) < 8 else None)
self.add_validator("password", lambda v: "Need uppercase" if not any(c.isupper() for c in v) else None)

# If multiple fail, all error messages are returned
errors = self.validation_for("password").get()
# errors might be: ["Min 8 chars", "Need uppercase"]
```

## See Also

- [Model Widgets](model-widgets.md) - Understanding `Widget[T]`
- [Dirty Tracking](dirty.md) - Detect unsaved changes
- [Save & Load](save-load.md) - Persisting form data
- [Reactive State](state.md) - Observable state management
