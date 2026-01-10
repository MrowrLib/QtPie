# Variable Bindings Test Summary

## Required vs Optional Bindings

Variables declared without `new()` are required bindings. Variables with `new(default)` are optional.

```python
@widget
class Child(Widget):
    count: Variable[int]  # No = new()

assert "count" in Child._qtpie_config.required_bindings
```

```python
@widget
class Child(Widget):
    required_var: Variable[int]  # Required
    optional_var: Variable[str] = new("default")  # Optional
    another_required: Variable[bool]  # Required

assert Child._qtpie_config.required_bindings == {"required_var", "another_required"}
```

## Validation of Required Bindings

Missing required bindings raise a TypeError at instantiation.

```python
@widget
class Child(Widget):
    count: Variable[int]  # Required!

@widget
class Parent(Widget):
    child: Child = new()  # Missing count binding!

with pytest.raises(TypeError, match="requires binding for 'count'"):
    Parent()
```

```python
@widget
class Child(Widget):
    count: Variable[int]

@widget
class Parent(Widget):
    _my_count: Variable[int] = new(0)
    child: Child = new(count="_my_count")

# Should not raise
parent = Parent()
assert parent.child is not None
```

## Two-Way Reactive Bindings

Parent variable changes propagate to child, and child changes propagate back to parent.

```python
@widget
class Child(Widget):
    count: Variable[int]

@widget
class Parent(Widget):
    _my_count: Variable[int] = new(0)
    child: Child = new(count="_my_count")

parent = Parent()

# Initially synced
assert parent.child.count.value == 0

# Parent changes -> child updates
parent._my_count.value = 42
assert parent.child.count.value == 42

# Child changes -> parent updates (two-way!)
parent.child.count.value = 100
assert parent._my_count.value == 100
```

## Expression Bindings

One-way computed bindings using format string expressions.

```python
@widget
class Child(Widget):
    enabled: Variable[bool]

@widget
class Parent(Widget):
    _items: Variable[list[str]] = new([])
    child: Child = new(enabled="{len(_items) > 0}")

parent = Parent()
assert parent.child.enabled.value is False

parent._items.value = ["a", "b"]
assert parent.child.enabled.value is True
```

## Literal Value Bindings

Non-binding values set the Variable's default.

```python
@widget
class Child(Widget):
    label_text: Variable[str]

@widget
class Parent(Widget):
    # "Hello" doesn't start with _ or contain {}, so it's a literal
    child: Child = new(label_text="Hello")

parent = Parent()
assert parent.child.label_text.value == "Hello"
```

## Nested Widget Bindings

Bindings pass through multiple levels of widget hierarchy.

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]

@widget
class Child(Widget):
    theme: Variable[str]  # Required, will pass to grandchild
    grandchild: GrandChild = new(theme="theme")  # Pass our theme down

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")

parent = Parent()
assert parent.child.grandchild.theme.value == "dark"

# Changes propagate through the chain
parent._theme.value = "light"
assert parent.child.grandchild.theme.value == "light"
```

## Nested Bindings with Format Strings

Required bindings work correctly with format string bindings at nested levels.

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]
    _label: QLabel = new(bind="Theme: {theme}")

@widget
class Child(Widget):
    theme: Variable[str]  # Required, passed to grandchild
    grandchild: GrandChild = new(theme="theme")

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")

parent = Parent()

# Format binding should work
assert parent.child.grandchild._label.text() == "Theme: dark"

# Updates should propagate
parent._theme.value = "light"
assert parent.child.grandchild._label.text() == "Theme: light"
```

## Deep Nesting

Bindings work correctly through many levels of widget hierarchy.

```python
@widget
class L6(Widget):
    v: Variable[str]
    _l: QLabel = new(bind="{v}")

@widget
class L5(Widget):
    v: Variable[str]
    l6: L6 = new(v="v")

@widget
class L4(Widget):
    v: Variable[str]
    l5: L5 = new(v="v")

@widget
class L3(Widget):
    v: Variable[str]
    l4: L4 = new(v="v")

@widget
class L2(Widget):
    v: Variable[str]
    l3: L3 = new(v="v")

@widget
class L1(Widget):
    v: Variable[str]
    l2: L2 = new(v="v")

@widget
class Root(Widget):
    _v: Variable[str] = new("deep")
    l1: L1 = new(v="_v")

root = Root()
assert root.l1.l2.l3.l4.l5.l6._l.text() == "deep"
```

## Multiple Required Bindings

Multiple required bindings pass through hierarchy and work in format expressions.

```python
@widget
class GrandChild(Widget):
    name: Variable[str]
    count: Variable[int]
    enabled: Variable[bool]
    _label: QLabel = new(bind="{name}: {count} ({'on' if enabled else 'off'})")

@widget
class Child(Widget):
    name: Variable[str]
    count: Variable[int]
    enabled: Variable[bool]
    grandchild: GrandChild = new(name="name", count="count", enabled="enabled")

@widget
class Parent(Widget):
    _name: Variable[str] = new("test")
    _count: Variable[int] = new(5)
    _enabled: Variable[bool] = new(True)
    child: Child = new(name="_name", count="_count", enabled="_enabled")

parent = Parent()
assert parent.child.grandchild._label.text() == "test: 5 (on)"

parent._name.value = "updated"
parent._count.value = 10
parent._enabled.value = False
assert parent.child.grandchild._label.text() == "updated: 10 (off)"
```

## Sibling Widgets with Shared Bindings

Multiple sibling widgets can receive the same binding and all update together.

```python
@widget
class ChildWidget(Widget):
    value: Variable[str]
    _label: QLabel = new(bind="{value}")

@widget
class Parent(Widget):
    _shared: Variable[str] = new("shared")
    child1: ChildWidget = new(value="_shared")
    child2: ChildWidget = new(value="_shared")
    child3: ChildWidget = new(value="_shared")

parent = Parent()
assert parent.child1._label.text() == "shared"
assert parent.child2._label.text() == "shared"
assert parent.child3._label.text() == "shared"

parent._shared.value = "updated"
assert parent.child1._label.text() == "updated"
assert parent.child2._label.text() == "updated"
assert parent.child3._label.text() == "updated"
```

## Diamond Dependency Pattern

Multiple widget branches can share the same root binding.

```python
@widget
class Leaf(Widget):
    value: Variable[str]
    _label: QLabel = new(bind="{value}")

@widget
class IntermediateA(Widget):
    value: Variable[str]
    leaf: Leaf = new(value="value")

@widget
class IntermediateB(Widget):
    value: Variable[str]
    leaf: Leaf = new(value="value")

@widget
class Root(Widget):
    _shared: Variable[str] = new("shared")
    intermediate_a: IntermediateA = new(value="_shared")
    intermediate_b: IntermediateB = new(value="_shared")

root = Root()
assert root.intermediate_a.leaf._label.text() == "shared"
assert root.intermediate_b.leaf._label.text() == "shared"

# Both should update
root._shared.value = "updated"
assert root.intermediate_a.leaf._label.text() == "updated"
assert root.intermediate_b.leaf._label.text() == "updated"
```

## Complex Format Expressions

Format bindings support method calls, complex expressions, and conditionals.

```python
@widget
class GrandChild(Widget):
    items: Variable[list[str]]
    _label: QLabel = new(bind="Items: {len(items)} - {', '.join(items)}")

@widget
class Child(Widget):
    items: Variable[list[str]]
    grandchild: GrandChild = new(items="items")

@widget
class Parent(Widget):
    _items: Variable[list[str]] = new(["a", "b", "c"])
    child: Child = new(items="_items")

parent = Parent()
assert parent.child.grandchild._label.text() == "Items: 3 - a, b, c"
```

```python
@widget
class GrandChild(Widget):
    active: Variable[bool]
    count: Variable[int]
    _label: QLabel = new(bind="{'Active' if active else 'Inactive'}: {count if count > 0 else 'none'}")

@widget
class Child(Widget):
    active: Variable[bool]
    count: Variable[int]
    grandchild: GrandChild = new(active="active", count="count")

@widget
class Parent(Widget):
    _active: Variable[bool] = new(False)
    _count: Variable[int] = new(0)
    child: Child = new(active="_active", count="_count")

parent = Parent()
assert parent.child.grandchild._label.text() == "Inactive: none"

parent._active.value = True
parent._count.value = 5
assert parent.child.grandchild._label.text() == "Active: 5"
```

## Mixed Binding and Literal Values

Widgets can receive both bound and literal values simultaneously.

```python
@widget
class ChildWidget(Widget):
    value: Variable[str]
    _label: QLabel = new(bind="{value}")

@widget
class Parent(Widget):
    _dynamic: Variable[str] = new("dynamic")
    # One child gets a binding, one gets a literal
    bound_child: ChildWidget = new(value="_dynamic")
    literal_child: ChildWidget = new(value="static")

parent = Parent()
assert parent.bound_child._label.text() == "dynamic"
assert parent.literal_child._label.text() == "static"

parent._dynamic.value = "changed"
assert parent.bound_child._label.text() == "changed"
assert parent.literal_child._label.text() == "static"  # Unchanged
```
