# Widget Name and CSS Classes

## Widget Decorator `name=` and `classes=`

Set `objectName` and CSS classes on the widget itself using decorator parameters.

```python
@widget(name="my-widget")
class MyWidget(Widget):
    pass

w = MyWidget()
assert w.objectName() == "my-widget"
```

```python
@widget(name="styled-card", classes=["card", "elevated"])
class MyWidget(Widget):
    pass

w = MyWidget()
assert w.objectName() == "styled-card"
assert get_classes(w) == ["card", "elevated"]
```

## QWidget Fields with `name=` and `classes=`

Set `objectName` and CSS classes on QWidget fields.

```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new("Click", name="action-button")

w = MyWidget()
assert w._button.objectName() == "action-button"
```

```python
@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello", name="greeting", classes=["text", "large"])

w = MyWidget()
assert w._label.objectName() == "greeting"
assert get_classes(w._label) == ["text", "large"]
```

## Variable[T, W] with `name=` and `classes=`

Set `objectName` and CSS classes on the widget created for a `Variable[T, W]`.

```python
from qtpie import Variable

@widget
class MyWidget(Widget):
    _name: Variable[str, QLineEdit] = new("initial")(name="name-input")

w = MyWidget()
assert w._name.widget.objectName() == "name-input"
```

```python
from qtpie import Variable

@widget
class MyWidget(Widget):
    _name: Variable[str, QLineEdit] = new("initial")(name="name-field", classes=["input", "large"])

w = MyWidget()
assert w._name.widget.objectName() == "name-field"
assert get_classes(w._name.widget) == ["input", "large"]
```

## List Repeater Items with `name=` and `classes=`

Set `objectName` and CSS classes on each item widget in a list repeater. Applies to all items, including dynamically added ones.

```python
from qtpie import Variable

@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new(["a", "b", "c"])
    _labels: list[QLabel] = new(bind="_items", name="list-item")

w = MyWidget()
for label in w._labels:
    assert label.objectName() == "list-item"
```

```python
from qtpie import Variable

@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new(["x", "y"])
    _labels: list[QLabel] = new(bind="_items", name="entry", classes=["row"])

w = MyWidget()
for label in w._labels:
    assert label.objectName() == "entry"
    assert get_classes(label) == ["row"]
```

## Variable[list[T], W] with `name=` and `classes=`

Set `objectName` and CSS classes on each item in a `Variable[list[T], W]` repeater.

```python
from qtpie import Variable

@widget
class MyWidget(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b"])(name="list-label")

w = MyWidget()
repeater = w._items.widget
for widget_item in repeater:
    assert widget_item.objectName() == "list-label"
```

## Variable[dict[K, V], W] with `name=` and `classes=`

Set `objectName` and CSS classes on each item in a `Variable[dict[K, V], W]` repeater.

```python
from qtpie import Variable

@widget
class MyWidget(Widget):
    _items: Variable[dict[str, int], QLabel] = new({"a": 1, "b": 2})(name="dict-label")

w = MyWidget()
repeater = w._items.widget
for widget_item in repeater:
    assert widget_item.objectName() == "dict-label"
```

## Non-QWidget Classes Receive `name=` and `classes=` as Constructor Args

For non-QWidget classes, `name=` and `classes=` are passed as constructor kwargs instead of being set via methods.

```python
class RegularClass:
    def __init__(self, name: str = "default"):
        self.name = name

@widget
class MyWidget(Widget):
    _obj: RegularClass = new(name="custom-name")

w = MyWidget()
assert w._obj.name == "custom-name"
```

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

## Automatic Default `objectName`

When `name=` is not specified, QtPie sets sensible defaults:
- Widget classes: class name
- QWidget fields: field name
- List/dict repeater items: field name

```python
@widget
class MyDefaultWidget(Widget):
    pass

w = MyDefaultWidget()
assert w.objectName() == "MyDefaultWidget"
```

```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new("Click")
    _label: QLabel = new("Hello")

w = MyWidget()
assert w._button.objectName() == "_button"
assert w._label.objectName() == "_label"
```

```python
from qtpie import Variable

@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new(["a", "b"])
    _labels: list[QLabel] = new(bind="_items")

w = MyWidget()
for label in w._labels:
    assert label.objectName() == "_labels"
```

## QSS Selector Support

Default `objectName` values work with QSS selectors.

```python
@widget(
    stylesheet="""
#TestQssWidget {
    background-color: red;
}
#_my_label {
    color: blue;
}
"""
)
class TestQssWidget(Widget):
    _my_label: QLabel = new("Label")

w = TestQssWidget()
assert w.objectName() == "TestQssWidget"
assert w._my_label.objectName() == "_my_label"
```
