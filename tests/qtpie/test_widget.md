# Widget Test Summary

## Auto-Layout

Widgets automatically create layouts for their child fields. Default is vertical layout (QVBoxLayout). Can specify horizontal layout or no layout.

```python
@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click")

w = qt.track(MyWidget())
assert_that(w.layout()).is_instance_of(QVBoxLayout)
```

```python
@widget(layout="horizontal")
class MyWidget(Widget):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click")

w = qt.track(MyWidget())
assert_that(w.layout()).is_instance_of(QHBoxLayout)
```

## Layout Margins

Control layout margins with `margins=` decorator kwarg. Accepts int (all sides) or tuple (left, top, right, bottom).

```python
@widget(margins=10)
class MyWidget(Widget):
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
margins = w.layout().contentsMargins()
assert_that(margins.left()).is_equal_to(10)
```

```python
@widget(margins=(1, 2, 3, 4))
class MyWidget(Widget):
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
margins = w.layout().contentsMargins()
assert_that(margins.left()).is_equal_to(1)
assert_that(margins.top()).is_equal_to(2)
```

## Layout Exclusion

Exclude specific widgets from the auto-layout with `layout=False` in `new()`. Widget still exists as an attribute but isn't added to the parent layout.

```python
@widget
class MyWidget(Widget):
    _visible: QLabel = new("Visible")
    _hidden: QLabel = new("Hidden", layout=False)
    _also_visible: QLabel = new("Also Visible")

w = qt.track(MyWidget())
layout = w.layout()
assert_that(layout.count()).is_equal_to(2)
assert_that(w._hidden).is_not_none()
```

```python
@widget
class MyWidget(Widget):
    _visible: QLabel = new("Visible")
    _name: Variable[str, QLineEdit] = new("test")(layout=False)
    _also_visible: QLabel = new("Also Visible")

w = qt.track(MyWidget())
layout = w.layout()
assert_that(layout.count()).is_equal_to(2)
assert_that(w._name.widget).is_not_none()
```

## Variable Fields

Variable fields work in widgets but are not added to the layout (they're not QWidgets themselves).

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
w._count = 42
assert_that(w._count.value).is_equal_to(42)
```

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
layout = w.layout()
assert_that(layout.count()).is_equal_to(1)
```

## Setup Hook

Widgets can define `__setup__()` which is called after the layout is ready and all fields are initialized.

```python
@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello")

    def __setup__(self) -> None:
        assert self.layout() is not None
        assert self._label.text() == "Hello"
```

## Non-QWidget Fields

Fields with non-QWidget types are instantiated with their `new()` args/kwargs. QtPie-specific kwargs (`layout=`, `bind=`) are passed through to non-QWidget constructors (only consumed for QWidgets).

```python
class Config:
    def __init__(self, name: str = "default") -> None:
        self.name = name

@widget
class MyWidget(Widget):
    _config: Config = new(name="custom")
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
assert_that(w._config.name).is_equal_to("custom")
```

```python
class Config:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs

@widget
class MyWidget(Widget):
    _config: Config = new(layout=123)
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
assert_that(w._config.kwargs).contains_key("layout")
```

## Decorator Required

Widgets must be decorated with `@widget`. Missing decorator raises TypeError.

```python
class MyWidget(Widget):
    _label: QLabel = new("Hello")

with pytest.raises(TypeError) as exc_info:
    MyWidget()

assert "must be decorated with @widget" in str(exc_info.value)
```

## Signal Connections

Declaratively connect signals to callables (lambdas, functions) or method names (strings).

```python
@widget
class MyWidget(Widget):
    _btn: QPushButton = new("Click", clicked=on_click)

w = qt.track(MyWidget())
w._btn.click()
```

```python
@widget
class MyWidget(Widget):
    _btn: QPushButton = new("Click", clicked="on_clicked")
    was_clicked: bool = False

    def on_clicked(self) -> None:
        self.was_clicked = True

w = qt.track(MyWidget())
w._btn.click()
assert_that(w.was_clicked).is_true()
```

## Widget Properties (Decorator)

Decorator kwargs become `setXXX()` calls on the widget. Supports aliases like `title` for `windowTitle` and `stylesheet` for `styleSheet`.

```python
@widget(windowTitle="My Window")
class MyWidget(Widget):
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
assert_that(w.windowTitle()).is_equal_to("My Window")
```

```python
@widget(minimumWidth=400, minimumHeight=300)
class MyWidget(Widget):
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())
assert_that(w.minimumWidth()).is_equal_to(400)
assert_that(w.minimumHeight()).is_equal_to(300)
```

## Widget Properties (new)

`new()` kwargs become `setXXX()` calls on child widgets. Supports same aliases as decorator.

```python
@widget
class MyWidget(Widget):
    label: QLabel = new("Hello", toolTip="This is a label")

w = qt.track(MyWidget())
assert_that(w.label.toolTip()).is_equal_to("This is a label")
```

```python
@widget
class MyWidget(Widget):
    label: QLabel = new("Hello", toolTip="Tip", styleSheet="color: blue;")

w = qt.track(MyWidget())
assert_that(w.label.toolTip()).is_equal_to("Tip")
assert_that(w.label.styleSheet()).is_equal_to("color: blue;")
```
