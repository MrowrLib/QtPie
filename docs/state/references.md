# Widget References

`ref()` creates deferred references to other widget fields. Unlike `bind=`, references resolve **once** at widget initialization.

## When to Use ref()

Use `ref()` when you need to:
- Reference a field declared later (forward reference)
- Reference a sibling field's widget/value
- Access parent widget attributes
- Set initial values from computed expressions

## Basic References

### Forward Reference

Reference a field declared after the current one:

```python
from qtpie import Widget, new, ref, widget

@widget
class Form(Widget):
    _label: QLabel = new(buddy=ref("_input"))  # Forward ref
    _input: QLineEdit = new()
```

### Backward Reference

Reference a field declared earlier:

```python
@widget
class Toolbar(Widget):
    _menu: QMenu = new()
    _button1: QPushButton = new(menu=ref("_menu"))
    _button2: QPushButton = new(menu=ref("_menu"))  # Same menu
```

## Variable Resolution

When referencing a `Variable`, `ref()` automatically extracts the value:

```python
@widget
class Display(Widget):
    _title: Variable[str] = new("Welcome")
    _label: QLabel = new(text=ref("_title"))  # Gets "Welcome"
```

## Parent References

Access parent widget attributes using `#parent`:

```python
@widget
class ChildWidget(Widget):
    _btn: QPushButton = new(menu=ref("#parent._shared_menu"))

@widget
class ParentWidget(Widget):
    _shared_menu: QMenu = new()
    _child1: ChildWidget = new()
    _child2: ChildWidget = new()  # Both share the same menu
```

## Nested Attributes

Traverse object hierarchies with dot notation:

```python
@dataclass
class Theme:
    name: str = "dark"

@dataclass
class Config:
    theme: Theme = field(default_factory=Theme)

@widget
class App(Widget):
    _config: Variable[Config] = new(default=Config())
    _label: QLabel = new(text=ref("_config.theme.name"))  # "dark"
```

### Optional Chaining

Use `?.` to safely access nullable attributes:

```python
@dataclass
class Config:
    theme: Theme | None = None

@widget
class App(Widget):
    _config: Variable[Config] = new(default=Config())
    _label: QLabel = new(text=ref("_config.theme?.name"))  # None-safe
```

## Expression Syntax

Evaluate Python expressions using `{...}`:

```python
@widget
class Calculator(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)

    _result: QLabel = new(text=ref("{_x} + {_y} = {_x + _y}"))
    # Shows: "10 + 20 = 30"
```

### Method Calls

```python
@widget
class StringWidget(Widget):
    _name: Variable[str] = new("alice")
    _upper: QLabel = new(text=ref("{_name.upper()}"))  # "ALICE"
```

### Function Calls

```python
@widget
class ListWidget(Widget):
    _items: Variable[list[str]] = new(["a", "b", "c"])
    _count: QLabel = new(text=ref("Count: {len(_items)}"))  # "Count: 3"
```

### Format Specs

```python
@widget
class PriceWidget(Widget):
    _price: Variable[float] = new(19.9)
    _label: QLabel = new(text=ref("${_price:.2f}"))  # "$19.90"
```

## ref() vs bind=

**Key difference**: `ref()` resolves once at init; `bind=` updates reactively.

```python
@widget
class Comparison(Widget):
    _count: Variable[int] = new(0)

    # ref() - resolved once, does NOT update
    _static: QLabel = new(text=ref("Initial: {_count}"))

    # bind= - reactive, DOES update
    _reactive: QLabel = new(bind="Current: {_count}")

    _button: QPushButton = new("+1", clicked="increment")

    def increment(self) -> None:
        self._count += 1
        # _static still shows "Initial: 0"
        # _reactive shows "Current: 1", then "Current: 2", etc.
```

### When to Use Each

| Use Case | Solution |
|----------|----------|
| Widget needs to update when data changes | `bind=` |
| Initial value from another field | `ref()` |
| Passing widget references (menu, buddy) | `ref()` |
| Computed display that tracks changes | `bind=` |
| One-time initialization | `ref()` |

## Special Placeholders

### #self

Access the widget instance:

```python
@widget
class SelfRef(Widget):
    name: str = "MyWidget"
    _label: QLabel = new(text=ref("Widget: {type(#self).__name__}"))
```

### Underscore Fallback

Expressions try both `name` and `_name`:

```python
@widget
class Fallback(Widget):
    _name: Variable[str] = new("Value")
    _label: QLabel = new(text=ref("{name}"))  # Finds _name
```

## Common Patterns

### Shared Menu

```python
@widget
class MultiButton(Widget):
    _menu: QMenu = new()

    _file_btn: QPushButton = new("File", menu=ref("_menu"))
    _edit_btn: QPushButton = new("Edit", menu=ref("_menu"))
    _view_btn: QPushButton = new("View", menu=ref("_menu"))
```

### Label Buddies

```python
@widget
class FormField(Widget):
    _label: QLabel = new("Name:", buddy=ref("_input"))
    _input: QLineEdit = new()
```

### Computed Initial Values

```python
@widget
class Summary(Widget):
    _first: Variable[str] = new("John")
    _last: Variable[str] = new("Doe")

    # Initial value computed from other fields
    _full: QLabel = new(text=ref("{_first} {_last}"))
    # Note: Won't update when _first or _last changes!
    # Use bind= for reactive updates
```

## See Also

- [Bindings](bindings.md) - Reactive content bindings
- [Format Expressions](format-expressions.md) - Expression syntax
- [Widget Bindings](widget-bindings.md) - Parent-child state passing
