# Widget[T] Record Support

## Basic Record Type

`Widget[T]` extracts the type parameter as the record type and creates a `RecordVariable[T]` accessible via `record_state`.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())
assert_that(w._qtpie_config.record_type).is_equal_to(Person)
assert_that(w.record_state).is_instance_of(RecordVariable)
```

## Record Field Access

`self.record` provides direct field access and assignment with reactive updates.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())

# Direct assignment triggers reactivity
w.record.name = "Bob"
w.record.age = 42

# Direct read returns actual value (not Observable)
assert_that(w.record.name).is_equal_to("Bob")
assert_that(w.record.age).is_equal_to(42)
```

## Record State Access

`record_state` returns the `RecordVariable` for accessing state properties like `is_dirty`, `value`, and `observable`.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())

assert_that(w.record_state.is_dirty.get()).is_false()

w.record.name = "Changed"
assert_that(w.record_state.is_dirty.get()).is_true()
assert_that(w.record_state.value.name).is_equal_to("Changed")
```

## Dirty Tracking

Record participates in dirty tracking automatically.

```python
@widget
class PersonEditor(Widget[Person]):
    pass

w = qt.track(PersonEditor())
assert_that(w.record_state.is_dirty.get()).is_false()

w.record_state.observable.name.set("Bob")
assert_that(w.record_state.is_dirty.get()).is_true()
```

## Record + Other Variables

Widget can have both a record and other independent variables.

```python
@widget
class PersonEditor(Widget[Person]):
    _status: Variable[str] = new("idle")
    _label: QLabel = new("Editor")

w = qt.track(PersonEditor())

# Record works
w.record_state.observable.name.set("Charlie")
assert_that(w.record_state.value.name).is_equal_to("Charlie")

# Other variable works independently
w._status.value = "editing"
assert_that(w._status.value).is_equal_to("editing")
```

## Types Without Default Values

For types without default constructors, record starts as `None` and can be set in `__setup__`.

```python
@widget
class CatEditor(Widget[Cat]):
    def __setup__(self) -> None:
        self.record = Cat(name="Whiskers", lives=9)

w = qt.track(CatEditor())
assert_that(w.record_state.value.name).is_equal_to("Whiskers")
```

## Explicit Record Declaration

Can declare record explicitly with a default value instead of using the type parameter.

```python
@widget
class CatEditor(Widget[Cat]):
    record: Variable[Cat] = new(default=Cat("Whiskers", 9))  # type: ignore[assignment]

w = qt.track(CatEditor())
assert_that(w.record_state.value.name).is_equal_to("Whiskers")
assert_that(w.record_state.value.lives).is_equal_to(9)
```

## Decorator Record Parameter

`@widget(record=...)` sets the initial record value.

```python
@widget(record=Dog("Fido", "Lab"))
class DogEditor(Widget[Dog]):
    pass

w = qt.track(DogEditor())
assert_that(w.record.name).is_equal_to("Fido")
assert_that(w.record.breed).is_equal_to("Lab")
```

Works with types that have no defaults:

```python
@widget(record=Cat("Whiskers", 9))
class CatEditor(Widget[Cat]):
    pass

w = qt.track(CatEditor())
assert_that(w.record.name).is_equal_to("Whiskers")
assert_that(w.record.lives).is_equal_to(9)
```

## Dirty Change Hook

`on_dirty_changed` fires when record dirty state changes.

```python
@widget
class PersonEditor(Widget[Person]):
    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        dirty_states.append(is_dirty)

w = qt.track(PersonEditor())
_ = w.record_state  # Touch record to register it
w.record_state.observable.name.set("Dirty")
assert_that(dirty_states).contains(True)
```
