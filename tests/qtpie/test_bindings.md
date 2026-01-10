# bind() - Variable to Widget Property Bindings

## One-Way Binding (Variable → Widget)

Connect a `Variable` to a widget property. When the Variable changes, the widget updates automatically.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Hello")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._name).to(self._label)
```

```python
w._name.value = "Updated"
assert_that(w._label.text()).is_equal_to("Updated")
```

Explicit property name can be specified:

```python
bind(self._name).to(self._label, "text")
```

## Two-Way Binding (Variable ↔ Widget)

Automatically detects when widgets support change signals (like QLineEdit, QSpinBox). Changes flow both directions.

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _spinbox: QSpinBox = new()

    def __setup__(self) -> None:
        self._spinbox.setMaximum(1000)
        bind(self._count).to(self._spinbox)

w = MyWidget()

# Variable → widget
w._count.value = 42
assert_that(w._spinbox.value()).is_equal_to(42)

# Widget → Variable
w._spinbox.setValue(100)
assert_that(w._count.value).is_equal_to(100)
```

Disable with `two_way=False`:

```python
bind(self._name).to(self._input, two_way=False)

# Variable → widget works
w._name.value = "From Variable"
assert_that(w._input.text()).is_equal_to("From Variable")

# Widget → Variable does NOT update
w._input.setText("From Widget")
assert_that(w._name.value).is_equal_to("From Variable")  # Unchanged
```

## Default Property Resolution

When no property name is specified, `bind()` uses sensible defaults:

- `QLabel` → `"text"`
- `QLineEdit` → `"text"`
- `QSpinBox` → `"value"`

```python
bind(self._msg).to(self._label)  # Uses "text" automatically
bind(self._count).to(self._spinbox)  # Uses "value" automatically
```
