# Event Signals in QtPie

`Event` annotations on QtPie classes automatically create real Qt Signals. This enables type-safe, declarative custom events.

## Bare Event (No Arguments)

A bare `Event` annotation creates a signal with no payload.

```python
class MyWidget(Widget):
    on_save: Event

# Usage
instance.on_save.connect(lambda: print("saved"))
instance.on_save.emit()
```

## Typed Event (Single Argument)

`Event[T]` creates a signal that emits a value of type `T`.

```python
class MyWidget(Widget):
    on_value: Event[int]
    on_name: Event[str]

# Usage
instance.on_value.connect(lambda x: print(x))
instance.on_value.emit(42)
```

## Multi-Argument Event (Tuple)

`Event[tuple[T1, T2, ...]]` creates a signal with multiple arguments.

```python
class MyWidget(Widget):
    on_update: Event[tuple[int, str]]

# Usage
instance.on_update.connect(lambda x, y: print(x, y))
instance.on_update.emit(42, "hello")
```

## Connecting Handlers via `new(on=...)`

The `on=` parameter connects a handler at declaration time.

### Method Name String

```python
class MyWidget(Widget):
    on_test: Event = new(on="_on_test")

    def _on_test(self) -> None:
        print("triggered")
```

### Lambda

```python
class MyWidget(Widget):
    on_test: Event = new(on=lambda: print("triggered"))
    on_value: Event[int] = new(on=lambda x: print(x))
```

### Expression String

```python
class MyWidget(Widget):
    on_test: Event = new(on="{_log()}")

    def _log(self) -> None:
        print("logged")
```

## Connecting Handlers via Decorator

Wire signals to methods in the decorator kwargs.

```python
@widget(on_save="_on_save")
class MyWidget(Widget):
    on_save: Event

    def _on_save(self) -> None:
        print("saved")
```

## Assignment Expressions in Handlers

Expression handlers support assignments to Variables.

### Direct Assignment

```python
class MyWidget(Widget):
    count: Variable[int] = new(0)
    on_reset: Event = new(on="{count = 0}")
```

### Increment/Compound Assignment

```python
class MyWidget(Widget):
    count: Variable[int] = new(0)
    on_increment: Event = new(on="{count += 1}")
```

### Computed Assignment

```python
class MyWidget(Widget):
    a: Variable[int] = new(10)
    b: Variable[int] = new(20)
    result: Variable[int] = new(0)
    on_compute: Event = new(on="{result = a + b}")
```

## Programmatic Emit via `emit_event()`

Emit signals by name using the `emit_event()` method.

```python
class MyWidget(Widget):
    on_action: Event
    on_data: Event[tuple[int, str]]

    def trigger(self) -> None:
        self.emit_event("on_action")
        self.emit_event("on_data", 42, "hello")
```

## Coexistence with Variables

Events and Variables work together naturally.

```python
class Counter(Widget):
    _count: Variable[int] = new(0)
    on_count_changed: Event[int]

    def increment(self) -> None:
        self._count.value += 1
        self.on_count_changed.emit(self._count.value)
```

## Explicit Signal Override

If you assign a Signal explicitly, it is preserved (not overwritten).

```python
from qtpy.QtCore import Signal

class MyWidget(Widget):
    on_explicit: Event = Signal(str)  # Explicit Signal preserved
```
