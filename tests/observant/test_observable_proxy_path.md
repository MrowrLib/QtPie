# ObservableProxy Path Traversal

## Path Traversal

Get observables for nested object fields using dot-notation paths.

```python
person = Person(name="Bob", address=Address(city="NYC", zip_code="10001"))
proxy = ObservableProxy(person)

city_obs = proxy.observable_for_path("address.city")
assert_that(city_obs).is_instance_of(Observable)
assert_that(city_obs.get()).is_equal_to("NYC")
```

Single field access:

```python
person = Person(name="Alice", age=30)
proxy = ObservableProxy(person)

name_obs = proxy.observable_for_path("name")
assert_that(name_obs).is_instance_of(Observable)
assert_that(name_obs.get()).is_equal_to("Alice")
```

## Optional Chaining

Use `?.` to safely traverse nullable fields. Returns `Observable(None)` if any intermediate value is `None`.

```python
person = Person(name="Charlie", address=None)
proxy = ObservableProxy(person)

result = proxy.observable_for_path("address?.city")
assert_that(result).is_instance_of(Observable)
assert_that(result.get()).is_none()
```

Deep optional chains:

```python
company = Company(name="Acme", ceo=None)
proxy = ObservableProxy(company)

result = proxy.observable_for_path("ceo?.address?.city")
assert_that(result).is_instance_of(Observable)
assert_that(result.get()).is_none()
```

## Error Handling

Missing fields without `?` raise `AttributeError`:

```python
person = Person(name="Dan")
proxy = ObservableProxy(person)

try:
    proxy.observable_for_path("nonexistent")
    assert_that(False).is_true()  # Should not reach
except AttributeError as e:
    assert_that(str(e)).contains("nonexistent")
```
