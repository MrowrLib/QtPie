# Signal Event Prototyping - QtPie Usage Patterns

This file documents the experimental `Event[T]` annotation pattern for creating Qt Signals declaratively in QtPie.

## Overview

The prototype explores replacing Qt's `Signal(int)` class attribute syntax with a type annotation approach: `Event[int]`. Signals are created automatically via `__init_subclass__`.

---

## Basic Qt Signal Pattern

Standard Qt signals must be defined as class attributes before instantiation.

```python
class MyWidget(QWidget):
    my_signal = Signal(int)

w.my_signal.connect(lambda x: received.append(x))
w.my_signal.emit(42)
```

---

## Event Annotation (Proposed QtPie Pattern)

Use `Event[T]` type annotation instead of explicit `Signal()`. The signal is created automatically.

```python
class MyWidget(EventBase):
    on_something: Event[int]

w.on_something.connect(lambda x: print(x))
w.on_something.emit(42)
```

---

## Event Without Arguments

Bare `Event` (no type parameter) creates a signal with no arguments.

```python
class MyWidget(EventBase):
    on_click: Event  # No args

w.on_click.connect(lambda: print("clicked"))
w.on_click.emit()
```

---

## Signal Creation via __init_subclass__

The pattern relies on processing annotations in `__init_subclass__` to create real `Signal` objects.

```python
class EventBase(QWidget):
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        _process_event_annotations(cls)
```

---

## Event Type Marker

`Event[T]` is a generic marker class used purely for type hints. The actual signal creation happens at subclass definition time.

```python
class Event[T = None]:
    """Marker type for event annotations."""
    pass
```

---

## Key Takeaways

| Pattern | Syntax | Signal Args |
|---------|--------|-------------|
| No args | `Event` | `Signal()` |
| Single arg | `Event[int]` | `Signal(int)` |
| Multiple args | `Event[tuple[int, str]]` | `Signal(int, str)` |

The `Event` annotation provides:
- Declarative signal definition
- Type safety via generics
- Automatic signal creation (no manual `Signal()` calls)
