# ObservableProxy Path Traversal

This document describes the `observable_for_path()` feature of `ObservableProxy`, which allows accessing nested observables using dot-notation path strings.

## Basic Path Access

Access a single field by name to get its `Observable`:

```python
proxy = ObservableProxy(Person(name="Alice", age=30))
name_obs = proxy.observable_for_path("name")  # Observable[str]
name_obs.get()  # "Alice"
```

## Nested Path Traversal

Use dot notation to traverse nested objects:

```python
person = Person(address=Address(city="NYC", zip_code="10001"))
proxy = ObservableProxy(person)
city_obs = proxy.observable_for_path("address.city")  # Observable[str]
```

## Intermediate Proxy Access

When the path points to a nested object (not a primitive), returns an `ObservableProxy`:

```python
addr_proxy = proxy.observable_for_path("address")  # ObservableProxy[Address]
```

## Optional Chaining (`?.`)

Use `?.` for safe navigation through nullable fields. Returns `Observable(None)` if any intermediate is `None`:

```python
person = Person(address=None)
proxy = ObservableProxy(person)
result = proxy.observable_for_path("address?.city")  # Observable with None
```

When the value exists, returns the actual observable:

```python
person = Person(address=Address(city="Boston"))
result = proxy.observable_for_path("address?.city")  # Observable with "Boston"
```

## Deep Optional Chains

Chain multiple optional navigations for deeply nested nullable structures:

```python
company = Company(ceo=Person(address=Address(city="SF")))
proxy = ObservableProxy(company)
result = proxy.observable_for_path("ceo?.address?.city")  # "SF"
```

If any intermediate is `None`, the entire chain returns `Observable(None)`:

```python
company = Company(ceo=None)
result = proxy.observable_for_path("ceo?.address?.city")  # None
```

## Path Syntax Summary

| Syntax | Meaning |
|--------|---------|
| `field` | Direct field access |
| `a.b.c` | Nested traversal (required at each level) |
| `a?.b` | Optional chaining (safe if `a` is None) |
| `a?.b?.c` | Multiple optional navigations |

## Typical Model Structure

```python
@dataclass
class Address:
    city: str = ""
    zip_code: str = ""

@dataclass
class Person:
    name: str = ""
    age: int = 0
    address: Address | None = None  # Nullable for optional chaining
```
