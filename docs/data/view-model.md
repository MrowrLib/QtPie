# View Model

Every widget automatically gets a `view_model` that contains all its Variable fields. This enables separation of concerns, testing, and MVVM patterns.

## What Is It?

The view model is an automatically generated object containing references to all `Variable[T]` fields on your widget. It provides an alternative access path to the same Variable instances.

```python
from qtpie import Widget, Variable, new, widget

@widget
class PersonForm(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)
    _label: QLabel = new("Hello")

form = PersonForm()

# Access via view_model
form.view_model._name.value = "Alice"
form.view_model._age.value = 30

# Same Variables - changes are shared
assert form._name.value == "Alice"
assert form._age.value == 30
```

Only `Variable` fields are included - QWidget fields like `_label` are not part of the view model.

## Same Instance

The view model Variables are the **exact same instances** as the widget's Variables:

```python
form = PersonForm()

# Same object
assert form.view_model._name is form._name

# Changes via either path are visible
form.view_model._name.value = "Bob"
assert form._name.value == "Bob"

form._name.value = "Charlie"
assert form.view_model._name.value == "Charlie"
```

## When to Use

### Direct Access (Most Cases)

For simple widgets, access Variables directly:

```python
def on_save(self) -> None:
    print(f"Name: {self._name.value}")
    self._name.value = ""
```

### View Model (Advanced)

Use view_model for:

- **Testing** - Pass to functions without widget dependency
- **MVVM patterns** - Separate UI from state logic
- **Composition** - Share state with child components

## Testing Example

```python
def process_name(view_model) -> None:
    """Business logic - no Qt dependency"""
    view_model._name.value = view_model._name.value.strip().title()

def test_process_name():
    form = PersonForm()
    form._name.value = "  alice  "

    process_name(form.view_model)

    assert form._name.value == "Alice"
```

## Dirty Tracking

The view model provides dirty tracking properties:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    _save_btn: QPushButton = new(
        "Save",
        enabled="{view_model.is_dirty}",
        clicked="save"
    )

    def save(self) -> None:
        if self.view_model.is_dirty:
            print(f"Changed: {self.view_model.dirty_fields}")
            # ... save logic
            self.view_model.reset_dirty()
```

## Validation

Validators also work through the view model:

```python
@widget
class Form(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required",
            lambda v: None if v else "Name required")

    def check(self) -> None:
        if self.view_model.is_valid:
            print("Form is valid")
        else:
            print(self.view_model.validation_error_messages)
```

## What's Included

| Field Type | In view_model? |
|------------|----------------|
| `Variable[T]` | Yes |
| `Variable[T, W]` | Yes |
| `QLabel`, `QPushButton`, etc. | No |
| `list[QLabel]` (repeater) | No |

## See Also

- [Variables](../state/variables.md) - Reactive state
- [Records](records.md) - Widget[T] for external data
- [Validation](validation.md) - Form validation
- [Dirty Tracking](dirty-tracking.md) - Change tracking
