# Dirty Tracking

## Basic Dirty State

Widgets track whether their Variables have changed from initial values. `is_dirty` returns an `Observable[bool]`, and `dirty_fields` returns a set of changed field names.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

w = MyWidget()
w._name.value = "changed"
w._count.value = 42

assert w.is_dirty.get() == True
assert w.dirty_fields == {"_name", "_count"}
```

## Reset Dirty

`reset_dirty()` marks all fields as clean, treating current values as the new baseline.

```python
w._name.value = "changed"
w._count.value = 42
w.reset_dirty()

assert w.is_dirty.get() == False
assert w.dirty_fields == set()

w._name.value = "second"
assert w.is_dirty.get() == True  # dirty again after reset
```

## Reactive Bindings

`is_dirty` is an Observable, so it can be used in property bindings and subscriptions.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _save_btn: QPushButton = new("Save", enabled="is_dirty")

w = MyWidget()
assert w._save_btn.isEnabled() == False

w._name.value = "changed"
assert w._save_btn.isEnabled() == True

w.reset_dirty()
assert w._save_btn.isEnabled() == False
```

## on_dirty_changed Hook

Optional lifecycle hook that fires only on state transitions (clean ↔ dirty).

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        dirty_states.append(is_dirty)

w = MyWidget()
w._name.value = "first"   # clean -> dirty (fires: True)
w._name.value = "second"  # dirty -> dirty (no fire)
w._count.value = 42       # dirty -> dirty (no fire)

assert dirty_states == [True]
```

## Record Dirty Tracking

Widgets with records (`Widget[T]`) track both Variable changes and record field changes. `dirty_fields` prefixes record fields with `record.`.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    _extra: Variable[str] = new("")

w = PersonEditor()
w._extra.value = "extra"
w.record.name = "Alice"
w.record.age = 30

assert w.is_dirty.get() == True
assert w.dirty_fields == {"_extra", "record.name", "record.age"}

w.reset_dirty()
assert w.is_dirty.get() == False
assert w.dirty_fields == set()
```
