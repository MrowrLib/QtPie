# Documentation Proposal: Dirty Tracking

## Priority

**HIGH** - Core form/data-editing feature that's critical for save button UX and data management workflows.

---

## Files to Add/Update

### Primary File (Create New)

**`docs/data/dirty-tracking.md`** - Comprehensive guide to dirty tracking feature

### Secondary Updates

1. **`docs/index.md`** - Add dirty tracking to "Built-in Validation & Dirty Tracking" example (currently shows it but could be clearer)
2. **`docs/data/records.md`** - Add section on dirty tracking with records (specifically `record.field` naming in `dirty_fields`)
3. **`docs/reference/classes/widget.md`** - Document dirty tracking API methods and properties

---

## Suggested Nav Location

Already correctly placed in `mkdocs.yml`:

```yaml
nav:
  - Data & Forms:
      - Record Widgets: data/records.md
      - Lists & Dicts: data/lists-dicts.md
      - Validation: data/validation.md
      - Dirty Tracking: data/dirty-tracking.md  # ← Here
```

This placement makes sense because dirty tracking is primarily used in data/form contexts.

---

## Content Outline

### 1. Introduction
- What is dirty tracking and why it matters
- Common use cases: save buttons, unsaved changes warnings, form reset functionality
- Brief mention that it works with both `Variable[T]` and `Widget[T]` record types

### 2. Basic Usage

#### 2.1 Checking Dirty State
- `is_dirty` property returns `Observable[bool]`
- `is_dirty.get()` for current value
- `dirty_fields` property returns `set[str]` of changed field names

#### 2.2 Resetting Dirty State
- `reset_dirty()` method
- Treats current values as new baseline
- Use case: after successful save operation

### 3. Reactive Bindings
- Using `is_dirty` in `enabled=` bindings for buttons
- Using `is_dirty` in `visible=` bindings for warnings
- Combining with validation: `enabled="{is_valid and is_dirty}"`

### 4. Lifecycle Hook: `on_dirty_changed`
- Fires only on state transitions (clean ↔ dirty)
- Does NOT fire on every field change when already dirty
- Signature: `def on_dirty_changed(self, is_dirty: bool) -> None`
- Use cases: logging, analytics, custom UI updates

### 5. Record Dirty Tracking
- How `Widget[T]` tracks both Variable changes and record field changes
- `dirty_fields` naming convention: `"record.field"` for record fields
- Example with dataclass record
- Combined tracking example (Variables + record fields)

### 6. Patterns & Best Practices

#### 6.1 Save Button Pattern
```python
_save_btn: QPushButton = new("Save", enabled="is_dirty")
```

#### 6.2 Unsaved Changes Warning
```python
_warning: QLabel = new("You have unsaved changes", visible="is_dirty")
```

#### 6.3 Save and Reset Pattern
```python
def save(self):
    # Persist data...
    self.reset_dirty()  # Mark as clean after save
```

#### 6.4 Revert Changes Pattern
```python
def revert(self):
    # Restore from original values
    self._name.value = self._original_name
    self.reset_dirty()
```

### 7. Advanced Topics

#### 7.1 Programmatic Dirty Checks
- Checking specific fields: `"_name" in self.dirty_fields`
- Iterating dirty fields for custom logic

#### 7.2 Initial State Management
- Dirty tracking starts from initial `new()` values
- How `reset_dirty()` updates the baseline
- Considerations for dynamically loaded data

#### 7.3 Combining with Validation
- Common pattern: `enabled="{is_valid and is_dirty}"`
- Preventing saves when invalid OR clean
- Example combining both features

### 8. API Reference (Brief)
- `is_dirty: Observable[bool]` - Reactive dirty state
- `dirty_fields: set[str]` - Set of changed field names
- `reset_dirty() -> None` - Reset to clean state
- `on_dirty_changed(is_dirty: bool) -> None` - Optional lifecycle hook

### 9. Comparison with Other Frameworks
- Brief note on similarity to form libraries in web frameworks
- Angular forms: pristine/dirty
- React Hook Form: isDirty
- Position QtPie as bringing these patterns to Qt

---

## Code Examples Needed

### Example 1: Basic Save Button
```python
@widget
class UserForm(Widget):
    _name: Variable[str] = new("")
    _email: Variable[str] = new("")
    _save_btn: QPushButton = new("Save", enabled="is_dirty")

    def on_save(self):
        # Save logic...
        self.reset_dirty()
```

### Example 2: Unsaved Changes Warning
```python
@widget
class DocumentEditor(Widget):
    _content: Variable[str] = new("")
    _warning: QLabel = new(
        "⚠ Unsaved changes",
        visible="is_dirty",
        classes=["warning"]
    )
```

### Example 3: Lifecycle Hook
```python
@widget
class TrackedForm(Widget):
    _name: Variable[str] = new("")

    dirty_log: list[bool] = []

    def on_dirty_changed(self, is_dirty: bool) -> None:
        self.dirty_log.append(is_dirty)  # Only state transitions
        print(f"Form {'dirty' if is_dirty else 'clean'}")
```

### Example 4: Record Dirty Tracking
```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    _notes: Variable[str] = new("")  # Variable field
    name: QLineEdit = new()          # Record field
    age: QLineEdit = new()           # Record field

w = PersonEditor()
w._notes.value = "Updated notes"
w.record.name = "Alice"

# dirty_fields contains both:
assert w.dirty_fields == {"_notes", "record.name"}
```

### Example 5: Combined with Validation
```python
@widget
class ValidatedForm(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    _save_btn: QPushButton = new(
        "Save",
        enabled="{is_valid and is_dirty}",  # Both conditions
        clicked="on_save"
    )

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

    def on_save(self):
        # Only called when valid AND dirty
        save_to_database(self._name.value, self._age.value)
        self.reset_dirty()
```

### Example 6: Multiple Field Tracking
```python
@widget
class MultiFieldForm(Widget):
    _first_name: Variable[str] = new("")
    _last_name: Variable[str] = new("")
    _email: Variable[str] = new("")

    def check_what_changed(self):
        if "_first_name" in self.dirty_fields:
            print("First name changed")
        if "_last_name" in self.dirty_fields:
            print("Last name changed")
        if "_email" in self.dirty_fields:
            print("Email changed")
```

### Example 7: Revert Pattern
```python
@widget
class RevertableForm(Widget):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    _save_btn: QPushButton = new("Save", enabled="is_dirty", clicked="on_save")
    _revert_btn: QPushButton = new("Revert", enabled="is_dirty", clicked="on_revert")

    _original_data: dict[str, Any] = {}

    def __setup__(self) -> None:
        # Store initial values
        self._original_data = {
            "name": self._name.value,
            "age": self._age.value
        }

    def on_save(self):
        # Update baseline after save
        self._original_data["name"] = self._name.value
        self._original_data["age"] = self._age.value
        self.reset_dirty()

    def on_revert(self):
        # Restore from baseline
        self._name.value = self._original_data["name"]
        self._age.value = self._original_data["age"]
        # Dirty state auto-clears when values match baseline
```

---

## Cross-References

### Internal Links

1. **From Dirty Tracking page:**
   - Link to [Validation](validation.md) - "Combine dirty tracking with validation"
   - Link to [Record Widgets](records.md) - "Using dirty tracking with Widget[T]"
   - Link to [Variables](../state/variables.md) - "Understanding Variable[T]"
   - Link to [Property Bindings](../state/property-bindings.md) - "Using is_dirty in enabled= and visible="
   - Link to [Widget reference](../reference/classes/widget.md) - "Full API reference"

2. **From other pages to Dirty Tracking:**
   - [data/validation.md] - Add note: "See [Dirty Tracking](dirty-tracking.md) for save button patterns"
   - [data/records.md] - Add section: "Record fields appear in dirty_fields as `record.field`" with link
   - [state/property-bindings.md] - Add example: "Use `enabled="is_dirty"` for save buttons" with link
   - [basics/widgets.md] - Mention dirty tracking in "Lifecycle Hooks" section
   - [start/concepts.md] - Add dirty tracking to "Built-in Features" section

### External Concepts

- Brief comparison to Angular forms (pristine/dirty)
- Brief comparison to React Hook Form (isDirty)
- Note similarity to Django forms' changed_data

---

## Notes & Considerations

### API Consistency Note
The test file shows `w.is_dirty.get()` (Observable pattern) while CLAUDE.md shows `self.view_model.is_dirty` (old API?). **Verify current API** before writing docs:
- Is it `self.is_dirty` or `self.view_model.is_dirty`?
- Test file also shows `w.dirty_fields` directly, CLAUDE.md shows both patterns

**Update**: Based on test file (authoritative source), the current API is:
- `widget.is_dirty` (Observable[bool])
- `widget.is_dirty.get()` (bool value)
- `widget.dirty_fields` (set[str])
- `widget.reset_dirty()` (method)

### Naming Convention Clarity
Emphasize the `"record.field"` naming in `dirty_fields` for record-bound widgets to avoid confusion.

### Hook Behavior Emphasis
Strongly emphasize that `on_dirty_changed` fires ONLY on transitions, not on every field change. This is a common source of confusion.

### Common Gotcha
Users might expect `reset_dirty()` to revert values - clarify it only resets the dirty state, not the actual values.

---

## Related Features to Mention

1. **Validation** - Natural pairing with dirty tracking for form UX
2. **Record Widgets** - How dirty tracking extends to `Widget[T]`
3. **Property Bindings** - Using `is_dirty` in `enabled=` and `visible=`
4. **Lifecycle Hooks** - `on_dirty_changed` is a lifecycle hook
5. **Observable Pattern** - `is_dirty` returns `Observable[bool]`

---

## Success Metrics

After reading this documentation, users should be able to:

1. Enable/disable save buttons based on dirty state
2. Show unsaved changes warnings
3. Implement save-and-reset patterns
4. Track which specific fields changed
5. Use `on_dirty_changed` hook appropriately
6. Understand dirty tracking with record types
7. Combine dirty tracking with validation
