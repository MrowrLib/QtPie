# Documentation Proposal: Variable[T, W] (Inline Widget Variables)

## Overview

The `Variable[T, W]` pattern deserves dedicated documentation as it's a powerful but nuanced feature. Currently scattered across CLAUDE.md examples - needs proper explanation with complete examples.

## Files to Add/Update

### New Files

1. **docs/state/variable-widgets.md** - Primary documentation for Variable[T, W]
2. **docs/cookbook/inline-forms.md** - Practical cookbook example (optional, lower priority)

### Files to Update

1. **docs/state/variables.md** - Add "See Also" section linking to Variable[T, W] page
2. **docs/index.md** - Consider adding Variable[T, W] to key features if space permits
3. **docs/reference/classes/variable.md** - Add dedicated section on the widget type parameter

## Suggested Nav Location

### Option A: New page under "Reactive State"
```yaml
- Reactive State:
    - Variables: state/variables.md
    - Variable Widgets: state/variable-widgets.md  # NEW
    - Bindings: state/bindings.md
    - Format Expressions: state/format-expressions.md
    - Property Bindings: state/property-bindings.md
```

### Option B: Under "Data & Forms" (alternative)
```yaml
- Data & Forms:
    - Record Widgets: data/records.md
    - Variable Widgets: data/variable-widgets.md  # NEW
    - Lists & Dicts: data/lists-dicts.md
    - Validation: data/validation.md
    - Dirty Tracking: data/dirty-tracking.md
```

**Recommendation: Option A** - Variable[T, W] is fundamentally about reactive state with inline widgets, fits better with other Variable concepts.

## Content Outline

### docs/state/variable-widgets.md

```markdown
# Variable Widgets

## Introduction
- What is Variable[T, W]?
- When to use vs regular Variable[T] + separate widget
- Comparison with Widget[T] (different use cases)

## Basic Usage
- Creating a Variable[T, W]
- Type parameter extraction
- Automatic binding (two-way)
- Accessing the widget via .widget property

## Callable Chain Syntax
- new(value_args)(widget_args) pattern
- Passing constructor kwargs separately
- Examples with QLineEdit, QSpinBox, QComboBox

## Layout Integration
- Variables appear in layout order (interleaved with regular widgets)
- Form layout example with mixed Variable[T, W] and regular widgets
- Grid layout considerations

## Signal Connections
- Connecting signals in the widget kwargs
- Multiple signal connections
- Signal forwarding to parent methods

## Advanced Patterns
- Proxy field access for complex types
- Using custom widgets as W parameter
- Combining with Widget[T] record types
- Variable[SomeDataclass, CustomEditor] pattern

## Type Conversion
- Automatic type conversion (int -> str for QLabel)
- Dataclass rendering via __str__()
- Custom converters (future?)

## Common Patterns
- Inline form fields: Variable[str, QLineEdit]
- Inline numeric inputs: Variable[int, QSpinBox]
- Inline selections: Variable[str, QComboBox]
- Inline displays: Variable[T, QLabel]
- Inline complex widgets: Variable[Dog, DogEditor]

## Type Safety
- Pyright support
- Generic widget constraints
- Common type errors and fixes

## Pitfalls & Best Practices
- When NOT to use Variable[T, W]
- Prefer regular widgets if no reactive binding needed
- Use Widget[T] for record editing, Variable[T, W] for inline state
```

## Code Examples Needed

### 1. Basic Variable[T, W]
```python
@widget
class BasicExample(Widget):
    _name: Variable[str, QLineEdit] = new("default")
    _age: Variable[int, QSpinBox] = new(25)

w = BasicExample()
print(w._name.value)  # "default"
print(w._name.widget.text())  # "default"
w._name.value = "changed"  # Widget updates automatically
```

### 2. Callable Chain Syntax
```python
@widget
class ChainExample(Widget):
    _username: Variable[str, QLineEdit] = new("admin")(
        placeholderText="Enter username",
        maxLength=50
    )
    _count: Variable[int, QSpinBox] = new(50)(
        minimum=0,
        maximum=100,
        suffix=" items"
    )
```

### 3. Signal Connections
```python
@widget
class SignalExample(Widget):
    _input: Variable[str, QLineEdit] = new("")(
        returnPressed="on_submit",
        textChanged="on_text_changed"
    )

    def on_submit(self) -> None:
        print(f"Submitted: {self._input.value}")

    def on_text_changed(self) -> None:
        print(f"Text changed: {self._input.value}")
```

### 4. Layout Order
```python
@widget
class LayoutExample(Widget):
    _label1: QLabel = new("First")
    _field1: Variable[str, QLineEdit] = new("Second")
    _label2: QLabel = new("Third")
    _field2: Variable[int, QSpinBox] = new(0)
    # Layout order: label1, field1.widget, label2, field2.widget
```

### 5. Complex Types with Proxy Access
```python
@dataclass
class Dog:
    name: str
    age: int

@widget(layout="form")
class DogEditor(Widget[Dog]):
    name: QLineEdit = new(label="Name")
    age: QSpinBox = new(label="Age")

@widget
class DogManager(Widget):
    _current_dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))

    def update_dog(self):
        self._current_dog.name = "Rex"  # Proxy access
        self._current_dog.age = 5
        # DogEditor widget automatically updates
```

### 6. Variable[T, W] vs Widget[T] Comparison
```python
# Use Variable[T, W] for inline editing
@widget
class InlineForm(Widget):
    _title: Variable[str, QLineEdit] = new("Untitled")
    _author: Variable[str, QLineEdit] = new("Unknown")

# Use Widget[T] for structured record editing
@dataclass
class Book:
    title: str
    author: str

@widget(record=Book("Untitled", "Unknown"))
class BookEditor(Widget[Book]):
    title: QLineEdit = new()
    author: QLineEdit = new()
```

### 7. Display-Only Pattern (Variable[T, QLabel])
```python
@widget
class Dashboard(Widget):
    _status: Variable[str, QLabel] = new("Ready")(
        styleSheet="color: green; font-weight: bold;"
    )
    _count: Variable[int, QLabel] = new(0)(
        bind="Total: {#self} items"
    )

    def update_status(self, msg: str):
        self._status.value = msg  # Label updates
```

## Cross-References

### Related Features
- [Variables](state/variables.md) - Basic Variable[T] usage
- [Bindings](state/bindings.md) - Data binding fundamentals
- [Record Widgets](data/records.md) - Widget[T] for dataclass editing
- [new() factory](reference/factories/new.md) - The new() callable chain
- [Variable class](reference/classes/variable.md) - Full Variable API

### From Other Pages
- `state/variables.md` should link to Variable[T, W] page in "Advanced" section
- `basics/widgets.md` should mention Variable[T, W] as inline widget pattern
- `data/records.md` should clarify when to use Variable[T, CustomWidget] vs Widget[T]
- `start/concepts.md` could briefly mention Variable[T, W] as advanced reactive pattern

## Priority

**HIGH** - This is a core feature that:
1. Distinguishes QtPie from other frameworks
2. Is already implemented and tested
3. Appears in CLAUDE.md examples but lacks dedicated docs
4. Has nuanced usage patterns (callable chain, signal connections, proxy access)
5. Users will encounter early (after learning basic Variables)

## Open Questions

1. Should we document the type parameter extraction mechanism or treat it as implementation detail?
2. Should we warn about potential performance implications of proxy access?
3. Should Variable[T, QLabel] with bind= be documented here or in bindings.md?
4. Do we need a migration guide from Widget[T] to Variable[T, W] patterns?

## Implementation Notes

- Use admonitions for warnings/tips (e.g., when NOT to use Variable[T, W])
- Include type signatures in examples for clarity
- Add "See Also" boxes at the end
- Use tabs for alternative approaches where applicable
- Consider adding a comparison table: Variable[T] vs Variable[T, W] vs Widget[T]

## Cookbook Ideas (Future)

If we add `docs/cookbook/inline-forms.md`:
- Login form with Variable[T, W] fields
- Settings panel with mixed widget types
- Dynamic form with conditional Variable[T, W] fields
- Search bar with Variable[str, QLineEdit] + debouncing
