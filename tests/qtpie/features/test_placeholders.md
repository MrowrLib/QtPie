# QtPie Placeholders Feature Documentation

This document describes the special placeholder syntax used in QtPie's binding system. Placeholders provide access to contextual values within `bind=`, `visible=`, `enabled=`, and signal handler expressions.

---

## Overview

Placeholders are prefixed with `#` and provide access to different contexts:

| Placeholder | Description |
|-------------|-------------|
| `{#widget}` | The current widget instance (self) |
| `{#window}` | The parent window (alias for #widget on Window) |
| `{#app}` | The QApplication instance |
| `{#var}` | Variable's value in Variable[T, W] context |
| `{#self}` | Alias for #var or current item value |
| `{#index}` | Item index in list repeaters |
| `{#key}` | Dict key in dict repeaters |
| `{#value}` | Dict value in dict repeaters |
| `{#args}` | Signal arguments passed to handler |
| `{#record}` | Record instance in Widget[T] context |

---

## #widget Placeholder

Access the current widget instance and its properties/methods.

### Accessing Widget Properties

```python
@widget
class Example(Widget):
    my_prop: str = "hello-world"
    _label: QLabel = new(bind="{#widget.my_prop}")
```

### Calling Widget Methods

```python
@widget
class Example(Widget):
    _label: QLabel = new(bind="{#widget.get_greeting()}")

    def get_greeting(self) -> str:
        return "Hello from widget!"
```

### Widget Method in Signal Handler

```python
@widget
class Example(Widget):
    _button: QPushButton = new("Click", clicked="{#widget.on_click()}")

    def on_click(self) -> None:
        print("Clicked!")
```

### Widget Variable in Signal Statement

```python
@widget
class Example(Widget):
    _count: Variable[int] = new(0)
    _button: QPushButton = new("Click", clicked="{#widget._count += 1}")
```

### Visibility Binding

```python
@widget
class Example(Widget):
    show_label: bool = True
    _label: QLabel = new("Visible!", visible="{#widget.show_label}")
```

---

## #window Placeholder

Alias for `#widget` when used in Window classes. Provides semantic clarity.

```python
@window(title="My Window Title")
class MainWindow(Window):
    _label: QLabel = new(bind="{#window.windowTitle()}")
```

---

## #app Placeholder

Access the QApplication instance.

```python
@widget
class Example(Widget):
    _label: QLabel = new(bind="{#app.applicationName()}")
```

### Check App Existence

```python
@widget
class Example(Widget):
    _label: QLabel = new("App exists!", visible="{#app is not None}")
```

---

## #var Placeholder

In `Variable[T, W]` context, access the Variable's value directly.

### Display Variable Value

```python
@widget
class Example(Widget):
    _count: Variable[int, QLabel] = new(42)(bind="Count: {#var}")
```

### Math Operations

```python
@widget
class Example(Widget):
    _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")
```

### Method Calls on Value

```python
@widget
class Example(Widget):
    _name: Variable[str, QLabel] = new("hello")(bind="Upper: {#var.upper()}")
```

### Reactive Updates

```python
@widget
class Example(Widget):
    _count: Variable[int, QLabel] = new(0)(bind="Value: {#var}")

    def update(self) -> None:
        self._count.value = 100  # Label auto-updates to "Value: 100"
```

---

## #index Placeholder

In list repeaters, access the current item's index (0-based).

```python
@widget
class Example(Widget):
    _items: Variable[list[str]] = new(default=["a", "b", "c"])
    _labels: list[QLabel] = new(bind="_items", format="{#index}: {#self}")
    # Produces: "0: a", "1: b", "2: c"
```

### With Object Items

```python
@widget
class Example(Widget):
    _people: Variable[list[Person]] = new(default=[Person("Alice", 30)])
    _labels: list[QLabel] = new(bind="_people", format="{#index}. {name}")
    # Produces: "0. Alice"
```

---

## #key and #value Placeholders

In dict repeaters, access the current key-value pair.

### Simple Dict Binding

```python
@widget
class Example(Widget):
    _scores: Variable[dict[str, int]] = new(default={"Alice": 100, "Bob": 85})
    _labels: list[QLabel] = new(bind="_scores", format="{#key} = {#value}")
    # Produces: "Alice = 100", "Bob = 85"
```

### Object Values with Field Access

```python
@widget
class Example(Widget):
    _people: Variable[dict[str, Person]] = new(default={"p1": Person("Alice", 30)})
    _labels: list[QLabel] = new(bind="_people", format="{#key}: {name}, age {age}")
    # Produces: "p1: Alice, age 30"
```

---

## #args Placeholder

In signal handlers, access signal arguments.

### Text Changed Signal

```python
@widget
class Example(Widget):
    _input: QLineEdit = new(textChanged="{on_text_changed(#args)}")

    def on_text_changed(self, text: str) -> None:
        print(f"Text: {text}")
```

### No-Argument Signals

```python
@widget
class Example(Widget):
    _button: QPushButton = new("Click", clicked="{on_click(#args)}")

    def on_click(self) -> None:
        print("Clicked!")
```

---

## Signal Expressions vs Statements

Signal handlers support both expressions (method calls) and statements (assignments).

### Expression: Method Call

```python
_button: QPushButton = new("Click", clicked="{on_click()}")
```

### Statement: Simple Assignment

```python
_count: Variable[int] = new(0)
_button: QPushButton = new("Click", clicked="{_count = 42}")
```

### Statement: Augmented Assignment

```python
_count: Variable[int] = new(10)
_button: QPushButton = new("Add", clicked="{_count += 5}")
_button2: QPushButton = new("Sub", clicked="{_count -= 3}")
_button3: QPushButton = new("Mul", clicked="{_count *= 2}")
```

---

## #record Placeholder

In `Widget[T]` or `Window[T]` context, access the record instance.

### Display Record Field

```python
@widget(record=Person("Alice", 30))
class PersonView(Widget[Person]):
    _label: QLabel = new(bind="Name: {#record.name}")
```

### Multiple Fields

```python
@widget(record=Person("Bob", 35))
class PersonView(Widget[Person]):
    _label: QLabel = new(bind="{#record.name}, age {#record.age}")
```

### Method Calls on Record Fields

```python
@widget(record=Person("alice", 25))
class PersonView(Widget[Person]):
    _label: QLabel = new(bind="Upper: {#record.name.upper()}")
```

### Visibility Based on Record Field

```python
@widget(record=Person("Test", 20, is_active=True))
class PersonView(Widget[Person]):
    _label: QLabel = new("Active!", visible="{#record.is_active}")
```

### Comparison Expressions

```python
@widget(record=Person("Adult", 25))
class PersonView(Widget[Person]):
    _label: QLabel = new("Adult!", visible="{#record.age >= 18}")
```

### Check Record Existence

```python
@widget(record=Person())
class PersonView(Widget[Person]):
    _label: QLabel = new("Has record!", visible="{#record is not None}")
```

### Signal Handler with Record Method

```python
@widget(record=SaveableRecord())
class RecordView(Widget[SaveableRecord]):
    _button: QPushButton = new("Save", clicked="{#record.save()}")
```

---

## Record Reactivity

Record bindings are reactive - UI updates when record fields change.

### Format Binding Reactivity

```python
@widget(record=Person("Alice", 30))
class PersonView(Widget[Person]):
    _label: QLabel = new(bind="Name: {#record.name}")

    def update_name(self) -> None:
        self.record.name = "Bob"  # Label auto-updates to "Name: Bob"
```

### Visibility Reactivity

```python
@widget(record=Person("Test", 20, is_active=True))
class PersonView(Widget[Person]):
    _label: QLabel = new("Active!", visible="{#record.is_active}")

    def deactivate(self) -> None:
        self.record.is_active = False  # Label becomes hidden
```

---

## Binding Contexts Summary

| Binding Type | Syntax | Description |
|--------------|--------|-------------|
| Format binding | `bind="{#widget.prop}"` | Text display with placeholders |
| Expression binding | `visible="{#record.is_active}"` | Boolean expression for visibility/enabled |
| Signal expression | `clicked="{on_click()}"` | Method call on signal |
| Signal statement | `clicked="{_count += 1}"` | Assignment on signal |
