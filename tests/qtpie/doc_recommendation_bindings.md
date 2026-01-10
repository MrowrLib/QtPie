# Documentation Proposal: Bindings

## Priority: **HIGH**
Bindings are a core feature used extensively throughout QtPie. Currently scattered across CLAUDE.md and test_bindings.md without proper user-facing documentation.

---

## Files to Add/Update

### 1. **NEW: `docs/state/bindings.md`** (Primary Documentation)
**Status:** Missing - nav references it but file doesn't exist
**Purpose:** Complete guide to all binding patterns and features

### 2. **UPDATE: `docs/index.md`**
**Changes:** Update binding examples to show full spectrum (not just simple format strings)

### 3. **UPDATE: `docs/state/format-expressions.md`** (if exists)
**Changes:** This should be created/updated to focus specifically on expression syntax within bindings

### 4. **UPDATE: `docs/start/concepts.md`** (if exists)
**Changes:** Add "Bindings" as core concept with link to detailed guide

---

## Suggested Nav Location

Already correctly positioned in `mkdocs.yml`:
```yaml
- Reactive State:
    - Variables: state/variables.md
    - Bindings: state/bindings.md        # ← Main bindings doc
    - Format Expressions: state/format-expressions.md  # ← Expression syntax reference
    - Property Bindings: state/property-bindings.md    # ← visible=/enabled= patterns
```

---

## Content Outline: `docs/state/bindings.md`

### Structure

```markdown
# Bindings

Brief intro: Bindings connect Variables to widgets, creating reactive updates.

## Quick Start
- Minimal example showing bind= parameter
- When Variable changes, widget updates

## Basic Binding Patterns

### Simple Value Binding
- bind="_variable_name"
- Auto-detects widget property (text, value, etc.)
- One-way: Variable → Widget

### Format String Binding
- bind="Count: {_count}"
- Mix static text with reactive values
- Multiple variables: bind="{_first} {_last}"

### Two-Way Binding (Variable[T, W])
- Variable[str, QLineEdit] creates widget + binding
- Widget changes update Variable
- Variable changes update widget

## Widget List Bindings

### Bind to list[Widget]
- _labels: list[QLabel] = new(bind="_items")
- Creates/removes widgets as list changes
- WidgetRepeater under the hood

### Custom Format for Lists
- format="Item #{#index}: {#self}"
- Special placeholders: #index, #self

### Dict Bindings
- format="{#key}: {#value} points"
- Reactive dict changes

## Expression Bindings

### Math & Functions
- bind="Sum: {_x + _y}"
- bind="Length: {len(_name)}"
- bind="Upper: {_name.upper()}"

### Complex Expressions
- Parentheses: {(_x + _y) * _z}
- Format specs: {_price:.2f}
- Method calls: {compute()}

### Special Placeholders
Table of #self, #var, #widget, #index, #key, #value

## Property Auto-Detection

### Default Properties by Widget Type
Table showing QLabel→text, QLineEdit→text, QSpinBox→value, etc.

### Explicit Property Names
- bind(...).to(widget, "propertyName")
- When auto-detection isn't enough

## Advanced Patterns

### Binding to Record Properties
- Widget[T] with auto-binds
- Field names match record properties

### Cross-Variable Dependencies
- One binding referencing multiple Variables
- Reactivity tracks all dependencies

### Conditional Content
- Combine with visible=/enabled= for dynamic UI
- Example: error message that appears/disappears

## Binding Lifecycle

### When Bindings Activate
- After __setup__
- Before widget shown

### Cleanup & Memory
- Auto-cleanup when widget destroyed
- Weak references to avoid leaks

## Common Patterns

### Form Field Binding
Complete form example with validation

### Master-Detail Lists
List selection updates detail panel

### Computed Displays
Derived values that update reactively

## Troubleshooting

### Common Issues
- "Variable not found" - typo or scoping
- "Widget doesn't update" - property name mismatch
- "Circular binding" - mutual updates

### Performance Notes
- Bindings are efficient (only update on change)
- Avoid expensive computations in format strings
- Use computed properties for complex logic

## See Also
- [Format Expressions](format-expressions.md) - Full expression syntax
- [Property Bindings](property-bindings.md) - visible=/enabled= patterns
- [Variables](variables.md) - Creating reactive state
- [Record Widgets](../data/records.md) - Widget[T] auto-bindings
```

---

## Code Examples Needed

### 1. **Basic Binding Examples**
```python
# Simple value
_count: Variable[int] = new(0)
_label: QLabel = new(bind="_count")

# Format string
_label: QLabel = new(bind="Count: {_count}")

# Multiple variables
_first: Variable[str] = new("John")
_last: Variable[str] = new("Doe")
_full: QLabel = new(bind="{_first} {_last}")
```

### 2. **Two-Way Binding Example**
```python
_name: Variable[str, QLineEdit] = new("")(placeholderText="Enter name")
_display: QLabel = new(bind="Hello, {_name}!")

# User types in QLineEdit → Variable updates → QLabel updates
```

### 3. **List Binding Example**
```python
_items: Variable[list[str]] = new(["Apple", "Banana"])
_labels: list[QLabel] = new(bind="_items", format="• {#self}")

# Later: self._items.append("Cherry")  # New QLabel automatically added
```

### 4. **Dict Binding Example**
```python
_scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
_labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value} pts")
```

### 5. **Expression Binding Example**
```python
_x: Variable[int] = new(10)
_y: Variable[int] = new(20)
_sum: QLabel = new(bind="Sum: {_x + _y}")
_product: QLabel = new(bind="Product: {_x * _y}")
_complex: QLabel = new(bind="Complex: {(_x + _y) * 2:.2f}")
```

### 6. **Special Placeholders Example**
```python
# In Variable[T, W] context
_name: Variable[str, QLabel] = new("World")(bind="Hello, {#self}!")

# With parent widget reference
class MyWidget(Widget):
    title: str = "MyApp"
    _status: Variable[str, QLabel] = new("Ready")(bind="{#widget.title}: {#self}")
```

### 7. **Record Auto-Binding Example**
```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to self.record.name
    age: QSpinBox = new()    # Auto-binds to self.record.age
```

### 8. **Complete Form Example**
```python
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")

    username_field: QLineEdit = new(bind="_username", placeholderText="Username")
    password_field: QLineEdit = new(bind="_password", echoMode=QLineEdit.EchoMode.Password)

    # Binding with expression
    submit_btn: QPushButton = new("Login", enabled="{len(_username) > 0 and len(_password) > 0}")

    # Status display
    _status: Variable[str] = new("")
    status_label: QLabel = new(bind="Status: {_status}", visible="{len(_status) > 0}")
```

### 9. **Master-Detail Pattern**
```python
@widget
class MasterDetail(Widget):
    _items: Variable[list[str]] = new(["Item A", "Item B", "Item C"])
    _selected_index: Variable[int] = new(0)
    _selected_item: Variable[str] = new("")

    # List of selectable items
    _list_labels: list[QPushButton] = new(
        bind="_items",
        format="{#self}",
        clicked=lambda i="{#index}": self._select_item(i)
    )

    # Detail panel showing selected item
    _detail: QLabel = new(bind="Selected: {_selected_item}")

    def _select_item(self, index: int) -> None:
        self._selected_index.value = index
        self._selected_item.value = self._items.value[index]
```

---

## Cross-References

### Link TO (from bindings.md):
- **[Variables](variables.md)** - How to create Variables
- **[Format Expressions](format-expressions.md)** - Full expression syntax reference
- **[Property Bindings](property-bindings.md)** - visible=/enabled= patterns
- **[Record Widgets](../data/records.md)** - Widget[T] auto-binding behavior
- **[Lists & Dicts](../data/lists-dicts.md)** - Collection bindings in depth
- **[Validation](../data/validation.md)** - Using bindings with validation errors

### Link FROM (to bindings.md):
- **index.md** - Quick binding example in features
- **start/concepts.md** - "Bindings" as core concept
- **start/hello-world.md** - First binding example
- **basics/widgets.md** - Mention bind= as field parameter
- **state/variables.md** - Variables work with bindings
- **data/records.md** - Auto-bindings based on field names
- **examples.md** - Real-world binding patterns

---

## Additional Notes

### Terminology Consistency
- **"Binding"** (noun) - The connection between Variable and widget
- **"bind="** (parameter) - How to declare a binding
- **"bind()"** (function) - Imperative binding API (mentioned in test_bindings.md but not yet in user docs)

### Current Gaps in Documentation
1. `bind()` function not documented in user docs (only in test_bindings.md)
2. Two-way binding behavior not fully explained
3. WidgetRepeater mechanics (auto-sync on list changes) not documented
4. Property auto-detection rules not listed
5. Memory/lifecycle guarantees not mentioned
6. Performance characteristics not covered

### Should `bind()` Function Be Documented?
From test_bindings.md, there's a `bind(var).to(widget)` imperative API. Decision needed:
- **Option A:** Document in bindings.md as "Advanced: Imperative Bindings"
- **Option B:** Keep as internal/advanced feature, document only `bind=` parameter
- **Option C:** Separate doc page for imperative API

**Recommendation:** Option A - show it exists but emphasize `bind=` as primary/preferred approach.

---

## Migration from CLAUDE.md

Current CLAUDE.md has extensive binding examples but they're mixed with other features. Extract and organize:

1. **Lines 216-261** → Widget List Bindings section
2. **Lines 264-275** → Variable[T, W] section
3. **Lines 366-490** → Format String Bindings section
4. **Lines 421-444** → Special Placeholders section
5. **Lines 549-568** → Property Bindings (move to property-bindings.md)

Keep CLAUDE.md examples concise; full details go to docs.
