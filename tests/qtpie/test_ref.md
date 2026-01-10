# ref() - Deferred Attribute References

## Basic References

References sibling widget fields using `ref("field_name")`. Works forward and backward.

```python
@widget
class MyWidget(Widget):
    _first: QLabel = new(buddy=ref("_second"))  # Forward ref
    _second: QLineEdit = new()
```

```python
@widget
class MyWidget(Widget):
    _menu: QMenu = new()
    _button: QPushButton = new(menu=ref("_menu"))  # Backward ref
```

## Variable Resolution

When referencing a `Variable`, resolves to its `.value` automatically.

```python
@widget
class MyWidget(Widget):
    _text: Variable[str] = new("Hello World")
    _label: QLabel = new(text=ref("_text"))  # Gets "Hello World"
```

## Parent References

Access parent widget attributes using `#parent.` prefix.

```python
@widget
class Child(Widget):
    _button: QPushButton = new(menu=ref("#parent._shared_menu"))

@widget
class Parent(Widget):
    _shared_menu: QMenu = new()
    _child: Child = new()
```

## Nested Attributes

Traverse object hierarchies with dot notation.

```python
class Config:
    def __init__(self, title: str) -> None:
        self.title = title

@widget
class MyWidget(Widget):
    _config: Variable[Config] = new(Config("Default Title"))

w = qt.track(MyWidget())
r = ref("_config.title")
resolved = r.resolve(w)  # "Default Title"
```

## Optional Chaining

Use `?.` to safely access potentially None attributes.

```python
class Theme:
    def __init__(self) -> None:
        self.name = "dark"

class Config:
    def __init__(self) -> None:
        self.theme: Theme | None = Theme()

@widget
class MyWidget(Widget):
    _config: Variable[Config] = new(Config())

r = ref("_config.theme?.name")  # Returns "dark" or None if theme is None
```

```python
# Multiple levels
r = ref("level1?.level2?.level3?.value")
```

## Expression Syntax

Evaluate Python expressions using `{...}` syntax.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Alice")
    _label: QLabel = new(text=ref("Hello: {_name}"))
```

```python
@widget
class MyWidget(Widget):
    _x: Variable[int] = new(21)
    _result: QLabel = new(text=ref("Double: {_x * 2}"))  # "Double: 42"
```

## Expression Features

Method calls, functions, multiple variables, and format specs.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("alice")
    _upper: QLabel = new(text=ref("{_name.upper()}"))  # "ALICE"

    _items: Variable[list[str]] = new(["a", "b", "c"])
    _count: QLabel = new(text=ref("Count: {len(_items)}"))  # "Count: 3"

    _a: Variable[int] = new(10)
    _b: Variable[int] = new(20)
    _sum: QLabel = new(text=ref("{_a} + {_b} = {_a + _b}"))  # "10 + 20 = 30"

    _price: Variable[float] = new(19.9)
    _formatted: QLabel = new(text=ref("${_price:.2f}"))  # "$19.90"
```

## Special Placeholders in Expressions

`#self` refers to the instance.

```python
@widget
class MyWidget(Widget):
    name: str = "TestWidget"

r = ref("Type: {type(#self).__name__}")  # "Type: MyWidget"
```

## Underscore Fallback

Expressions try both `name` and `_name` when resolving attributes.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Fallback")

r = ref("Name: {name}")  # Resolves to _name -> "Name: Fallback"
```
