# Form Layouts

Form layouts (`QFormLayout`) are perfect for data entry forms. They automatically arrange labels and input fields in a two-column layout, creating a clean, professional appearance.

## Basic Form Layout

Use `layout="form"` with the `@widget` decorator, and `form_label` in `make()` to specify label text:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox

@widget(layout="form")
class PersonForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    email: QLineEdit = make(QLineEdit, form_label="Email")
    age: QSpinBox = make(QSpinBox, form_label="Age")
```

This creates a professional form:

```
Name:   [                    ]
Email:  [                    ]
Age:    [  0  ]
```

## How It Works

When you use `layout="form"`:

1. QtPie creates a `QFormLayout` for your widget
2. Each field with `form_label` gets added as a row
3. Qt creates a `QLabel` for you automatically
4. Fields are arranged in declaration order

No manual `QLabel` creation needed - QtPie handles it all.

## Real-World Example: Contact Form

Here's a complete contact form with various input types:

```python
from qtpie import widget, make, entrypoint
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox, QTextEdit, QComboBox

@entrypoint
@widget(layout="form")
class ContactForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Full Name", placeholderText="John Doe")
    email: QLineEdit = make(QLineEdit, form_label="Email", placeholderText="john@example.com")
    age: QSpinBox = make(QSpinBox, form_label="Age", minimum=0, maximum=120)
    country: QComboBox = make(QComboBox, form_label="Country")
    bio: QTextEdit = make(QTextEdit, form_label="Bio", placeholderText="Tell us about yourself...")

    def setup(self) -> None:
        self.country.addItems(["USA", "Canada", "UK", "Other"])
```

## Data Binding with Forms

Forms work seamlessly with data binding and model widgets:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget, entrypoint
from qtpy.QtWidgets import QWidget, QLineEdit, QSlider, QLabel
from qtpy.QtCore import Qt

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@entrypoint
@widget(layout="form")
class DogEditor(QWidget, Widget[Dog]):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    age: QSlider = make(
        QSlider,
        Qt.Orientation.Horizontal,
        form_label="Age",
        minimum=0,
        maximum=20
    )
    info: QLabel = make(QLabel, bind="Name: {name}, Age: {age}")
```

The `name` and `age` fields automatically bind to the model. When you edit the form, the `info` label updates in real-time.

See [Record Widgets](../data/record-widgets.md) for more on data binding.

## Fields Without Labels

You can omit `form_label` - the field will still be added to the form, just without a label:

```python
@widget(layout="form")
class MyForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    notes: QTextEdit = make(QTextEdit)  # No label, full-width field
```

This is useful for fields that don't need labels, like large text areas or buttons.

## Styling Forms

Form layouts automatically get a `"form"` CSS class:

```python
@widget(layout="form", classes=["card", "shadow"])
class MyForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Name")
```

The widget will have both `"card"` and `"form"` classes:

```python
# widget.property("class") => ["card", "shadow", "form"]
```

This lets you style forms consistently:

```css
QWidget[class~="form"] {
    padding: 20px;
    background: white;
}

QWidget[class~="form"][class~="card"] {
    border: 1px solid #ddd;
    border-radius: 8px;
}
```

See [Styling](../basics/styling.md) for more on CSS classes.

## Field Order

Fields appear in the form in **declaration order**:

```python
@widget(layout="form")
class PersonForm(QWidget):
    # These appear in this exact order:
    first_name: QLineEdit = make(QLineEdit, form_label="First Name")
    last_name: QLineEdit = make(QLineEdit, form_label="Last Name")
    email: QLineEdit = make(QLineEdit, form_label="Email")
    phone: QLineEdit = make(QLineEdit, form_label="Phone")
```

Rearrange the field declarations to change the form order.

## Field Naming Conventions

Fields follow the standard QtPie underscore conventions:

- `foo` and `_foo` - Added to the form
- `_foo_` - **Excluded** from the form (starts AND ends with `_`)

```python
@widget(layout="form")
class MyForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Name")      # In form
    _age: QSpinBox = make(QSpinBox, form_label="Age")          # In form (private)
    _helper_: QLabel = make(QLabel, "Helper")                  # NOT in form

    def setup(self) -> None:
        # You can position _helper_ manually
        pass
```

Use `_foo_` naming for widgets you want to position manually or use internally.

## Combining with Other Features

### Forms with signals

```python
@widget(layout="form")
class LoginForm(QWidget):
    username: QLineEdit = make(
        QLineEdit,
        form_label="Username",
        textChanged="on_username_changed"
    )
    password: QLineEdit = make(
        QLineEdit,
        form_label="Password",
        echoMode=QLineEdit.EchoMode.Password
    )

    def on_username_changed(self, text: str) -> None:
        print(f"Username: {text}")
```

### Forms with validation

```python
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QWidget, QLineEdit, QLabel

@widget(layout="form")
class ValidatedForm(QWidget, Widget):
    email: QLineEdit = make(QLineEdit, form_label="Email")
    error: QLabel = make(QLabel)

    def setup(self) -> None:
        self.add_validator("email", self.validate_email)
        self.is_valid().subscribe(lambda valid: self.update_error(valid))

    def validate_email(self, value: str) -> list[str]:
        if "@" not in value:
            return ["Invalid email address"]
        return []

    def update_error(self, valid: bool) -> None:
        if not valid:
            errors = self.validation_for("email")
            self.error.setText(errors[0] if errors else "")
        else:
            self.error.setText("")
```

See [Validation](../data/validation.md) for more on form validation.

## When to Use Forms

**Use forms when:**

- Building data entry screens
- Creating settings/preferences dialogs
- Designing login/signup forms
- Making structured input layouts

**Consider other layouts when:**

- Building toolbars → `layout="horizontal"`
- Stacking content vertically → `layout="vertical"` (default)
- Creating calculators or grids → `layout="grid"`
- Needing custom positioning → `layout="none"`

## Complete Example: User Profile Editor

Here's a complete, runnable example combining forms with data binding, validation, and signals:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget, entrypoint
from qtpy.QtWidgets import QWidget, QLineEdit, QSpinBox, QPushButton, QLabel

@dataclass
class User:
    name: str = ""
    email: str = ""
    age: int = 18

@entrypoint
@widget(layout="form", classes=["card"])
class UserProfileEditor(QWidget, Widget[User]):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    email: QLineEdit = make(QLineEdit, form_label="Email")
    age: QSpinBox = make(QSpinBox, form_label="Age", minimum=0, maximum=120)

    status: QLabel = make(QLabel)
    save_btn: QPushButton = make(QPushButton, "Save", clicked="save_profile")

    def setup(self) -> None:
        # Add validation
        self.add_validator("email", self.validate_email)

        # Update status when validation state changes
        self.is_valid().subscribe(self.update_status)

    def validate_email(self, value: str) -> list[str]:
        if "@" not in value or "." not in value:
            return ["Please enter a valid email address"]
        return []

    def update_status(self, valid: bool) -> None:
        if valid:
            self.status.setText("✓ All fields valid")
        else:
            errors = self.validation_for("email")
            self.status.setText(f"✗ {errors[0]}" if errors else "")

    def save_profile(self) -> None:
        if self.is_valid().value:
            # Save the data
            self.save_to(self.model)
            print(f"Saved: {self.model}")
```

## See Also

- [Layouts](../basics/layouts.md) - Overview of all layout types
- [Record Widgets](../data/record-widgets.md) - Binding forms to data models
- [Validation](../data/validation.md) - Validating form input
- [Styling](../basics/styling.md) - Styling forms with CSS
- [Grid Layouts Guide](grids.md) - For more complex positioning needs
