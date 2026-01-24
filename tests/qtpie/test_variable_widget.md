# Variable[T, W] - Variable with Widget Type

This document describes the `Variable[T, W]` feature in QtPie, which combines reactive state with an auto-bound widget.

## Basic Declaration

Declare a `Variable[T, W]` to create both reactive state and an associated widget.

```python
_name: Variable[str, QLineEdit] = new("hello")
```

The widget is automatically created and bound to the variable. Changes flow both directions.

## Two-Way Binding

Changing the variable updates the widget, and vice versa.

```python
w._name.value = "world"        # Widget updates
w._name.widget.setText("new")  # Variable updates
```

## Widget Configuration via Chained Call

Use `new(value)(widget_kwargs)` to configure the widget.

```python
_name: Variable[str, QLineEdit] = new("default")(placeholderText="Enter name...")
_count: Variable[int, QSpinBox] = new(50)(minimum=0, maximum=100)
```

## Signal Connections on Variable Widgets

Connect signals using kwargs in the widget call.

```python
_input: Variable[str, QLineEdit] = new("")(returnPressed="on_submit")

def on_submit(self) -> None:
    print("Enter pressed!")
```

## Layout Ordering

Variable[T, W] widgets interleave correctly with regular widgets.

```python
_label1: QLabel = new("First")
_name: Variable[str, QLabel] = new("Second")
_label2: QLabel = new("Third")
# Layout order: label1, name.widget, label2
```

## Accessing the Widget

Use `.widget` to access the underlying Qt widget.

```python
w._name.widget.setFocus()
w._name.widget.placeholderText()
```

## Type Conversion in Bindings

Variables of various types auto-convert when bound to widgets.

```python
# int -> str for QLabel
_count: Variable[int] = new(42)
_label: QLabel = new("")
bind(self._count).to(self._label)  # Shows "42"

# Dataclass uses __str__
bind(self._person).to(self._label)  # Uses Person.__str__
```

## Dataclass Field Access via Proxy

For `Variable[DataclassType]`, access fields directly on the variable.

```python
_dog: Variable[Dog] = new(Dog("Fido", 3))

# Direct field access
w._dog.name  # Returns "Fido"
w._dog.age   # Returns 3

# Reactive field assignment
w._dog.name = "Max"  # Triggers reactive updates
```

## Replacing the Entire Object

Replace the whole value reactively.

```python
w._dog.value = Dog("Buddy", 5)  # All bindings update
```

## Variable Without Widget Type

`Variable[T]` (single type param) has no widget - `.widget` is `None`.

```python
_name: Variable[str] = new("hello")
w._name.widget  # None
```

## Using Widget[T] as the Widget Type

Nest a `Widget[T]` as the widget for complex editing scenarios.

```python
@widget(layout="form")
class DogEditor(Widget[Dog]):
    _name: QLineEdit = new(label="Name")
    _age: QSpinBox = new(label="Age")

@widget
class Parent(Widget):
    _dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))
```

Changes to `_dog.name` propagate to the editor widget, and vice versa.
