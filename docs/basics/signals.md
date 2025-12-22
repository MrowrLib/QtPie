# Signals

Connect Qt signals to methods using QtPie's declarative syntax in `make()`.

## Basic Signal Connection

Connect a signal to a method by name using a string:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QWidget, QPushButton

@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click Me", clicked="on_click")
    click_count: int = 0

    def on_click(self) -> None:
        self.click_count += 1
        print(f"Clicked {self.click_count} times!")
```

The `clicked="on_click"` syntax connects the button's `clicked` signal to the `on_click()` method.

## Lambda and Callable Connections

You can also connect signals to lambda functions or any callable:

```python
@widget
class MyWidget(QWidget):
    button: QPushButton = make(
        QPushButton,
        "Click",
        clicked=lambda: print("Button clicked!")
    )
```

This is useful for simple, inline handlers that don't need a full method.

## Multiple Signals on One Widget

Connect multiple signals from the same widget by passing additional keyword arguments:

```python
from qtpy.QtWidgets import QSlider

@widget
class MyWidget(QWidget):
    slider: QSlider = make(
        QSlider,
        valueChanged="on_value_changed",
        sliderReleased="on_released",
    )
    value_changes: int = 0
    releases: int = 0

    def on_value_changed(self, value: int) -> None:
        self.value_changes += 1
        print(f"Value: {value}")

    def on_released(self) -> None:
        self.releases += 1
        print("Slider released")
```

Each signal is connected independently, and both handlers will be called.

## Signals with Arguments

QtPie automatically handles signal arguments. Your method signature must match the signal:

```python
from qtpy.QtWidgets import QLineEdit, QSpinBox

@widget
class MyWidget(QWidget):
    edit: QLineEdit = make(QLineEdit, textChanged="on_text_changed")
    spin: QSpinBox = make(QSpinBox, valueChanged="on_value_changed")

    def on_text_changed(self, text: str) -> None:
        print(f"Text is now: {text}")

    def on_value_changed(self, value: int) -> None:
        print(f"Value is now: {value}")
```

**Common signals with arguments:**

- `textChanged(str)` - QLineEdit, QTextEdit
- `valueChanged(int)` - QSpinBox, QSlider
- `valueChanged(double)` - QDoubleSpinBox
- `currentIndexChanged(int)` - QComboBox
- `stateChanged(int)` - QCheckBox
- `toggled(bool)` - QCheckBox, QRadioButton

## Common Signal Patterns

### Button Clicks

```python
button: QPushButton = make(QPushButton, "Save", clicked="save")
```

The `clicked` signal is parameterless, so your handler needs no arguments:

```python
def save(self) -> None:
    print("Saving...")
```

### Text Input Changes

```python
name_edit: QLineEdit = make(QLineEdit, textChanged="on_name_changed")
```

The `textChanged` signal passes the new text:

```python
def on_name_changed(self, text: str) -> None:
    print(f"Name: {text}")
```

### Value Changes (Sliders, SpinBoxes)

```python
age_spin: QSpinBox = make(QSpinBox, valueChanged="on_age_changed")
```

The `valueChanged` signal passes the new value:

```python
def on_age_changed(self, value: int) -> None:
    print(f"Age: {value}")
```

### Checkbox Toggles

```python
from qtpy.QtWidgets import QCheckBox

@widget
class MyWidget(QWidget):
    check: QCheckBox = make(QCheckBox, "Enable", toggled="on_toggled")

    def on_toggled(self, checked: bool) -> None:
        print(f"Enabled: {checked}")
```

## Async Slots with @slot

For async signal handlers, use the `@slot` decorator:

```python
import asyncio
from qtpie import widget, make, slot
from qtpy.QtWidgets import QWidget, QPushButton, QLabel

@widget
class AsyncWidget(QWidget):
    button: QPushButton = make(QPushButton, "Fetch", clicked="fetch_data")
    label: QLabel = make(QLabel, "Ready")

    @slot
    async def fetch_data(self) -> None:
        self.label.setText("Loading...")
        await asyncio.sleep(2)  # Simulate async operation
        self.label.setText("Done!")
```

The `@slot` decorator wraps async functions with `qasync.asyncSlot`, allowing them to work correctly with Qt's signal system. Without it, the coroutine would be created but never awaited.

For sync functions, `@slot` is optional - but you can use it for consistency or when you need Qt's `@Slot` type declarations:

```python
@slot(str)
def on_text_changed(self, text: str) -> None:
    print(f"Text: {text}")
```

See [@slot Reference](../reference/decorators/slot.md) for full documentation.

## How It Works

QtPie's `make()` function separates signal connections from widget properties:

1. **String or callable kwargs** are treated as potential signal connections
2. **Other kwargs** are passed as constructor arguments or set as properties
3. During widget initialization, QtPie verifies each string/callable kwarg is actually a signal
4. If it's a signal, it connects it; if not, it sets it as a property

This means you can mix signals and properties freely:

```python
edit: QLineEdit = make(
    QLineEdit,
    placeholderText="Enter name",  # Property (string, but not a signal)
    textChanged="on_text_changed",  # Signal (string, verified as signal)
    maxLength=50                     # Property (not string/callable)
)
```

## Real Example: Counter

A complete working example showing signal connections:

```python
from qtpie import entry_point, widget, make
from qtpy.QtWidgets import QWidget, QLabel, QPushButton

@entry_point
@widget
class Counter(QWidget):
    count: int = 0
    label: QLabel = make(QLabel, "Count: 0")
    increment_btn: QPushButton = make(QPushButton, "+1", clicked="increment")
    reset_btn: QPushButton = make(QPushButton, "Reset", clicked="reset")

    def increment(self) -> None:
        self.count += 1
        self.label.setText(f"Count: {self.count}")

    def reset(self) -> None:
        self.count = 0
        self.label.setText(f"Count: {self.count}")
```

Two buttons, each connected to a different handler method.

## See Also

- [Widgets](widgets.md) - Basic widget creation with `@widget` and `make()`
- [Reactive State](../data/state.md) - For reactive updates without manual signal handling
- [Format Expressions](../data/format.md) - Bind widget text to state automatically
- [make() Reference](../reference/factories/make.md) - Full API documentation
