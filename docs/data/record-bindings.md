# Record Field Bindings

When using `Widget[T]` with a dataclass, widget fields automatically bind to record properties. This enables declarative form editing with minimal configuration.

## Auto-Binding by Name

Fields with matching names bind automatically:

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

### Underscore Stripping

Leading underscores are stripped for matching:

```python
@widget(record=Person())
class PersonEditor(Widget[Person]):
    _name: QLineEdit = new()  # Binds to record.name (underscore stripped)
    _age: QSpinBox = new()    # Binds to record.age
```

## Two-Way Binding

Bindings are bidirectional:

```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()

editor = PersonEditor()

# Record → Widget
editor.record.name = "Bob"
# Widget now shows "Bob"

# Widget → Record
editor.name.setText("Charlie")
print(editor.record.name)  # "Charlie"
```

## Explicit Binding

Use `bind=` to map a widget to a different field:

```python
@dataclass
class User:
    email: str = ""
    username: str = ""

@widget(record=User())
class UserEditor(Widget[User]):
    # Field name doesn't match record property - use bind=
    email_input: QLineEdit = new(bind="email")
    user_field: QLineEdit = new(bind="username")
```

## Disabling Auto-Binding

Use `auto_bind=False` to prevent automatic name matching:

```python
@widget(record=Person(), auto_bind=False)
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Won't auto-bind
    age_field: QSpinBox = new(bind="age")  # Explicit still works
```

## Format String Binding

Combine multiple fields in a single widget:

```python
@widget(record=Person("Alice", 30))
class PersonView(Widget[Person]):
    summary: QLabel = new(bind="{name}, age {age}")
    # Shows: "Alice, age 30"
```

### Mixing Record and Widget Attributes

```python
@widget(record=Person("Alice", 30))
class PersonView(Widget[Person]):
    title: str = "Profile"
    display: QLabel = new(bind="{title}: {name}")
    # Shows: "Profile: Alice"
```

## Optional Chaining

Use `?.` for safe access to nullable nested fields:

```python
@dataclass
class Address:
    city: str = ""

@dataclass
class Employee:
    name: str = ""
    address: Address | None = None

@widget(record=Employee("Bob", None))
class EmployeeEditor(Widget[Employee]):
    city: QLineEdit = new(bind="address?.city")
    # Shows empty string when address is None (no crash)
```

## Binding Resolution Order

When a field name could match multiple sources, resolution follows this priority:

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Widget attribute | `self.title` |
| 2 | Record field | `self.record.title` |
| 3 | Underscore widget attribute | `self._title` |

```python
@widget(record=Person("Alice", 30))
class Example(Widget[Person]):
    title: str = "Static Title"  # Widget attribute

    # {title} uses widget attribute, {name} uses record field
    display: QLabel = new(bind="{title}: {name}")
    # Shows: "Static Title: Alice"
```

## Variable Auto-Binding

Fields also auto-bind to widget-level Variables (not just records):

```python
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    count: QSpinBox = new()  # Auto-binds to _count

counter = Counter()
counter._count = 42
# Spin box now shows 42
```

## Supported Widget Types

| Widget Type | Bound Property | Two-Way |
|-------------|----------------|---------|
| `QLineEdit` | `text` | Yes |
| `QSpinBox` | `value` | Yes |
| `QDoubleSpinBox` | `value` | Yes |
| `QCheckBox` | `checked` | Yes |
| `QComboBox` | `currentText` | Yes |
| `QLabel` | `text` | No (display only) |

## Complete Example

```python
@dataclass
class Contact:
    name: str = ""
    email: str = ""
    age: int = 0
    subscribed: bool = False

@widget(record=Contact())
class ContactForm(Widget[Contact]):
    # Auto-bound fields
    name: QLineEdit = new(placeholderText="Name")
    email: QLineEdit = new(placeholderText="Email")
    age: QSpinBox = new(minimum=0, maximum=120)
    subscribed: QCheckBox = new(text="Subscribe to newsletter")

    # Display-only summary
    preview: QLabel = new(bind="{name} ({email})")

    # Submit button
    _submit: QPushButton = new("Save", clicked="save")

    def save(self) -> None:
        print(f"Saving: {self.record}")
```

## See Also

- [Variables](../state/variables.md) - Reactive state management
- [Bindings](../state/bindings.md) - Content bindings overview
- [Format Expressions](../state/format-expressions.md) - Expression syntax
