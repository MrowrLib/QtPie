# Record Types

`Widget[T]` binds a dataclass to a widget, enabling declarative form editing with automatic field binding, dirty tracking, and reactive updates.

## Basic Usage

```python
from dataclasses import dataclass
from qtpie import Widget, new, widget

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QSpinBox = new()    # Auto-binds to record.age
```

The `record=` decorator parameter sets the initial record value.

## Accessing the Record

### Direct Field Access

Read and write record fields directly:

```python
@widget(record=Person("Bob", 25))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()

    def save(self) -> None:
        # Read fields
        print(f"Name: {self.record.name}")
        print(f"Age: {self.record.age}")

        # Write fields (triggers reactivity)
        self.record.name = "Robert"
```

### Record State

Access the underlying state for dirty tracking:

```python
def check_changes(self) -> None:
    if self.view_model.is_dirty:
        print("Has unsaved changes")
        print(f"Changed fields: {self.view_model.dirty_fields}")
```

## Initialization Options

### Decorator Parameter (Preferred)

```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()
```

### In __setup__

For types without defaults or dynamic initialization:

```python
@dataclass
class Cat:
    name: str
    lives: int  # No default

@widget
class CatEditor(Widget[Cat]):
    name: QLineEdit = new()
    lives: QSpinBox = new()

    def __setup__(self) -> None:
        self.record = Cat(name="Whiskers", lives=9)
```

## Field Auto-Binding

Fields with matching names bind automatically:

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()   # Binds to record.name
    age: QSpinBox = new()     # Binds to record.age
    _name: QLineEdit = new()  # Also binds to record.name (underscore stripped)
```

See [Record Bindings](record-bindings.md) for details.

## Dirty Tracking

Record changes are tracked automatically:

```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()

    _save_btn: QPushButton = new(
        "Save",
        enabled="{view_model.is_dirty}",
        clicked="save"
    )

    def save(self) -> None:
        print(f"Saving: {self.record.name}, {self.record.age}")
        self.view_model.reset_dirty()
```

### Dirty Changed Hook

React to dirty state transitions:

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    _status: QLabel = new("No changes")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        if is_dirty:
            self._status.setText("Unsaved changes")
        else:
            self._status.setText("Saved")
```

## Combining Records with Variables

Use both record fields and independent Variables:

```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    # Record fields
    name: QLineEdit = new()
    age: QSpinBox = new()

    # UI-only state (not part of record)
    _loading: Variable[bool] = new(False)
    _error_msg: Variable[str] = new("")

    _spinner: QLabel = new("Loading...", visible="_loading")
    _error: QLabel = new(bind="{_error_msg}", visible="{len(_error_msg) > 0}")
```

## Using Record in Bindings

Reference record fields in bind expressions:

```python
@widget(record=Person("Alice", 30))
class PersonView(Widget[Person]):
    summary: QLabel = new(bind="{record.name}, age {record.age}")
```

## Window[T]

The same pattern works for `Window[T]`:

```python
@dataclass
class AppSettings:
    theme: str = "light"
    auto_save: bool = True
    font_size: int = 12

@window(title="Settings", record=AppSettings())
class SettingsWindow(Window[AppSettings]):
    theme: QComboBox = new()
    auto_save: QCheckBox = new()
    font_size: QSpinBox = new()

    _save_btn: QPushButton = new("Save", clicked="save")

    def save(self) -> None:
        print(f"Theme: {self.record.theme}")
        print(f"Auto-save: {self.record.auto_save}")
```

## Common Patterns

### CRUD Form

```python
@widget
class PersonManager(Widget):
    _people: Variable[list[Person]] = new([])
    _selected: Variable[Person | None] = new(None)

    # List on left
    _list: list[QLabel] = new(bind="_people", format="{name}")

    # Editor on right
    _editor: PersonEditor = new(visible="{_selected is not None}")

    def on_person_clicked(self, person: Person) -> None:
        self._selected = person
        self._editor.record = person
```

### Save/Cancel Workflow

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()

    _save_btn: QPushButton = new(
        "Save",
        enabled="{view_model.is_dirty}",
        clicked="save"
    )
    _cancel_btn: QPushButton = new("Cancel", clicked="cancel")

    def save(self) -> None:
        save_to_database(self.record)
        self.view_model.reset_dirty()

    def cancel(self) -> None:
        # Reload original data
        self.record = load_from_database()
```

## See Also

- [Record Bindings](record-bindings.md) - Field binding mechanics
- [Validation](validation.md) - Validating record fields
- [Dirty Tracking](dirty-tracking.md) - Change tracking details
- [Variables](../state/variables.md) - Reactive state
