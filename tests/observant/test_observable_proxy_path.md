# ObservableProxy Path Traversal

## Simple Path Traversal

Get observables for nested object properties using dot notation.

```python
person = Person(name="Alice", age=30)
proxy = ObservableProxy(person)

name_obs = proxy.observable_for_path("name")
assert_that(name_obs.get()).is_equal_to("Alice")
```

```python
person = Person(name="Bob", address=Address(city="NYC", zip_code="10001"))
proxy = ObservableProxy(person)

city_obs = proxy.observable_for_path("address.city")
assert_that(city_obs.get()).is_equal_to("NYC")
```

## Optional Chaining

Use `?.` syntax to safely traverse nullable fields. Returns `Observable(None)` if any intermediate is None.

```python
person = Person(name="Charlie", address=None)
proxy = ObservableProxy(person)

result = proxy.observable_for_path("address?.city")
assert_that(result.get()).is_none()
```

```python
company = Company(name="Acme", ceo=None)
proxy = ObservableProxy(company)

result = proxy.observable_for_path("ceo?.address?.city")
assert_that(result.get()).is_none()
```

## Path Segment Parsing

Internal helper `_parse_path_segments()` parses paths into tuples of (field_name, is_optional).

```python
segments = proxy._parse_path_segments("a?.b.c?.d")
assert_that(segments).is_equal_to([("a", True), ("b", False), ("c", True), ("d", False)])
```
