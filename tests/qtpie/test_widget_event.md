# Widget Event Feature Documentation

The `Event` annotation in QtPie provides a declarative way to create Qt Signals on widgets without boilerplate `Signal()` definitions.

## Basic Event Declaration

Declare a parameterless event by simply annotating with `Event`:

```python
@widget
class MyWidget(Widget):
    on_click: Event  # Creates Signal()
```

The event can be connected to and emitted like any Qt Signal:
```python
w.on_click.connect(lambda: print("clicked"))
w.on_click.emit()
```

## Typed Events (Single Parameter)

Use `Event[T]` to create a Signal that carries a value:

```python
@widget
class MyWidget(Widget):
    on_value_changed: Event[int]  # Creates Signal(int)
```

Emit with a value:
```python
w.on_value_changed.emit(42)
```

## Multi-Parameter Events

Use `Event[tuple[...]]` for signals with multiple parameters:

```python
@widget
class MyWidget(Widget):
    on_update: Event[tuple[int, str]]  # Creates Signal(int, str)
```

Connect with matching lambda signature:
```python
w.on_update.connect(lambda x, y: print(f"{x}: {y}"))
w.on_update.emit(42, "hello")
```

## Wiring Events to Handlers via Decorator

Use decorator kwargs to auto-connect events to handler methods:

```python
@widget(on_save="_on_save")
class MyWidget(Widget):
    on_save: Event

    def _on_save(self) -> None:
        print("saved")
```

When `on_save.emit()` is called, `_on_save()` is invoked automatically.

## Multiple Events

A widget can have any number of Event annotations:

```python
@widget
class MyWidget(Widget):
    on_first: Event
    on_second: Event[int]
    on_third: Event[str]
```

## Convention Summary

| Pattern | Description |
|---------|-------------|
| `on_*: Event` | Parameterless signal |
| `on_*: Event[T]` | Signal with single typed parameter |
| `on_*: Event[tuple[A, B, ...]]` | Signal with multiple parameters |
| `@widget(on_*="_handler")` | Auto-wire event to instance method |
