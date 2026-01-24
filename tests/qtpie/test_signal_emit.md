# Signal Emit Patterns in QtPie

This document describes signal connection and emission patterns in QtPie based on test usage.

## Signal Handler Basics

QtPie supports three types of signal handlers in the `new()` function:

### Method Name Handler

Connect a Qt signal to a widget method by name string:

```python
_button: QPushButton = new("Click", clicked="on_click")

def on_click(self) -> None:
    print("Clicked!")
```

### Lambda/Callable Handler

Connect a signal directly to a callable:

```python
_button: QPushButton = new("Click", clicked=lambda: print("Clicked"))
```

### Signal Name Handler (Signal-to-Signal)

Connect a Qt signal to a custom Signal by name, re-emitting the event:

```python
button_pressed = Signal()
_button: QPushButton = new("Click", clicked="button_pressed")
```

When clicked, the button's `clicked` signal automatically emits `button_pressed`.

## Custom Signals with Arguments

Signals with arguments forward their values when connected:

```python
value_changed = Signal(int)
_slider: QSlider = new(valueChanged="value_changed")
```

When the slider value changes, the `value_changed` signal receives the new value.

### Multiple Arguments

Multiple signal arguments are forwarded correctly:

```python
range_changed = Signal(int, int)
_slider: QSlider = new(rangeChanged="range_changed")
```

### Argument Count Mismatch

Target signals with fewer arguments than the source ignore extra arguments:

```python
simple_clicked = Signal()  # No args
_button: QPushButton = new("Click", clicked="simple_clicked")  # clicked emits bool
```

## Parent-Child Signal Flow

Child widgets can expose signals that parents connect to handlers.

### Child Emits Signal, Parent Handles

```python
@widget
class Counter(Widget):
    increment_requested = Signal()
    _button: QPushButton = new("+", clicked="increment_requested")

@widget
class App(Widget):
    counter: Counter = new(increment_requested="_on_increment")

    def _on_increment(self) -> None:
        # Handle child's signal
        pass
```

### Signal Chaining (Child Signal to Parent Signal)

Child signals can connect to parent signals, creating a chain:

```python
@widget
class Counter(Widget):
    increment_requested = Signal()
    _button: QPushButton = new("+", clicked="increment_requested")

@widget
class App(Widget):
    app_incremented = Signal()
    counter: Counter = new(increment_requested="app_incremented")
```

Clicking the button emits `increment_requested`, which emits `app_incremented`.

## Expression-Based Signal Handlers

Signal handlers can use expression syntax with curly braces for more control.

### Method Call Expression

```python
_button: QPushButton = new("Click", clicked="{on_click()}")
```

### Signal Emit with Literal Value

Emit a signal with a hardcoded value:

```python
custom_signal = Signal(int)
_button: QPushButton = new("Click", clicked="{custom_signal(123)}")
```

### Signal Emit with Variable Reference

Reference Variable values (without underscore prefix) in expressions:

```python
custom_signal = Signal(int, int)
_some_number: Variable[int] = new(42)
simple_number: int = 99
_button: QPushButton = new("Click", clicked="{custom_signal(some_number, simple_number)}")
```

### Using `#args` Placeholder

Forward the original signal arguments using `#args`:

```python
_slider: QSlider = new(valueChanged="{on_value(#args)}")

def on_value(self, val: int) -> None:
    print(f"Value: {val}")
```

## Works with Widget, Window, and App

All signal patterns work consistently across:

- `Widget` - Standard widget class
- `Window` - QMainWindow-based class
- `App` (with `QObject, AppBase`) - Application class with signal support

```python
@window(title="Test")
class MyWindow(Window):
    custom_signal = Signal(int)
    _button: QPushButton = new("Click", clicked="{custom_signal(123)}")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(QObject, AppBase):
    custom_signal = Signal(int)
    _button: QPushButton = new("Click", clicked="{custom_signal(123)}")
```
