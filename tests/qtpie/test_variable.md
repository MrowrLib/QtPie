# Variable Usage Patterns in QtPie

This document describes the usage patterns and conventions for `Variable[T]` in QtPie, extracted from the test suite.

## Basic Variable Declaration

Variables are declared using the `Variable[T]` type annotation with `new()` to set defaults.

```python
@new_fields
class MyClass:
    _name: Variable[str] = new("default")
    _count: Variable[int] = new(0)
```

## Accessing Variable Values

Use `.value` to get/set the underlying value.

```python
obj._count.value = 42
print(obj._name.value)
```

## Direct Assignment (Descriptor Pattern)

Variables support direct assignment syntax as a shorthand.

```python
obj._count = 42  # Equivalent to obj._count.value = 42
```

## Per-Instance Isolation

Each instance gets its own variable state - no shared state between instances.

```python
a = MyClass()
b = MyClass()
a._value.value = 10
b._value.value = 20  # Independent from a
```

## Reactivity / Change Callbacks

Variables are reactive and trigger callbacks when values change.

```python
obj._name.on_change(lambda v: print(f"Changed to: {v}"))
obj._name.value = "hello"  # Triggers callback
```

## Primitive Type Defaults

All primitive types work directly with `new()` - no `default=` keyword needed.

```python
_name: Variable[str] = new("hello")
_count: Variable[int] = new(42)
_ratio: Variable[float] = new(3.14)
_enabled: Variable[bool] = new(True)
```

The `default=` keyword is available for backwards compatibility:

```python
_value: Variable[int] = new(default=99)
```

## Augmented Assignment Operators

Variables support `+=`, `-=`, `*=`, `/=`, `//=`, `%=` operators.

```python
obj._count += 5
obj._count -= 3
obj._count *= 2
```

These trigger change callbacks automatically.

## Variable[list[T]] - Observable Lists

List variables automatically become `ObservableList` with empty list default.

```python
_tags: Variable[list[str]] = new()           # Defaults to []
_tags: Variable[list[str]] = new(default=["a", "b"])
```

Modification through `.observable`:

```python
obj._items.observable.append(1)
obj._items.value = [10, 20, 30]  # Replace entire list
```

## Variable[dict[K, V]] - Observable Dicts

Dict variables automatically become `ObservableDict` with empty dict default.

```python
_data: Variable[dict[str, int]] = new()               # Defaults to {}
_data: Variable[dict[str, int]] = new(default={"a": 1})
```

Modification through `.observable`:

```python
obj._data.observable["x"] = 10
obj._data.value = {"new": 100}  # Replace entire dict
```

## Variable[ComplexType] - Observable Proxy

Complex types (like dataclasses) become `ObservableProxy` for field-level reactivity.

```python
@dataclass
class Person:
    name: str
    age: int

@new_fields
class MyClass:
    _person: Variable[Person] = new(default=Person("Alice", 30))
```

Modify through `.observable`:

```python
obj._person.observable.name.set("Charlie")
```

**Note**: Complex type defaults are shared across instances. Use factory pattern if per-instance data is needed.

## Variable[T | None] - Optional Types

Union with None auto-constructs complex types but keeps primitives as None.

```python
# Complex type: auto-constructs Workspace()
_workspace: Variable[Workspace | None] = new()

# Primitive type: defaults to None
_value: Variable[str | None] = new()

# Explicit value works for both
_count: Variable[int | None] = new(42)
_config: Variable[Config | None] = new(host="localhost", port=8080)
```

## Dirty Tracking

Variables track whether they've been modified from their initial value.

```python
obj._items.is_dirty.get()  # False initially
obj._items.observable.append("test")
obj._items.is_dirty.get()  # True after modification
```

## Mixing Variable and Regular Fields

`@new_fields` handles both `Variable[T]` and regular type annotations.

```python
@new_fields
class MyClass:
    _name: Variable[str] = new("test")     # Reactive variable
    _counter: Counter = new(start=10)       # Regular instance
```

## RecordVariable Field Access

`RecordVariable` provides direct field access without shadowing record fields named `items`, `keys`, `values`, `get`, or `update`.

```python
@dataclass
class Container:
    items: list[str]

rv.items[0]  # Accesses Container.items, not Variable.items()
```

## @new_fields Decorator

The `@new_fields` decorator processes `new()` field definitions. It is idempotent (safe to apply multiple times).

```python
@new_fields
class MyClass:
    _value: Variable[int] = new(0)
```
