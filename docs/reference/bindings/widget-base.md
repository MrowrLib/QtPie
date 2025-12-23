# Widget[T] Base Class

The `Widget[T]` base class is the foundation of model-driven widgets in QtPie. It provides automatic model binding, validation, dirty tracking, undo/redo, and save/load functionality.

## Overview

`Widget[T]` can be used in two ways:

1. **Without type parameter** - Just a mixin, no model binding
2. **With type parameter** - Enables automatic model binding and reactive features

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox
from qtpie import Widget, widget, make

# Without type parameter - simple widget
@widget
class SimpleWidget(QWidget, Widget):
    label: QLabel = make(QLabel, "Hello")

# With type parameter - model-bound widget
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # Auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # Auto-binds to model.age
```

## Model & Proxy Attributes

When using `Widget[T]`, two key attributes are automatically created:

### `model: T`

The underlying data model. This is the source of truth for your data.

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)

w = PersonEditor()
print(w.model.name)  # Access model directly
w.model.name = "Bob"  # Direct assignment (won't trigger UI update)
```

**Model Creation:**

By default, the model is auto-created as `T()`:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)

w = PersonEditor()
# model = Person() automatically created
assert w.model.name == ""
```

**Custom Model:**

Use `make()` to provide a custom initial model:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make(Person, name="Alice", age=30)
    name: QLineEdit = make(QLineEdit)

w = PersonEditor()
assert w.model.name == "Alice"
```

**Deferred Initialization:**

Use `make_later()` for manual setup:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make_later()
    name: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        self.model = Person(name="Charlie", age=25)
```

### `proxy: ObservableProxy[T]`

An [ObservableProxy](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/) wrapper around the model that enables reactive bindings. Changes to the proxy automatically update bound widgets, and widget changes update the proxy. See [Observant](https://mrowrlib.github.io/observant.py/) ([PyPI](https://pypi.org/project/observant/)) for more on the underlying reactive system.

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)

w = PersonEditor()

# Changes via proxy trigger UI updates
w.proxy.observable(str, "name").set("Alice")
assert w.name.text() == "Alice"

# Widget changes update the proxy (and model)
w.name.setText("Bob")
assert w.proxy.observable(str, "name").get() == "Bob"
assert w.model.name == "Bob"
```

## Automatic Binding

By default (`auto_bind=True`), widget fields automatically bind to model properties when their names match:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0
    active: bool = False

@widget
class PersonEditor(QWidget, Widget[Person]):
    # These auto-bind by name matching:
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
    active: QCheckBox = make(QCheckBox)

    # This doesn't match any model field - no binding:
    submit: QPushButton = make(QPushButton, "Submit")

w = PersonEditor()

# Two-way binding works automatically:
w.name.setText("Alice")
assert w.model.name == "Alice"

w.proxy.observable(int, "age").set(30)
assert w.age.value() == 30
```

### Disabling Auto-Binding

Use `auto_bind=False` to disable automatic name-based binding:

```python
@widget(auto_bind=False)
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # NOT auto-bound
    age: QSpinBox = make(QSpinBox, bind="age")  # Explicit binding still works

w = PersonEditor()

w.name.setText("Alice")
assert w.model.name == ""  # No binding occurred

w.age.setValue(30)
assert w.model.age == 30  # Explicit binding works
```

## set_model()

Change the model after widget creation and rebind all widgets.

```python
def set_model(self, model: T) -> None
```

**Example:**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

w = PersonEditor()
assert w.name.text() == ""

# Switch to a different person
new_person = Person(name="Alice", age=30)
w.set_model(new_person)

assert w.model == new_person
assert w.model.name == "Alice"
```

## Validation Methods

Validation is powered by the underlying [ObservableProxy](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/). All validation methods delegate to `self.proxy`.

### add_validator()

Add a validation rule to a field.

```python
def add_validator(self, field: str, validator: Callable[[Any], str | None]) -> None
```

**Parameters:**
- `field`: The field name to validate
- `validator`: Function that returns `None` if valid, or an error message if invalid

**Example:**

```python
@dataclass
class User:
    name: str = ""
    age: int = 0
    email: str = ""

@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
    email: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        # Add validation rules
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)
        self.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
```

### is_valid()

Get an observable indicating whether all fields are valid.

```python
def is_valid(self) -> Observable[bool]
```

**Returns:** Observable that emits `True` when all validators pass, `False` otherwise.

**Example:**

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    save_btn: QPushButton = make(QPushButton, "Save")

    def setup(self) -> None:
        self.add_validator("name", lambda v: "Required" if not v else None)

        # Enable save button only when form is valid
        self.is_valid().on_change(lambda valid: self.save_btn.setEnabled(valid))

w = UserEditor()
assert w.is_valid().get() is False  # Empty name is invalid

w.name.setText("Alice")
assert w.is_valid().get() is True  # Now valid
```

### validation_for()

Get an observable list of validation errors for a specific field.

```python
def validation_for(self, field: str) -> Observable[list[str]]
```

**Parameters:**
- `field`: The field name

**Returns:** Observable list of error messages (empty if valid)

**Example:**

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
    name_error: QLabel = make(QLabel)
    age_error: QLabel = make(QLabel)

    def setup(self) -> None:
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)

        # Show errors for each field
        self.validation_for("name").on_change(self.show_name_errors)
        self.validation_for("age").on_change(self.show_age_errors)

    def show_name_errors(self, errors: list[str]) -> None:
        self.name_error.setText(", ".join(errors) if errors else "")

    def show_age_errors(self, errors: list[str]) -> None:
        self.age_error.setText(", ".join(errors) if errors else "")

w = UserEditor()
name_errors = w.validation_for("name").get()
assert "Name required" in name_errors
```

### validation_errors()

Get an observable dict of all validation errors.

```python
def validation_errors(self) -> ObservableDict[str, list[str]]
```

**Returns:** Observable dictionary mapping field names to lists of error messages

**Example:**

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        self.add_validator("name", lambda v: "Required" if not v else None)
        self.add_validator("email", lambda v: "Invalid" if "@" not in v else None)

w = UserEditor()

# Get all errors as a dict
all_errors = w.validation_errors()
name_errors = all_errors.get("name", [])
email_errors = all_errors.get("email", [])

assert "Required" in name_errors
assert "Invalid" in email_errors
```

## Dirty Tracking Methods

Dirty tracking lets you detect which fields have been modified since the last reset.

### is_dirty()

Check whether any field has been modified.

```python
def is_dirty(self) -> bool
```

**Returns:** `True` if any field is dirty, `False` otherwise

**Example:**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)

w = PersonEditor()
assert w.is_dirty() is False  # Initially clean

w.name.setText("Alice")
assert w.is_dirty() is True  # Now dirty
```

### dirty_fields()

Get the set of dirty field names.

```python
def dirty_fields(self) -> set[str]
```

**Returns:** Set of field names that have been modified

**Example:**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

w = PersonEditor()

w.name.setText("Alice")
assert "name" in w.dirty_fields()
assert "age" not in w.dirty_fields()

w.age.setValue(30)
assert "age" in w.dirty_fields()
```

### reset_dirty()

Reset dirty state, making current values the new baseline.

```python
def reset_dirty(self) -> None
```

**Example:**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    save_btn: QPushButton = make(QPushButton, "Save", clicked="save")

    def save(self) -> None:
        # Save to database...
        self.save_to(self.model)
        self.reset_dirty()  # Mark as clean after save

w = PersonEditor()
w.name.setText("Alice")
assert w.is_dirty() is True

w.save()
assert w.is_dirty() is False  # Clean after save
```

**Common Pattern: Unsaved Changes Warning**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    status: QLabel = make(QLabel)

    def setup_bindings(self) -> None:
        # Show status when dirty state changes
        self.proxy.is_dirty_observable().on_change(self.update_status)

    def update_status(self, dirty: bool) -> None:
        if dirty:
            self.status.setText("* Unsaved changes")
        else:
            self.status.setText("Saved")
```

## Undo/Redo Methods

Undo/redo functionality requires enabling it in the `@widget` decorator.

**Enable undo:**

```python
@widget(undo=True)
class TextEditor(QWidget, Widget[Document]):
    content: QTextEdit = make(QTextEdit)
```

**Configure undo:**

```python
@widget(
    undo=True,
    undo_max=50,          # Max 50 history entries per field (default: 20)
    undo_debounce_ms=500  # Debounce rapid changes (default: 300ms)
)
class TextEditor(QWidget, Widget[Document]):
    content: QTextEdit = make(QTextEdit)
```

### undo()

Undo the last change to a field.

```python
def undo(self, field: str) -> None
```

**Parameters:**
- `field`: The field name

**Example:**

```python
@widget(undo=True)
class TextEditor(QWidget, Widget[Document]):
    content: QLineEdit = make(QLineEdit)

w = TextEditor()

w.content.setText("Alice")
assert w.proxy.observable(str, "content").get() == "Alice"

w.undo("content")
assert w.proxy.observable(str, "content").get() == ""  # Reverted
```

### redo()

Redo the last undone change to a field.

```python
def redo(self, field: str) -> None
```

**Parameters:**
- `field`: The field name

**Example:**

```python
@widget(undo=True)
class TextEditor(QWidget, Widget[Document]):
    content: QLineEdit = make(QLineEdit)

w = TextEditor()

w.content.setText("Alice")
w.undo("content")
assert w.proxy.observable(str, "content").get() == ""

w.redo("content")
assert w.proxy.observable(str, "content").get() == "Alice"  # Restored
```

### can_undo()

Check whether undo is available for a field.

```python
def can_undo(self, field: str) -> bool
```

**Parameters:**
- `field`: The field name

**Returns:** `True` if undo is available, `False` otherwise

**Example:**

```python
@widget(undo=True)
class TextEditor(QWidget, Widget[Document]):
    content: QLineEdit = make(QLineEdit)
    undo_btn: QPushButton = make(QPushButton, "Undo", clicked="do_undo")

    def setup_bindings(self) -> None:
        # Update button state when undo availability changes
        self.proxy.observable(str, "content").on_change(self.update_undo_btn)

    def update_undo_btn(self, _: str) -> None:
        self.undo_btn.setEnabled(self.can_undo("content"))

    def do_undo(self) -> None:
        if self.can_undo("content"):
            self.undo("content")

w = TextEditor()
assert w.can_undo("content") is False  # No history yet

w.content.setText("Alice")
assert w.can_undo("content") is True  # Can now undo

w.undo("content")
assert w.can_undo("content") is False  # No more undo
```

### can_redo()

Check whether redo is available for a field.

```python
def can_redo(self, field: str) -> bool
```

**Parameters:**
- `field`: The field name

**Returns:** `True` if redo is available, `False` otherwise

**Example:**

```python
@widget(undo=True)
class TextEditor(QWidget, Widget[Document]):
    content: QLineEdit = make(QLineEdit)
    redo_btn: QPushButton = make(QPushButton, "Redo", clicked="do_redo")

    def setup_bindings(self) -> None:
        self.proxy.observable(str, "content").on_change(self.update_redo_btn)

    def update_redo_btn(self, _: str) -> None:
        self.redo_btn.setEnabled(self.can_redo("content"))

    def do_redo(self) -> None:
        if self.can_redo("content"):
            self.redo("content")

w = TextEditor()
assert w.can_redo("content") is False  # Nothing to redo

w.content.setText("Alice")
w.undo("content")
assert w.can_redo("content") is True  # Can now redo
```

**Complete Example: Text Editor with Undo/Redo**

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QWidget, QTextEdit, QPushButton
from qtpie import Widget, widget, make

@dataclass
class Document:
    content: str = ""

@widget(undo=True, undo_max=100, undo_debounce_ms=500)
class TextEditor(QWidget, Widget[Document]):
    content: QTextEdit = make(QTextEdit)
    undo_btn: QPushButton = make(QPushButton, "Undo", clicked="do_undo")
    redo_btn: QPushButton = make(QPushButton, "Redo", clicked="do_redo")

    def setup_bindings(self) -> None:
        # Update button states when content changes
        self.proxy.observable(str, "content").on_change(self.update_buttons)
        self.update_buttons("")  # Initial state

    def update_buttons(self, _: str) -> None:
        self.undo_btn.setEnabled(self.can_undo("content"))
        self.redo_btn.setEnabled(self.can_redo("content"))

    def do_undo(self) -> None:
        if self.can_undo("content"):
            self.undo("content")

    def do_redo(self) -> None:
        if self.can_redo("content"):
            self.redo("content")
```

## Save/Load Methods

Save and load methods let you transfer data between the proxy and model instances or dictionaries.

### save_to()

Save the current proxy state to a model instance.

```python
def save_to(self, target: T) -> None
```

**Parameters:**
- `target`: The model instance to save to

**Example:**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

w = PersonEditor()

w.name.setText("Alice")
w.age.setValue(30)

# Save back to original model
w.save_to(w.model)
assert w.model.name == "Alice"
assert w.model.age == 30

# Save to a different instance
new_person = Person()
w.save_to(new_person)
assert new_person.name == "Alice"
assert new_person.age == 30
```

**Common Pattern: Edit Form with Save/Cancel**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make_later()  # Set externally

    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
    save_btn: QPushButton = make(QPushButton, "Save", clicked="save")
    cancel_btn: QPushButton = make(QPushButton, "Cancel", clicked="cancel")

    original_model: Person | None = None

    def edit(self, person: Person) -> None:
        """Start editing a person."""
        self.original_model = person
        self.set_model(Person(name=person.name, age=person.age))  # Work on copy

    def save(self) -> None:
        """Save changes back to original."""
        if self.original_model:
            self.save_to(self.original_model)
            self.reset_dirty()
            self.close()

    def cancel(self) -> None:
        """Discard changes."""
        if self.is_dirty():
            # Show confirmation dialog...
            pass
        self.close()
```

### load_dict()

Load data from a dictionary into the proxy.

```python
def load_dict(self, data: dict[str, Any]) -> None
```

**Parameters:**
- `data`: Dictionary of field names to values

**Example:**

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

w = PersonEditor()

# Load from dictionary (e.g., from JSON API)
w.load_dict({"name": "Charlie", "age": 25})

assert w.name.text() == "Charlie"
assert w.age.value() == 25
```

**Common Pattern: Load from API**

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)
    load_btn: QPushButton = make(QPushButton, "Load User", clicked="load_user")

    def load_user(self) -> None:
        # Fetch from API
        response = api.get_user(user_id=123)
        data = response.json()  # {"name": "Alice", "email": "alice@example.com"}

        # Load into form
        self.load_dict(data)
        self.reset_dirty()  # Mark as clean since we just loaded
```

## Lifecycle Hooks

`Widget[T]` provides several lifecycle hooks you can override to customize initialization:

```python
@widget
class MyWidget(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        """Called after widget initialization. Set up initial state."""
        pass

    def setup_values(self) -> None:
        """Called after setup(). Initialize values."""
        pass

    def setup_bindings(self) -> None:
        """Called after setup_values(). Set up data bindings."""
        pass

    def setup_layout(self, layout: QLayout) -> None:
        """Called after setup_bindings() if widget has a layout."""
        pass

    def setup_styles(self) -> None:
        """Called after setup_layout(). Apply styles."""
        pass

    def setup_events(self) -> None:
        """Called after setup_styles(). Set up event handlers."""
        pass

    def setup_signals(self) -> None:
        """Called after setup_events(). Connect signals."""
        pass
```

**Execution Order:**

1. `__init__()` - Widget fields created
2. `setup()`
3. `setup_values()`
4. `setup_bindings()`
5. `setup_layout(layout)` (if layout exists)
6. `setup_styles()`
7. `setup_events()`
8. `setup_signals()`

## Complete Example: User Form

Here's a complete example combining validation, dirty tracking, and save/load:

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox, QPushButton, QLabel
from qtpie import Widget, widget, make

@dataclass
class User:
    name: str = ""
    age: int = 0
    email: str = ""

@widget(undo=True)
class UserEditor(QWidget, Widget[User]):
    # Input fields
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
    email: QLineEdit = make(QLineEdit)

    # Error displays
    name_error: QLabel = make(QLabel)
    email_error: QLabel = make(QLabel)

    # Status and actions
    status: QLabel = make(QLabel)
    save_btn: QPushButton = make(QPushButton, "Save", clicked="save")
    undo_btn: QPushButton = make(QPushButton, "Undo", clicked="do_undo")
    redo_btn: QPushButton = make(QPushButton, "Redo", clicked="do_redo")

    def setup(self) -> None:
        # Add validation rules
        self.add_validator("name", lambda v: "Name required" if not v else None)
        self.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)
        self.add_validator(
            "email",
            lambda v: "Invalid email" if v and "@" not in v else None
        )

    def setup_bindings(self) -> None:
        # Show validation errors
        self.validation_for("name").on_change(
            lambda errors: self.name_error.setText(", ".join(errors))
        )
        self.validation_for("email").on_change(
            lambda errors: self.email_error.setText(", ".join(errors))
        )

        # Enable save only when valid
        self.is_valid().on_change(lambda valid: self.save_btn.setEnabled(valid))

        # Show dirty status
        self.proxy.is_dirty_observable().on_change(self.update_status)

        # Update undo/redo buttons
        self.proxy.observable(str, "name").on_change(self.update_undo_buttons)

    def update_status(self, dirty: bool) -> None:
        if dirty:
            self.status.setText("* Unsaved changes")
        else:
            self.status.setText("Saved")

    def update_undo_buttons(self, _: str) -> None:
        self.undo_btn.setEnabled(self.can_undo("name"))
        self.redo_btn.setEnabled(self.can_redo("name"))

    def save(self) -> None:
        if self.is_valid().get():
            self.save_to(self.model)
            self.reset_dirty()
            print(f"Saved: {self.model}")

    def do_undo(self) -> None:
        if self.can_undo("name"):
            self.undo("name")

    def do_redo(self) -> None:
        if self.can_redo("name"):
            self.redo("name")
```

## See Also

- [Data Binding with bind()](bind.md) - Manual binding function
- [Model Widgets Guide](../../data/model-widgets.md) - Using Widget[T] in practice
- [Validation Guide](../../data/validation.md) - Building validated forms
- [Dirty Tracking Guide](../../data/dirty.md) - Tracking unsaved changes
- [Undo & Redo Guide](../../data/undo.md) - Implementing undo/redo
- [Save & Load Guide](../../data/save-load.md) - Saving and loading data
- [Observant Integration](../../guides/observant.md) - Understanding the reactive layer
