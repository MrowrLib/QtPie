# Widget.build() and create_instance() - Runtime Widget Instantiation

The `build()` method and `create_instance()` function provide runtime widget creation with `new()`-like features. Use `build()` within widgets for dynamic widget creation with automatic signal connections and bindings.

## Core API

### create_instance() - Low-Level Factory

Creates widget instances with signal connections and property bindings.

```python
from qtpie.create import create_instance

label = create_instance(None, QLabel, "Hello World")
btn = create_instance(self, QPushButton, "Click", clicked="on_click")
```

### Widget.build() - Preferred Method

Widgets have a `build()` method that wraps `create_instance()` with `self` as context.

```python
@widget
class Parent(Widget):
    def __setup__(self) -> None:
        self.child = self.build(ChildWidget, on_action="on_action")
```

---

## Signal Connections

### Connect to Method by Name

```python
self.child = self.build(ChildWidget, on_action="on_action")
```

### Connect to Lambda

```python
child = create_instance(None, ChildWidget, on_action=lambda: print("called"))
```

### Connect to Callable Object

```python
handler = CallableHandler()
child = create_instance(None, ChildWidget, on_action=handler)
```

### Connect Signal to Signal

```python
self.child = create_instance(self, ChildWidget, on_action="forwarded")
# Where self.forwarded is a Signal
```

---

## Constructor Arguments

### Positional Args

```python
label = create_instance(None, QLabel, "Hello World")
```

### Keyword Args (Non-Signal/Prop)

```python
btn = create_instance(None, QPushButton, text="Click Me")
```

---

## Widget Properties

Properties like `enabled`, `visible`, `toolTip` are applied via `setXxx()` methods.

```python
btn = create_instance(None, QPushButton, "Click", enabled=False)
label = create_instance(None, QLabel, "Hidden", visible=False)
btn = create_instance(None, QPushButton, "Hover", toolTip="This is a tooltip")
```

### Object Name via `name=`

```python
label = create_instance(None, QLabel, "Test", name="my-label")
```

---

## CSS Classes

```python
label = create_instance(None, QLabel, "Test", classes=["highlight", "large"])
# Classes stored in "class" property for QSS selector matching
```

---

## Reactive Bindings

### bind= Format Strings

Create reactive bindings to parent Variables.

```python
@widget
class Parent(Widget):
    _count: Variable[int] = new(42)

    def __setup__(self) -> None:
        self.label = self.build(QLabel, bind="Count: {_count}")
```

### bind= with Expressions

```python
self.label = self.build(QLabel, bind="Sum: {_x + _y}")
```

---

## Property Bindings (visible=, enabled=)

### Simple Variable Reference

```python
self.label = self.build(QLabel, "Hello", visible="_show_label")
```

### Expression Binding

```python
self.btn = self.build(QPushButton, "Submit", enabled="{_count > 0}")
```

---

## Deferred References with ref()

Resolve attribute from context at build time.

```python
from qtpie import ref

@widget
class Parent(Widget):
    my_tooltip = "This is my tooltip"

    def __setup__(self) -> None:
        self.btn = self.build(QPushButton, "Click", toolTip=ref("my_tooltip"))
```

---

## Layout Integration

### Add to Named Layout

```python
@widget
class Parent(Widget):
    _row: QHBoxLayout = new()

    def __setup__(self) -> None:
        self.label = self.build(QLabel, "Dynamic", layout="_row")
```

### Add to Default Layout

```python
self.label = self.build(QLabel, "Dynamic", layout=True)
```

### Skip Layout

```python
self.hidden = self.build(QLabel, "Hidden", layout=False)
```

---

## Form Layout with Labels

```python
@widget
class Parent(Widget):
    _form: QFormLayout = new()

    def __setup__(self) -> None:
        self.name = self.build(QLineEdit, layout="_form", label="Name:")
        self.email = self.build(QLineEdit, layout="_form", label="Email:")
```

---

## Grid Layout with Positions

### Basic Grid Position

```python
self.cell = self.build(QLabel, "(0,0)", layout="_grid", grid=(0, 0))
```

### Grid with Span

```python
# grid=(row, col, rowspan, colspan)
self.header = self.build(QLabel, "Header", layout="_grid", grid=(0, 0, 1, 2))
```

---

## Dynamic Widget Creation

`build()` works in methods called after construction.

```python
@widget
class Parent(Widget):
    _row: QHBoxLayout = new()

    def add_item(self, text: str) -> QLabel:
        return self.build(QLabel, text, layout="_row")
```

---

## Combining Features

All build features can be used together.

```python
self.btn = self.build(
    QPushButton,
    "Click",
    layout="_row",
    enabled="_enabled",
    clicked="on_click",
    toolTip="A button",
)
```
