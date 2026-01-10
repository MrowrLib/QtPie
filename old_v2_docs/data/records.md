# Records (Widget[T])

QtPie supports typed record models using the `Widget[T]` generic syntax. This provides type-safe, reactive data binding between your domain models and UI widgets.

## Basic Record Widget

Use the type parameter to declare your widget works with a specific model type:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit, QSpinBox
from qtpie import Widget, new, widget

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()
```

When you use `Widget[T]`:
- The `record` property gives you direct access to model fields
- Fields are automatically reactive
- Widget fields with matching names auto-bind to model properties

## Accessing the Record

### Direct Field Access

The `record` property provides convenient field access:

```python
@widget
class PersonEditor(Widget[Person]):
    pass

editor = PersonEditor()

# Direct read
print(editor.record.name)  # "Bob"

# Direct write (triggers reactivity)
editor.record.name = "Alice"
editor.record.age = 30
```

### Record State Access

Use `record_state` to access the underlying `RecordVariable`:

```python
editor = PersonEditor()

# Access the RecordVariable
state = editor.record_state

# Check if dirty
print(state.is_dirty.get())  # False

# Modify through observable
state.observable.name.set("Changed")
print(state.is_dirty.get())  # True

# Get current value
print(state.value.name)  # "Changed"
```

## Auto-Binding Fields to Record Properties

Fields automatically bind to record properties when:
1. The field name matches a record property (e.g., `name` field binds to `record.name`)
2. The field name with leading underscore removed matches (e.g., `_name` binds to `record.name`)

```python
@widget
class PersonEditor(Widget[Person]):
    # Auto-binds to record.name
    name: QLineEdit = new()

    # Also auto-binds to record.age (underscore stripped)
    _age: QSpinBox = new()

editor = PersonEditor()

# Change record - widgets update automatically
editor.record.name = "Bob"
print(editor.name.text())  # "Bob"

# Change widget - record updates automatically (two-way binding)
editor.name.setText("Alice")
print(editor.record.name)  # "Alice"
```

### Explicit Binding

Override auto-binding with explicit `bind=`:

```python
@dataclass
class Person:
    name: str = ""
    email: str = ""

@widget
class PersonEditor(Widget[Person]):
    # Map email_input field to email property
    email_input: QLineEdit = new(bind="email")

editor = PersonEditor()
editor.record.email = "test@example.com"
print(editor.email_input.text())  # "test@example.com"
```

### Disabling Auto-Binding

Disable auto-binding entirely with `auto_bind=False`:

```python
@widget(auto_bind=False)
class PersonEditor(Widget[Person]):
    # No auto-binding occurs
    _name: QLineEdit = new()

    # But explicit bind= still works
    name_field: QLineEdit = new(bind="name")
```

## Initializing Records

### Types with Default Values

For dataclasses with default values, the record initializes automatically:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(Widget[Person]):
    pass

# Record auto-creates with defaults
editor = PersonEditor()
print(editor.record.name)  # ""
print(editor.record.age)   # 0
```

### Using @widget(record=...)

Set the initial record value using the decorator parameter:

```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()

editor = PersonEditor()
print(editor.record.name)  # "Alice"
print(editor.record.age)   # 30
```

This is the recommended approach as it provides the best type inference for IDE autocomplete.

### Setting in __setup__

For types without defaults, set the record in `__setup__`:

```python
@dataclass
class Cat:
    name: str  # No default
    lives: int

@widget
class CatEditor(Widget[Cat]):
    def __setup__(self) -> None:
        self.record = Cat("Whiskers", 9)

editor = CatEditor()
print(editor.record.name)  # "Whiskers"
```

### Explicit Field Declaration

Declare `record` as an explicit `Variable` field:

```python
@widget
class CatEditor(Widget[Cat]):
    record: Variable[Cat] = new(default=Cat("Mittens", 7))  # type: ignore[assignment]

editor = CatEditor()
print(editor.record.name)  # "Mittens"
```

Note: The `type: ignore[assignment]` is needed due to pyright's handling of the descriptor pattern.

## Format String Bindings

Use format strings to display formatted record data:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonView(Widget[Person]):
    # Single field
    name_label: QLabel = new(bind="{name}")

    # Multiple fields
    summary: QLabel = new(bind="{name}, age {age}")

    # Mixed with static widget attributes
    title: str = "Profile"
    display: QLabel = new(bind="{title}: {name}")

view = PersonView()
view.record.name = "Alice"
view.record.age = 25

print(view.summary.text())  # "Alice, age 25"
print(view.display.text())  # "Profile: Alice"
```

Format strings are reactive - they update automatically when any referenced field changes.

## Binding Resolution Order

When resolving names in format strings, QtPie checks in this order:

1. Exact widget attribute match (e.g., `title` → `widget.title`)
2. Record field match (e.g., `name` → `widget.record.name`)
3. Widget attribute with underscore removed (e.g., `count` → `widget._count`)

```python
@widget
class PersonEditor(Widget[Person]):
    title: str = "Editor"  # Widget attribute
    _name: QLineEdit = new()  # Widget field (auto-binds to record.name)

    # {title} resolves to widget.title
    # {name} resolves to record.name (not _name widget)
    header: QLabel = new(bind="{title}: {name}")

editor = PersonEditor()
editor.record.name = "Alice"
print(editor.header.text())  # "Editor: Alice"
```

## Optional Chaining

Access nested optional fields safely with `?`:

```python
@dataclass
class Address:
    city: str = ""

@dataclass
class Employee:
    name: str = ""
    address: Address | None = None

@widget
class EmployeeEditor(Widget[Employee]):
    # Won't crash if address is None
    city: QLineEdit = new(bind="address?.city")

editor = EmployeeEditor()
print(editor.city.text())  # "" (empty, not crash)

editor.record.address = Address(city="NYC")
# Binding continues to work after value is set
```

## Dirty Tracking

Records automatically participate in dirty tracking:

```python
@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()

editor = PersonEditor()

# Check dirty state
print(editor.record_state.is_dirty.get())  # False

# Modify record
editor.record.name = "Changed"
print(editor.record_state.is_dirty.get())  # True

# Reset dirty state
editor.view_model.reset_dirty()
print(editor.record_state.is_dirty.get())  # False
```

### Dirty Change Hook

React to dirty state changes with the `on_dirty_changed` lifecycle method:

```python
@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    save_btn: QPushButton = new("Save")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        # Enable save button only when form is dirty
        self.save_btn.setEnabled(is_dirty)

editor = PersonEditor()
editor.record.name = "Changed"  # save_btn becomes enabled
```

## Combining Records with Variables

Widgets can have both a record and independent `Variable` fields:

```python
@widget
class PersonEditor(Widget[Person]):
    # Record fields (auto-bind)
    name: QLineEdit = new()
    age: QSpinBox = new()

    # Independent widget state
    _status: Variable[str] = new("idle")
    status_label: QLabel = new(bind="{_status}")

editor = PersonEditor()

# Record operations
editor.record.name = "Alice"

# Independent variable operations
editor._status.value = "editing"
```

## Widgets Without Records

Not all widgets need records. Accessing `record` or `record_state` on a plain `Widget` raises a `TypeError`:

```python
@widget
class PlainWidget(Widget):
    label: QLabel = new("Hello")

w = PlainWidget()

try:
    _ = w.record
except TypeError as e:
    print(e)  # "PlainWidget has no record type"

try:
    _ = w.record_state
except TypeError as e:
    print(e)  # "PlainWidget has no record"
```

## Practical Example

Here's a complete form editor demonstrating key record features:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit, QSpinBox, QPushButton, QLabel
from qtpie import Widget, new, widget

@dataclass
class Person:
    name: str = ""
    age: int = 0
    email: str = ""

@widget(record=Person("Alice", 30, "alice@example.com"))
class PersonEditor(Widget[Person]):
    # Auto-bound fields
    name: QLineEdit = new()
    age: QSpinBox = new()
    email: QLineEdit = new()

    # Display formatted record data
    summary: QLabel = new(bind="Name: {name}, Age: {age}")

    # Buttons
    save_btn: QPushButton = new("Save", clicked="on_save")
    reset_btn: QPushButton = new("Reset", clicked="on_reset")

    def __setup__(self) -> None:
        self.age.setMaximum(150)
        self.save_btn.setEnabled(False)

    def on_dirty_changed(self, is_dirty: bool) -> None:
        # Enable save only when form has changes
        self.save_btn.setEnabled(is_dirty)

    def on_save(self) -> None:
        print(f"Saving: {self.record.name}, {self.record.age}, {self.record.email}")
        self.view_model.reset_dirty()

    def on_reset(self) -> None:
        # Reset to decorator values
        self.record.name = "Alice"
        self.record.age = 30
        self.record.email = "alice@example.com"
        self.view_model.reset_dirty()
```

## Common Patterns

### Read-Only Display

Create a read-only view using `QLabel` fields:

```python
@widget
class PersonView(Widget[Person]):
    name_display: QLabel = new(bind="Name: {name}")
    age_display: QLabel = new(bind="Age: {age}")
```

### Partial Forms

Only bind fields you need:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0
    email: str = ""
    phone: str = ""

@widget
class QuickEdit(Widget[Person]):
    # Only edit name and email
    name: QLineEdit = new()
    email: QLineEdit = new()
    # age and phone are accessible via record but not in UI
```

### Validation with Records

Combine record binding with validation:

```python
@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    email: QLineEdit = new()
    errors: list[QLabel] = new(bind="validation_error_messages")

    def __setup__(self) -> None:
        self.add_validator("name", "required",
            lambda v: None if v.record.name else "Name required")
        self.add_validator("email", "format",
            lambda v: None if "@" in v.record.email else "Invalid email")
```
