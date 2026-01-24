# Variable Resolution with `var()` Method

The `var()` method provides hierarchical variable resolution across Widget, Window, Menu, and App instances. It resolves variables from self first, then walks up the parent widget hierarchy.

## Basic Variable Resolution

### Resolve Variable by Name

Access a Variable's value by name. The underscore prefix is optional when looking up `_variable` names.

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(42)

# Both work:
instance.var("count", int)   # Returns 42
instance.var("_count", int)  # Returns 42
```

### Resolve Plain Attributes

`var()` also works with plain class attributes, not just Variables.

```python
@widget
class MyWidget(Widget):
    my_value: int = 123

instance.var("my_value", int)  # Returns 123
```

## Parent Hierarchy Resolution

### Access Parent Variables from Child

Child widgets can access Variables defined on parent widgets through `var()`.

```python
@widget
class Child(Widget):
    def get_parent_count(self) -> int:
        return self.var("count", int)

@widget
class Parent(Widget):
    _count: Variable[int] = new(42)
    child: Child = new()

parent.child.get_parent_count()  # Returns 42
```

### Multi-Level Resolution

`var()` walks up the entire parent hierarchy to find Variables.

```python
@widget
class GrandChild(Widget):
    def get_root_value(self) -> str:
        return self.var("root_value", str)

@widget
class Child(Widget):
    grandchild: GrandChild = new()

@widget
class Root(Widget):
    _root_value: Variable[str] = new("from_root")
    child: Child = new()

root.child.grandchild.get_root_value()  # Returns "from_root"
```

### Closest Parent Wins

When multiple parents have the same variable name, the closest one is used.

```python
@widget
class Child(Widget):
    _count: Variable[int] = new(100)  # Closer - this wins
    grandchild: GrandChild = new()

@widget
class Root(Widget):
    _count: Variable[int] = new(1)  # Further away
    child: Child = new()

# GrandChild.var("count") returns 100 (from Child, not Root)
```

### Self Over Parent

Variables on `self` take precedence over parent variables.

```python
@widget
class Child(Widget):
    _count: Variable[int] = new(999)  # Self - wins

    def get_count(self) -> int:
        return self.var("count", int)  # Returns 999, not parent's value
```

## Reactivity

### Updated Values Reflected

`var()` always returns the current value - changes to Variables are immediately visible.

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)

instance.var("count", int)  # Returns 0
instance._count.value = 42
instance.var("count", int)  # Returns 42
```

### Parent Variable Changes Reflected

Child widgets see updated values when parent Variables change.

```python
parent._count.value = 0
parent.child.get_parent_count()  # Returns 0

parent._count.value = 123
parent.child.get_parent_count()  # Returns 123
```

## Method Signature

```python
def var(self, name: str, type: Type[T]) -> T
```

- `name`: Variable name (with or without underscore prefix)
- `type`: Expected type for type safety
- Returns: The current value of the Variable
- Raises: `AttributeError` if variable not found anywhere in hierarchy
