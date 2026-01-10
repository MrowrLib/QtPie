# Signal-to-Signal Connections

## Signal Forwarding

QtPie supports connecting widget signals directly to custom signals by using the signal name as the handler string. When a widget emits a signal, it's automatically forwarded to the named Signal attribute.

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

Signal arguments are automatically forwarded from the source signal to the target signal.

```python
@widget
class MyWidget(Widget):
    value_changed = Signal(int)
    _slider: QSlider = new(valueChanged="value_changed")

w = MyWidget()
w.value_changed.connect(on_value)
w._slider.setValue(42)  # Emits value_changed(42)
```

## Argument Count Mismatch

Target signals with fewer parameters ignore extra arguments from the source signal.

```python
@widget
class MyWidget(Widget):
    # clicked emits bool, but our signal takes no args
    simple_clicked = Signal()
    _button: QPushButton = new("Click", clicked="simple_clicked")
```

## Parent-Child Signal Flow

Child widget signals can connect to parent methods or signals, enabling component communication.

```python
@widget
class Counter(Widget):
    increment_requested = Signal()
    _button: QPushButton = new("+", clicked="increment_requested")

@widget
class App(Widget):
    counter: Counter = new(increment_requested="_on_increment")

    def _on_increment(self) -> None:
        # Triggered when counter._button is clicked
        pass
```

## Signal Chaining

Child signals can connect to parent signals, creating a signal chain that bubbles up the component hierarchy.

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
app.counter._button.click()  # Flows through signal chain
```
