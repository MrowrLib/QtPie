# Validation Tests

## Named Validators

Add validators by name, returning `None` for valid or error string(s) for invalid.

```python
obs = Observable("")
obs.add_validator("required", lambda v: None if v else "Required")
obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")
```

## Validation State

`is_valid` is an `Observable[bool]` that updates automatically when value changes.

```python
obs = Observable("")
obs.add_validator("required", lambda v: None if v else "Required")

assert_that(obs.is_valid.get()).is_false()

obs.set("hello")
assert_that(obs.is_valid.get()).is_true()
```

## Error Reporting

Errors available as structured dict or flat list.

```python
obs = Observable("")
obs.add_validator("required", lambda v: None if v else "Required")
obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

# Structured: {validator_name: [errors]}
errors = obs.validation_errors.get()
assert_that(errors["required"]).is_equal_to(["Required"])

# Flat list
msgs = obs.validation_error_messages.get()
assert_that(msgs).contains("Required", "Too short")
```

## Multiple Errors Per Validator

Validators can return a list of errors.

```python
obs = Observable("")
obs.add_validator("multi", lambda v: ["Error 1", "Error 2"] if not v else None)

errors = obs.validation_errors.get()
assert_that(errors["multi"]).is_equal_to(["Error 1", "Error 2"])
```

## ObservableList Validation

Validators receive the entire list and re-run on mutations.

```python
lst = ObservableList[int]([1, 2, 3])
lst.add_validator("max_3", lambda items: None if len(items) <= 3 else "Max 3 items")

assert_that(lst.is_valid.get()).is_true()

lst.append(4)
assert_that(lst.is_valid.get()).is_false()
```

## ObservableDict Validation

Validators receive the entire dict and re-run on mutations.

```python
dct = ObservableDict[str, int]({"a": 1})
dct.add_validator(
    "has_required",
    lambda d: None if "required" in d else "Missing 'required' key",
)

assert_that(dct.is_valid.get()).is_false()

dct["required"] = 42
assert_that(dct.is_valid.get()).is_true()
```

## ObservableProxy Validation

Proxy aggregates validity from child fields and can have its own whole-object validators.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

proxy: ObservableProxy[Person] = ObservableProxy(Person())

# Field validators
proxy.name.add_validator("required", lambda v: None if v else "Name required")
assert_that(proxy.is_valid.get()).is_false()

proxy.name.set("Alice")
assert_that(proxy.is_valid.get()).is_true()

# Whole-object validators
proxy.add_validator(
    "adult_named",
    lambda p: None if p.name and p.age >= 18 else "Must be named adult",
)
```

## Invalid Fields Tracking

Proxy provides list of which fields are currently invalid.

```python
proxy: ObservableProxy[Person] = ObservableProxy(Person())
proxy.name.add_validator("required", lambda v: None if v else "Required")
proxy.age.add_validator("positive", lambda v: None if v > 0 else "Must be positive")

invalid = proxy.invalid_fields
assert_that(invalid).contains("name", "age")

proxy.name.set("Alice")
invalid = proxy.invalid_fields
assert_that(invalid).contains("age")
assert_that(invalid).does_not_contain("name")
```
