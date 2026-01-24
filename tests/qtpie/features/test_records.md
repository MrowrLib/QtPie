# Records Feature - QtPie Usage Patterns

Records in QtPie allow widgets to bind to typed dataclass objects, providing reactive two-way data binding between UI fields and data models.

## Widget[T] Type Pattern

Declare a widget with a record type using the generic `Widget[T]` or `Window[T]` syntax.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(Widget[Person]):
    pass
```

## Setting Record via Decorator

Use the `record=` parameter in the decorator to provide initial values.

```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    pass
```

## Setting Record via __setup__

For dynamic initialization, set the record in the `__setup__` lifecycle method.

```python
@widget
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        self.record = Person("Bob", 25)
```

## Accessing Record Properties

Access record fields directly via `self.record.fieldname` - both reading and writing.

```python
# Reading
name = self.record.name

# Writing (triggers reactive updates)
self.record.name = "NewName"
```

## Auto-Binding Fields to Record

Fields named the same as record properties automatically bind to those properties.

```python
@widget(record=Person("Ivy", 28))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
```

## Two-Way Binding

Changes flow both directions - record changes update widgets, widget edits update record.

```python
# Changing record updates widget
instance.record.name = "Jackie"
# instance.name.text() == "Jackie"

# Editing widget updates record
instance.name.setText("Katherine")
# instance.record.name == "Katherine"
```

## Multiple Field Bindings

Multiple fields can bind to different record properties in the same widget.

```python
@widget(record=Address("123 Main", "Springfield", "12345"))
class AddressEditor(Widget[Address]):
    street: QLineEdit = new()  # Binds to record.street
    city: QLineEdit = new()    # Binds to record.city
```

## Dirty Tracking Integration

Record changes automatically integrate with widget-level dirty tracking.

```python
instance.is_dirty.get()  # False initially
instance.record.name = "Michael"
instance.is_dirty.get()  # True after change
instance.reset_dirty()   # Clears dirty state
```

## Combining Record and Variable Dirty State

Both record changes and Variable changes contribute to the widget's dirty state.

```python
@widget(record=Person("Oscar", 65))
class Editor(Widget[Person]):
    _count: Variable[int] = new(0)

# Either change makes widget dirty
instance._count.value = 5  # is_dirty = True
instance.record.name = "Ozzy"  # is_dirty = True
```

## Replacing Entire Record

The entire record can be replaced with a new instance.

```python
instance.record = Person("Patricia", 72)
```

## Raw Record Access via record_value

Use `record_value` property to get the unwrapped dataclass (not the ObservableProxy).

```python
raw = instance.record_value
isinstance(raw, Person)  # True
raw.name  # Direct access to raw dataclass
```

## Record Callable Shorthand

Call `record()` as a function shorthand for accessing the raw value.

```python
raw = instance.record()  # Same as instance.record.value
raw.name  # "Charlie"
```

## Supported Base Classes

Records work with `Widget`, `Window`, and `App` base classes. Auto-binding of fields to record properties works with `Widget` and `Window`.
