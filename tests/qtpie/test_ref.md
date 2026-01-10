# ref() - Deferred Attribute References

## Basic Reference Resolution

`ref()` creates deferred references to widget fields that are resolved after widget initialization. Works with fields defined before or after the reference.

```python
@widget
class MyWidget(Widget):
    _menu: QMenu = new()
    _button: QPushButton = new(menu=ref("_menu"))

w = qt.track(MyWidget())
assert_that(w._button.menu()).is_equal_to(w._menu)
```

```python
@widget
class MyWidget(Widget):
    _first: QLabel = new(buddy=ref("_second"))
    _second: QLineEdit = new()

w = qt.track(MyWidget())
assert_that(w._first.buddy()).is_equal_to(w._second)
```

## Variable Resolution

When `ref()` targets a `Variable`, it automatically resolves to the Variable's `.value`, not the Variable instance itself.

```python
@widget
class MyWidget(Widget):
    _text: Variable[str] = new("Hello World")
    _label: QLabel = new(text=ref("_text"))

w = qt.track(MyWidget())
assert_that(w._label.text()).is_equal_to("Hello World")
```

## Parent References

`#parent` prefix accesses attributes from parent widgets in nested composition.

```python
@widget
class Child(Widget):
    _button: QPushButton = new(menu=ref("#parent._shared_menu"))

@widget
class Parent(Widget):
    _shared_menu: QMenu = new()
    _child: Child = new()

w = qt.track(Parent())
assert_that(w._child._button.menu()).is_equal_to(w._shared_menu)
```

## Nested Attribute Access

`ref()` supports dot notation for traversing nested attributes. Variables in the chain are automatically unwrapped.

```python
class Config:
    def __init__(self, title: str) -> None:
        self.title = title

@widget
class MyWidget(Widget):
    _config: Variable[Config] = new(Config("Default Title"))

w = qt.track(MyWidget())
r = ref("_config.title")
resolved = r.resolve(w)
assert_that(resolved).is_equal_to("Default Title")
```

## Optional Chaining

`?.` syntax provides safe navigation through potentially None attributes.

```python
@widget
class MyWidget(Widget):
    _config: Variable[None] = new(None)

w = qt.track(MyWidget())
r = ref("_config?.nonexistent")
resolved = r.resolve(w)
assert_that(resolved).is_none()
```

```python
class Theme:
    def __init__(self) -> None:
        self.name = "dark"

class Config:
    def __init__(self) -> None:
        self.theme = Theme()

@widget
class MyWidget(Widget):
    _config: Variable[Config] = new(Config())

w = qt.track(MyWidget())
r = ref("_config?.theme?.name")
resolved = r.resolve(w)
assert_that(resolved).is_equal_to("dark")
```

## Expression Refs

Format string expressions with `{}` syntax support complex Python expressions, function calls, methods, math, and format specs.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("alice")

w = qt.track(MyWidget())
r = ref("{_name.upper()}")
result = r.resolve(w)
assert_that(result).is_equal_to("ALICE")
```

```python
@widget
class MyWidget(Widget):
    _a: Variable[int] = new(10)
    _b: Variable[int] = new(20)

w = qt.track(MyWidget())
r = ref("{_a} + {_b} = {_a + _b}")
result = r.resolve(w)
assert_that(result).is_equal_to("10 + 20 = 30")
```

```python
@widget
class MyWidget(Widget):
    _price: Variable[float] = new(19.9)

w = qt.track(MyWidget())
r = ref("${_price:.2f}")
result = r.resolve(w)
assert_that(result).is_equal_to("$19.90")
```

## Expression Placeholders

Special placeholders in expressions: `{#self}` for instance reference, `{#var}` for Variable value, `{#widget}` for parent widget.

```python
@widget
class MyWidget(Widget):
    name: str = "TestWidget"

w = qt.track(MyWidget())
r = ref("Type: {type(#self).__name__}")
result = r.resolve(w)
assert_that(result).is_equal_to("Type: MyWidget")
```
