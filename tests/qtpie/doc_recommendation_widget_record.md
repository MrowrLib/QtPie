# Documentation Proposal: Widget Record Types (`Widget[T]`)

## Priority
**HIGH** - This is a core feature that distinguishes QtPie from plain Qt. It enables the dataclass-to-UI pattern that's essential for form/CRUD apps.

---

## Files to Add/Update

### New File: `docs/data/records.md`
**Status:** Create new (nav already has placeholder at line 70)

**Purpose:** Comprehensive guide to using `Widget[T]` and `Window[T]` with record types.

### Update: `docs/start/concepts.md`
**Status:** Update existing (if it exists)

**Purpose:** Add "Record Types" to the key concepts overview with a brief intro and link to full guide.

### Update: `docs/index.md`
**Status:** Update existing

**Purpose:** The "Record Types" example in the index (lines 67-80) is good, but should link to the full guide. Add a line: "Learn more about [Record Types](data/records.md)".

### Update: `docs/reference/classes/widget.md`
**Status:** Update existing (if it exists)

**Purpose:** API reference documenting `Widget[T]`, `self.record`, `self.record_state`, and related properties.

---

## Suggested Nav Location

Already correct in `mkdocs.yml`:

```yaml
- Data & Forms:
    - Record Widgets: data/records.md  # Line 70
    - Lists & Dicts: data/lists-dicts.md
    - Validation: data/validation.md
    - Dirty Tracking: data/dirty-tracking.md
```

**Rationale:** "Record Widgets" is the first item in "Data & Forms" section, which makes sense as it's foundational for form-based UIs.

---

## Content Outline: `docs/data/records.md`

### 1. Introduction (What & Why)
- **What:** Bind entire dataclasses/objects to widgets using `Widget[T]`
- **Why:** Reduces boilerplate for form/CRUD apps, automatic field mapping, built-in dirty tracking
- **Quick example:** Simple Person editor

### 2. Basic Usage
- Declaring a `Widget[T]` with type parameter
- Two initialization patterns:
  - `@widget(record=...)` decorator parameter (preferred)
  - Setting `self.record` in `__setup__()` (for types without defaults)
- How field names auto-bind to record properties
- What `self.record` returns (ObservableProxy)

### 3. Accessing the Record
- **Direct access:** `self.record.name` (read/write, reactive)
- **Record state:** `self.record_state` (RecordVariable with `.is_dirty`, `.value`, `.observable`)
- Read vs write semantics
- Why direct assignment triggers reactivity

### 4. Field Auto-Binding
- Fields matching record property names auto-bind
- Supported widget types (QLineEdit, QSpinBox, QCheckBox, QComboBox, etc.)
- Override with explicit `bind=` if needed
- Example with mixed auto-bind + custom widgets

### 5. Working with Record State
- Accessing the underlying RecordVariable
- Using `.value` to get raw dataclass instance
- Using `.observable` to access ObservableProxy directly
- When to use which accessor

### 6. Dirty Tracking Integration
- Record fields participate in widget-level dirty tracking
- Checking `self.record_state.is_dirty`
- Using widget-level `self.view_model.is_dirty` and `self.view_model.dirty_fields`
- `on_dirty_changed(is_dirty: bool)` lifecycle hook
- Resetting dirty state with `self.view_model.reset_dirty()`

### 7. Combining Records with Variables
- Widgets can have both `Widget[T]` and independent `Variable` fields
- Use cases: UI-only state (loading spinners, tab selection, etc.)
- Example: PersonEditor with `_status: Variable[str]`

### 8. Complex Patterns
- **Nested records:** Record types with other dataclass fields
- **Reactive bindings:** Using record fields in `bind=` expressions
- **Validation:** Adding validators to record fields (link to validation docs)
- **Lists of records:** Using `Variable[list[T]]` with record types (link to lists-dicts docs)

### 9. Window[T] for Main Windows
- Same pattern works for `Window[T]`
- Example: Settings/preferences window
- When to use `Widget[T]` vs `Window[T]`

### 10. Common Patterns
- CRUD forms (create/read/update/delete)
- Master-detail views (list of records + editor)
- Multi-step wizards with shared state
- Settings/configuration panels

### 11. Tips & Gotchas
- **Type safety:** Use `record=` decorator param to avoid pyright errors about overriding `record` property
- **Immutability:** Record assignments create new instances (ObservableProxy semantics)
- **Widget types:** Not all Qt widgets auto-bind (custom handling needed for complex widgets)
- **Performance:** Record changes trigger reactive updates (avoid tight loops)

---

## Code Examples Needed

### Example 1: Basic Person Editor
```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLineEdit, QSpinBox
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

### Example 2: Setting Record in __setup__
```python
@dataclass
class Cat:
    name: str
    lives: int  # No default - can't instantiate with Person()

@widget
class CatEditor(Widget[Cat]):
    name: QLineEdit = new()
    lives: QSpinBox = new()

    def __setup__(self) -> None:
        self.record = Cat(name="Whiskers", lives=9)
```

### Example 3: Direct Record Access
```python
@widget(record=Person("Bob", 25))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()

    def on_save_clicked(self) -> None:
        # Read record fields
        print(f"Name: {self.record.name}")
        print(f"Age: {self.record.age}")

        # Write record fields (triggers reactivity)
        self.record.name = "Robert"
```

### Example 4: Using Record State
```python
@widget(record=Person("Charlie", 35))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()
    save_btn: QPushButton = new("Save", enabled="{record_state.is_dirty}")

    def on_save_clicked(self) -> None:
        if self.record_state.is_dirty.get():
            person = self.record_state.value  # Get raw dataclass
            save_to_database(person)
            self.view_model.reset_dirty()
```

### Example 5: Dirty Tracking Hook
```python
@widget(record=Person("Diana", 40))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()
    status_label: QLabel = new("No changes")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        if is_dirty:
            self.status_label.setText("Unsaved changes")
        else:
            self.status_label.setText("Saved")
```

### Example 6: Record + Variables
```python
@widget(record=Person("Eve", 45))
class PersonEditor(Widget[Person]):
    # Record fields
    name: QLineEdit = new()
    age: QSpinBox = new()

    # UI-only state
    _loading: Variable[bool] = new(False)
    _status_msg: Variable[str] = new("")

    loading_spinner: QLabel = new(visible="{_loading}")
    status_label: QLabel = new(bind="{_status_msg}")
```

### Example 7: Nested Records
```python
@dataclass
class Address:
    street: str = ""
    city: str = ""

@dataclass
class Employee:
    name: str = ""
    address: Address = field(default_factory=Address)

@widget(record=Employee("Frank", Address("123 Main St", "NYC")))
class EmployeeEditor(Widget[Employee]):
    name: QLineEdit = new()
    # For nested records, manual handling:
    address_editor: AddressEditor = new(record="_record.observable.address")
```

### Example 8: CRUD Form Pattern
```python
@widget
class PersonCRUD(Widget):
    _selected_person: Variable[Person | None] = new(None)

    # List view (left side)
    person_list: QListWidget = new()

    # Editor (right side)
    editor: PersonEditor = new(visible="{_selected_person is not None}")

    def on_person_selected(self, person: Person) -> None:
        self._selected_person.value = person
        self.editor.record = person  # Update editor's record

    def on_save_clicked(self) -> None:
        if self.editor.record_state.is_dirty.get():
            save_to_database(self.editor.record_state.value)
```

### Example 9: Window[T] for Settings
```python
@dataclass
class AppSettings:
    theme: str = "light"
    auto_save: bool = True
    font_size: int = 12

@window(title="Settings", record=AppSettings())
class SettingsWindow(Window[AppSettings]):
    theme: QComboBox = new()  # Auto-populated with themes
    auto_save: QCheckBox = new()
    font_size: QSpinBox = new()

    save_btn: QPushButton = new("Save", clicked="on_save")

    def on_save(self) -> None:
        save_settings(self.record_state.value)
```

---

## Cross-References

### Link FROM records.md TO:
- **[Dirty Tracking](dirty-tracking.md)** - Detailed dirty tracking docs
- **[Validation](validation.md)** - Adding validators to record fields
- **[Lists & Dicts](lists-dicts.md)** - Working with `Variable[list[Person]]`
- **[Variables](../state/variables.md)** - Understanding `Variable[T]` basics
- **[Bindings](../state/bindings.md)** - Using record fields in bind expressions
- **[Property Bindings](../state/property-bindings.md)** - `visible=`, `enabled=` with record state
- **[Window Reference](../reference/classes/window.md)** - `Window[T]` API details
- **[Widget Reference](../reference/classes/widget.md)** - `Widget[T]` API details

### Link TO records.md FROM:
- **docs/index.md** (line 80) - Add link after Record Types example
- **docs/start/concepts.md** - Add "Record Types" concept with link
- **docs/why-qtpie.md** - Already mentions it (line 113), add link
- **docs/data/validation.md** - Cross-ref for validating record fields
- **docs/data/dirty-tracking.md** - Cross-ref for record dirty tracking
- **docs/guides/forms.md** - Link to record types as best practice for forms
- **docs/reference/classes/widget.md** - Link from `Widget[T]` API docs
- **docs/reference/classes/window.md** - Link from `Window[T]` API docs

---

## Key Messages to Emphasize

1. **Use `record=` decorator param** - Preferred pattern for type safety (pyright compliance)
2. **Auto-binding is convention-driven** - Field names must match record properties
3. **ObservableProxy semantics** - Assignments trigger reactivity, reads return actual values
4. **Dirty tracking is automatic** - No manual setup needed
5. **Works with Window[T] too** - Same pattern for main windows
6. **Combines with other features** - Works alongside Variables, validation, bindings

---

## Testing Coverage Note

The test file `test_widget_record.md` provides excellent coverage of:
- Type parameter extraction
- Direct field access (read/write)
- Record state access
- Dirty tracking
- Combination with Variables
- `__setup__` initialization
- Decorator parameter initialization
- Explicit record declaration
- `on_dirty_changed` hook

All these behaviors should be documented with examples in the guide.

---

## Documentation Style Notes

- Use progressive complexity (simple examples first)
- Show both Widget[T] and Window[T] where applicable
- Include complete, runnable code snippets
- Use admonitions for tips/warnings
- Add "See also" boxes for cross-references
- Include a "Common Mistakes" section
- End with "Next Steps" pointing to validation and dirty tracking docs
