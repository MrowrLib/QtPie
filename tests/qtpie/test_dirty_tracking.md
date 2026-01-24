# Dirty Tracking in QtPie

This document covers the dirty tracking feature in QtPie, which tracks whether widget state has changed from its initial values.

## Basic Dirty State

Widgets with `Variable` fields automatically track dirty state. Access via `is_dirty` (Observable) and `dirty_fields` (set of field names).

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)
```

- `w.is_dirty.get()` - Returns `True` if any field changed
- `w.dirty_fields` - Returns set of changed field names, e.g. `{"_name"}`

## Modifying Variables

Assigning to a Variable's `.value` marks it dirty:

```python
w._name.value = "changed"
assert w.is_dirty.get() is True
assert w.dirty_fields == {"_name"}
```

## Resetting Dirty State

Call `reset_dirty()` to mark all fields as clean:

```python
w._name.value = "changed"
w.reset_dirty()
assert w.is_dirty.get() is False
```

## is_dirty as Observable

`is_dirty` is an `Observable[bool]` that can be subscribed to or used in bindings:

```python
# Subscribe to changes
w.is_dirty.on_change(lambda v: print(f"Dirty: {v}"))

# Use in enabled= binding
_save_btn: QPushButton = new("Save", enabled="is_dirty")
```

When bound to `enabled=`, the button enables when dirty and disables when clean.

## on_dirty_changed Lifecycle Hook

Override `on_dirty_changed()` to react to dirty state transitions:

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        print(f"Dirty state changed to: {is_dirty}")
```

Key behavior:
- Only fires on state *transitions* (clean→dirty, dirty→clean)
- Does NOT fire for every value change while already dirty
- Hook is optional - widget works fine without it

## Record Dirty Tracking

Widgets with `Widget[T]` (record type) also track record field changes:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    pass

w.record.name = "Alice"
assert w.is_dirty.get() is True
assert "record.name" in w.dirty_fields
```

## Combined Variable + Record Tracking

`is_dirty` and `dirty_fields` aggregate both Variable and record changes:

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _extra: Variable[str] = new("")

w._extra.value = "extra"
w.record.name = "Bob"
assert w.dirty_fields == {"_extra", "record.name"}

w.reset_dirty()  # Clears both
```

## Reactive Binding with Record

Record changes also trigger reactive bindings:

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _save_btn: QPushButton = new("Save", enabled="is_dirty")

w.record.name = "Alice"  # Button becomes enabled
```
