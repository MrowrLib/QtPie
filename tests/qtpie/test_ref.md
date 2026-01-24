# QtPie `ref()` Feature Documentation

The `ref()` function provides deferred attribute references in QtPie widgets. It allows you to reference sibling fields, parent widget fields, or use expression-based string interpolation with reactive values.

## Importing

```python
from qtpie import Ref, ref
```

## Basic Ref Creation

Create a reference to a sibling field by name:

```python
r = ref("_field")
```

## Sibling Widget References

Reference other fields within the same widget using `ref()` in `new()` kwargs:

```python
@widget
class MyWidget(Widget):
    _menu: QMenu = new()
    _button: QPushButton = new(menu=ref("_menu"))
```

Works for any Qt property that has a setter:

```python
@widget
class MyWidget(Widget):
    _input: QLineEdit = new()
    _label: QLabel = new("Name:", buddy=ref("_input"))
```

Order doesn't matter - refs can reference fields defined before or after:

```python
@widget
class MyWidget(Widget):
    _first: QLabel = new(buddy=ref("_second"))  # Forward reference
    _second: QLineEdit = new()
```

## Variable References

When referencing a `Variable`, `ref()` automatically resolves to the `.value`:

```python
@widget
class MyWidget(Widget):
    _text: Variable[str] = new("Hello World")
    _label: QLabel = new(text=ref("_text"))  # Gets "Hello World"
```

## Parent Widget References

Access fields from a parent widget using `#parent.` prefix:

```python
@widget
class Child(Widget):
    _button: QPushButton = new(menu=ref("#parent._shared_menu"))

@widget
class Parent(Widget):
    _shared_menu: QMenu = new()
    _child: Child = new()
```

Parent refs also unwrap Variables:

```python
@widget
class Child(Widget):
    _label: QLabel = new(text=ref("#parent._message"))

@widget
class Parent(Widget):
    _message: Variable[str] = new("Hello from parent")
    _child: Child = new()
```

## Nested Attribute Access

Access nested properties with dot notation:

```python
r = ref("settings.config.title")
resolved = r.resolve(widget_instance)
```

Variables in the chain are automatically unwrapped:

```python
@widget
class MyWidget(Widget):
    _config: Variable[Config] = new(Config("Default Title"))

# Access nested through Variable
r = ref("_config.title")  # Unwraps _config, then gets .title
```

## Optional Chaining

Use `?.` for optional attribute access that returns `None` if the attribute is `None`:

```python
r = ref("_config?.theme?.name")  # Returns None if any step is None
```

Mix required and optional access:

```python
r = ref("_config.theme?.name")  # _config required, theme optional
```

## Expression Refs

Use `{}` syntax for string interpolation with expressions:

```python
# Simple value interpolation
r = ref("{_name}")

# With literal text
r = ref("Hello: {_name}")

# Function calls
r = ref("Count: {len(_items)}")

# Method calls
r = ref("{_name.upper()}")

# Math expressions
r = ref("Double: {_x * 2}")

# Multiple variables
r = ref("{_a} + {_b} = {_a + _b}")

# Format specifiers
r = ref("${_price:.2f}")
```

Use expressions directly in `new()`:

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(42)
    _label: QLabel = new(text=ref("Count: {_count}"))
```

## Special Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{#self}` | The widget instance |

```python
r = ref("Type: {type(#self).__name__}")
```

## Ref Properties

```python
r = ref("_field")
r.name            # "_field"
r.is_parent_ref   # False
r.target_name     # "_field"

r = ref("#parent._field")
r.is_parent_ref   # True
r.target_name     # "_field" (without #parent. prefix)

r = ref("{_name}")
r.is_expression   # True
```

## Combining with Other Kwargs

Refs work alongside regular kwargs:

```python
@widget
class MyWidget(Widget):
    _input: QLineEdit = new()
    _label: QLabel = new("Name:", buddy=ref("_input"), toolTip="Enter name")
```

## Instance Independence

Each widget instance resolves refs independently:

```python
w1 = MyWidget()
w2 = MyWidget()
# w1._button.menu() == w1._menu (not w2._menu)
```
