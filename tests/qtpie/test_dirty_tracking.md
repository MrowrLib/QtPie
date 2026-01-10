# Dirty Tracking Tests

## Dirty Tracking

The `is_dirty` property tracks whether any `Variable` fields have changed from their initial values. `dirty_fields` returns which specific fields changed. `reset_dirty()` marks all fields as clean.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

w = qt.track(MyWidget())
w._name.value = "changed"
w._count.value = 42

assert_that(w.is_dirty.get()).is_true()
assert_that(w.dirty_fields).is_equal_to({"_name", "_count"})

w.reset_dirty()
assert_that(w.is_dirty.get()).is_false()
```

## Reactive is_dirty Observable

`is_dirty` is an `Observable[bool]` that can be subscribed to or used in reactive bindings. It updates automatically when dirty state changes.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _save_btn: QPushButton = new("Save", enabled="is_dirty")

w = qt.track(MyWidget())
assert_that(w._save_btn.isEnabled()).is_false()

w._name.value = "changed"
assert_that(w._save_btn.isEnabled()).is_true()

w.reset_dirty()
assert_that(w._save_btn.isEnabled()).is_false()
```

## on_dirty_changed Lifecycle Hook

Optional `on_dirty_changed(is_dirty: bool)` hook fires when dirty state transitions (clean→dirty or dirty→clean). Only fires on state changes, not every field modification.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        dirty_states.append(is_dirty)

w = qt.track(MyWidget())
w._name.value = "first"   # clean -> dirty (fires with True)
w._name.value = "second"  # dirty -> dirty (no fire)
w._count.value = 42       # dirty -> dirty (no fire)

assert_that(dirty_states).is_equal_to([True])
```

## Widget-Level Dirty Tracking

`Widget.is_dirty` aggregates dirty state from both `Variable` fields and record (if `Widget[T]`). `Widget.reset_dirty()` resets both.

```python
@dataclass
class Person:
    name: str = ""

@widget(record=Person())
class PersonEditor(Widget[Person]):
    _extra: Variable[str] = new("")

w = qt.track(PersonEditor())

# Dirty from Variable
w._extra.value = "extra"
assert_that(w.is_dirty.get()).is_true()

w.reset_dirty()
assert_that(w.is_dirty.get()).is_false()

# Dirty from record
w.record.name = "Bob"
assert_that(w.is_dirty.get()).is_true()

# Reset both
w.reset_dirty()
assert_that(w.is_dirty.get()).is_false()
assert_that(w.is_dirty.get()).is_false()
assert_that(w.record_state.is_dirty.get()).is_false()
```

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _save_btn: QPushButton = new("Save", enabled="is_dirty")

w = qt.track(PersonEditor())
assert_that(w._save_btn.isEnabled()).is_false()

w.record.name = "Alice"
assert_that(w._save_btn.isEnabled()).is_true()
```
