# Widget[T] and Smart Variable[T]

## Goal
Implement `Widget[T]` for model-bound widgets, with `Variable[T]` as a universal reactive wrapper that automatically picks the right underlying implementation.

## Core Concept

```python
Variable[T]  # universal reactive wrapper

# Automatically becomes:
Variable[str]       → wraps Observable[str]
Variable[int]       → wraps Observable[int]
Variable[list[X]]   → wraps ObservableList[X]
Variable[dict[K,V]] → wraps ObservableDict[K,V]
Variable[Dog]       → wraps ObservableProxy[Dog]  (complex types)
```

`Widget[Person]` gives you `self.record: Variable[Person]` which is proxy-based.

## Design

### Variable[T] Smart Detection

```python
_name: Variable[str] = new("")
_name.value = "Bob"           # scalar access

_dog: Variable[Dog] = new()
_dog.name.value = "Buddy"     # proxy field access (nested Variable)
_dog.breed.name.value = "Lab" # deep nested access
```

Detection logic in `new()` or Variable init:
- `str`, `int`, `float`, `bool` → Observable
- `list` origin → ObservableList
- `dict` origin → ObservableDict
- Otherwise → ObservableProxy

### Widget[T]

```python
@widget
class PersonEditor(Widget[Person]):
    _input: QLineEdit = new(bind="name")  # binds to self.record.name

    def __setup__(self):
        # self.record auto-created as Variable[Person] (proxy-based)
        # Or set explicitly:
        self.record = some_existing_person
```

**Record creation:**
1. Auto-create `T()` if no required args
2. Explicit: `record: Variable[Person] = new(name="Bob")`
3. Set in `__setup__`: `self.record = existing_person`

**Binding resolution for `bind="{foo}"`:**
1. Check regular attribute (`foo: int = 123`)
2. Check Variable (`_foo: Variable[str]`)
3. Check record field (`self.record.foo`)

**Format binding:** `bind="{name}, age {age}"` - template with multiple fields

**Nested paths:** `bind="{dog.breed.name}"` works via proxy traversal

### Auto-binding

```python
@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()           # auto-binds to record.name (same name)
    age: QSpinBox = new()             # auto-binds to record.age
    email_input: QLineEdit = new(bind="email")  # explicit bind

@widget(auto_bind=False)
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()           # NO auto-bind
    name_input: QLineEdit = new(bind="name")  # explicit only
```

### Dirty/Validation on Widget[T]

Delegate to `self.record` (the Variable[T] proxy):
- `self.is_dirty` → `self.record.is_dirty` (aggregated)
- `self.dirty_fields` → fields of record that changed
- `self.reset_dirty()` → reset all record fields
- `self.add_validator("name", fn)` → add to record
- `self.is_valid` → all validators pass
- `on_dirty_changed(bool)` → hook
- `on_valid_changed(bool)` → hook

## Implementation Phases

### Phase 1: ObservableList & ObservableDict
- `lib/observant/observable_list.py`
- `lib/observant/observable_dict.py`
- Dirty tracking, change callbacks
- Tests

### Phase 2: ObservableProxy
- `lib/observant/observable_proxy.py`
- Wraps any object, exposes fields as Variables
- Lazy Variable creation per field
- Nested path support
- Dirty tracking aggregation
- Tests

### Phase 3: Smart Variable[T]
- Update `Variable` to detect type and wrap appropriately
- Update `new()` to handle complex types
- Unified access patterns
- Tests

### Phase 4: Widget[T] Basics
- Type parameter extraction at class creation
- `self.record` property (auto-created Variable[T])
- `record: Variable[T] = new(...)` explicit declaration
- Setting record in `__setup__`
- Tests

### Phase 5: Binding to Record
- `bind="field"` binds to record field
- `bind="{field}"` format string
- `bind="{a.b.c}"` nested paths
- Auto-bind by matching field names
- `auto_bind=False` option
- Tests

### Phase 6: Validation
- `add_validator("field", fn)`
- `is_valid` property (Observable[bool])
- `validation_for("field")` → errors
- `validation_errors` → all errors
- `on_valid_changed(bool)` hook
- Tests

## Files to Create/Modify

**New files:**
- `lib/observant/observable_list.py`
- `lib/observant/observable_dict.py`
- `lib/observant/observable_proxy.py`
- `tests/observant/test_observable_list.py`
- `tests/observant/test_observable_dict.py`
- `tests/observant/test_observable_proxy.py`
- `tests/qtpie/test_widget_t.py`

**Modify:**
- `lib/qtpie/variable.py` - smart type detection
- `lib/qtpie/new_field.py` - handle complex types
- `lib/qtpie/widget.py` - Widget[T] support
- `lib/observant/__init__.py` - exports
