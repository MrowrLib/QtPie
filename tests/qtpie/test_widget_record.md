# Widget[T] Record Support

## Record Type Declaration

`Widget[T]` extracts the type parameter as the record type, automatically creating a `RecordVariable[T]` accessible via `record_state`.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())
assert_that(w._qtpie_config.record_type).is_equal_to(Person)
assert_that(w._qtpie.record_state).is_instance_of(RecordVariable)
```

## Direct Field Access

The `record` property provides direct field access with reactive assignment. Read returns actual values, write triggers reactivity.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())
w.record.name = "Bob"
w.record.age = 42

assert_that(w.record.name).is_equal_to("Bob")
assert_that(w.record.age).is_equal_to(42)
```

## Record State Access

`record_state` returns the underlying `RecordVariable` for accessing state properties like `is_dirty`, `value`, and `observable`.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())
assert_that(w._qtpie.record_state.is_dirty.get()).is_false()

w.record.name = "Changed"
assert_that(w._qtpie.record_state.is_dirty.get()).is_true()
assert_that(w._qtpie.record_state.value.name).is_equal_to("Changed")
```

## Dirty Tracking

Record fields participate in dirty tracking automatically. Changes to record fields set the dirty flag.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())
assert_that(w._qtpie.record_state.is_dirty.get()).is_false()

w._qtpie.record_state.observable.name.set("Bob")
assert_that(w._qtpie.record_state.is_dirty.get()).is_true()
```

## Combination with Variables

Widgets can have both a record type and independent variables. They work side-by-side.

```python
@widget
class PersonEditor(Widget[Person]):
    _status: Variable[str] = new("idle")
    _label: QLabel = new("Editor")

w = qt.track(PersonEditor())
w._qtpie.record_state.observable.name.set("Charlie")
w._status.value = "editing"

assert_that(w._qtpie.record_state.value.name).is_equal_to("Charlie")
assert_that(w._status.value).is_equal_to("editing")
```

## Setting Record in __setup__

Record fields can be initialized in `__setup__`. Useful for types with required constructor arguments.

```python
@widget
class CatEditor(Widget[Cat]):
    def __setup__(self) -> None:
        self.record = Cat(name="Whiskers", lives=9)

w = qt.track(CatEditor())
assert_that(w._qtpie.record_state.value.name).is_equal_to("Whiskers")
```

## Decorator Parameter

`@widget(record=...)` sets the initial record value at class decoration time.

```python
@widget(record=Dog("Fido", "Lab"))
class DogEditor(Widget[Dog]):
    pass

w = qt.track(DogEditor())
assert_that(w.record.name).is_equal_to("Fido")
assert_that(w.record.breed).is_equal_to("Lab")
```

```python
@widget(record=Dog("Buddy", "Golden"))
class DogEditor(Widget[Dog]):
    def __setup__(self) -> None:
        captured_name.append(self.record.name)

qt.track(DogEditor())
assert_that(captured_name[0]).is_equal_to("Buddy")
```

## Explicit Record Declaration

Record can be declared explicitly as a `Variable[T]` field with a default value.

```python
@widget
class CatEditor(Widget[Cat]):
    record: Variable[Cat] = new(default=Cat("Whiskers", 9))  # type: ignore[assignment]

w = qt.track(CatEditor())
assert_that(w._qtpie.record_state.value.name).is_equal_to("Whiskers")
assert_that(w._qtpie.record_state.value.lives).is_equal_to(9)
```

## on_dirty_changed Hook

The `on_dirty_changed` lifecycle hook fires when the record's dirty state changes.

```python
@widget
class PersonEditor(Widget[Person]):
    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        dirty_states.append(is_dirty)

w = qt.track(PersonEditor())
w._qtpie.record_state.observable.name.set("Dirty")
assert_that(dirty_states).contains(True)
```
