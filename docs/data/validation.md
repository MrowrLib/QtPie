# Validation

QtPie provides reactive validation for form fields. Validators run automatically when values change, and validation state can drive UI (like disabling submit buttons).

## Quick Start

```python
from qtpie import Widget, Variable, new, widget

@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")

    _submit: QPushButton = new(
        "Login",
        enabled="{view_model.is_valid}",
        clicked="login"
    )

    def __setup__(self) -> None:
        self.add_validator("_username", "required",
            lambda v: None if v else "Username required")
        self.add_validator("_password", "min_len",
            lambda v: None if len(v) >= 8 else "Min 8 characters")

    def login(self) -> None:
        # Only called when form is valid
        print(f"Logging in: {self._username.value}")
```

## Validator Functions

Validators return `None` for valid, or an error message string:

```python
def validate_name(value: str) -> str | None:
    if not value:
        return "Name is required"
    if len(value) < 3:
        return "Name must be at least 3 characters"
    return None  # Valid
```

## Adding Validators

### In __setup__

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _email: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Required")
        self.add_validator("_email", "email",
            lambda v: None if "@" in v else "Invalid email")
```

### With validate= Parameter

```python
@widget
class Form(Widget):
    # Method name
    _name: Variable[str] = new("", validate="validate_name")

    # Lambda
    _age: Variable[int] = new(0, validate=lambda v: None if v > 0 else "Must be positive")

    # Multiple validators
    _email: Variable[str] = new("", validate=["validate_required", "validate_email"])

    def validate_name(self, value: str) -> str | None:
        return None if value else "Name required"

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_email(self, value: str) -> str | None:
        return None if "@" in value else "Invalid email"
```

## Checking Validity

### Widget-Level

```python
# Check overall form validity
if self.view_model.is_valid:
    # All fields are valid
    save_data()

# Get all error messages
errors = self.view_model.validation_error_messages
print(errors)  # ["Name required", "Invalid email"]
```

### Displaying Errors

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    # Show errors in label
    _errors: QLabel = new(
        bind="{', '.join(view_model.validation_error_messages)}",
        visible="{not view_model.is_valid}"
    )

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Name required")
```

## Reactive Bindings

Use validation state in property bindings:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    # Enable submit only when valid
    _submit: QPushButton = new(
        "Submit",
        enabled="{view_model.is_valid}",
        clicked="submit"
    )

    # Show/hide error panel
    _error_panel: QWidget = new(
        visible="{not view_model.is_valid}"
    )
```

## on_valid_changed Hook

React to validity state transitions:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _status: QLabel = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Required")

    def on_valid_changed(self, is_valid: bool) -> None:
        if is_valid:
            self._status.setText("Form is valid")
        else:
            self._status.setText("Please fix errors")
```

The hook fires only on transitions (valid → invalid or invalid → valid), not on every validation.

## Record Validation

Validate record fields in `Widget[T]`:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()

    def __setup__(self) -> None:
        # Validate record fields by property name
        self.add_validator("name", "required",
            lambda v: None if v else "Name required")
        self.add_validator("age", "positive",
            lambda v: None if v > 0 else "Must be positive")
```

## Combining with Dirty Tracking

Common pattern: enable save only when valid AND dirty:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _email: Variable[str] = new("")

    _save_btn: QPushButton = new(
        "Save",
        enabled="{view_model.is_valid and view_model.is_dirty}",
        clicked="save"
    )

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Required")
        self.add_validator("_email", "email",
            lambda v: None if "@" in v else "Invalid email")

    def save(self) -> None:
        # Only called when valid AND dirty
        save_to_database(self._name.value, self._email.value)
        self.view_model.reset_dirty()
```

## Common Validators

### Required

```python
def validate_required(value: str) -> str | None:
    return None if value else "This field is required"
```

### Email

```python
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(value: str) -> str | None:
    if not value:
        return "Email required"
    if not EMAIL_REGEX.match(value):
        return "Invalid email format"
    return None
```

### Password Strength

```python
def validate_password(value: str) -> str | None:
    if len(value) < 8:
        return "Min 8 characters"
    if not any(c.isdigit() for c in value):
        return "Must contain a number"
    if not any(c.isupper() for c in value):
        return "Must contain uppercase"
    return None
```

### Range

```python
def validate_age(value: int) -> str | None:
    if value < 0:
        return "Cannot be negative"
    if value > 150:
        return "Invalid age"
    return None
```

## Removing Validators

```python
def __setup__(self) -> None:
    self.add_validator("_name", "required", validate_required)

def disable_validation(self) -> None:
    self.remove_validator("_name", "required")
```

## API Reference

### Widget Methods

| Method/Property | Description |
|-----------------|-------------|
| `add_validator(field, name, fn)` | Add validator to field |
| `remove_validator(field, name)` | Remove validator by name |
| `view_model.is_valid` | `bool` - True if all fields valid |
| `view_model.validation_error_messages` | `list[str]` - All error messages |
| `on_valid_changed(is_valid)` | Hook for state transitions |

### Validator Signature

```python
def validator(value: T) -> str | None:
    """Return None if valid, error message if invalid."""
```

## See Also

- [Dirty Tracking](dirty-tracking.md) - Track unsaved changes
- [Records](records.md) - Widget[T] with record types
- [Property Bindings](../state/property-bindings.md) - enabled=/visible=
