# Widget Name and CSS Classes

QtPie provides declarative syntax for setting Qt `objectName` and CSS classes on widgets, enabling QSS (Qt Style Sheets) styling.

## Widget-Level Name and Classes

Use `@widget(name=..., classes=[...])` to set the widget's objectName and CSS classes.

```python
@widget(name="my-widget", classes=["card", "primary"])
class MyWidget(Widget):
    pass
```

**Default behavior**: Without explicit `name=`, the objectName defaults to the class name (e.g., `"MyWidget"`).

## Field-Level Name and Classes

Use `new(name=..., classes=[...])` on QWidget fields.

```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new("Click", name="action-button", classes=["btn", "btn-primary"])
```

**Default behavior**: Without explicit `name=`, the objectName defaults to the field name with leading underscore stripped (e.g., `_button` becomes `"button"`).

## Variable with Widget Type

For `Variable[T, W]` syntax, chain the widget kwargs after the initial value.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str, QLineEdit] = new("initial")(name="name-input", classes=["input", "bordered"])
```

Access the widget via `w._name.widget`.

## List Bindings

For `list[QWidget]` bound to a Variable, name/classes apply to each generated item.

```python
@widget
class MyWidget(Widget):
    _items: Variable[list[str]] = new(["a", "b", "c"])
    _labels: list[QLabel] = new(bind="_items", name="list-item", classes=["item", "clickable"])
```

Items added dynamically also receive the same name/classes.

## Variable List/Dict with Widget

For `Variable[list[T], W]` and `Variable[dict[K, V], W]` syntax.

```python
@widget
class MyWidget(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b"])(name="list-label", classes=["list-item"])
    _entries: Variable[dict[str, int], QLabel] = new({"a": 1})(name="dict-label", classes=["dict-item"])
```

## Non-QWidget Classes

For regular Python classes, `name=` and `classes=` are passed as constructor kwargs.

```python
class DataHolder:
    def __init__(self, name: str = "", classes: list[str] | None = None):
        self.name = name
        self.classes = classes or []

@widget
class MyWidget(Widget):
    _data: DataHolder = new(name="holder", classes=["data"])
```

## Reading CSS Classes

Use `get_classes(widget)` from `qtpie.styles` to retrieve classes.

```python
from qtpie.styles import get_classes

classes = get_classes(w._button)  # Returns list[str]
```

## QSS Selector Compatibility

Default objectNames work with QSS ID selectors.

```python
@widget(stylesheet="""
#MyWidget { background-color: red; }
#my_label { color: blue; }
""")
class MyWidget(Widget):
    _my_label: QLabel = new("Label")  # objectName = "my_label"
```
