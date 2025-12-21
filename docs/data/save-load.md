# Save & Load

When you're working with `Widget[T]` model widgets, you often need to save edited values back to a model or load data from external sources. QtPie provides two simple methods for this.

## Quick Overview

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QLineEdit, QSpinBox, QWidget

from qtpie import Widget, make, widget

@dataclass
class User:
    name: str = ""
    age: int = 0

@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

# Create the editor
editor = UserEditor()

# Edit values via UI...
editor.name.setText("Alice")
editor.age.setValue(30)

# Save proxy values back to model
editor.save_to(editor.model)
print(editor.model.name)  # "Alice"

# Load from dictionary
editor.load_dict({"name": "Bob", "age": 25})
print(editor.name.text())  # "Bob"
```

## save_to(model)

The `save_to()` method copies all current proxy values to a target model instance.

### Save to Original Model

The most common pattern is saving back to the widget's own model:

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

editor = UserEditor()

# User edits the form...
editor.name.setText("Charlie")
editor.age.setValue(28)

# Save changes back to the model
editor.save_to(editor.model)

# Model now has the edited values
assert editor.model.name == "Charlie"
assert editor.model.age == 28
```

### Save to Different Instance

You can also save to a different model instance:

```python
editor = UserEditor()
editor.name.setText("Diana")

# Create a new user and save to it
new_user = User(name="Original")
editor.save_to(new_user)

# New user gets the proxy values
assert new_user.name == "Diana"
```

This is useful when you want to keep the original model unchanged or when creating new instances from form data.

## load_dict(data)

The `load_dict()` method updates proxy values from a dictionary. This is useful for loading data from JSON, databases, or other sources.

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    age: QSpinBox = make(QSpinBox)

editor = UserEditor()

# Load data from dictionary
editor.load_dict({"name": "Eve", "age": 35})

# Widgets are updated automatically
assert editor.name.text() == "Eve"
assert editor.age.value() == 35
```

You can load partial data - fields not in the dictionary remain unchanged:

```python
editor.load_dict({"name": "Frank"})
# Only name is updated, age stays the same
```

## Complete Example: Edit Form with Save/Cancel

Here's a realistic example with Save and Cancel buttons:

```python
from dataclasses import dataclass
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QSpinBox, QWidget

from qtpie import Widget, make, widget

@dataclass
class User:
    name: str = ""
    age: int = 0

@widget(layout="form")
class UserEditor(QWidget, Widget[User]):
    # Form fields (auto-bind to model)
    name: QLineEdit = make(QLineEdit, form_label="Name")
    age: QSpinBox = make(QSpinBox, form_label="Age", minimum=0, maximum=120)

    # Display original values
    original: QLabel = make(QLabel, bind="Original: {name}, age {age}")

    # Buttons
    save_btn: QPushButton = make(QPushButton, "Save", clicked="on_save")
    cancel_btn: QPushButton = make(QPushButton, "Cancel", clicked="on_cancel")

    def on_save(self) -> None:
        """Save proxy values back to model."""
        self.save_to(self.model)
        print(f"Saved: {self.model.name}, age {self.model.age}")
        # In real app: send to database, close dialog, etc.

    def on_cancel(self) -> None:
        """Reset to original model values."""
        # Reload from current model values
        self.load_dict({
            "name": self.model.name,
            "age": self.model.age,
        })
        print("Changes discarded")

# Usage
editor = UserEditor()
editor.model.name = "Original Name"
editor.model.age = 42

# Reload to show original values
editor.load_dict({"name": editor.model.name, "age": editor.model.age})

# User edits...
editor.name.setText("New Name")
editor.age.setValue(99)

# Click Cancel - resets to original
editor.on_cancel()
assert editor.name.text() == "Original Name"

# Edit again and click Save
editor.name.setText("Saved Name")
editor.on_save()
assert editor.model.name == "Saved Name"
```

## How It Works

Under the hood:

- **`save_to(model)`** calls `self.proxy.save_to(model)`, copying all proxy field values to the target model using `setattr()`
- **`load_dict(data)`** calls `self.proxy.load_dict(data)`, updating proxy values which automatically triggers bound widget updates

Both methods are thin wrappers around the underlying `ObservableProxy` from the `observant` library.

## Working with Dirty Tracking

Save/load pairs naturally with dirty tracking:

```python
@widget
class UserEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit)
    save_btn: QPushButton = make(QPushButton, "Save", clicked="on_save")

    def on_save(self) -> None:
        if self.is_dirty():
            self.save_to(self.model)
            self.reset_dirty()  # Mark as clean after save
            print("Saved changes")
        else:
            print("No changes to save")
```

See [Dirty Tracking](dirty.md) for more details.

## See Also

- [Model Widgets](model-widgets.md) - Understanding `Widget[T]`
- [Dirty Tracking](dirty.md) - Track which fields changed
- [Validation](validation.md) - Validate before saving
