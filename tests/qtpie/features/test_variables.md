# Variables in QtPie

`Variable[T]` is QtPie's reactive state primitive. Variables hold values that automatically trigger updates when changed.

## Basic Variable Declaration

Variables are declared as class fields with type annotations and initialized via `new()`.

```python
_count: Variable[int] = new(0)
_name: Variable[str] = new("hello")
_enabled: Variable[bool] = new(True)
```

## Var Alias

`Var` is an alias for `Variable` - they are identical.

```python
_name: Var[str] = new("hello")  # Same as Variable[str]
```

## Accessing and Setting Values

Use `.value` property or call the variable directly.

```python
# Read
instance._count.value  # via .value property
instance._count()      # callable shorthand

# Write
instance._count.value = 42
```

## Augmented Assignment Operators

Variables support all augmented assignment operators.

```python
instance._count += 5   # __iadd__
instance._count -= 3   # __isub__
instance._count *= 2   # __imul__
instance._value /= 4   # __itruediv__
instance._count //= 3  # __ifloordiv__
instance._count %= 3   # __imod__
```

## Variable with Inline Widget

`Variable[T, W]` creates both a reactive value and an auto-bound widget.

```python
_message: Variable[str, QLabel] = new("Hello")
_name: Variable[str, QLineEdit] = new("")

# Access widget via .widget property
instance._message.widget  # QLabel
instance._name.widget     # QLineEdit
```

## List Variables

`Variable[list[T]]` provides reactive lists. Use `default=` for initial values.

```python
_items: Variable[list[str]] = new()                      # Empty list
_items: Variable[list[str]] = new(default=["a", "b"])    # With initial values

# Modify via .observable
instance._items.observable.append("hello")
```

## Dict Variables

`Variable[dict[K, V]]` provides reactive dictionaries.

```python
_data: Variable[dict[str, int]] = new()                       # Empty dict
_data: Variable[dict[str, int]] = new(default={"a": 1})       # With initial values

# Modify via .observable
instance._data.observable["key"] = 42
```

## Set Variables

`Variable[set[T]]` provides reactive sets.

```python
_tags: Variable[set[str]] = new()                        # Empty set
_tags: Variable[set[str]] = new(default={"a", "b"})      # With initial values

# Modify via .observable
instance._tags.observable.add("hello")
instance._tags.observable.discard("a")
instance._tags.observable.clear()
```

## Instance Isolation

Each widget instance has its own independent variable values - no shared state.

```python
a = MyWidget()
b = MyWidget()
a._count += 10
b._count += 20
# a._count.value == 10, b._count.value == 20
```

## Bare Variable Resolution (Dependency Injection)

Declare a Variable without `new()` to auto-resolve from parent widget hierarchy.

```python
@widget
class Child(Widget):
    _count: Variable[int]  # Bare - resolves from parent

@widget
class Parent(Widget):
    _count: Variable[int] = new(0)
    _child: Child = new()

# parent._child._count is the SAME object as parent._count
```

Resolution rules:
- Matches by exact field name
- Closest parent wins (child before grandparent)
- Raises `AttributeError` if not found in hierarchy

## Explicit Variable Binding

Override auto-resolution with explicit binding in `new()`.

```python
@widget
class Parent(Widget):
    _count: Variable[int] = new(0)
    _other: Variable[int] = new(999)
    _child: Child = new(_count="_other")  # Binds child's _count to _other
```

## Widget Property Bindings (visible/enabled)

For `Variable[T, W]`, bind widget visibility/enabled state via widget kwargs.

```python
_show: Variable[bool] = new(True)
_name: Variable[str, QLineEdit] = new("")(visible="_show")
_input: Variable[str, QLineEdit] = new("")(enabled="_can_edit")

# Expression bindings
_message: Variable[str, QLabel] = new("Hello")(visible="{_count > 0}")
```

## onChange Callback

React to value changes with the `onChange` parameter.

```python
# Method name reference
_count: Variable[int] = new(0, onChange="_on_count_changed")

def _on_count_changed(self) -> None:
    print(f"Count changed to {self._count.value}")

# Callback receives value as argument
def _on_count_changed(self, value: int) -> None:
    print(f"Count changed to {value}")

# Lambda callback
_count: Variable[int] = new(0, onChange=lambda v: print(v))
```

## Supported Types

Variables work with all Python types:
- Primitives: `int`, `str`, `bool`, `float`
- Optional: `Variable[Item | None] = new(None)`
- Union types: `Variable[TypeA | TypeB | None]`
- Collections: `list[T]`, `dict[K, V]`, `set[T]`
