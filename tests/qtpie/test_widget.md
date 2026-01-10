# Widget Test Summary

## Layout Types

Widget supports vertical (default), horizontal, or no layout.

```python
@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click")
# Default: QVBoxLayout

@widget(layout="horizontal")
class MyWidget(Widget):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click")
# QHBoxLayout

@widget(layout=None)
class MyWidget(Widget):
    _label: QLabel = new("Hello")
# No layout
```

## Layout Margins

Integer applies to all sides, tuple applies to (left, top, right, bottom).

```python
@widget(margins=10)
class MyWidget(Widget):
    _label: QLabel = new("Hello")
# All sides: 10

@widget(margins=(1, 2, 3, 4))
class MyWidget(Widget):
    _label: QLabel = new("Hello")
# left=1, top=2, right=3, bottom=4
```

## Excluding Widgets from Layout

Use `layout=False` on `new()` to keep widgets out of the layout.

```python
@widget
class MyWidget(Widget):
    _visible: QLabel = new("Visible")
    _hidden: QLabel = new("Hidden", layout=False)
    _also_visible: QLabel = new("Also Visible")
# Only 2 widgets in layout, but _hidden still exists

@widget
class MyWidget(Widget):
    _visible: QLabel = new("Visible")
    _name: Variable[str, QLineEdit] = new("test")(layout=False)
    _also_visible: QLabel = new("Also Visible")
# Variable's widget excluded from layout
```

## Variable Fields

Variable fields are not added to layout (not QWidgets themselves).

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new("Hello")

w = MyWidget()
w._count = 42  # Direct assignment works
assert w._count.value == 42
# Layout only contains _label
```

## Setup Hook

`__setup__()` is called after layout is ready.

```python
@widget
class MyWidget(Widget):
    _label: QLabel = new("Hello")

    def __setup__(self) -> None:
        # Layout is ready here
        assert self.layout() is not None
        assert self._label.text() == "Hello"
```

## Non-QWidget Field Instantiation

Non-QWidget types are instantiated with args/kwargs. QtPie-specific kwargs like `layout=` and `bind=` are passed through to non-QWidget constructors.

```python
class Config:
    def __init__(self, name: str = "default") -> None:
        self.name = name

@widget
class MyWidget(Widget):
    _config: Config = new(name="custom")
    _label: QLabel = new("Hello")

w = MyWidget()
assert w._config.name == "custom"
```

## Decorator Required

Widget subclasses must use `@widget` decorator.

```python
class MyWidget(Widget):
    _label: QLabel = new("Hello")

# Raises TypeError: "must be decorated with @widget"
MyWidget()
```

## Signal Connections

Connect signals to lambdas or method names.

```python
@widget
class MyWidget(Widget):
    _btn: QPushButton = new("Click", clicked=lambda: print("clicked"))

@widget
class MyWidget(Widget):
    _btn: QPushButton = new("Click", clicked="on_clicked")
    was_clicked: bool = False

    def on_clicked(self) -> None:
        self.was_clicked = True

@widget
class MyWidget(Widget):
    _btn: QPushButton = new(
        "Click",
        pressed=lambda: inc_pressed(),
        released=lambda: inc_released(),
    )
```

## Widget Properties

Decorator kwargs become `setXXX()` calls on the widget.

```python
@widget(windowTitle="My Window")
class MyWidget(Widget):
    _label: QLabel = new("Hello")

@widget(title="My Window")  # alias for windowTitle
class MyWidget(Widget):
    _label: QLabel = new("Hello")

@widget(minimumWidth=400, minimumHeight=300)
class MyWidget(Widget):
    _label: QLabel = new("Hello")

@widget(windowTitle="Test", toolTip="A tooltip")
class MyWidget(Widget):
    _label: QLabel = new("Hello")
```

## Child Widget Properties

`new()` kwargs become `setXXX()` calls on child widgets.

```python
@widget
class MyWidget(Widget):
    label: QLabel = new("Hello", toolTip="This is a label")

@widget
class MyWidget(Widget):
    label: QLabel = new("Hello", styleSheet="color: red;")

@widget
class MyWidget(Widget):
    label: QLabel = new("Disabled", enabled=False)

@widget
class MyWidget(Widget):
    label: QLabel = new("Hidden", visible=False)

@widget
class MyWidget(Widget):
    label: QLabel = new("Hello", title="My Label")  # alias for windowTitle
```

## Property Aliases

Convenience aliases: `title` for `windowTitle`, `stylesheet` for `styleSheet`.

```python
@widget(stylesheet="background: yellow;")
class MyWidget(Widget):
    label: QLabel = new("Hello")

@widget
class MyWidget(Widget):
    label: QLabel = new("Hello", stylesheet="color: green;")
```

## ref() with Required Bindings

`ref()` works with literal text and expressions in nested widget composition.

```python
@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogDisplay(Widget):
    dog: Variable[Dog]
    name_label: QLabel = new(text=ref("Dog name: {dog.name}"))

@widget(record=Dog("Rover", 5))
class ParentWidget(Widget[Dog]):
    dog_display: DogDisplay = new(dog="record")

parent = ParentWidget()
assert parent.dog_display.name_label.text() == "Dog name: Rover"
```
