# Model Widgets

Model widgets bind Qt input widgets to data models automatically. They eliminate boilerplate by using the `Widget[T]` base class with automatic field name matching.

## Basic Usage

Create a model widget by inheriting from `Widget[T]` where `T` is your data model type:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # auto-binds to model.age
```

That's it! Widget fields automatically bind to model properties with matching names. Changes flow both ways: widget → model and model → widget.

## How Auto-Binding Works

When you use `Widget[T]`:

1. **Model is auto-created** - A `T()` instance is created automatically
2. **Proxy is auto-created** - An [ObservableProxy[T]](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/) wraps the model
3. **Fields auto-bind by name** - Widget fields bind to model properties with the same name

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # binds to model.name
    age: QSpinBox = make(QSpinBox)      # binds to model.age
    # extra_widget: QLabel - won't auto-bind (no matching model field)

editor = PersonEditor()

# Use the auto-created model and proxy
print(editor.model.name)  # ""
print(editor.proxy)       # ObservableProxy[Person]

# Changes sync both ways
editor.name.setText("Alice")
print(editor.model.name)  # "Alice"

editor.proxy.observable(int, "age").set(30)
print(editor.age.value())  # 30
```

## model and proxy Attributes

Every `Widget[T]` has two attributes:

### model: T

The underlying data model instance. This is a plain dataclass (or any object):

```python
@widget
class DogEditor(QWidget, Widget[Dog]):
    name: QLineEdit = make(QLineEdit)

editor = DogEditor()
print(editor.model)  # Dog(name="", breed="")
print(type(editor.model))  # <class 'Dog'>
```

### proxy: ObservableProxy[T]

An [ObservableProxy](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/) wrapper around the model that enables reactive bindings. See [Observant](https://mrowrlib.github.io/observant.py/) ([PyPI](https://pypi.org/project/observant/)) for more on the underlying reactive system:

```python
editor = DogEditor()

# Access model fields through proxy observables
name_obs = editor.proxy.observable(str, "name")
name_obs.on_change(lambda value: print(f"Name changed to: {value}"))

# Setting through proxy triggers observers
name_obs.set("Buddy")  # prints: "Name changed to: Buddy"

# Widget is updated automatically
print(editor.name.text())  # "Buddy"
```

## Custom Model Initialization

### Using make()

Provide initial values by using `make()` with your model type:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make(Person, name="Bob", age=25)
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

editor = PersonEditor()
print(editor.name.text())  # "Bob"
print(editor.age.value())  # 25
```

### Using make_later()

For dynamic initialization in the `setup()` hook:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make_later()
    name: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        # Load from database, file, etc.
        self.model = load_person_from_db()

editor = PersonEditor()  # model is set during initialization
```

**Important**: If you use `make_later()`, you MUST set the field in `setup()`. Otherwise, you'll get a `ValueError`.

## Disabling Auto-Binding

By default, `Widget[T]` auto-binds fields by name (`auto_bind=True`). To disable this:

```python
@widget(auto_bind=False)
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # NOT auto-bound
    age: QSpinBox = make(QSpinBox)      # NOT auto-bound

editor = PersonEditor()
editor.name.setText("Alice")
print(editor.model.name)  # "" (no binding occurred)
```

With `auto_bind=False`, you must use explicit `bind=` parameters:

```python
@widget(auto_bind=False)
class PersonEditor(QWidget, Widget[Person]):
    name_input: QLineEdit = make(QLineEdit, bind="name")  # Explicit binding
    age_input: QSpinBox = make(QSpinBox, bind="age")      # Explicit binding

editor = PersonEditor()
editor.name_input.setText("Alice")
print(editor.model.name)  # "Alice" (explicit binding works)
```

## Explicit Bindings Override Auto-Binding

If a field has an explicit `bind=` parameter, it takes precedence over auto-binding:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    # This field has a different name but explicitly binds to model.name
    full_name: QLineEdit = make(QLineEdit, bind="name")

    # Display-only label also bound to model.name
    name_display: QLabel = make(QLabel, bind="Name: {name}")

editor = PersonEditor()
editor.full_name.setText("Alice")
print(editor.model.name)        # "Alice"
print(editor.name_display.text())  # "Name: Alice"
```

## Changing Models at Runtime

Use `set_model()` to switch to a different model instance:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

editor = PersonEditor()
print(editor.name.text())  # ""

# Switch to a different person
new_person = Person(name="Charlie", age=40)
editor.set_model(new_person)

print(editor.name.text())  # "Charlie"
print(editor.age.value())  # 40
```

## Without Type Parameter

You can use `Widget` without a type parameter as a simple mixin:

```python
@widget
class SimpleWidget(QWidget, Widget):
    label: QLabel = make(QLabel, "Hello")
    input: QLineEdit = make(QLineEdit)

widget = SimpleWidget()
# No model or proxy attributes
print(hasattr(widget, "model"))  # False
print(hasattr(widget, "proxy"))  # False
```

This is useful when you don't need model binding but want to use the lifecycle hooks from `Widget`.

## Supported Widget Types

Auto-binding works with all registered widget types:

| Widget Type | Binds To | Direction |
|------------|----------|-----------|
| `QLineEdit` | `text` | Two-way |
| `QTextEdit` | `text` | Two-way |
| `QPlainTextEdit` | `text` | Two-way |
| `QLabel` | `text` | One-way (model → widget) |
| `QSpinBox` | `value` (int) | Two-way |
| `QDoubleSpinBox` | `value` (float) | Two-way |
| `QCheckBox` | `checked` (bool) | Two-way |
| `QRadioButton` | `checked` (bool) | Two-way |
| `QSlider` | `value` (int) | Two-way |
| `QDial` | `value` (int) | Two-way |
| `QProgressBar` | `value` (int) | One-way (model → widget) |
| `QComboBox` | `currentText` | Two-way |
| `QDateEdit` | `date` (QDate) | Two-way |
| `QTimeEdit` | `time` (QTime) | Two-way |
| `QDateTimeEdit` | `dateTime` (QDateTime) | Two-way |
| `QFontComboBox` | `currentFont` (QFont) | Two-way |
| `QKeySequenceEdit` | `keySequence` (QKeySequence) | Two-way |
| `QListWidget` | `currentRow` (int) | Two-way |

## Complete Example

Here's a full person editor with custom initialization:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox, QCheckBox

@dataclass
class Person:
    name: str = ""
    age: int = 0
    active: bool = False

@widget
class PersonEditor(QWidget, Widget[Person]):
    # Custom initial model
    model: Person = make(Person, name="Alice", age=30, active=True)

    # Auto-bound fields (by matching names)
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)
    active: QCheckBox = make(QCheckBox, "Active")

# Use it
editor = PersonEditor()

# Initial values from custom model
print(editor.name.text())       # "Alice"
print(editor.age.value())       # 30
print(editor.active.isChecked()) # True

# Changes sync automatically
editor.name.setText("Bob")
print(editor.model.name)        # "Bob"

editor.age.setValue(25)
print(editor.model.age)         # 25

# Change via proxy
editor.proxy.observable(bool, "active").set(False)
print(editor.active.isChecked()) # False
```

## See Also

- [Reactive State](state.md) - Using `state()` for reactive properties
- [Format Expressions](format.md) - Binding with format strings
- [Validation](validation.md) - Adding validators to model fields
- [Dirty Tracking](dirty.md) - Tracking which fields changed
- [Undo & Redo](undo.md) - Enabling undo/redo on model fields
- [Save & Load](save-load.md) - Saving and loading model data
- [Widget[T] Reference](../reference/bindings/widget-base.md) - Full API reference
- [Observant Integration](../guides/observant.md) - Understanding the reactive layer
