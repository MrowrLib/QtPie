# CSS Classes and Object Names in QtPie

This document describes how to use `name=` and `classes=` parameters for styling widgets in QtPie.

## Decorator-Level Styling

The `@widget` and `@window` decorators accept `name=` and `classes=` parameters to set the container's objectName and CSS classes.

### Setting Object Name on Container

```python
@widget(name="my-widget")
class MyWidget(Widget):
    pass
```

### Setting CSS Classes on Container

```python
@widget(classes=["card", "primary"])
class StyledCard(Widget):
    pass
```

### Both Name and Classes

```python
@widget(name="styled-card", classes=["card", "elevated"])
class ElevatedCard(Widget):
    pass
```

### Default Object Name

Without an explicit `name=`, the objectName defaults to the class name:

```python
@widget
class MyCustomClassName(Widget):
    pass
# objectName will be "MyCustomClassName"
```

## Field-Level Styling

Use `new(name=..., classes=[...])` to style individual child widgets.

### Object Name on Field

```python
button: QPushButton = new("Click", name="action-button")
```

### CSS Classes on Field

```python
button: QPushButton = new("Click", classes=["btn", "btn-primary"])
```

### Default Field Object Name

Without `name=`, field objectName defaults to the field name:

```python
my_button: QPushButton = new("Click")
# objectName will be "my_button"
```

## Variable[T, W] Styling

For Variable fields with inline widgets, use the second call for widget properties:

```python
_name: Variable[str, QLineEdit] = new("initial")(name="name-input")
_email: Variable[str, QLineEdit] = new("")(classes=["input", "bordered"])
_field: Variable[str, QLineEdit] = new("x")(name="my-field", classes=["input"])
```

Access widget objectName via `.widget`:

```python
instance._name.widget.objectName()  # "name-input"
```

## Leading Underscore Stripping

Field names with leading underscores have the underscore stripped from objectName:

```python
_button: QPushButton = new("Click")  # objectName = "button"
_label: QLabel = new("Text")         # objectName = "label"
button: QPushButton = new("OK")      # objectName = "button"
```

This also applies to Variable[T, W]:

```python
_name: Variable[str, QLineEdit] = new("initial")
# widget objectName = "name"
```

## Name Inheritance from Decorator

When `@decorator(name=...)` is set, children without explicit `name=` inherit it:

```python
@widget(name="form-container")
class Form(Widget):
    _button: QPushButton = new("Click")    # objectName = "form-container"
    _label: QLabel = new("Text")           # objectName = "form-container"
    explicit: QLabel = new("X", name="x")  # objectName = "x" (overrides)
```

Explicit `name=` on a field always overrides the decorator-level name.

## Reactive CSS Classes

Classes can include format string bindings that update reactively when Variables change.

### Variable Binding in Classes

```python
@widget
class Badge(Widget):
    _method: Variable[str] = new("GET")
    _label: QLabel = new("Request", classes=["badge", "method-{_method}"])
    # Classes: ["badge", "method-GET"]
    # When _method changes to "POST", becomes ["badge", "method-POST"]
```

### Record Field Binding in Classes

```python
@widget(record=Item("Test", "active"))
class ItemRow(Widget[Item]):
    _label: QLabel = new(bind="{name}", classes=["item", "status-{status}"])
    # Classes update when record.status changes
```

### Multiple Dynamic Classes

```python
_label: QLabel = new("Styled", classes=["btn", "size-{_size}", "color-{_color}"])
```

## Reactive Object Name

Object names can also use format string bindings:

```python
@widget
class DynamicItem(Widget):
    _id: Variable[int] = new(1)
    _label: QLabel = new("Item", name="item-{_id}")
    # objectName = "item-1", updates when _id changes
```

With record fields:

```python
@widget(record=Row(5, "Hello"))
class RowWidget(Widget[Row]):
    _label: QLabel = new(bind="{text}", name="row-{id}")
    # objectName = "row-5", updates when record.id changes
```

## Reading CSS Classes

Use `get_classes()` from `qtpie.styles` to retrieve classes from a widget:

```python
from qtpie.styles import get_classes

classes = get_classes(instance.button)  # Returns list[str]
```
