# Observable[T] Tests

## Value Storage and Retrieval

Store and retrieve values of any type.

```python
obs = Observable[int](42)
assert_that(obs.get()).is_equal_to(42)

obs.set("world")
assert_that(obs.get()).is_equal_to("world")
```

## Change Callbacks

Register callbacks that fire when `set()` is called. Multiple callbacks are supported, and duplicates are ignored.

```python
obs = Observable[int](0)
received: list[int] = []

obs.on_change(lambda v: received.append(v))
obs.set(1)

assert_that(received).is_equal_to([1])
```

```python
obs.on_change(lambda v: results.append(f"a:{v}"))
obs.on_change(lambda v: results.append(f"b:{v}"))
obs.set(5)

assert_that(results).is_equal_to(["a:5", "b:5"])
```

## Callback Fires on Every Set

Callbacks fire on every `set()` call, regardless of whether the value actually changed.

```python
obs.on_change(lambda _: count.__setitem__(0, count[0] + 1))
obs.set(1)
obs.set(2)
obs.set(3)

assert_that(count[0]).is_equal_to(3)
```

## Type Flexibility

Works with strings, numbers, lists, and any other type.

```python
str_obs = Observable[str]("test")
float_obs = Observable[float](3.14)
list_obs = Observable[list[int]]([1, 2, 3])

assert_that(str_obs.get()).is_equal_to("test")
assert_that(float_obs.get()).is_equal_to(3.14)
assert_that(list_obs.get()).is_equal_to([1, 2, 3])
```
