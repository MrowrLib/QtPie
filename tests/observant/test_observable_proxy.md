# ObservableProxy Test Summary

## Field Access via Observable

Accessing a field on the proxy returns an `Observable` that can be used with `.get()` and `.set()` methods.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)

assert_that(proxy.name.get()).is_equal_to("Alice")
assert_that(proxy.age.get()).is_equal_to(30)

proxy.name.set("Bob")
assert_that(proxy.name.get()).is_equal_to("Bob")
assert_that(person.name).is_equal_to("Bob")
```

## Direct Field Assignment

Fields can be set directly on the proxy without using `.set()`.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)

proxy.name = "Bob"
assert_that(proxy.name.get()).is_equal_to("Bob")
assert_that(person.name).is_equal_to("Bob")
```

## Change Callbacks

Proxy-level callbacks fire when any field changes. Field-level callbacks fire when that specific field changes.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)
changes: list[str] = []

proxy.on_change(lambda: changes.append("changed"))
proxy.name.set("Bob")
assert_that(changes).is_equal_to(["changed"])
```

```python
proxy.name.on_change(lambda v: changes.append(f"name={v}"))
proxy.name.set("Bob")
assert_that(changes).is_equal_to(["name=Bob"])
```

## Dirty Tracking

Tracks which fields have been modified since creation or last reset. `is_dirty` is itself an `Observable`.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person)

assert_that(bool(proxy.is_dirty)).is_false()
proxy.name.set("Bob")
assert_that(bool(proxy.is_dirty)).is_true()
assert_that(proxy.dirty_fields).contains("name")

proxy.reset_dirty()
assert_that(bool(proxy.is_dirty)).is_false()
```

```python
dirty_states: list[bool] = []
proxy.is_dirty.on_change(lambda d: dirty_states.append(d))

proxy.name.set("Bob")  # clean -> dirty
proxy.age.set(31)  # stays dirty
proxy.reset_dirty()  # dirty -> clean

assert_that(dirty_states).is_equal_to([True, False])
```

## Nested Objects

Nested objects are automatically wrapped as `ObservableProxy`. Changes propagate callbacks and dirty state to parent.

```python
breed = Breed("Labrador", "Canada")
dog = Dog("Buddy", 5, breed)
proxy = ObservableProxy(dog)

breed_proxy = proxy.breed
assert_that(breed_proxy).is_instance_of(ObservableProxy)

assert_that(proxy.breed.name.get()).is_equal_to("Labrador")
proxy.breed.name.set("Golden Retriever")
assert_that(breed.name).is_equal_to("Golden Retriever")
```

```python
proxy.on_change(lambda: changes.append("dog_changed"))
proxy.breed.name.set("Golden Retriever")
assert_that(changes).is_equal_to(["dog_changed"])

assert_that(bool(proxy.is_dirty)).is_true()
assert_that(bool(proxy.breed.is_dirty)).is_true()
```

## List Fields

List fields are automatically wrapped as `ObservableList`. Modifications fire callbacks and mark dirty.

```python
person = PersonWithCollections("Alice", ["admin", "user"], {"age": 30})
proxy = ObservableProxy(person)

tags = proxy.tags
assert_that(tags).is_instance_of(ObservableList)

proxy.tags.append("moderator")
assert_that(proxy.tags.to_list()).is_equal_to(["admin", "user", "moderator"])
assert_that(bool(proxy.is_dirty)).is_true()
assert_that(proxy.dirty_fields).contains("tags")
```

## Dict Fields

Dict fields are automatically wrapped as `ObservableDict`. Modifications fire callbacks and mark dirty.

```python
person = PersonWithCollections("Alice", ["admin"], {"age": 30})
proxy = ObservableProxy(person)

metadata = proxy.metadata
assert_that(metadata).is_instance_of(ObservableDict)

proxy.metadata["score"] = 100
assert_that(proxy.metadata.to_dict()).is_equal_to({"age": 30, "score": 100})
assert_that(bool(proxy.is_dirty)).is_true()
assert_that(proxy.dirty_fields).contains("metadata")
```

## Disable Dirty Tracking

Dirty tracking can be disabled via constructor parameter. Proxy still works normally for field access and callbacks.

```python
person = Person("Alice", 30)
proxy = ObservableProxy(person, dirty_tracking=False)

try:
    _ = proxy.is_dirty
    assert_that(False).is_true()  # Should not reach here
except RuntimeError as e:
    assert_that(str(e)).contains("not enabled")

# But normal operations work fine
proxy.name.set("Bob")
assert_that(proxy.name.get()).is_equal_to("Bob")
```
