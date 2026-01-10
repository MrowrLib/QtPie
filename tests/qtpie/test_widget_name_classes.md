# Widget Name and Classes

## Widget Decorator Name and Classes

Set `objectName` and CSS classes on the widget itself using `@widget` decorator parameters.

```python
@widget(name="styled-card", classes=["card", "elevated"])
class MyWidget(Widget):
    pass

w = MyWidget()
assert w.objectName() == "styled-card"
assert get_classes(w) == ["card", "elevated"]
```

## Field Name and Classes

Set `objectName` and CSS classes on QWidget fields using `new()` parameters.

```python
@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello", name="greeting", classes=["text", "large"])

w = MyWidget()
assert w._label.objectName() == "greeting"
assert get_classes(w._label) == ["text", "large"]
```

## Variable Widget Name and Classes

Set `objectName` and CSS classes on the widget portion of `Variable[T, W]` fields using chained `new()` call.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str, QLineEdit] = new("initial")(name="name-field", classes=["input", "large"])

w = MyWidget()
assert w._name.widget.objectName() == "name-field"
assert get_classes(w._name.widget) == ["input", "large"]
```

## List Widget Name and Classes

Set `objectName` and CSS classes on each item in a list repeater. Works for both `list[QWidget]` and `Variable[list[T], W]`.

```python
@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new(["a", "b", "c"])
    _labels: list[QLabel] = new(bind="_items", name="list-item", classes=["item", "clickable"])

w = MyWidget()
for label in w._labels:
    assert label.objectName() == "list-item"
    assert get_classes(label) == ["item", "clickable"]
```

```python
@widget
class MyWidget(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b"])(name="list-label", classes=["list-item"])

w = MyWidget()
for widget_item in w._items.widget:
    assert widget_item.objectName() == "list-label"
    assert get_classes(widget_item) == ["list-item"]
```

## Dict Widget Name and Classes

Set `objectName` and CSS classes on each item in a dict repeater with `Variable[dict[K, V], W]`.

```python
@widget
class MyWidget(Widget):
    _items: Variable[dict[str, int], QLabel] = new({"a": 1, "b": 2})(name="dict-label", classes=["dict-item"])

w = MyWidget()
for widget_item in w._items.widget:
    assert widget_item.objectName() == "dict-label"
    assert get_classes(widget_item) == ["dict-item"]
```

## Non-QWidget Name and Classes

For non-QWidget classes, `name=` and `classes=` are passed to the constructor as kwargs.

```python
class ConfiguredClass:
    def __init__(self, value: int, name: str = "", classes: list[str] | None = None):
        self.value = value
        self.name = name
        self.classes = classes or []

@widget
class MyWidget(Widget):
    _config: ConfiguredClass = new(42, name="my-config", classes=["config"])

w = MyWidget()
assert w._config.value == 42
assert w._config.name == "my-config"
assert w._config.classes == ["config"]
```

## Dynamic List Items

Items added dynamically to list repeaters also receive `name=` and `classes=` specified in the field definition.

```python
@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new([])
    _labels: list[QLabel] = new(bind="_items", name="dynamic-item", classes=["dynamic", "styled"])

w = MyWidget()
w._items.append("new1")

assert w._labels[0].objectName() == "dynamic-item"
assert get_classes(w._labels[0]) == ["dynamic", "styled"]
```

## Default Object Names

Without explicit `name=`, `objectName` defaults to the class name or field name.

```python
@widget
class MyDefaultWidget(Widget):
    _button: QPushButton = new("Click")
    _name: Variable[str, QLineEdit] = new("initial")

w = MyDefaultWidget()
assert w.objectName() == "MyDefaultWidget"  # Class name
assert w._button.objectName() == "_button"  # Field name
assert w._name.widget.objectName() == "_name"  # Field name
```

```python
@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new(["a", "b"])
    _labels: list[QLabel] = new(bind="_items")

w = MyWidget()
for label in w._labels:
    assert label.objectName() == "_labels"  # Field name for each item
```
