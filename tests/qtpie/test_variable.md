# Variable[T] Features

## Basic Variable Storage

`Variable[T]` stores reactive values with get/set access. Each instance has its own storage.

```python
@new_fields
class MyClass:
    _count: Variable[int] = new(0)

obj = MyClass()
obj._count.value = 42
assert_that(obj._count.value).is_equal_to(42)
```

## Direct Assignment

Variables support direct assignment syntax (`obj._count = 42`) as sugar for `.value =`.

```python
@new_fields
class MyClass:
    _count: Variable[int] = new(0)

obj = MyClass()
obj._count = 42  # Direct assignment
assert_that(obj._count.value).is_equal_to(42)
```

## Reactivity

Variable changes trigger callbacks via the underlying observable.

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

## Primitive Defaults

`new()` accepts primitive values directly without requiring `default=` keyword.

```python
@new_fields
class MyClass:
    _name: Variable[str] = new("hello")
    _count: Variable[int] = new(42)
    _ratio: Variable[float] = new(3.14)
    _enabled: Variable[bool] = new(True)
```

## Augmented Assignment Operators

Variables support `+=`, `-=`, `*=`, `/=`, `//=`, `%=` operators that trigger change callbacks.

```python
@new_fields
class MyClass:
    _count: Variable[int] = new(10)

obj = MyClass()
obj._count += 5
assert_that(obj._count.value).is_equal_to(15)

obj._count -= 3
assert_that(obj._count.value).is_equal_to(7)
```

## Variable[list[T]] → ObservableList

List-typed variables automatically use `ObservableList` with granular change tracking and dirty state.

```python
@new_fields
class MyClass:
    _items: Variable[list[int]] = new()

obj = MyClass()
obj._items.observable.append(1)
obj._items.observable.append(2)
assert_that(obj._items.value).is_equal_to([1, 2])

assert_that(obj._items.is_dirty.get()).is_true()
```

## Variable[dict[K,V]] → ObservableDict

Dict-typed variables automatically use `ObservableDict` with granular change tracking and dirty state.

```python
@new_fields
class MyClass:
    _data: Variable[dict[str, int]] = new()

obj = MyClass()
obj._data.observable["x"] = 10
obj._data.observable["y"] = 20
assert_that(obj._data.value).is_equal_to({"x": 10, "y": 20})

assert_that(obj._data.is_dirty.get()).is_true()
```

## Variable[ComplexType] → ObservableProxy

Complex object variables automatically use `ObservableProxy` for reactive field access.

```python
@dataclass
class Person:
    name: str
    age: int

@new_fields
class MyClass:
    _person: Variable[Person] = new(default=Person("Bob", 25))

obj = MyClass()
obj._person.observable.name.set("Charlie")
assert_that(obj._person.value.name).is_equal_to("Charlie")

assert_that(obj._person.is_dirty.get()).is_true()
```

## new() with Non-Variable Types

`new()` can instantiate any type, not just `Variable[T]`, passing args and kwargs to the constructor.

```python
class Config:
    def __init__(self, *, host: str, port: int) -> None:
        self.host = host
        self.port = port

@new_fields
class MyClass:
    _config: Config = new(host="localhost", port=8080)

obj = MyClass()
assert_that(obj._config.host).is_equal_to("localhost")
assert_that(obj._config.port).is_equal_to(8080)
```
