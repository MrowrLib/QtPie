# Observant Validation Patterns

This document describes the validation features available in the Observant reactive library.

## Adding Named Validators

Validators are added with a unique name and a validation function. The function returns `None` for valid, or an error message string (or list of strings) for invalid.

```python
obs = Observable("hello")
obs.add_validator("required", lambda v: None if v else "Required")
```

## Checking Validity

The `is_valid` property is itself an Observable that tracks validation state.

```python
obs.is_valid.get()  # Returns True or False
```

## Accessing Validation Errors

Two ways to access errors:
- `validation_errors` - dict keyed by validator name
- `validation_error_messages` - flat list of all error messages

```python
errors = obs.validation_errors.get()  # {"required": ["Required"], "min_len": ["Too short"]}
msgs = obs.validation_error_messages.get()  # ["Required", "Too short"]
```

## Multiple Error Messages

A validator can return a list of error strings:

```python
obs.add_validator("multi", lambda v: ["Error 1", "Error 2"] if not v else None)
```

## Automatic Revalidation

Validation runs automatically when the value changes:

```python
obs = Observable("")
obs.add_validator("required", lambda v: None if v else "Required")
obs.is_valid.get()  # False
obs.set("hello")
obs.is_valid.get()  # True
```

## Reactive Validity Tracking

Since `is_valid` is an Observable, you can subscribe to validity changes:

```python
obs.is_valid.on_change(lambda v: print(f"Valid: {v}"))
```

## Removing Validators

Validators can be removed by name:

```python
obs.remove_validator("required")
```

## ObservableList Validation

Lists validate on any mutation (append, pop, etc.):

```python
lst = ObservableList[str]([])
lst.add_validator("not_empty", lambda items: None if items else "List cannot be empty")
lst.append("item")  # Triggers revalidation
```

## ObservableDict Validation

Dicts validate the entire dictionary:

```python
dct = ObservableDict[str, int]({"a": 1})
dct.add_validator("has_required", lambda d: None if "required" in d else "Missing 'required' key")
dct["required"] = 42  # Triggers revalidation
```

## ObservableSet Validation

Sets validate on add/remove operations:

```python
s = ObservableSet[str](set())
s.add_validator("not_empty", lambda items: None if items else "Set cannot be empty")
s.add("item")  # Triggers revalidation
```

## ObservableProxy Field Validation

Proxy aggregates validity from all child fields:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

proxy: ObservableProxy[Person] = ObservableProxy(Person())
proxy.name.add_validator("required", lambda v: None if v else "Name required")
proxy.is_valid.get()  # False - aggregates from fields
```

## Proxy-Level Validation

Proxies can have validators on the whole object:

```python
proxy.add_validator(
    "adult_named",
    lambda p: None if p.name and p.age >= 18 else "Must be named adult"
)
```

## Tracking Invalid Fields

Proxy provides `invalid_fields` to see which fields are failing:

```python
proxy.name.add_validator("required", lambda v: None if v else "Required")
proxy.age.add_validator("positive", lambda v: None if v > 0 else "Must be positive")

invalid = proxy.invalid_fields  # ["name", "age"]
```
