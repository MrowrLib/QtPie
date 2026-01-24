# Validation Feature Documentation

QtPie provides a declarative validation system for `Variable[T]` fields with reactive validation state, error aggregation, and lifecycle hooks.

## Adding Validators

Use `add_validator()` to register validation rules on Variable fields. Validators are named and replaceable.

```python
def __setup__(self) -> None:
    self.add_validator("_name", "required", lambda v: None if v else "Required")
```

### Validator Function Signature

- Return `None` for valid
- Return error message string for invalid

```python
self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")
```

### Multiple Validators Per Field

Multiple validators can be registered on the same field; all are evaluated.

```python
self.add_validator("_name", "required", lambda v: None if v else "Required")
self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Min 3 chars")
```

### Replacing Validators

Adding a validator with the same name replaces the previous one.

```python
self.add_validator("_name", "check", lambda v: "Second error")  # replaces first
```

---

## Checking Validity

### Widget/Window-Level `is_valid`

The `is_valid` observable aggregates all field validations. Returns `Observable[bool]`.

```python
if instance.is_valid.get():
    print("All fields valid")
```

### Variable-Level `is_valid`

Each Variable exposes its own validation state.

```python
if instance._name.is_valid.get():
    print("Name field valid")
```

### Reactive Updates

Validity updates reactively when variable values change.

```python
instance._name.value = "hello"  # triggers re-validation
assert instance._name.is_valid.get() is True
```

---

## Accessing Validation Errors

### Structured Errors

`validation_errors` returns `{field: {validator: [errors]}}`.

```python
errors = instance.validation_errors
# {'_name': {'required': ['Name required']}, '_age': {'positive': ['Age must be positive']}}
```

### Flat Error Messages

`validation_error_messages` returns `Observable[list[str]]` with all messages.

```python
msgs = instance.validation_error_messages.get()
# ['Required', 'Too short']
```

### Variable-Level Errors

Each Variable has its own error accessors.

```python
instance._name.validation_errors.get()           # {'required': ['Required']}
instance._name.validation_error_messages.get()   # ['Required', 'Too short']
```

---

## Lifecycle Hook: `on_valid_changed`

Override `on_valid_changed(is_valid: bool)` to react to validity state transitions.

```python
@override
def on_valid_changed(self, is_valid: bool) -> None:
    self.save_btn.setEnabled(is_valid)
```

- Fires only on state transitions (not repeated invalid/valid states)
- Optional - class works without it

---

## Validation with Different Types

Validators work with any Variable type: `str`, `int`, `float`, `list`, `dict`, `set`.

```python
# Integer validation
self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

# Float range validation
self.add_validator("_rate", "range", lambda v: None if 0 <= v <= 1 else "Must be 0-1")

# List non-empty validation
self.add_validator("_items", "not_empty", lambda v: None if v else "Add at least one item")

# Dict key presence validation
self.add_validator("_data", "has_key", lambda v: None if "required" in v else "Missing key")
```

---

## Reactive Subscriptions

Subscribe to validation changes using `on_change`.

```python
instance.is_valid.on_change(lambda v: print(f"Valid: {v}"))
```

---

## Default Behavior

- Classes without validators are always valid
- Empty classes are always valid
- Validators receive current value after each change
