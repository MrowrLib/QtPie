# Signal-to-Signal Connections

## Signal Emit via String Handler

Widget signals can connect to custom signals by using the signal name as a string handler. When a Qt widget signal fires, it automatically emits the custom signal.

```python
@widget
class MyWidget(Widget):
    button_pressed = Signal()
    _button: QPushButton = new("Click", clicked="button_pressed")

w = MyWidget()
w.button_pressed.connect(on_signal)
w._button.click()  # Emits button_pressed
```

## Argument Forwarding

Signal arguments are automatically forwarded from source to target signal. If the target signal has fewer parameters, extra arguments are ignored.

```python
@widget
class MyWidget(Widget):
    value_changed = Signal(int)
    _slider: QSlider = new(valueChanged="value_changed")

    range_changed = Signal(int, int)
    _slider2: QSlider = new(rangeChanged="range_changed")

w = MyWidget()
w.value_changed.connect(on_value)
w._slider.setValue(42)  # Forwards 42 to value_changed
```

## Parent-Child Signal Flow

Child widget signals can connect to parent methods or signals using the same string handler syntax, enabling signal chains across widget hierarchies.

```python
@widget
class Counter(Widget):
    increment_requested = Signal()
    _button: QPushButton = new("+", clicked="increment_requested")

@widget
class App(Widget):
    app_incremented = Signal()
    counter: Counter = new(increment_requested="app_incremented")

app = App()
app.app_incremented.connect(on_app_signal)
app.counter._button.click()  # Chains through both signals
```
