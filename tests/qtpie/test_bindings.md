# QtPie Bindings - Usage Patterns

This document describes the `bind()` function usage patterns in QtPie based on `test_bindings.py`.

## Overview

The `bind()` function creates reactive connections between `Variable` state and Qt widgets. It supports both one-way (Variable → widget) and two-way (Variable ↔ widget) bindings.

## Imports

```python
from qtpie import Variable, Widget, bind, new, widget
```

## One-Way Binding: Variable → Widget

Binds a Variable to a widget so changes to the Variable automatically update the widget.

### Basic Usage

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Hello")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._label)
```

### With Explicit Property

You can specify which widget property to bind to:

```python
bind(self._name).to(self._label, "text")
```

## Two-Way Binding: Variable ↔ Widget

For editable widgets (QLineEdit, QSpinBox, etc.), bindings are two-way by default. Changes from either direction sync automatically.

### QLineEdit Two-Way Binding

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _input: QLineEdit = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._input)
```

- Setting `w._name.value = "x"` updates the QLineEdit
- User typing in QLineEdit updates `w._name.value`

### QSpinBox Two-Way Binding

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _spinbox: QSpinBox = new()

    def __setup__(self) -> None:
        bind(self._count).to(self._spinbox)
```

### Disabling Two-Way Binding

Use `two_way=False` to make binding one-way only:

```python
bind(self._name).to(self._input, two_way=False)
```

## Default Property Inference

When no property is specified, QtPie infers the appropriate property based on widget type:

| Widget Type | Default Property |
|-------------|------------------|
| `QLabel` | `text` |
| `QLineEdit` | `text` |
| `QSpinBox` | `value` |

```python
bind(self._msg).to(self._label)  # Binds to "text" property
bind(self._count).to(self._spinbox)  # Binds to "value" property
```

## Syntax Summary

```python
# Basic one-way binding
bind(variable).to(widget)

# Explicit property
bind(variable).to(widget, "propertyName")

# One-way only (no widget → variable updates)
bind(variable).to(widget, two_way=False)

# Combined
bind(variable).to(widget, "propertyName", two_way=False)
```

## Key Conventions

1. **Bindings are set up in `__setup__`** - The lifecycle hook that runs after widget initialization
2. **Two-way is the default** for editable widgets - Use `two_way=False` to opt out
3. **Property names are auto-inferred** - QtPie knows common widget properties
4. **Reactive updates are automatic** - No manual synchronization needed
