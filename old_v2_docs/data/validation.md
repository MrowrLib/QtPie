# Validation

QtPie provides declarative validation that works seamlessly with `Variable` fields. Use the `validate=` parameter to define validators, and bind UI state reactively to `is_valid` and `validation_error_messages`.

## Basic Validation

Add validators using the `validate=` parameter with a method name:

```python
from PySide6.QtWidgets import QLineEdit, QPushButton, QLabel
from qtpie import Widget, Variable, new, widget

@widget
class LoginForm(Widget):
    _username: Variable[str, QLineEdit] = new("", validate="validate_username")
    _password: Variable[str, QLineEdit] = new("", validate="validate_password")

    _errors: list[QLabel] = new(bind="validation_error_messages")
    _submit: QPushButton = new("Login", enabled="{is_valid}", clicked="on_submit")

    def validate_username(self, value: str) -> str | None:
        return None if value else "Username required"

    def validate_password(self, value: str) -> str | None:
        return None if len(value) >= 8 else "Min 8 characters"

    def on_submit(self) -> None:
        print(f"Logging in as {self._username}")
```

That's it. No manual setup, no imperative state management. The button enables when valid, errors display automatically.

Validator functions:

- Take the field value as a parameter
- Return `None` if valid
- Return an error message string if invalid

## Complex Validation Logic

For multi-step validation, method references keep things readable:

```python
@widget
class SignupForm(Widget):
    _email: Variable[str, QLineEdit] = new("", validate="validate_email")
    _password: Variable[str, QLineEdit] = new("", validate="validate_password")

    _submit: QPushButton = new("Sign Up", enabled="{is_valid}")

    def validate_email(self, value: str) -> str | None:
        if not value:
            return "Email required"
        if "@" not in value:
            return "Invalid email format"
        return None

    def validate_password(self, value: str) -> str | None:
        if len(value) < 8:
            return "Password must be at least 8 characters"
        if not any(c.isdigit() for c in value):
            return "Password must contain a number"
        return None
```

## Lambda Validators

For simple one-liners, you can use lambdas:

```python
_name: Variable[str] = new("", validate=lambda v: None if v else "Required")
```

Note: Lambdas don't support type annotations, so method references are preferred for type-checked codebases.

## Multiple Validators

Pass a list to apply multiple validators to a field:

```python
@widget
class MyForm(Widget):
    _name: Variable[str] = new("", validate=[
        "validate_required",
        "validate_length",
        "validate_characters"
    ])

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_length(self, value: str) -> str | None:
        return None if len(value) >= 3 else "Too short"

    def validate_characters(self, value: str) -> str | None:
        return None if value.isalnum() else "Letters and numbers only"
```

## Mixed Validator Formats

You can combine different validator formats in a single list:

```python
def external_check(value: str) -> str | None:
    return None if value.isalpha() else "Letters only"

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("", validate=[
        "validate_required",           # Method name
        external_check,                # Callable
        lambda v: None if v else "Cannot be empty",  # Lambda
    ])

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"
```

## Validation State

QtPie provides reactive properties for validation state:

```python
@widget
class MyForm(Widget):
    _name: Variable[str] = new("", validate=lambda v: None if v else "Required")
    _age: Variable[int] = new(0, validate=lambda v: None if v > 0 else "Must be positive")

    # Bind UI to validation state
    _errors: list[QLabel] = new(bind="validation_error_messages")
    _submit: QPushButton = new("Submit", enabled="{is_valid}")
```

**Available properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_valid` | `bool` | `True` when all fields are valid |
| `validation_error_messages` | `list[str]` | Flat list of all error messages |
| `validation_errors` | `dict` | Structured: `{field: {validator: [errors]}}` |

## Displaying Errors

Use a list of labels - one per error message:

```python
_errors: list[QLabel] = new(bind="validation_error_messages")
```

This creates one `QLabel` for each error, updating automatically as validation state changes. Style them with `classes=` or `stylesheet=`:

```python
_errors: list[QLabel] = new(bind="validation_error_messages", stylesheet="color: red;")
```

## Validation with Records

Validators work with `Widget[T]` record fields:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    name: QLineEdit = new(validate=lambda v: None if v else "Name required")
    age: QSpinBox = new(validate=lambda v: None if v > 0 else "Must be positive")

    _submit: QPushButton = new("Save", enabled="{is_valid}")
```

## Validation with Variable[T, W]

The `validate=` parameter works in the chained call syntax:

```python
@widget
class MyWidget(Widget):
    _email: Variable[str, QLineEdit] = new("")(
        placeholderText="Email",
        validate="validate_email"
    )

    def validate_email(self, value: str) -> str | None:
        return None if "@" in value else "Invalid email"
```

## The `on_valid_changed` Hook

For complex side-effects that can't be expressed declaratively, use the `on_valid_changed` lifecycle hook:

```python
@widget
class MyForm(Widget):
    _name: Variable[str] = new("", validate=lambda v: None if v else "Required")

    def on_valid_changed(self, is_valid: bool) -> None:
        # Called only on state transitions (valid -> invalid or invalid -> valid)
        if is_valid:
            self.save_draft()
```

**Note:** Prefer declarative bindings (`enabled="{is_valid}"`) over this hook when possible. The hook is for side-effects like saving drafts, logging, or triggering animations.

## Complete Example

```python
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton
from qtpie import Widget, Variable, new, widget, entrypoint

@entrypoint
@widget(layout="form")
class RegistrationForm(Widget):
    _username: Variable[str, QLineEdit] = new("")(
        label="Username:",
        validate="validate_username"
    )
    _email: Variable[str, QLineEdit] = new("")(
        label="Email:",
        validate=lambda v: None if "@" in v else "Invalid email"
    )
    _password: Variable[str, QLineEdit] = new("")(
        label="Password:",
        validate=["validate_required", "validate_password_strength"]
    )

    _errors: list[QLabel] = new(bind="validation_error_messages", stylesheet="color: red;")

    _register: QPushButton = new("Register", enabled="{is_valid}", clicked="on_register")

    def validate_username(self, value: str) -> str | None:
        if not value:
            return "Username required"
        if len(value) < 3:
            return "Username must be at least 3 characters"
        if not value.isalnum():
            return "Username must be alphanumeric"
        return None

    def validate_required(self, value: str) -> str | None:
        return None if value else "Password required"

    def validate_password_strength(self, value: str) -> str | None:
        if len(value) < 8:
            return "Password must be at least 8 characters"
        return None

    def on_register(self) -> None:
        print(f"Registering {self._username} with email {self._email}")
```

## Summary

| Pattern | Usage |
|---------|-------|
| `validate=lambda v: ...` | Inline validator |
| `validate="method_name"` | Method reference |
| `validate=[...]` | Multiple validators |
| `enabled="{is_valid}"` | Reactive button state |
| `list[QLabel] = new(bind="validation_error_messages")` | Reactive error list |
| `visible="{not is_valid}"` | Conditional error visibility |
