# ViewModel Feature Documentation

Auto-generated view model from Variable fields in QtPie widgets.

## Overview

The `view_model` is an auto-generated object that exposes all `Variable` fields from a widget. It provides a separate access point for reactive state, useful for binding and external access patterns.

## Accessing the ViewModel

Access via the internal `_qtpie` state object:

```python
w = MyWidget()
vm = w._qtpie.view_model
```

## Variable Fields in ViewModel

All `Variable[T]` fields are accessible through the view_model:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("hello")
    _count: Variable[int] = new(42)

w = MyWidget()
w._qtpie.view_model._name.value   # "hello"
w._qtpie.view_model._count.value  # 42
```

## Non-Variable Fields Excluded

Regular Qt widgets are NOT included in the view_model:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")   # In view_model
    _label: QLabel = new("Hello")    # NOT in view_model
```

## Same Variable Instances

The view_model Variables are the exact same instances as widget Variables:

```python
w._qtpie.view_model._name is w._name  # True
```

## Bidirectional Synchronization

Changes through either path are reflected in both:

```python
# Change via view_model
w._qtpie.view_model._name.value = "changed"
w._name.value  # "changed"

# Change via widget
w._name.value = "new"
w._qtpie.view_model._name.value  # "new"
```

## Using with bind()

The view_model can be used with QtPie's `bind()` function:

```python
from qtpie import bind

@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Hello")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._qtpie.view_model._name).to(self._label)
```

## Key Characteristics

- **Lazy singleton**: Same instance returned on repeated access
- **Variable-only**: Contains only `Variable[T]` fields
- **Same references**: Not copies - actual Variable instances
- **Reactive**: Bindings work identically through view_model
