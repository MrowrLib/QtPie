# Widget[T] Record Feature Documentation

This document describes the `Widget[T]` record feature in QtPie, which provides reactive data binding for dataclass models.

## Widget[T] - Type Parameter for Record Type

Specify a dataclass type parameter to enable record support on a widget.

```python
@widget
class PersonEditor(Widget[Person]):
    pass
```

The type parameter extracts the record type automatically, enabling `self.record` access.

## Direct Field Access via self.record

Access and modify record fields directly through `self.record`. Assignment triggers reactivity.

```python
w.record.name = "Bob"
w.record.age = 42
print(w.record.name)  # "Bob"
```

## Record State Access via record_state

Access the underlying `RecordVariable` for state operations like dirty tracking.

```python
w._qtpie.record_state.is_dirty.get()  # False initially
w.record.name = "Changed"
w._qtpie.record_state.is_dirty.get()  # True after modification
```

## Setting Record in __setup__

For types without default values, or to initialize with specific values, set fields in `__setup__`.

```python
@widget
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        self.record.name = "Setup Name"
        self.record.age = 25
```

## @widget(record=...) Decorator Pattern

Preferred approach for types without defaults or for specifying initial values. Provides full pyright support.

```python
@widget(record=Dog("Fido", "Lab"))
class DogEditor(Widget[Dog]):
    pass
```

The record is accessible in `__setup__` and participates in dirty tracking.

## Explicit record: Variable[T] Declaration

Alternative pattern using explicit `Variable[T]` field with `new(default=...)`.

```python
@widget
class CatEditor(Widget[Cat]):
    record: Variable[Cat] = new(default=Cat("Whiskers", 9))
```

## Combining Record with Other Variables

Widgets can have both a record type and additional `Variable` fields.

```python
@widget
class PersonEditor(Widget[Person]):
    _status: Variable[str] = new("idle")
    _label: QLabel = new("Editor")
```

## Dirty Tracking Hook

Override `on_dirty_changed` to respond to record state transitions.

```python
@widget
class PersonEditor(Widget[Person]):
    def on_dirty_changed(self, is_dirty: bool) -> None:
        self.save_btn.setEnabled(is_dirty)
```

## Typical Dataclass Models

Record types are standard Python dataclasses.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@dataclass
class Cat:
    name: str  # No default - requires explicit record= or __setup__
    lives: int
```
