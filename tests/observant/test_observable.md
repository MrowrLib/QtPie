# Observable[T] Tests

## Value Storage

Observable stores and retrieves values of any type.

```python
obs = Observable[int](42)
assert_that(obs.get()).is_equal_to(42)

obs.set("world")
assert_that(obs.get()).is_equal_to("world")
```

## Change Callbacks

Register callbacks that fire when `set()` is called.

```python
obs = Observable[int](0)
received: list[int] = []

obs.on_change(lambda v: received.append(v))
obs.set(1)

assert_that(received).is_equal_to([1])
```

Multiple callbacks all fire:

```python
obs.on_change(lambda v: results.append(f"a:{v}"))
obs.on_change(lambda v: results.append(f"b:{v}"))
obs.set(5)

assert_that(results).is_equal_to(["a:5", "b:5"])
```

## Callback Deduplication

Same callback registered twice only fires once.

```python
def increment(_: int) -> None:
    count[0] += 1

obs.on_change(increment)
obs.on_change(increment)  # duplicate
obs.set(1)

assert_that(count[0]).is_equal_to(1)
```

## Type Support

Works with strings, numbers, lists, and other types.

```python
str_obs = Observable[str]("test")
float_obs = Observable[float](3.14)
list_obs = Observable[list[int]]([1, 2, 3])
```
