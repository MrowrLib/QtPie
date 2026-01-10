# Observable Validation

## Named Validators

Add validators with names to `Observable[T]`. Validators return `None` if valid, or a string/list of strings if invalid.

```python
obs = Observable("")
obs.add_validator("required", lambda v: None if v else "Required")
obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

assert_that(obs.is_valid.get()).is_false()
```

## Validation Errors

Access validation errors as a dict (by validator name) or flat list of messages.

```python
obs = Observable("")
obs.add_validator("required", lambda v: None if v else "Required")
obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")

errors = obs.validation_errors.get()
assert_that(errors).contains_key("required", "min_len")
assert_that(errors["required"]).is_equal_to(["Required"])

msgs = obs.validation_error_messages.get()
assert_that(msgs).contains("Required", "Too short")
```

## Reactive Validation

Validation runs automatically when the observable value changes. `is_valid` is itself an `Observable[bool]`.

```python
obs = Observable("")
obs.add_validator("required", lambda v: None if v else "Required")

transitions: list[bool] = []
obs.is_valid.on_change(lambda v: transitions.append(v))

obs.set("hello")  # now valid
assert_that(transitions).contains(True)
```

## List Validation

`ObservableList[T]` supports validators that receive the entire list.

```python
lst = ObservableList[int]([1, 2, 3])
lst.add_validator("max_3", lambda items: None if len(items) <= 3 else "Max 3 items")

assert_that(lst.is_valid.get()).is_true()

lst.append(4)
assert_that(lst.is_valid.get()).is_false()
```

## Dict Validation

`ObservableDict[K, V]` supports validators that receive the entire dict.

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

## Proxy Field Validation

`ObservableProxy[T]` aggregates validity from all child fields. Individual fields can have validators.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

proxy: ObservableProxy[Person] = ObservableProxy(Person())
proxy.name.add_validator("required", lambda v: None if v else "Name required")

assert_that(proxy.is_valid.get()).is_false()

proxy.name.set("Alice")
assert_that(proxy.is_valid.get()).is_true()
```

## Proxy Object Validation

`ObservableProxy[T]` can have validators on the entire object, not just individual fields.

```python
proxy: ObservableProxy[Person] = ObservableProxy(Person())
proxy.add_validator(
    "adult_named",
    lambda p: None if p.name and p.age >= 18 else "Must be named adult",
)

assert_that(proxy.is_valid.get()).is_false()
```

## Invalid Fields List

`ObservableProxy[T]` can list which fields are currently invalid.

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
