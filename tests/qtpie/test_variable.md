# Variable Tests Summary

## Variable[T] basic usage

`Variable[T]` fields created with `new()` store reactive values that can be get/set via `.value` property.

```python
@new_fields
class MyClass:
    _name: Variable[str] = new("default")

obj = MyClass()
assert_that(obj._name.value).is_equal_to("default")
obj._name.value = "updated"
```

## Direct assignment

Variables support direct assignment syntax that sets the underlying value.

```python
@new_fields
class MyClass:
    _count: Variable[int] = new(0)

obj = MyClass()
obj._count = 42  # Sets the value
assert_that(obj._count.value).is_equal_to(42)
```

## Per-instance state

Each instance gets its own independent Variable value.

```python
@new_fields
class MyClass:
    _value: Variable[int] = new(0)

a = MyClass()
b = MyClass()
a._value.value = 10
b._value.value = 20

assert_that(a._value.value).is_equal_to(10)
assert_that(b._value.value).is_equal_to(20)
```

## Reactivity

Variable changes trigger callbacks registered via `on_change()`.

```python
@new_fields
class MyClass:
    _name: Variable[str] = new("")

obj = MyClass()
received: list[str] = []
observable = cast(Observable[str], obj._name.observable)
observable.on_change(lambda v: received.append(v))

obj._name.value = "hello"
obj._name.value = "world"

assert_that(received).is_equal_to(["hello", "world"])
```

## Regular types with new()

`new()` works with non-Variable types, instantiating them with provided args/kwargs.

```python
class Greeter:
    def __init__(self, name: str) -> None:
        self.name = name

@new_fields
class MyClass:
    _greeter: Greeter = new("Alice")

obj = MyClass()
assert_that(obj._greeter.name).is_equal_to("Alice")
```

```python
class Config:
    def __init__(self, *, host: str, port: int) -> None:
        self.host = host
        self.port = port

@new_fields
class MyClass:
    _config: Config = new(host="localhost", port=8080)
```

## Primitive defaults

Primitives (str, int, float, bool) can be passed directly as first arg without `default=` kwarg.

```python
@new_fields
class MyClass:
    _name: Variable[str] = new("hello")
    _count: Variable[int] = new(42)
    _ratio: Variable[float] = new(3.14)
    _enabled: Variable[bool] = new(True)
```

## Augmented assignment operators

Variables support `+=`, `-=`, `*=`, `/=`, `//=`, `%=` operators that modify and trigger reactivity.

```python
@new_fields
class MyClass:
    _count: Variable[int] = new(10)

obj = MyClass()
obj._count += 5
assert_that(obj._count.value).is_equal_to(15)
```

```python
@new_fields
class MyClass:
    _count: Variable[int] = new(0)

obj = MyClass()
obj._count.on_change(on_change)
obj._count += 1  # Triggers callback
```

## Variable[list[T]]

`Variable[list[T]]` wraps an ObservableList with reactive list operations.

```python
@new_fields
class MyClass:
    _items: Variable[list[int]] = new()

obj = MyClass()
obj._items.observable.append(1)
obj._items.observable.append(2)
assert_that(obj._items.value).is_equal_to([1, 2])
```

```python
@new_fields
class MyClass:
    _items: Variable[list[str]] = new()

obj = MyClass()
changes: list[str] = []
obj._items.on_change(lambda: changes.append("changed"))
obj._items.observable.append("hello")
assert_that(changes).is_equal_to(["changed"])
```

## Variable[dict[K, V]]

`Variable[dict[K, V]]` wraps an ObservableDict with reactive dict operations.

```python
@new_fields
class MyClass:
    _data: Variable[dict[str, int]] = new()

obj = MyClass()
obj._data.observable["x"] = 10
obj._data.observable["y"] = 20
assert_that(obj._data.value).is_equal_to({"x": 10, "y": 20})
```

```python
@new_fields
class MyClass:
    _data: Variable[dict[str, int]] = new()

obj = MyClass()
changes: list[str] = []
obj._data.on_change(lambda: changes.append("changed"))
obj._data.observable["key"] = 42
assert_that(changes).is_equal_to(["changed"])
```

## Variable[ComplexType]

`Variable[ComplexType]` wraps custom objects in ObservableProxy for reactive field access.

```python
@dataclass
class Person:
    name: str
    age: int

@new_fields
class MyClass:
    _person: Variable[Person] = new(default=Person("Alice", 30))

obj = MyClass()
obj._person.observable.name.set("Charlie")
assert_that(obj._person.value.name).is_equal_to("Charlie")
```

```python
@new_fields
class MyClass:
    _person: Variable[Person] = new(default=Person("Dana", 40))

obj = MyClass()
changes: list[str] = []
obj._person.on_change(lambda: changes.append("changed"))
obj._person.observable.age.set(41)
assert_that(changes).is_equal_to(["changed"])
```

## Dirty tracking

Variables track whether they've been modified via `.is_dirty` observable.

```python
@new_fields
class MyClass:
    _items: Variable[list[str]] = new()

obj = MyClass()
assert_that(obj._items.is_dirty.get()).is_false()
obj._items.observable.append("test")
assert_that(obj._items.is_dirty.get()).is_true()
```

```python
@new_fields
class MyClass:
    _person: Variable[Person] = new(default=Person("Eve", 35))

obj = MyClass()
assert_that(obj._person.is_dirty.get()).is_false()
obj._person.observable.name.set("Evelyn")
assert_that(obj._person.is_dirty.get()).is_true()
```
