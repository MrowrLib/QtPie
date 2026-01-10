# Documentation Proposal: View Model

## Priority

**High** - The view model is a core architectural feature that enables proper separation of concerns and testable code patterns. It's essential for understanding how to write maintainable QtPie applications.

## Files to Add/Update

### New Files

1. **`docs/guides/view-model.md`** - Main guide for view model usage
2. **`docs/patterns/mvvm.md`** - Advanced MVVM patterns with QtPie

### Update Files

1. **`docs/index.md`** - Add view model mention in "Key Features" section
2. **`docs/start/concepts.md`** - Add view model to core concepts
3. **`docs/reference/classes/widget.md`** - Document `view_model` property API
4. **`docs/reference/classes/window.md`** - Document `view_model` property API (inherits from Widget)
5. **`mkdocs.yml`** - Add new pages to navigation

## Suggested Nav Location

### Option 1: As a Guide (Recommended)

```yaml
nav:
  - Guides:
      - Windows & Menus: guides/windows-menus.md
      - Form Layouts: guides/forms.md
      - Grid Layouts: guides/grids.md
      - View Model: guides/view-model.md  # NEW
      - Translations: guides/translations.md
      - App & Entry Points: guides/app.md
      - Async: guides/async.md
      - Testing: guides/testing.md
```

### Option 2: As an Advanced Pattern

```yaml
nav:
  - Patterns:  # NEW SECTION
      - MVVM Architecture: patterns/mvvm.md  # NEW (includes view model)
```

**Recommendation:** Option 1 + Option 2. Create the guide first for practical usage, then add the patterns section for advanced architectural discussion.

## Content Outline

### `docs/guides/view-model.md`

```markdown
# View Model

## What Is It?

- Automatic ViewModel instance containing all Variable fields
- Enables separation of UI (Widget) from state (ViewModel)
- Same Variable instances, different access path
- Useful for testing, composition, and MVVM patterns

## Basic Usage

- Accessing `self._qtpie.view_model` vs direct field access
- When to use view_model vs direct Variable access

## Same Instance Sharing

- Variables are shared, not copied
- Changes via either path are immediately visible
- Performance: zero overhead (same objects)

## Use Cases

### Testing
- Test view model logic without creating Qt widgets
- Pass view model to business logic functions

### Composition
- Pass view model to child widgets that need state but not UI
- Build reusable state containers

### Separation of Concerns
- Keep UI logic in Widget methods
- Keep state manipulation in separate functions that take view_model

## Working with Bindings

- View model Variables work with bind() just like widget Variables
- Use in format expressions: {view_model._field}

## Comparison to Direct Access

Table showing:
- `widget._field` vs `widget._qtpie.view_model._field`
- When to prefer each approach

## Common Patterns

- View model as DTO (Data Transfer Object)
- View model for form state
- View model for testing

## Limitations

- Only includes Variable fields (not QWidget fields)
- Read-only access to view model container (can't reassign variables)
```

### `docs/patterns/mvvm.md`

```markdown
# MVVM Architecture with QtPie

## Overview

QtPie's view model enables Model-View-ViewModel patterns naturally.

## The Three Layers

### Model
- Your domain/business objects (dataclasses, ORM models, etc.)
- Independent of Qt

### ViewModel (QtPie's view_model)
- Mediates between Model and View
- Contains presentation state as Variables
- Validation, dirty tracking, computed properties

### View (QtPie Widget)
- Pure UI: QWidgets, layouts, styling
- Binds to ViewModel Variables
- Delegates actions to ViewModel or controllers

## Complete Example

Full working example showing:
- Model: dataclass
- ViewModel: Widget[T] with view_model
- View: Widget bindings
- Controller/Service layer

## Testing Strategy

- Unit test Models (pure Python)
- Unit test ViewModel logic (minimal Qt)
- Integration test full Widget (with Qt)

## When to Use MVVM

- Complex business logic
- Multiple views of same data
- Testability requirements
- Team with separate UI/logic developers
```

### Update to `docs/start/concepts.md`

Add section:

```markdown
## View Model

Every Widget automatically gets a `view_model` property containing all Variable fields. This enables:

- Separation of UI from state
- Testing without Qt widgets
- MVVM patterns
- Composition patterns

The view model shares the same Variable instances—changes via either path are instantly visible.

[Learn more about view models →](../guides/view-model.md)
```

### Update to `docs/index.md`

Add to "Key Features":

```markdown
### View Model

Automatic separation of state from UI. Every widget gets a `view_model` property containing all Variables.

```python
# Access state via view_model
self._qtpie.view_model._name.value = "Alice"

# Or directly on widget
self._name.value = "Alice"

# Same Variable, both approaches work!
```

Perfect for testing, MVVM patterns, and separation of concerns.
```

## Code Examples Needed

### Basic Access Pattern

```python
from PySide6.QtWidgets import QLabel, QLineEdit
from qtpie import Widget, Variable, new, widget

@widget
class PersonForm(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)
    name_input: QLineEdit = new()
    age_label: QLabel = new(bind="Age: {_age}")

w = PersonForm()

# Direct access (typical)
w._name.value = "Alice"

# Via view_model (for separation)
w._qtpie.view_model._name.value = "Bob"

# Both work, same Variable instance
assert w._name is w._qtpie.view_model._name
```

### Testing Example

```python
def update_person_name(view_model, new_name: str) -> None:
    """Business logic function - no Qt dependency"""
    view_model._name.value = new_name.strip().title()

def test_update_person_name():
    """Test business logic without creating widgets"""
    widget = PersonForm()
    view_model = widget._qtpie.view_model

    update_person_name(view_model, "  alice  ")

    assert view_model._name.value == "Alice"
```

### Composition Example

```python
@widget
class UserProfile(Widget):
    """Child widget that only needs state, not parent UI"""
    def __init__(self, user_data):
        super().__init__()
        self._user_view_model = user_data  # Pass view_model from parent

        # Bind to parent's view model
        self.name_label: QLabel = new(bind="{_user_view_model._name}")

@widget
class MainWindow(Window):
    _username: Variable[str] = new("Alice")

    # Pass view_model to child
    profile: UserProfile = new(user_data="{_qtpie.view_model}")
```

### MVVM Pattern Example

```python
from dataclasses import dataclass

# MODEL
@dataclass
class User:
    id: int
    username: str
    email: str

# VIEWMODEL (using QtPie Widget)
@widget
class UserEditorViewModel(Widget[User]):
    # Variables for form state
    _username: Variable[str] = new("")
    _email: Variable[str] = new("")
    _is_saving: Variable[bool] = new(False)

    def __setup__(self) -> None:
        # Validation
        self.add_validator("_username", "required",
            lambda v: None if v else "Username required")
        self.add_validator("_email", "email",
            lambda v: None if "@" in v else "Invalid email")

    def save(self) -> None:
        if not self.is_valid:
            return
        self._is_saving.value = True
        # Save to backend...
        self._is_saving.value = False

# VIEW (pure UI bindings)
@widget
class UserEditorView(Widget):
    viewmodel: UserEditorViewModel  # Injected

    username_input: QLineEdit = new(bind="{viewmodel._username}")
    email_input: QLineEdit = new(bind="{viewmodel._email}")
    save_btn: QPushButton = new("Save",
        enabled="{viewmodel.is_valid and not viewmodel._is_saving}",
        clicked=lambda: self.viewmodel.save())
    errors: QLabel = new(bind="{', '.join(viewmodel.validation_error_messages)}")
```

### Binding with view_model

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _name: Variable[str] = new("User")

    # Bind using view_model path
    status: QLabel = new(bind="{view_model._name} has {view_model._count} items")

    def __setup__(self) -> None:
        # Programmatic binding to view_model
        from qtpie import bind
        bind(self._qtpie.view_model._count).to(self.status, format="Count: {}")
```

### What's NOT in view_model

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")      # ✓ In view_model
    _count: Variable[int] = new(0)      # ✓ In view_model
    label: QLabel = new("Hello")        # ✗ NOT in view_model (QWidget)
    button: QPushButton = new("Click")  # ✗ NOT in view_model (QWidget)

w = MyWidget()
w._qtpie.view_model._name  # ✓ Works
w._qtpie.view_model._count  # ✓ Works
w._qtpie.view_model.label  # ✗ AttributeError
w._qtpie.view_model.button  # ✗ AttributeError
```

## Cross-References

### Internal Links

- [Variables](../state/variables.md) - Understanding Variable[T]
- [Bindings](../state/bindings.md) - Using Variables with bind()
- [Record Widgets](../data/records.md) - Widget[T] and self.record
- [Validation](../data/validation.md) - Validators work with view_model
- [Dirty Tracking](../data/dirty-tracking.md) - is_dirty works with view_model
- [Testing Guide](../guides/testing.md) - Testing with view_model
- [Widget Class Reference](../reference/classes/widget.md) - `view_model` property API

### External Concepts

- MVVM Pattern explanation
- Separation of Concerns principle
- Dependency Injection pattern
- Data Transfer Objects (DTOs)

## API Reference Updates

### In `docs/reference/classes/widget.md`

Add property documentation:

```markdown
## Properties

### view_model

**Type:** `object` (dynamic type containing all Widget Variables)

**Access:** `self._qtpie.view_model`

An automatically generated object containing references to all `Variable[T]` fields declared on the widget. Regular QWidget fields are not included.

**Usage:**

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

w = MyWidget()

# Access via view_model
w._qtpie.view_model._name.value = "Alice"
w._qtpie.view_model._count.value = 42
```

**Notes:**

- Variables are shared, not copied—changes via either path are visible on both
- Useful for MVVM patterns, testing, and composition
- View model is created lazily on first access
- Type inference: pyright knows the structure based on class definition

**See Also:**

- [View Model Guide](../../guides/view-model.md)
- [MVVM Patterns](../../patterns/mvvm.md)
```

## Common Questions to Address

1. **Why use view_model instead of direct access?**
   - Separation of concerns
   - Testability without Qt
   - Pass to functions that shouldn't know about Widget
   - MVVM architecture

2. **Is there a performance cost?**
   - No—same Variable instances, zero overhead

3. **Can I modify the view_model structure?**
   - No—it's auto-generated from Variable fields
   - Add/remove Variables on Widget class, view_model reflects it

4. **Does view_model include nested widgets?**
   - No—only top-level Variable fields
   - Nested widget's Variables are on their own view_model

5. **How does this relate to Widget[T] and self.record?**
   - self.record is for external data (dataclasses)
   - view_model is for internal widget state (Variables)
   - Can use both together

6. **Can I access view_model in bindings?**
   - Yes: `bind="{view_model._field}"`
   - Equivalent to `bind="{_field}"` but more explicit

## Documentation Anti-Patterns to Avoid

1. **Don't call it a "feature"**—it's an architectural pattern/access path
2. **Don't over-promote it**—direct access is fine for simple cases
3. **Don't make it seem required**—it's opt-in for those who need it
4. **Don't compare to other frameworks' ViewModels** without context (they differ)
5. **Don't show only view_model examples**—show when to use each approach

## Related Features to Cross-Link

- Validation (validators work on Variables regardless of access path)
- Dirty tracking (self.is_dirty works with view_model changes)
- Record types (Widget[T] for external data vs view_model for internal state)
- Composition patterns (pass view_model to child widgets)
- Testing utilities (test view_model without Qt event loop)

## Success Metrics

Users should understand:

1. What view_model is and when to use it
2. That it's the same Variables, not a copy
3. How it enables testing and MVVM patterns
4. When direct access is simpler and preferred
5. How to combine view_model with Widget[T] record types
