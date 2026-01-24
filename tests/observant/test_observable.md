# Observable[T] Usage Patterns

Documentation of `Observable[T]` usage patterns from the Observant library.

## Creating an Observable

Create a typed observable with an initial value using generics:

```python
obs = Observable[int](42)
obs = Observable[str]("hello")
obs = Observable[list[int]]([1, 2, 3])
```

## Getting the Value

Use `.get()` to retrieve the current value:

```python
value = obs.get()
```

## Setting the Value

Use `.set()` to update the value (triggers callbacks):

```python
obs.set("world")
```

## Subscribing to Changes

Use `.on_change()` with a callback that receives the new value:

```python
obs.on_change(lambda v: print(f"New value: {v}"))
```

## Multiple Callbacks

Register multiple callbacks - all will fire in registration order:

```python
obs.on_change(lambda v: results.append(f"a:{v}"))
obs.on_change(lambda v: results.append(f"b:{v}"))
```

## Callback Deduplication

Registering the same callback twice only fires once (automatic dedup):

```python
obs.on_change(increment)
obs.on_change(increment)  # ignored - duplicate
```

## Key Behaviors

- Callbacks fire on **every** `.set()` call, not just when value actually changes
- Duplicate callback registrations are ignored (same function only fires once)
- Works with any type: primitives, strings, lists, custom objects
