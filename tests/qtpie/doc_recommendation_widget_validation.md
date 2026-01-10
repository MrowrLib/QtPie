# Documentation Proposal: Widget Validation

## Priority

**High** - Validation is a core feature for form-heavy applications (one of QtPie's main use cases per `why-qtpie.md`). It's already implemented and tested but lacks user-facing documentation.

---

## Files to Add/Update

### New File: `docs/data/validation.md`

Primary validation documentation page covering the complete feature.

### Update: `docs/index.md`

Add validation to the "Built-in Validation & Dirty Tracking" example (currently shows basic usage but could be expanded).

### Update: `docs/reference/classes/variable.md`

Document Variable-level validation methods:
- `add_validator(name, fn)`
- `remove_validator(name)`
- `is_valid` property (Observable[bool])
- `validation_errors` property (dict[str, list[str]])
- `validation_error_messages` property (list[str])

### Update: `docs/reference/classes/widget.md`

Document Widget-level validation methods:
- `add_validator(field, name, fn)`
- `remove_validator(field, name)`
- `is_valid` property (Observable[bool])
- `validation_errors` property (dict[str, dict[str, list[str]]])
- `validation_error_messages` property (list[str])
- `on_valid_changed(is_valid)` lifecycle hook

### Update: `docs/reference/factories/new.md`

Document the `validate=` parameter for declarative validation.

---

## Suggested Nav Location

The nav already has this entry (line 72 in mkdocs.yml):

```yaml
- Data & Forms:
    - Record Widgets: data/records.md
    - Lists & Dicts: data/lists-dicts.md
    - Validation: data/validation.md  # ← This file should be created
    - Dirty Tracking: data/dirty-tracking.md
```

No nav changes needed - just create `docs/data/validation.md`.

---

## Content Outline: `docs/data/validation.md`

### 1. Introduction
- Brief overview: validation for form fields with reactive error tracking
- Common use case: disable submit button until form is valid

### 2. Quick Start
```python
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")
    _submit: QPushButton = new("Login", enabled="{is_valid}")

    def __setup__(self) -> None:
        self.add_validator("_username", "required", lambda v: None if v else "Username required")
        self.add_validator("_password", "min_len", lambda v: None if len(v) >= 8 else "Min 8 chars")
```

### 3. Validator Functions
- Signature: `(value: T) -> str | None`
- Return `None` for valid, error message string for invalid
- Runs on every value change (reactive)

### 4. Adding Validators

#### Imperative (in `__setup__`)
```python
self.add_validator("_field", "validator_name", validator_fn)
```

#### Declarative (with `validate=` parameter)
```python
# Single validator by method name
_name: Variable[str] = new("", validate="validate_name")

# Multiple validators
_email: Variable[str] = new("", validate=["validate_required", "validate_email"])

# Lambda/external function
_age: Variable[int] = new(0, validate=lambda v: None if v > 0 else "Must be positive")

# Named validators
_field: Variable[str] = new("", validate=[("custom", "validate_method")])

# Mixed
_field: Variable[str] = new("", validate=[
    "validate_required",
    external_fn,
    ("length", "validate_length")
])
```

### 5. Checking Validity

#### Widget-level
```python
if self.is_valid.get():  # Observable[bool]
    # Form is valid
```

#### Variable-level
```python
if self._name.is_valid.get():  # Observable[bool]
    # Field is valid
```

### 6. Accessing Errors

#### Flat list of all error messages
```python
self.validation_error_messages.get()  # ["Username required", "Min 8 chars"]
```

#### Structured errors
```python
self.validation_errors  # {
#   "_username": {"required": ["Username required"]},
#   "_password": {"min_len": ["Min 8 chars"]}
# }
```

### 7. Reactive Bindings
```python
# Display errors in label
_errors: QLabel = new(bind="{', '.join(validation_error_messages)}")

# Enable submit only when valid
_submit: QPushButton = new("Submit", enabled="{is_valid.get()}")

# Show/hide error messages
_error_panel: QWidget = new(visible="{not is_valid.get()}")
```

### 8. Lifecycle Hook: `on_valid_changed`
```python
@override
def on_valid_changed(self, is_valid: bool) -> None:
    """Called when validity state transitions (not on every validation)"""
    self._submit.setEnabled(is_valid)
    if not is_valid:
        self._status.setText("Please fix errors")
```

### 9. Removing Validators
```python
# Widget-level
self.remove_validator("_field", "validator_name")

# Variable-level
self._field.remove_validator("validator_name")
```

### 10. Record Validation
```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        # Validate record fields by property name
        self.add_validator("name", "required", lambda v: None if v else "Name required")
        self.add_validator("age", "positive", lambda v: None if v > 0 else "Must be positive")

        # Or validate entire record
        self._qtpie.record_state.add_validator(
            "complete",
            lambda p: None if p.name and p.age > 0 else "Incomplete"
        )
```

### 11. Combined Variable + Record Validation
```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _extra_field: Variable[str] = new("")

    def __setup__(self) -> None:
        # Variable validation
        self.add_validator("_extra_field", "required", lambda v: None if v else "Required")
        # Record validation
        self.add_validator("name", "required", lambda v: None if v else "Name required")

# Widget.is_valid aggregates both Variable and record validation
# Widget.validation_errors includes both:
# {
#   "_extra_field": {"required": [...]},
#   "name": {"required": [...]}
# }
```

### 12. Common Patterns

#### Email validation
```python
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(self, value: str) -> str | None:
    if not value:
        return "Email required"
    if not EMAIL_REGEX.match(value):
        return "Invalid email format"
    return None
```

#### Password strength
```python
def validate_password(self, value: str) -> str | None:
    if len(value) < 8:
        return "Min 8 characters"
    if not any(c.isdigit() for c in value):
        return "Must contain a number"
    if not any(c.isupper() for c in value):
        return "Must contain uppercase"
    return None
```

#### Conditional validation
```python
def validate_zip_code(self, value: str) -> str | None:
    if self._country.value == "US":
        if not value or not re.match(r'^\d{5}(-\d{4})?$', value):
            return "Invalid US ZIP code"
    return None
```

---

## Code Examples Needed

### Complete Working Example: Registration Form
```python
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton
from qtpie import Widget, Variable, new, widget, entrypoint
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

@entrypoint
@widget
class RegistrationForm(Widget):
    # Fields with declarative validation
    _username: Variable[str, QLineEdit] = new(
        "",
        validate="validate_username"
    )(placeholderText="Username")

    _email: Variable[str, QLineEdit] = new(
        "",
        validate=["validate_required", "validate_email_format"]
    )(placeholderText="Email")

    _password: Variable[str, QLineEdit] = new(
        "",
        validate="validate_password"
    )(echoMode=QLineEdit.EchoMode.Password, placeholderText="Password")

    # Error display
    _error_label: QLabel = new(
        bind="{', '.join(validation_error_messages)}",
        visible="{not is_valid.get()}"
    )

    # Submit button (only enabled when valid)
    _submit: QPushButton = new(
        "Register",
        clicked="on_submit",
        enabled="{is_valid.get()}"
    )

    # Validators
    def validate_username(self, value: str) -> str | None:
        if not value:
            return "Username required"
        if len(value) < 3:
            return "Min 3 characters"
        return None

    def validate_required(self, value: str) -> str | None:
        return None if value else "This field is required"

    def validate_email_format(self, value: str) -> str | None:
        if value and not EMAIL_REGEX.match(value):
            return "Invalid email format"
        return None

    def validate_password(self, value: str) -> str | None:
        if not value:
            return "Password required"
        if len(value) < 8:
            return "Min 8 characters"
        if not any(c.isdigit() for c in value):
            return "Must contain a number"
        return None

    def on_submit(self) -> None:
        # This only runs when form is valid (button is disabled otherwise)
        print(f"Registering: {self._username.value}, {self._email.value}")

# Run: python registration.py
```

### Minimal Example: Single Field
```python
@widget
class SimpleForm(Widget):
    _name: Variable[str] = new("")
    _submit: QPushButton = new("Submit", enabled="{is_valid.get()}")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Name required")
```

### Example: Field-Level Error Display
```python
@widget
class FieldErrorsForm(Widget):
    _username: Variable[str, QLineEdit] = new("")(placeholderText="Username")
    _username_error: QLabel = new(
        bind="{', '.join(_username.validation_error_messages.get())}",
        visible="{not _username.is_valid.get()}"
    )

    _email: Variable[str, QLineEdit] = new("")(placeholderText="Email")
    _email_error: QLabel = new(
        bind="{', '.join(_email.validation_error_messages.get())}",
        visible="{not _email.is_valid.get()}"
    )

    def __setup__(self) -> None:
        self.add_validator("_username", "required", lambda v: None if v else "Username required")
        self.add_validator("_email", "required", lambda v: None if v else "Email required")
        self.add_validator("_email", "format", lambda v: None if "@" in v else "Invalid email")
```

---

## Cross-References

### Related Pages to Link To:
- [Variables](../state/variables.md) - Variable[T] basics
- [Bindings](../state/bindings.md) - Using validation state in bindings
- [Property Bindings](../state/property-bindings.md) - `enabled=` with validation
- [Record Widgets](../data/records.md) - Record validation
- [Dirty Tracking](../data/dirty-tracking.md) - Often used with validation
- [Widget Reference](../reference/classes/widget.md) - Full Widget API
- [Variable Reference](../reference/classes/variable.md) - Full Variable API

### Pages That Should Link Back:
- `docs/index.md` - Validation mentioned in features
- `docs/why-qtpie.md` - Validation in feature comparison table
- `docs/state/bindings.md` - Example using `is_valid` in bindings
- `docs/state/property-bindings.md` - Example using validation for `enabled=`
- `docs/data/records.md` - Record validation example
- `docs/data/dirty-tracking.md` - Combined dirty + validation example
- `docs/guides/forms.md` - Form validation best practices

### Related Concepts to Explain:
- Observable[bool] nature of `is_valid` (link to observant docs if available)
- Lifecycle hooks (link to lifecycle docs)
- `__setup__` method (explain when to use vs declarative)
- Difference between Widget-level and Variable-level validation

---

## API Reference Requirements

### `docs/reference/classes/variable.md`

Add section:

**Validation**

| Property/Method | Type | Description |
|----------------|------|-------------|
| `is_valid` | `Observable[bool]` | Reactive validity state |
| `validation_errors` | `dict[str, list[str]]` | Errors by validator name |
| `validation_error_messages` | `list[str]` | Flat list of error messages |
| `add_validator(name, fn)` | `None` | Add named validator |
| `remove_validator(name)` | `None` | Remove validator by name |

### `docs/reference/classes/widget.md`

Add section:

**Validation**

| Property/Method | Type | Description |
|----------------|------|-------------|
| `is_valid` | `Observable[bool]` | Aggregated validity (all fields + record) |
| `validation_errors` | `dict[str, dict[str, list[str]]]` | Errors by field and validator |
| `validation_error_messages` | `list[str]` | Flat list of all error messages |
| `add_validator(field, name, fn)` | `None` | Add validator to field/record property |
| `remove_validator(field, name)` | `None` | Remove validator |
| `on_valid_changed(is_valid)` | `None` | Lifecycle hook (override in subclass) |

### `docs/reference/factories/new.md`

Add parameter documentation:

**`validate` parameter**

Type: `str | Callable | list[str | Callable | tuple[str, str | Callable]]`

Declaratively add validators to Variable fields.

- `str` - Method name on widget (e.g., `"validate_name"`)
- `Callable` - External validator function
- `tuple[str, ...]` - Named validator: `("name", "method")` or `("name", callable)`
- `list` - Multiple validators (processed in order)

Examples:
```python
# Single validator method
_name: Variable[str] = new("", validate="validate_name")

# Multiple validators
_email: Variable[str] = new("", validate=["validate_required", "validate_email"])

# Lambda
_age: Variable[int] = new(0, validate=lambda v: None if v > 0 else "Positive only")

# Mixed
_field: Variable[str] = new("", validate=[
    "validate_required",
    external_validator,
    ("length", "validate_length")
])
```

---

## Testing Coverage

The test file `tests/qtpie/test_widget_validation.md` covers:
- ✅ Variable-level validation
- ✅ Widget-level aggregated validation
- ✅ Declarative `validate=` parameter
- ✅ Record validation
- ✅ Combined Variable + record validation
- ✅ `on_valid_changed` lifecycle hook
- ✅ Reactive `is_valid` in bindings

**All documented features are tested.** No additional tests needed before documentation.

---

## Notes

### Terminology Consistency
- Use "validator" (not "validation function" or "validator function")
- Use "field" (not "property" or "attribute") when referring to widget fields
- Use "record property" specifically for record types

### Common User Questions to Address
1. **When do validators run?** - On every value change (reactive)
2. **Can I validate multiple fields together?** - Use record-level validation
3. **How do I display errors per-field vs form-level?** - Show both patterns
4. **What's the difference between Widget and Variable validation?** - Clear explanation needed
5. **Can I re-validate manually?** - No need, it's automatic/reactive

### Advanced Topics (Lower Priority)
- Async validators (if supported)
- Server-side validation integration
- Custom error display widgets
- Validation groups/steps

### Implementation Notes from Test File
- Validators return `str | None` (None = valid)
- Widget validation aggregates all Variable fields + record
- `on_valid_changed` only fires on state transitions (not every validation run)
- Record validation uses `self._qtpie.record_state.add_validator()`
- `validate=` parameter supports multiple formats for flexibility
