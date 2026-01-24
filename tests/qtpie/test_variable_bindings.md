# Variable Bindings in QtPie

Variable bindings enable passing reactive state DOWN from parent widgets to child widgets. This is QtPie's primary mechanism for component composition with shared state.

## Required vs Optional Bindings

### Bare Variable (Required)

A `Variable[T]` annotation without `= new()` declares a **required binding** that must be provided by a parent.

```python
@widget
class Child(Widget):
    count: Variable[int]  # Required - parent must provide
```

### Variable with Default (Optional)

A `Variable[T] = new(default)` creates an **optional binding** that uses the default if no parent provides one.

```python
@widget
class Child(Widget):
    count: Variable[int] = new(42)  # Optional - uses 42 if not bound
```

## Binding Syntax in `new()`

### Direct Variable Binding

Pass a string prefixed with `_` to bind to a parent's Variable.

```python
@widget
class Parent(Widget):
    _my_count: Variable[int] = new(0)
    child: Child = new(count="_my_count")  # Binds child.count to parent._my_count
```

### Literal Value Binding

Non-Variable strings (no `_` prefix or `{}`) set a literal value.

```python
child: Child = new(label_text="Hello")  # Sets child.label_text to "Hello"
child: Child = new(count=42)            # Sets child.count to 42
```

### Expression Binding

Strings with `{}` create computed one-way bindings.

```python
child: Child = new(enabled="{len(_items) > 0}")  # Computed from parent._items
```

## Two-Way Reactive Sync

Bound variables sync bidirectionally - changes propagate both ways.

```python
parent._my_count.value = 42
assert parent.child.count.value == 42  # Parent -> Child

parent.child.count.value = 100
assert parent._my_count.value == 100   # Child -> Parent
```

## Nested Pass-Through Bindings

Required bindings can pass through multiple levels of widget hierarchy.

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]

@widget
class Child(Widget):
    theme: Variable[str]                         # Required from parent
    grandchild: GrandChild = new(theme="theme")  # Pass to grandchild

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")           # Provide to child chain
```

Changes at the root propagate through the entire chain automatically.

## Format Bindings with Required Variables

Required variables can be used in format string bindings on widgets.

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]
    _label: QLabel = new(bind="Theme: {theme}")  # Uses required var in format
```

## Multiple Required Bindings

Widgets can require multiple bindings, all passed via `new()`.

```python
@widget
class GrandChild(Widget):
    name: Variable[str]
    count: Variable[int]
    enabled: Variable[bool]

@widget
class Parent(Widget):
    _name: Variable[str] = new("test")
    _count: Variable[int] = new(5)
    _enabled: Variable[bool] = new(True)
    child: Child = new(name="_name", count="_count", enabled="_enabled")
```

## Sibling Widgets Sharing Bindings

Multiple child widgets can bind to the same parent Variable.

```python
@widget
class Parent(Widget):
    _shared: Variable[str] = new("shared")
    child1: ChildWidget = new(value="_shared")
    child2: ChildWidget = new(value="_shared")
    child3: ChildWidget = new(value="_shared")
```

All siblings update when the shared Variable changes.

## Mixed Literal and Bound Children

Some children can receive bindings while others receive literals.

```python
@widget
class Parent(Widget):
    _dynamic: Variable[str] = new("dynamic")
    bound_child: ChildWidget = new(value="_dynamic")   # Reactive binding
    literal_child: ChildWidget = new(value="static")   # Static literal
```

## Diamond Dependency Pattern

Multiple intermediate widgets can share the same root binding.

```python
@widget
class Root(Widget):
    _shared: Variable[str] = new("shared")
    intermediate_a: IntermediateA = new(value="_shared")
    intermediate_b: IntermediateB = new(value="_shared")
```

## Complex Expressions in Format Bindings

Format bindings support Python expressions, method calls, and conditionals.

```python
# Method calls
_label: QLabel = new(bind="{text.upper()}")

# Arithmetic
_sum: QLabel = new(bind="Sum: {val_x + val_y}")

# Conditionals
_label: QLabel = new(bind="{'Active' if active else 'Inactive'}")

# Built-in functions
_label: QLabel = new(bind="Items: {len(items)}")

# String methods
_label: QLabel = new(bind="{', '.join(items)}")
```

## Error Handling

Accessing an unresolved required binding raises `AttributeError`.

```python
@widget
class Child(Widget):
    count: Variable[int]  # Required but not provided

@widget
class Parent(Widget):
    child: Child = new()  # Missing count binding

parent = Parent()
parent.child.count  # Raises: AttributeError: 'count' requires a binding
```
