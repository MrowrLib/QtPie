# ObservableProxy Test Summary

## Field Access via Observable

Fields return `Observable` objects that can get/set values. Changes to observables update the wrapped object.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)

# Get via Observable
assert_that(proxy.name.get()).is_equal_to("Alice")

# Set via Observable
proxy.name.set("Bob")
assert_that(person.name).is_equal_to("Bob")
```

## Direct Field Assignment

Fields can be set directly on the proxy (syntactic sugar over `.set()`).

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)

proxy.name = "Bob"
assert_that(proxy.name.get()).is_equal_to("Bob")
assert_that(person.name).is_equal_to("Bob")
```

## Change Callbacks

Callbacks fire when any field changes. Both proxy-level and field-level callbacks are supported.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)
changes: list[str] = []

# Proxy-level callback
proxy.on_change(lambda: changes.append("changed"))

# Field-level callback
proxy.name.on_change(lambda v: changes.append(f"name={v}"))

proxy.name.set("Bob")
```

## Dirty Tracking

Tracks which fields have changed. `is_dirty` is itself an observable.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)

proxy.name.set("Bob")
assert_that(bool(proxy.is_dirty)).is_true()
assert_that(proxy.dirty_fields).contains("name")

proxy.reset_dirty()
assert_that(bool(proxy.is_dirty)).is_false()
```

```python
# is_dirty is observable
dirty_states: list[bool] = []
proxy.is_dirty.on_change(lambda d: dirty_states.append(d))

proxy.name.set("Bob")  # clean -> dirty
proxy.reset_dirty()    # dirty -> clean

assert_that(dirty_states).is_equal_to([True, False])
```

## Nested Objects

Nested objects are automatically wrapped in `ObservableProxy`. Changes propagate dirty state and callbacks to parent.

```python
breed = Breed("Labrador", "Canada")
dog = Dog("Buddy", 5, breed)
proxy = ObservableProxy(dog)

# Nested field returns proxy
breed_proxy = proxy.breed
assert_that(breed_proxy).is_instance_of(ObservableProxy)

# Access nested fields
assert_that(proxy.breed.name.get()).is_equal_to("Labrador")

# Set nested fields
proxy.breed.name.set("Golden Retriever")
assert_that(breed.name).is_equal_to("Golden Retriever")
```

```python
# Nested changes propagate dirty state
proxy.breed.name.set("Golden Retriever")
assert_that(bool(proxy.is_dirty)).is_true()
assert_that(bool(proxy.breed.is_dirty)).is_true()

# Reset propagates down
proxy.reset_dirty()
assert_that(bool(proxy.breed.is_dirty)).is_false()
```

## List Fields

List fields return `ObservableList`. Modifications mark proxy dirty and fire callbacks.

```python
person = PersonWithCollections("Alice", ["admin", "user"], {"age": 30})
proxy = ObservableProxy(person)

# Access list field
tags = proxy.tags
assert_that(tags).is_instance_of(ObservableList)

# Modify list
proxy.tags.append("moderator")
assert_that(proxy.tags.to_list()).is_equal_to(["admin", "user", "moderator"])

# Marks dirty and fires callbacks
assert_that(bool(proxy.is_dirty)).is_true()
assert_that(proxy.dirty_fields).contains("tags")
```

## Dict Fields

Dict fields return `ObservableDict`. Modifications mark proxy dirty and fire callbacks.

```python
person = PersonWithCollections("Alice", ["admin"], {"age": 30})
proxy = ObservableProxy(person)

# Access dict field
metadata = proxy.metadata
assert_that(metadata).is_instance_of(ObservableDict)

# Modify dict
proxy.metadata["score"] = 100
assert_that(proxy.metadata.to_dict()).is_equal_to({"age": 30, "score": 100})

# Marks dirty and fires callbacks
assert_that(bool(proxy.is_dirty)).is_true()
assert_that(proxy.dirty_fields).contains("metadata")
```

## Optional Dirty Tracking

Dirty tracking can be disabled via constructor parameter.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person, dirty_tracking=False)

# is_dirty raises if tracking disabled
try:
    _ = proxy.is_dirty
except RuntimeError as e:
    assert_that(str(e)).contains("not enabled")

# Everything else still works
proxy.name.set("Bob")
assert_that(proxy.name.get()).is_equal_to("Bob")
```
