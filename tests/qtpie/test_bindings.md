# bind() - Variable to Widget Property Bindings

## One-Way Binding (Variable → Widget)

Connect a `Variable` to a widget property. When the Variable changes, the widget updates automatically.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Initial")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._label)

w = MyWidget()
w._name.value = "Updated"
# w._label.text() is now "Updated"
```

Explicit property name:

```python
bind(self._name).to(self._label, "text")
```

## Two-Way Binding (Variable ↔ Widget)

For input widgets, changes flow both directions automatically. Widget edits update the Variable.

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _spinbox: QSpinBox = new()

    def __setup__(self) -> None:
        bind(self._count).to(self._spinbox)

w = MyWidget()
w._count.value = 42  # Variable → widget
w._spinbox.setValue(100)  # Widget → Variable (w._count.value is now 100)
```

Disable two-way binding:

```python
bind(self._name).to(self._input, two_way=False)
# Variable → widget works, widget → Variable does not
```

## Default Properties

`bind()` automatically selects the appropriate property for common widgets:

- `QLabel` → `text`
- `QLineEdit` → `text`
- `QSpinBox` → `value`
