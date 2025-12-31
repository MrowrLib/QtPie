# register_binding()

The `register_binding()` function allows you to register custom property bindings for Qt widgets. This extends QtPie's binding system to support custom widgets or non-default properties of built-in widgets.

## Why register_binding()?

QtPie includes default bindings for common Qt widgets (QLineEdit, QSpinBox, QCheckBox, etc.). But you may need to:

1. Add bindings for custom widgets you've created
2. Bind to a non-default property of a built-in widget
3. Override the default property for a widget type

`register_binding()` lets you teach QtPie how to bind any widget property.

## Basic Usage

### Registering a Custom Widget

```python
from qtpie import register_binding, widget, make, Widget
from qtpy.QtWidgets import QWidget

class CustomWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._custom_value = ""

    def custom_value(self) -> str:
        return self._custom_value

    def set_custom_value(self, v: str) -> None:
        self._custom_value = v

# Register the binding
register_binding(
    CustomWidget,
    "custom",
    getter=lambda w: w.custom_value(),
    setter=lambda w, v: w.set_custom_value(str(v)),
)

# Now you can bind to it
@widget
class MyWidget(QWidget, Widget):
    custom: CustomWidget = make(CustomWidget, bind="some_field", bind_prop="custom")
```

### Setting a Default Property

Use `default=True` to make a property the default for a widget type:

```python
register_binding(
    CustomWidget,
    "custom",
    getter=lambda w: w.custom_value(),
    setter=lambda w, v: w.set_custom_value(str(v)),
    default=True,  # Make this the default property
)

# Now you can omit bind_prop
@widget
class MyWidget(QWidget, Widget):
    custom: CustomWidget = make(CustomWidget, bind="some_field")  # Uses "custom" property
```

## Signal Support

For two-way binding (widget changes update the model), specify the signal that fires when the property changes:

```python
class CustomWidget(QWidget):
    # Assume this widget has a customValueChanged signal
    customValueChanged = Signal(str)

    def custom_value(self) -> str:
        return self._custom_value

    def set_custom_value(self, v: str) -> None:
        if self._custom_value != v:
            self._custom_value = v
            self.customValueChanged.emit(v)

register_binding(
    CustomWidget,
    "custom",
    getter=lambda w: w.custom_value(),
    setter=lambda w, v: w.set_custom_value(str(v)),
    signal="customValueChanged",  # Widget → Model updates
    default=True,
)
```

Now when the widget changes, the model automatically updates.

### One-Way Bindings (Read-Only)

For widgets that only display values (like QLabel or QProgressBar), omit the `signal` parameter:

```python
register_binding(
    QProgressBar,
    "value",
    getter=lambda w: w.value(),
    setter=lambda w, v: w.setValue(int(v)),
    signal=None,  # No signal = one-way binding (model → widget only)
    default=True,
)
```

## Real-World Example

Here's how QtPie registers the QSpinBox binding internally:

```python
from qtpy.QtWidgets import QSpinBox
from qtpie import register_binding

register_binding(
    QSpinBox,
    "value",
    getter=lambda w: w.value(),
    setter=lambda w, v: w.setValue(int(v)),
    signal="valueChanged",
    default=True,
)
```

This tells QtPie:
- QSpinBox has a bindable property called "value"
- Get the value with `w.value()`
- Set the value with `w.setValue(int(v))`
- Listen to the `valueChanged` signal for widget → model updates
- Make "value" the default property (so `bind="age"` works without `bind_prop="value"`)

## Advanced: Type Conversion

The getter and setter lambdas handle type conversion. Here's a checkbox example:

```python
register_binding(
    QCheckBox,
    "checked",
    getter=lambda w: w.isChecked(),  # Returns bool
    setter=lambda w, v: w.setChecked(bool(v) if v is not None else False),  # Converts to bool
    signal="checkStateChanged",
    default=True,
)
```

The setter converts the value to bool to handle cases where the model value might not be exactly the right type.

## Advanced: Complex Objects

You can bind to complex types like QDate, QFont, or custom objects:

```python
from qtpy.QtCore import QDate
from qtpy.QtWidgets import QDateEdit

register_binding(
    QDateEdit,
    "date",
    getter=lambda w: w.date(),  # Returns QDate
    setter=lambda w, v: w.setDate(v) if v is not None else None,  # Accepts QDate
    signal="dateChanged",
    default=True,
)
```

## Checking Registered Bindings

Use the binding registry to inspect what's registered:

```python
from qtpie.bindings import get_binding_registry
from qtpy.QtWidgets import QLineEdit, QSpinBox, QCheckBox

registry = get_binding_registry()

# Get default property for a widget
line_edit = QLineEdit()
default_prop = registry.get_default_prop(line_edit)
print(default_prop)  # "text"

spin = QSpinBox()
print(registry.get_default_prop(spin))  # "value"

check = QCheckBox()
print(registry.get_default_prop(check))  # "checked"

# Get adapter for a specific property
adapter = registry.get(line_edit, "text")
if adapter:
    print(adapter.signal_name)  # "textChanged"
```

## Built-in Bindings

QtPie comes with bindings pre-registered for these widgets:

| Widget | Property | Signal | Type |
|--------|----------|--------|------|
| QLineEdit | `text` | `textChanged` | str |
| QTextEdit | `text` | `textChanged` | str |
| QPlainTextEdit | `text` | `textChanged` | str |
| QLabel | `text` | None | str (read-only) |
| QSpinBox | `value` | `valueChanged` | int |
| QDoubleSpinBox | `value` | `valueChanged` | float |
| QCheckBox | `checked` | `checkStateChanged` | bool |
| QRadioButton | `checked` | `toggled` | bool |
| QSlider | `value` | `valueChanged` | int |
| QDial | `value` | `valueChanged` | int |
| QProgressBar | `value` | None | int (read-only) |
| QComboBox | `currentText` | `currentTextChanged` | str |
| QDateEdit | `date` | `dateChanged` | QDate |
| QTimeEdit | `time` | `timeChanged` | QTime |
| QDateTimeEdit | `dateTime` | `dateTimeChanged` | QDateTime |
| QFontComboBox | `currentFont` | `currentFontChanged` | QFont |
| QKeySequenceEdit | `keySequence` | `keySequenceChanged` | QKeySequence |
| QListWidget | `currentRow` | `currentRowChanged` | int |

You can override any of these by registering a different binding for the same widget type and property.

## API Reference

```python
def register_binding[TWidget: QObject, TValue](
    widget_type: type[TWidget],
    property_name: str,
    *,
    getter: Callable[[TWidget], TValue] | None = None,
    setter: Callable[[TWidget, TValue], None] | None = None,
    signal: str | None = None,
    default: bool = False,
) -> None
```

### Parameters

- **widget_type**: The Qt widget class (e.g., `QLineEdit`, `QSpinBox`, or your custom widget)
- **property_name**: The property name to bind (e.g., `"text"`, `"value"`, `"custom"`)
- **getter**: Function that gets the current value from the widget. If None, property is write-only
- **setter**: Function that sets a value on the widget. If None, property is read-only
- **signal**: Signal name that fires when the property changes (for two-way binding). If None, binding is one-way (model → widget)
- **default**: If True, this property becomes the default for this widget type (used when `bind_prop` is not specified)

### Type Parameters

- **TWidget**: The widget type, must be a QObject subclass
- **TValue**: The value type for the property

## See Also

- [bind()](bind.md) - Manual binding function
- [make()](../factories/make.md) - Factory function with `bind` and `bind_prop` parameters
- [Widget[T]](widget-base.md) - Base class for model-bound widgets
- [Data Binding Guide](../../data/record-widgets.md) - Complete guide to data binding
