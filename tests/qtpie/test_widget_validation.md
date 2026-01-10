# Widget Validation Tests

## Variable Validation API

Individual `Variable[T]` fields support validation with reactive error tracking.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")

w = TestWidget()
w._name.add_validator("required", lambda v: None if v else "Required")

# Access validation state
w._name.is_valid.get()  # Observable[bool]
w._name.validation_errors.get()  # dict[str, list[str]]
w._name.validation_error_messages.get()  # list[str]
```

## Widget-Level Validation

Widgets aggregate validation from all fields and provide a unified API.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

w = TestWidget()
w.is_valid  # Observable[bool] - aggregates all fields
w.validation_errors  # {field: {validator: [errors]}}
w.validation_error_messages.get()  # Flat list of all error messages
```

## Validation Lifecycle Hook

Widgets can override `on_valid_changed` to react to validity state transitions.

```python
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")
    _submit: QPushButton = new("Login")

    def __setup__(self) -> None:
        self.add_validator("_username", "required", lambda v: None if v else "Username required")
        self.add_validator("_password", "required", lambda v: None if v else "Password required")
        self._submit.setEnabled(False)

    @override
    def on_valid_changed(self, is_valid: bool) -> None:
        self._submit.setEnabled(is_valid)
```

## Reactive Validation in Bindings

`Widget.is_valid` is an `Observable[bool]` that can be used in property bindings.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")
    _submit: QPushButton = new("Submit", enabled="{is_valid.get()}")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
```

## Declarative Validation with validate= Parameter

Fields can declare validators inline using the `validate=` parameter.

```python
@widget
class TestWidget(Widget):
    # Single validator by method name
    _name: Variable[str] = new("", validate="validate_name")

    # Multiple validators
    _email: Variable[str] = new("", validate=["validate_required", "validate_format"])

    # External callable
    _age: Variable[int] = new(0, validate=lambda v: None if v > 0 else "Must be positive")

    # Explicit validator names
    _username: Variable[str] = new("", validate=[("custom_name", "validate_required")])

    # Mixed formats
    _field: Variable[str] = new("", validate=[
        "validate_required",
        external_check,
        ("length_check", "validate_length"),
    ])

    def validate_name(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_format(self, value: str) -> str | None:
        return None if "@" in value else "Invalid email"
```

## Record Validation

Widgets with record types (`Widget[T]`) support validation on record fields.

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        # Validate record field by name
        self.add_validator("name", "required", lambda v: None if v else "Name required")

w = PersonEditor()
w.is_valid.get()  # False

w.record.name = "Alice"
w.is_valid.get()  # True
```

## Combined Variable and Record Validation

Widget validation aggregates both Variable fields and record validation.

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _extra: Variable[str] = new("")

    def __setup__(self) -> None:
        # Validate Variable field
        self.add_validator("_extra", "required", lambda v: None if v else "Extra required")
        # Validate record
        self._qtpie.record_state.add_validator("name_required", lambda p: None if p and p.name else "Name required")

w = PersonEditor()
w.is_valid.get()  # False - both invalid
w.validation_errors  # {"_extra": {...}, "record": {...}}
w.validation_error_messages.get()  # ["Extra required", "Name required"]

w._extra.value = "filled"
w.is_valid.get()  # Still False - record invalid

w.record.name = "Alice"
w.is_valid.get()  # True - both valid
```
