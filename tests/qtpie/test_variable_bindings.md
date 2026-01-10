# Variable Bindings Test Summary

## Required vs Optional Bindings

Bare `Variable[T]` annotations (without `= new()`) are detected as required bindings. Variables with defaults are optional.

```python
@widget
class Child(Widget):
    count: Variable[int]  # Required - no = new()
    name: Variable[str] = new("default")  # Optional - has default

# Missing required binding raises error at instantiation
@widget
class Parent(Widget):
    child: Child = new()  # TypeError: requires binding for 'count'
```

## Two-Way Binding

Child variables bound to parent variables sync bidirectionally.

```python
@widget
class Child(Widget):
    count: Variable[int]

@widget
class Parent(Widget):
    _my_count: Variable[int] = new(0)
    child: Child = new(count="_my_count")

parent = Parent()
parent._my_count.value = 42
assert parent.child.count.value == 42  # Parent -> Child

parent.child.count.value = 100
assert parent._my_count.value == 100  # Child -> Parent
```

## Expression Bindings

Bindings can be Python expressions wrapped in `{}`, creating one-way computed bindings.

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

## Literal Values

Non-binding values (not starting with `_` or containing `{}`) set the Variable's default value.

```python
@widget
class Child(Widget):
    label_text: Variable[str]

@widget
class Parent(Widget):
    child: Child = new(label_text="Hello")

parent = Parent()
assert parent.child.label_text.value == "Hello"
```

## Nested Bindings (Pass-Through)

Bindings propagate through multiple levels of nested widgets, maintaining reactivity across the entire chain.

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]

@widget
class Child(Widget):
    theme: Variable[str]
    grandchild: GrandChild = new(theme="theme")

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")

parent = Parent()
assert parent.child.grandchild.theme.value == "dark"

parent._theme.value = "light"
assert parent.child.grandchild.theme.value == "light"
```

## Format Bindings with Required Variables

Format bindings work correctly with required variables, even in deeply nested widgets.

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]
    _label: QLabel = new(bind="Theme: {theme}")

@widget
class Child(Widget):
    theme: Variable[str]
    grandchild: GrandChild = new(theme="theme")

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")

parent = Parent()
assert parent.child.grandchild._label.text() == "Theme: dark"

parent._theme.value = "light"
assert parent.child.grandchild._label.text() == "Theme: light"
```

## Deep Nesting

The binding system handles extreme nesting depths (5+ levels) with format bindings at any level.

```python
# Six levels deep
@widget
class L6(Widget):
    v: Variable[str]
    _l: QLabel = new(bind="{v}")

@widget
class L5(Widget):
    v: Variable[str]
    l6: L6 = new(v="v")

# ... L4, L3, L2, L1 ...

@widget
class Root(Widget):
    _v: Variable[str] = new("deep")
    l1: L1 = new(v="_v")

root = Root()
assert root.l1.l2.l3.l4.l5.l6._l.text() == "deep"
```

## Multiple Required Bindings

Multiple required variables can be passed through each nesting level, with format bindings using multiple variables.

```python
@widget
class GrandChild(Widget):
    first: Variable[str]
    last: Variable[str]
    age: Variable[int]
    _label: QLabel = new(bind="{first} {last}, age {age}")

@widget
class Child(Widget):
    first: Variable[str]
    last: Variable[str]
    age: Variable[int]
    grandchild: GrandChild = new(first="first", last="last", age="age")

@widget
class Parent(Widget):
    _first: Variable[str] = new("John")
    _last: Variable[str] = new("Doe")
    _age: Variable[int] = new(30)
    child: Child = new(first="_first", last="_last", age="_age")

parent = Parent()
assert parent.child.grandchild._label.text() == "John Doe, age 30"
```

## Complex Format Expressions

Format bindings support method calls, complex expressions, and multiple format bindings per widget.

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

## Sibling Widgets

Multiple sibling widgets can receive the same binding or different bindings, all maintaining reactivity.

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
parent._shared.value = "updated"
assert parent.child1._label.text() == "updated"
assert parent.child2._label.text() == "updated"
assert parent.child3._label.text() == "updated"
```

## Mixed Literal and Binding

Some child widgets can receive bindings while others receive literal values.

```python
@widget
class ChildWidget(Widget):
    value: Variable[str]
    _label: QLabel = new(bind="{value}")

@widget
class Parent(Widget):
    _dynamic: Variable[str] = new("dynamic")
    bound_child: ChildWidget = new(value="_dynamic")
    literal_child: ChildWidget = new(value="static")

parent = Parent()
parent._dynamic.value = "changed"
assert parent.bound_child._label.text() == "changed"
assert parent.literal_child._label.text() == "static"
```
