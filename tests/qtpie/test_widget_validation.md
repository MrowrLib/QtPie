# Widget Validation Tests

## Variable Field Validation

Individual `Variable[T]` fields can have validators added via `add_validator()`. Validators return `None` for valid values, or an error message string for invalid values.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")

w = qt.track(TestWidget())
w._name.add_validator("required", lambda v: None if v else "Required")

assert_that(w._name.is_valid.get()).is_false()
```

## Variable Validation State

Each `Variable` exposes `is_valid` (Observable[bool]), `validation_errors` (nested dict), and `validation_error_messages` (flat list).

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")

w = qt.track(TestWidget())
w._name.add_validator("required", lambda v: None if v else "Required")
w._name.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

msgs = w._name.validation_error_messages.get()
assert_that(msgs).contains("Required", "Too short")
```

## Widget-Level Validation

Widgets can add validators to fields in `__setup__()` using `add_validator(field_name, validator_name, callable)`.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

w = qt.track(TestWidget())
assert_that(w._name.is_valid.get()).is_false()
```

## Widget Aggregated Validation State

`Widget.is_valid` aggregates validation from all fields. Returns `Observable[bool]` that reactively updates.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

w = qt.track(TestWidget())
assert_that(w.is_valid).is_false()

w._name.value = "Alice"
assert_that(w.is_valid).is_false()  # still invalid (age)

w._age.value = 25
assert_that(w.is_valid).is_true()
```

## Widget Aggregated Validation Errors

`Widget.validation_errors` returns nested dict `{field: {validator: [errors]}}`. `Widget.validation_error_messages` returns flat list.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

w = qt.track(TestWidget())
errors = w.validation_errors

assert_that(errors).contains_key("_name", "_age")
assert_that(errors["_name"]["required"]).is_equal_to(["Required"])
assert_that(errors["_age"]["positive"]).is_equal_to(["Must be positive"])
```

## Validation Lifecycle Hook

`on_valid_changed(is_valid: bool)` fires when validity transitions between states (not on initial state).

```python
valid_states: list[bool] = []

@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

    @override
    def on_valid_changed(self, is_valid: bool) -> None:
        valid_states.append(is_valid)

w = qt.track(TestWidget())
# Initially invalid, but hook fires on transition only

w._name.value = "hello"
assert_that(valid_states).contains(True)

w._name.value = ""
assert_that(valid_states).contains(False)
```

## Record Field Validation

Validators can be added to `Widget[T]` record fields by name.

```python
@widget
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        self.add_validator("name", "required", lambda v: None if v else "Name required")

w = qt.track(PersonEditor())
assert_that(w.is_valid).is_false()

w.record.name = "Alice"
assert_that(w.is_valid).is_true()
```

## Reactive Validation in Bindings

`is_valid` is `Observable[bool]`, usable in reactive bindings like `enabled=`.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("")
    _submit: QPushButton = new("Submit", enabled="{is_valid.get()}")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

w = qt.track(TestWidget())
# Initially invalid - button should be disabled
assert_that(w._submit.isEnabled()).is_false()

# Become valid - button should enable
w._name.value = "hello"
assert_that(w._submit.isEnabled()).is_true()
```

## Declarative Validation with validate= Parameter

The `validate=` parameter on `new()` registers validators at field definition time. Supports method names, callables, tuples for explicit naming, and lists for multiple validators.

```python
@widget
class TestWidget(Widget):
    _name: Variable[str] = new("", validate=["validate_required", "validate_length"])

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_length(self, value: str) -> str | None:
        return None if len(value) >= 3 else "Too short"

w = qt.track(TestWidget())
msgs = w._name.validation_error_messages.get()
assert_that(msgs).contains("Required", "Too short")
```

Mixed formats:

```python
def external_check(value: str) -> str | None:
    return None if value.isalpha() else "Letters only"

@widget
class TestWidget(Widget):
    _name: Variable[str] = new(
        "",
        validate=[
            "validate_required",
            external_check,
            ("length_check", "validate_length"),
        ],
    )

    def validate_required(self, value: str) -> str | None:
        return None if value else "Required"

    def validate_length(self, value: str) -> str | None:
        return None if len(value) >= 3 else "Too short"

w = qt.track(TestWidget())
msgs = w._name.validation_error_messages.get()
assert_that(msgs).contains("Required", "Letters only", "Too short")
```

## Widget.is_valid Aggregates Variables and Record

When a widget has both `Variable` fields and a record type, `is_valid` aggregates validation from both sources.

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _extra: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_extra", "required", lambda v: None if v else "Extra required")
        self.add_validator("name", "required", lambda v: None if v else "Name required")

w = qt.track(PersonEditor())
assert_that(w.is_valid.get()).is_false()

# Fill in Variable
w._extra.value = "extra"
assert_that(w.is_valid.get()).is_false()  # Still invalid - record field empty

# Fill in record field
w.record.name = "Alice"
assert_that(w.is_valid.get()).is_true()

# Clear Variable
w._extra.value = ""
assert_that(w.is_valid.get()).is_false()
```
