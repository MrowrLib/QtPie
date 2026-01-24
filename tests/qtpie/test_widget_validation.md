# Widget Validation Feature Documentation

This document covers the validation system in QtPie, extracted from test patterns.

## Adding Validators to Variables

Variables support validation through the `add_validator` method. Validators are functions that return `None` for valid values or an error message string for invalid values.

```python
w._name.add_validator("required", lambda v: None if v else "Required")
```

## Variable Validation State

Variables expose reactive validation state through several properties:

```python
# Check if valid (Observable[bool])
w._name.is_valid.get()

# Get errors by validator name (Observable[dict])
errors = w._name.validation_errors.get()  # {"required": ["Required"]}

# Get flat list of all error messages
msgs = w._name.validation_error_messages.get()  # ["Required", "Too short"]
```

## Widget-Level add_validator

Widgets can add validators to their fields using `self.add_validator()` in `__setup__`:

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
```

## Widget Aggregated Validation

Widget-level validation aggregates all field validators:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

# Widget-level validation state
w.is_valid  # Observable[bool] - True only when ALL fields valid
w.validation_errors  # {field: {validator: [errors]}}
w.validation_error_messages.get()  # ["Required", "Must be positive"]
```

## on_valid_changed Hook

Override `on_valid_changed` to react to validity transitions:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _submit: QPushButton = new("Submit")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

    @override
    def on_valid_changed(self, is_valid: bool) -> None:
        self._submit.setEnabled(is_valid)
```

## Record Field Validation

Validators can be added to record fields (for `Widget[T]`):

```python
@widget
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        self.add_validator("name", "required", lambda v: None if v else "Name required")
```

## Widgets Without Validators

Widgets without validators are always valid:

```python
@widget
class Simple(Widget):
    _name: Variable[str] = new("")

w = Simple()
assert w.is_valid.get() == True  # No validators = always valid
```

## is_valid as Observable

`Widget.is_valid` is an `Observable[bool]`, enabling reactive bindings:

```python
# Subscribe to changes
w.is_valid.on_change(lambda v: print(f"Valid: {v}"))

# Use in enabled= binding
_submit: QPushButton = new("Submit", enabled="{is_valid.get()}")
```

## validate= Parameter (Declarative)

The `validate=` parameter on `new()` provides declarative validator registration:

### Single method name:
```python
_name: Variable[str] = new("", validate="validate_name")

def validate_name(self, value: str) -> str | None:
    return None if value else "Required"
```

### List of method names:
```python
_name: Variable[str] = new("", validate=["validate_required", "validate_length"])
```

### Callable:
```python
def check_not_empty(value: str) -> str | None:
    return None if value else "Cannot be empty"

_name: Variable[str] = new("", validate=check_not_empty)
```

### Tuple with explicit name:
```python
_name: Variable[str] = new("", validate=[("custom_name", "validate_required")])
# Validator registered under key "custom_name"
```

### Mixed formats:
```python
_name: Variable[str] = new("", validate=[
    "validate_required",           # Method name
    external_check,                # Callable
    ("length_check", "validate_length"),  # Tuple
])
```

## validate= with Variable[T, W]

Works with inline widget syntax:

```python
name: Variable[str, QLineEdit] = new("", validate="check_name")

def check_name(self, value: str) -> str | None:
    return None if value else "Name required"
```

## Combined Variable and Record Validation

`Widget.is_valid` aggregates both Variable validators and record validators:

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _extra: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_extra", "required", lambda v: None if v else "Extra required")
        self.add_validator("name", "required", lambda v: None if v else "Name required")

# Both must be valid for w.is_valid to be True
```

## Record-Level Validators

For whole-record validation (not field-specific):

```python
self._qtpie.record_state.add_validator(
    "name_required",
    lambda p: None if p and p.name else "Name required"
)
```

## Validator Function Signature

Validators are functions with signature:

```python
def validator(value: T) -> str | None:
    """Return None if valid, error message if invalid."""
    return None if is_valid(value) else "Error message"
```

## Validation Timing

Validators registered via `validate=` are active before `__setup__` runs:

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("", validate="validate_name")

    def __setup__(self) -> None:
        # self._name.is_valid already works here
        pass
```
