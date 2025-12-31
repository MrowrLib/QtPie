# Validation

Real-time validation for `Widget[T]` forms using the [Observant](https://mrowrlib.github.io/observant.py/) library ([PyPI](https://pypi.org/project/observant/)).

## Overview

When you use `Widget[T]`, you get built-in validation capabilities through the underlying [ObservableProxy](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/). Add validation rules to fields and get real-time feedback as users edit.

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QWidget, QLineEdit, QLabel
from qtpie import widget, make, Widget, state

@dataclass
class User:
    name: str = ""
    email: str = ""

@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)

    errors: str = state("")
    error_label: QLabel = make(QLabel, bind="{errors}")

    def setup(self) -> None:
        # Add validation rules
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("email", self._validate_email)

    def on_valid_changed(self, is_valid: bool) -> None:
        # Called automatically when validation state changes
        if is_valid:
            self.errors = ""
        else:
            all_errors = []
            for msgs in self.validation_errors().values():
                all_errors.extend(msgs)
            self.errors = ", ".join(all_errors)

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
# Preferred: Override on_valid_changed hook (auto-wired by @widget)
def on_valid_changed(self, is_valid: bool) -> None:
    self.submit_btn.setEnabled(is_valid)

# Or use as a simple bool check
if self.is_valid():
    print("Form is valid!")
```

### `validation_for(field)`

Get validation errors for a specific field.

**Parameters:**
- `field: str` - The field name

**Returns:** `IObservable[list[str]]` - List of error messages (empty if valid)

```python
# Access field errors in on_valid_changed
def on_valid_changed(self, is_valid: bool) -> None:
    errors = self.validation_for("name").get()
    self.name_error = errors[0] if errors else ""
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
from qtpie import widget, make, Widget, state

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

    # Error state - reactive strings bound to labels
    name_error: str = state("")
    age_error: str = state("")
    email_error: str = state("")

    # Error displays with reactive binding
    name_error_label: QLabel = make(QLabel, bind="{name_error}", classes=["error"])
    age_error_label: QLabel = make(QLabel, bind="{age_error}", classes=["error"])
    email_error_label: QLabel = make(QLabel, bind="{email_error}", classes=["error"])

    # Submit button
    submit: QPushButton = make(QPushButton, "Submit", clicked="on_submit")

    def setup(self) -> None:
        # Add validation rules
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)
        self.add_validator("email", self._validate_email)

        # Initially disable submit
        self.submit.setEnabled(False)

    def _validate_email(self, value: str) -> str | None:
        if not value:
            return "Email required"
        if "@" not in value:
            return "Invalid email format"
        return None

    def on_valid_changed(self, is_valid: bool) -> None:
        # Called automatically when validation state changes!
        self.submit.setEnabled(is_valid)

        # Update field-specific error messages
        name_errors = self.validation_for("name").get()
        age_errors = self.validation_for("age").get()
        email_errors = self.validation_for("email").get()

        self.name_error = name_errors[0] if name_errors else ""
        self.age_error = age_errors[0] if age_errors else ""
        self.email_error = email_errors[0] if email_errors else ""

    def on_submit(self) -> None:
        if self.is_valid():
            print(f"Submitting: {self.record.name}, {self.record.age}, {self.record.email}")
            self.save_to(self.record)
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

- [Record Widgets](record-widgets.md) - Understanding `Widget[T]`
- [Dirty Tracking](dirty.md) - Detect unsaved changes
- [Save & Load](save-load.md) - Persisting form data
- [Reactive State](state.md) - Observable state management
- [Observant Integration](../guides/observant.md) - Understanding the reactive layer
