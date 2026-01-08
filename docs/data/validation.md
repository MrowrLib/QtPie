# Validation

QtPie provides a comprehensive validation system that works seamlessly with `Variable` fields. Validators can be added declaratively or programmatically, and validation state is automatically tracked and made available for reactive updates.

## Overview

The validation system offers:

- Named validators that can be added, removed, or replaced
- Automatic aggregation of validation state across all fields
- Reactive validation that updates as field values change
- Lifecycle hooks that fire on validation state transitions
- Multiple ways to declare validators (inline, in `__setup__`, via `validate=` parameter)

## Basic Validation

### Adding Validators

Use `add_validator()` to register validators on `Variable` fields:

```python
from qtpie import Widget, Variable, new, widget

@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")

    def __setup__(self) -> None:
        # add_validator(field_name, validator_name, validator_function)
        self.add_validator("_username", "required", lambda v: None if v else "Username required")
        self.add_validator("_password", "required", lambda v: None if v else "Password required")
        self.add_validator("_password", "min_length", lambda v: None if len(v) >= 8 else "Min 8 characters")
```

**Validator functions:**
- Take the field value as a parameter
- Return `None` if valid
- Return an error message string if invalid

**Named validators:**
- Each validator has a unique name (e.g., `"required"`, `"min_length"`)
- Names allow you to replace or remove specific validators later
- Multiple validators can be added to the same field

### Checking Validity

The `is_valid` property aggregates validation state across all fields:

```python
@widget
class MyForm(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Name required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

    def on_submit(self) -> None:
        if self.is_valid:
            print("Form is valid!")
        else:
            print("Form has errors")
```

**Key points:**
- `is_valid` is `True` only when ALL fields with validators are valid
- Widgets without any validators are always valid
- Validation is reactive - `is_valid` updates automatically when field values change

### Getting Error Messages

QtPie provides two ways to access validation errors:

```python
# Structured: {field_name: {validator_name: [error_messages]}}
errors = widget.validation_errors
# Example: {"_name": {"required": ["Name required"]}}

# Flat list of all error messages
messages = widget.validation_error_messages
# Example: ["Name required", "Min 8 characters"]
```

**Structured errors (`validation_errors`):**
- Nested dictionary organized by field and validator
- Useful when you need to display field-specific errors
- Format: `{field: {validator: [errors]}}`

**Flat messages (`validation_error_messages`):**
- Simple list of all error strings
- Useful for displaying a summary of all errors
- Example: `["Username required", "Password required", "Min 8 characters"]`

## Variable-Level Validation

You can also add validators directly to `Variable` instances:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        # Add validator directly to the Variable
        self._name.add_validator("required", lambda v: None if v else "Required")

        # Check validity at the Variable level
        if self._name.is_valid.get():
            print("Name is valid")

        # Get Variable-specific errors
        errors = self._name.validation_errors.get()  # {"required": ["Required"]}
        messages = self._name.validation_error_messages.get()  # ["Required"]
```

**Note:** Variable validation properties return `Observable` values, so use `.get()` to access them. Widget-level properties are plain values (not observables).

## The `validate=` Parameter

For cleaner code, use the `validate=` parameter when defining `Variable` fields:

### Single Validator (Method Name)

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("", validate="validate_name")

    def validate_name(self, value: str) -> str | None:
        return None if value else "Name required"
```

### Multiple Validators (List)

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("", validate=["validate_required", "validate_length"])

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_length(self, value: str) -> str | None:
        return None if len(value) >= 3 else "Too short"
```

### Callable Validators

```python
def check_not_empty(value: str) -> str | None:
    return None if value else "Cannot be empty"

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("", validate=check_not_empty)
```

### Explicit Validator Names

Use tuples to specify explicit validator names:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("", validate=[
        ("required", "validate_required"),  # (name, method)
        ("custom", lambda v: None if v.isalpha() else "Letters only"),  # (name, callable)
    ])

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"
```

### Mixed Formats

You can combine different validator formats in a single list:

```python
def external_check(value: str) -> str | None:
    return None if value.isalpha() else "Letters only"

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("", validate=[
        "validate_required",                    # Method name
        external_check,                          # Callable
        ("length", "validate_length"),           # Explicit name + method
        ("custom", lambda v: len(v) < 50 or None),  # Explicit name + lambda
    ])

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_length(self, value: str) -> str | None:
        return None if len(value) >= 3 else "Too short"
```

**Note:** Validators registered via `validate=` are applied before `__setup__()` runs, so they are active immediately.

## Lifecycle Hook: `on_valid_changed`

The `on_valid_changed` hook fires when the widget's validation state transitions between valid and invalid:

```python
from qtpy.QtWidgets import QPushButton

@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")
    _submit: QPushButton = new("Login")

    def __setup__(self) -> None:
        self.add_validator("_username", "required", lambda v: None if v else "Username required")
        self.add_validator("_password", "required", lambda v: None if v else "Password required")
        self._submit.setEnabled(False)  # Initially disabled

    def on_valid_changed(self, is_valid: bool) -> None:
        # Enable submit button only when form is valid
        self._submit.setEnabled(is_valid)
```

**Key points:**
- The hook receives a single `bool` parameter: `is_valid`
- It fires ONLY on state transitions (invalid → valid or valid → invalid)
- It does NOT fire on every field change, only when overall validity changes
- The hook is optional - widgets work fine without it

**Example of when it fires:**

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

    def on_valid_changed(self, is_valid: bool) -> None:
        print(f"Valid: {is_valid}")

w = MyWidget()
# Initially invalid, but hook doesn't fire (no transition yet)

w._name.value = "hello"
# Prints: "Valid: True" (transition: invalid → valid)

w._name.value = "world"
# No output (still valid, no transition)

w._name.value = ""
# Prints: "Valid: False" (transition: valid → invalid)
```

## Working with Record Fields

Validators work seamlessly with `Widget[T]` record fields:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        # Validate record fields directly
        self.add_validator("name", "required", lambda v: None if v else "Name required")
        self.add_validator("age", "positive", lambda v: None if v > 0 else "Must be positive")

w = PersonEditor()
print(w.is_valid)  # False

w.record.name = "Alice"
print(w.is_valid)  # Still False (age is 0)

w.record.age = 25
print(w.is_valid)  # True
```

## Variable with Widget Type

Validation works with the `Variable[T, W]` syntax:

```python
from qtpy.QtWidgets import QLineEdit

@widget
class MyWidget(Widget):
    name: Variable[str, QLineEdit] = new("", validate="check_name")

    def check_name(self, value: str) -> str | None:
        return None if value else "Name required"

w = MyWidget()
print(w.name.is_valid.get())  # False

w.name.widget.setText("Alice")
print(w.name.is_valid.get())  # True
```

## Practical Example: Login Form

Here's a complete example showing validation in action:

```python
from qtpy.QtWidgets import QLineEdit, QPushButton, QLabel
from qtpie import Widget, Variable, new, widget

@widget
class LoginForm(Widget):
    _username: Variable[str, QLineEdit] = new("", validate="validate_username")
    _password: Variable[str, QLineEdit] = new("", validate=["validate_required", "validate_password_length"])
    _errors: QLabel = new("")
    _submit: QPushButton = new("Login", clicked="on_submit")

    def __setup__(self) -> None:
        self._submit.setEnabled(False)
        self._password.widget.setEchoMode(QLineEdit.EchoMode.Password)

    def validate_username(self, value: str) -> str | None:
        if not value:
            return "Username required"
        if len(value) < 3:
            return "Username must be at least 3 characters"
        return None

    def validate_required(self, value: str) -> str | None:
        return None if value else "Password required"

    def validate_password_length(self, value: str) -> str | None:
        return None if len(value) >= 8 else "Password must be at least 8 characters"

    def on_valid_changed(self, is_valid: bool) -> None:
        self._submit.setEnabled(is_valid)
        if not is_valid:
            # Show all errors
            self._errors.setText(", ".join(self.validation_error_messages))
        else:
            self._errors.setText("")

    def on_submit(self) -> None:
        if self.is_valid:
            print(f"Logging in as {self._username.value}")
```

## Summary

**Key APIs:**
- `add_validator(field, name, fn)` - Add a validator to a field
- `is_valid` - Boolean property, `True` when all fields are valid
- `validation_errors` - Nested dict: `{field: {validator: [errors]}}`
- `validation_error_messages` - Flat list of all error messages
- `validate=` parameter - Declarative validator registration
- `on_valid_changed(is_valid)` - Lifecycle hook for state transitions

**Validator function signature:**
```python
def validator(value: T) -> str | None:
    return None if valid else "error message"
```

**Best practices:**
- Use named validators for maintainability
- Register validators in `__setup__()` or via `validate=` parameter
- Use `on_valid_changed` to update UI state (e.g., enable/disable buttons)
- Prefer `validation_error_messages` for simple error displays
- Use `validation_errors` when you need field-specific error handling
