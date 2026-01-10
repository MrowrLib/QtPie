# Form Layouts

QtPie makes building forms easy with `layout="form"` and the `label=` parameter. This guide covers form patterns for data entry, settings dialogs, and user input.

## Basic Form Layout

Set `layout="form"` on your widget to use `QFormLayout`:

```python
from PySide6.QtWidgets import QLineEdit, QSpinBox, QCheckBox
from qtpie import Widget, new, widget

@widget(layout="form")
class UserForm(Widget):
    username: QLineEdit = new(label="Username:")
    email: QLineEdit = new(label="Email:")
    age: QSpinBox = new(label="Age:")
    newsletter: QCheckBox = new(label="Subscribe:")
```

The `label=` parameter creates a `QLabel` paired with the widget in the form row.

## Form with Variables

Forms work seamlessly with reactive Variables:

```python
from PySide6.QtWidgets import QLineEdit, QSpinBox
from qtpie import Variable, Widget, new, widget

@widget(layout="form")
class ProfileForm(Widget):
    _name: Variable[str, QLineEdit] = new("")(label="Name:")
    _age: Variable[int, QSpinBox] = new(18)(label="Age:")

    def get_data(self) -> dict:
        return {
            "name": self._name.value,
            "age": self._age.value
        }
```

## Form with Record Type

Bind forms directly to dataclasses using `Widget[T]`:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit, QSpinBox
from qtpie import Widget, new, widget

@dataclass
class Person:
    name: str = ""
    email: str = ""
    age: int = 0

@widget(layout="form", record=Person())
class PersonForm(Widget[Person]):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")
    age: QSpinBox = new(label="Age:")
```

Fields with matching names auto-bind to record properties. Access the data via `self.record`.

## Validated Forms

Add validation to form fields:

```python
@widget(layout="form")
class ValidatedForm(Widget):
    _email: Variable[str, QLineEdit] = new("")(
        label="Email:",
        validate="validate_email"
    )
    _password: Variable[str, QLineEdit] = new("")(
        label="Password:",
        validate=["validate_required", "validate_min_length"]
    )

    def validate_email(self, value: str) -> str | None:
        if "@" not in value:
            return "Invalid email address"
        return None

    def validate_required(self, value: str) -> str | None:
        if not value:
            return "This field is required"
        return None

    def validate_min_length(self, value: str) -> str | None:
        if len(value) < 8:
            return "Minimum 8 characters"
        return None
```

Check `self.is_valid` and `self.validation_error_messages` for form state.

## Form with Conditional Fields

Use `visible=` to show/hide form fields conditionally:

```python
@widget(layout="form")
class ConditionalForm(Widget):
    _account_type: Variable[str] = new("personal")

    type_selector: QComboBox = new(label="Account Type:")

    # Only show for business accounts
    company_name: QLineEdit = new(
        label="Company:",
        visible="{_account_type == 'business'}"
    )
    tax_id: QLineEdit = new(
        label="Tax ID:",
        visible="{_account_type == 'business'}"
    )

    def __setup__(self) -> None:
        self.type_selector.addItems(["personal", "business"])
        self.type_selector.currentTextChanged.connect(
            lambda t: setattr(self._account_type, 'value', t)
        )
```

## Form Row Spanning

For widgets that should span the full width (no label):

```python
@widget(layout="form")
class FormWithSpanning(Widget):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")

    # Full-width section header (no label= means full span)
    header: QLabel = new("Additional Information")

    notes: QTextEdit = new(label="Notes:")
```

## Password Fields

Use `echoMode` for password entry:

```python
from PySide6.QtWidgets import QLineEdit

@widget(layout="form")
class LoginForm(Widget):
    _username: Variable[str, QLineEdit] = new("")(label="Username:")
    _password: Variable[str, QLineEdit] = new("")(
        label="Password:",
        echoMode=QLineEdit.EchoMode.Password
    )
```

## Form with Submit Button

Complete form with submission handling:

```python
from PySide6.QtWidgets import QLineEdit, QPushButton
from qtpie import Variable, Widget, new, widget

@widget(layout="form")
class ContactForm(Widget):
    _name: Variable[str, QLineEdit] = new("")(label="Name:")
    _email: Variable[str, QLineEdit] = new("")(label="Email:")
    _message: Variable[str, QTextEdit] = new("")(label="Message:")

    # Submit button without label (full width)
    submit_btn: QPushButton = new("Submit", clicked="on_submit")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_email", "email", lambda v: None if "@" in v else "Invalid")

    def on_submit(self) -> None:
        if not self.is_valid:
            print("Form has errors:", self.validation_error_messages)
            return

        print(f"Submitting: {self._name.value}, {self._email.value}")
```

## Translated Form Labels

Use `t()` for internationalized forms:

```python
from qtpie import t

@widget(layout="form")
class TranslatedForm(Widget):
    name: QLineEdit = new(label=t("Name:"))
    email: QLineEdit = new(label=t("Email:"))
    submit: QPushButton = new(t("Submit"))
```

## Form Layout Margins

Control form spacing with `margins=`:

```python
@widget(layout="form", margins=20)
class SpacedForm(Widget):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")

# Or specify each side: (left, top, right, bottom)
@widget(layout="form", margins=(10, 20, 10, 20))
class CustomMarginsForm(Widget):
    name: QLineEdit = new(label="Name:")
```

## Best Practices

1. **Use `label=` for all form fields** - Keeps labels and widgets paired
2. **Use `Variable[T, W]` for reactive forms** - Automatic two-way binding
3. **Add validation early** - Use `validate=` parameter or `add_validator()`
4. **Use record types for complex forms** - `Widget[T]` with dataclasses
5. **Group related fields** - Use section headers (QLabel without label=)
6. **Handle dirty state** - Check `self.view_model.is_dirty` before discarding

## See Also

- [Variables](../state/variables.md) - Reactive state management
- [Records](../data/records.md) - Binding to dataclasses
- [Validation](../data/validation.md) - Form validation
- [Dirty Tracking](../data/dirty-tracking.md) - Unsaved changes detection
