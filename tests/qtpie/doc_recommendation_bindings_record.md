# Documentation Proposal: Record Field Bindings

## Priority: HIGH

Record binding is a core QtPie feature that enables declarative form editing and data-driven UIs. Current documentation mentions it but lacks depth on the binding mechanics.

---

## Files to Add/Update

### 1. **NEW: `docs/data/record-bindings.md`**
   - Dedicated page for record field binding mechanics
   - Deep dive into auto-binding, explicit binding, resolution order
   - Belongs in "Data & Forms" section

### 2. **UPDATE: `docs/data/records.md`**
   - Currently covers `Widget[T]` basics
   - Should link to new `record-bindings.md` for binding details
   - Keep high-level overview, defer details to dedicated page

### 3. **UPDATE: `docs/state/bindings.md`**
   - Add cross-reference to record bindings
   - Clarify difference between Variable bindings and record bindings
   - Add "See Also" section pointing to record-bindings.md

### 4. **UPDATE: `docs/start/concepts.md`**
   - Add brief mention of record auto-binding in "Key Concepts"
   - Position as convention-over-configuration example

---

## Suggested Nav Location

```yaml
nav:
  - Data & Forms:
      - Record Widgets: data/records.md
      - Record Bindings: data/record-bindings.md  # NEW
      - Lists & Dicts: data/lists-dicts.md
      - Validation: data/validation.md
      - Dirty Tracking: data/dirty-tracking.md
```

**Rationale:** Place after `records.md` since users need to understand `Widget[T]` before diving into binding mechanics.

---

## Content Outline: `docs/data/record-bindings.md`

### Title: Record Field Bindings

### Introduction (2-3 paragraphs)
- What record bindings are (automatic two-way sync between widgets and dataclass fields)
- Why they matter (convention over configuration, reduce boilerplate)
- When to use them (forms, editors, data-driven UIs)

### 1. Auto-Binding by Name
- Default behavior: field names match record properties
- Leading underscore stripping (`_name` → `name`)
- Example: PersonEditor with name/age fields
- Diagram/table showing name resolution

### 2. Two-Way Binding
- Widget changes update record
- Record changes update widget
- Example: QLineEdit setText → record.name updated
- Note on supported widget types

### 3. Explicit Binding with `bind=`
- Override name-based matching
- Use case: different field names
- Example: `email_input: QLineEdit = new(bind="email")`
- Combining with format strings

### 4. Disabling Auto-Binding
- `@widget(auto_bind=False)` decorator parameter
- When to disable (custom logic, performance)
- Explicit `bind=` still works
- Example: mixed auto/manual binding

### 5. Variable Auto-Binding
- Widget fields auto-bind to widget-level Variables
- Example: `_count: Variable[int]` + `count: QSpinBox`
- Resolution priority (record vs Variable vs attribute)

### 6. Format String Binding
- Combine multiple fields in one widget
- Example: `bind="{name}, age {age}"`
- Reactive updates when any field changes
- Mixing record fields with widget attributes

### 7. Optional Chaining
- Safe access to nullable nested fields
- Syntax: `bind="address?.city"`
- Prevents crashes when field is None
- Example with nested dataclasses

### 8. Binding Resolution Order
- Priority: exact widget attribute > record field > underscore widget attribute
- Examples showing each priority level
- Common gotchas (e.g., `title` attribute shadowing record field)

### 9. Supported Widget Types
- Table of widget types and their binding behavior
- QLineEdit (text), QSpinBox (value), QLabel (text), etc.
- Custom widget support (via signal/property conventions)

### 10. Advanced Patterns
- Nested record editing
- List of records with repeaters
- Conditional bindings (visible/enabled based on record state)

### 11. Troubleshooting
- Widget not updating? (Check name matching)
- Record not updating? (Check two-way widget support)
- Binding conflicts (multiple widgets to same field)
- Type mismatches

### 12. See Also
- [Record Widgets](records.md) - Basic `Widget[T]` usage
- [Format Expressions](../state/format-expressions.md) - Complex binding syntax
- [Validation](validation.md) - Validate record fields
- [Dirty Tracking](dirty-tracking.md) - Track record changes

---

## Code Examples Needed

### Example 1: Basic Auto-Binding
```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person())
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QSpinBox = new()    # Auto-binds to record.age
```

### Example 2: Two-Way Binding
```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()

editor = PersonEditor()
editor.name.setText("Bob")
print(editor.record.name)  # "Bob" - automatically updated
```

### Example 3: Explicit Binding
```python
@dataclass
class User:
    email: str = ""

@widget(record=User())
class UserEditor(Widget[User]):
    email_input: QLineEdit = new(bind="email")  # Explicit binding
```

### Example 4: Disabling Auto-Binding
```python
@widget(record=Person(), auto_bind=False)
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()              # Won't auto-bind
    age_field: QSpinBox = new(bind="age")  # Explicit still works
```

### Example 5: Format String Binding
```python
@widget(record=Person("Alice", 30))
class PersonView(Widget[Person]):
    summary: QLabel = new(bind="{name}, age {age}")
    # Automatically shows "Alice, age 30"
```

### Example 6: Optional Chaining
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
    city: QLineEdit = new(bind="address?.city")  # Safe even when address=None
```

### Example 7: Resolution Priority
```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    # Widget attribute 'title' takes priority over potential record.title
    title: str = "Person Editor"
    display: QLabel = new(bind="{title}")  # Uses widget.title, not record.title
```

### Example 8: Variable Auto-Binding
```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    count: QSpinBox = new()  # Auto-binds to _count Variable
```

---

## Cross-References

### From Other Pages

**From `docs/data/records.md`:**
> For details on how field bindings work, see [Record Bindings](record-bindings.md).

**From `docs/state/bindings.md`:**
> ### Record Bindings
>
> When using `Widget[T]`, fields can auto-bind to record properties. See [Record Bindings](../data/record-bindings.md) for details.

**From `docs/start/concepts.md`:**
> **Convention Over Configuration:** Fields named to match record properties automatically bind—no manual wiring needed. See [Record Bindings](../data/record-bindings.md).

### To Other Pages

- Link to `data/records.md` for `Widget[T]` basics
- Link to `state/format-expressions.md` for complex binding syntax
- Link to `data/validation.md` for validating bound fields
- Link to `data/dirty-tracking.md` for tracking changes
- Link to `basics/widgets.md` for widget types reference

---

## Visual Aids Needed

### 1. **Binding Flow Diagram**
```
Record Field (name: str)
        ↕ (two-way sync)
Widget Field (name: QLineEdit)
```

### 2. **Resolution Order Table**
| Priority | Source | Example |
|----------|--------|---------|
| 1 | Widget attribute | `self.title` |
| 2 | Record field | `self.record.title` |
| 3 | Underscore widget attribute | `self._title` |

### 3. **Supported Widget Types Table**
| Widget Type | Bound Property | Signal |
|-------------|----------------|--------|
| QLineEdit | text | textChanged |
| QSpinBox | value | valueChanged |
| QLabel | text | N/A (read-only) |
| QCheckBox | checked | toggled |
| QComboBox | currentText | currentTextChanged |

---

## Tone & Style Notes

- **Practical, not academic:** Focus on what developers need to know
- **Code-first:** Show examples before explaining concepts
- **Progressive disclosure:** Start simple (auto-binding), then advanced (resolution order)
- **Troubleshooting-friendly:** Anticipate common mistakes
- **Cross-reference liberally:** Help users navigate related features

---

## Implementation Notes

### Update Existing Docs

**`docs/data/records.md` changes:**
- Move binding details to new page
- Keep only introduction to auto-binding (1 example)
- Add prominent link: "See [Record Bindings](record-bindings.md) for details"

**`docs/state/bindings.md` changes:**
- Add subsection "Record Bindings" (2-3 sentences + link)
- Clarify Variable bindings vs record bindings

**`docs/start/concepts.md` changes:**
- Add bullet point under "Convention Over Configuration"
- One sentence + link to record-bindings.md

### New Page Creation

- Use existing doc style (Material theme, code blocks, admonitions)
- Include "Prerequisites" admonition linking to `data/records.md`
- Use "Tip" admonitions for best practices
- Use "Warning" admonitions for common pitfalls

---

## Success Metrics

After implementation, users should be able to:

1. Understand how auto-binding works without reading source code
2. Choose between auto-binding and explicit binding confidently
3. Debug binding issues using resolution order rules
4. Use format strings with record fields effectively
5. Handle nullable nested fields with optional chaining

---

## Related Features to Document Later (Not in this proposal)

- Custom widget support (how to make your widgets bindable)
- Performance considerations (lazy evaluation, binding overhead)
- Debugging tools (introspecting bindings at runtime)
- Integration with validation/dirty tracking

These could be follow-up docs or subsections as the feature matures.
