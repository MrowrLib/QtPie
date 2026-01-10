# Documentation Proposal: List Widget Binding

## Overview

List widget binding is a core reactive feature that enables automatic synchronization between a `Variable[list[T]]` and a list of widgets. This feature lacks dedicated documentation despite being fundamental to building dynamic UIs with QtPie.

## Priority

**HIGH** - This is a core reactive feature with multiple use cases (dynamic lists, validation error displays, etc.) but is only mentioned briefly in CLAUDE.md. Users need clear, comprehensive docs.

---

## Files to Add/Update

### New Files

1. **`docs/state/list-bindings.md`** (NEW)
   - Dedicated page for list widget bindings
   - Replaces scattered examples in CLAUDE.md
   - Lives in the "Reactive State" section alongside other binding docs

### Files to Update

2. **`docs/state/bindings.md`** (UPDATE)
   - Add brief intro paragraph mentioning list bindings
   - Add cross-reference link to new `list-bindings.md` page
   - Keep focus on single-widget bindings

3. **`docs/data/lists-dicts.md`** (UPDATE if exists, or CREATE)
   - Cross-reference list widget bindings
   - May need to distinguish between:
     - Binding to list data (covered in `state/list-bindings.md`)
     - Working with dict data structures

4. **`docs/index.md`** (MINOR UPDATE)
   - Consider adding list binding example to "Key Features" section
   - Shows off reactive power with minimal code

5. **`mkdocs.yml`** (UPDATE)
   - Add new page to nav structure (see below)

---

## Suggested Nav Location

```yaml
nav:
  # ... existing nav items ...
  - Reactive State:
      - Variables: state/variables.md
      - Bindings: state/bindings.md
      - List Bindings: state/list-bindings.md  # <-- ADD HERE
      - Format Expressions: state/format-expressions.md
      - Property Bindings: state/property-bindings.md
  # ... rest of nav ...
```

**Rationale:** List bindings are a specialized form of reactive binding, so they belong in the "Reactive State" section alongside other binding documentation. Placing it after "Bindings" provides natural progression from simple to complex.

---

## Content Outline: `docs/state/list-bindings.md`

### 1. Introduction (What & Why)

- What are list bindings?
- When to use them (dynamic lists, validation errors, search results, etc.)
- One-sentence comparison to React/Vue: "Like `v-for` or `.map()` but automatic"

### 2. Basic Usage

- Simple string list example
- How items map to widgets
- Show layout behavior

### 3. Automatic Synchronization

- Adding items (append, insert)
- Removing items (remove, pop)
- Clearing lists
- Replacing entire list
- Code examples showing widgets updating automatically

### 4. Widget Configuration

- Passing constructor kwargs
- Styling all items
- Setting common properties

### 5. Format Expressions

- Using `format=` parameter
- Special placeholders: `{#index}`, `{#self}`
- Complex object properties
- Brief cross-reference to Format Expressions page

### 6. Layout Control

- `layout=False` parameter
- When to exclude from parent layout
- Manual positioning use cases

### 7. Accessing Widget Instances

- List interface (`labels[0]`, `len(labels)`)
- Iteration patterns
- Styling individual items in `__setup__`
- Warning about timing (widgets created during `__init__`)

### 8. Validation Error Display Pattern

- Common use case: showing validation errors
- Binding to `validation_error_messages`
- Binding to single variable's errors
- Widget-level vs field-level errors

### 9. Advanced Patterns

- Nested objects with property access
- Combining with property bindings (visible, enabled)
- Performance considerations (large lists)

### 10. Type Safety

- How typing works with `list[QWidget]`
- IDE autocomplete support
- When to specify widget type explicitly

### 11. Troubleshooting

- Common mistakes (wrong bind target, timing issues)
- Debugging tips
- When to use list bindings vs manual widget management

### 12. Related Features

- Cross-links to:
  - `state/bindings.md` - single widget bindings
  - `state/format-expressions.md` - format string syntax
  - `data/validation.md` - validation error patterns
  - `data/lists-dicts.md` - dict bindings

---

## Code Examples Needed

### Example 1: Basic Todo List

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])
    _labels: list[QLabel] = new(bind="_items")
    _input: QLineEdit = new()
    _add_btn: QPushButton = new("Add", clicked="add_item")

    def add_item(self) -> None:
        if text := self._input.text():
            self._items.append(text)
            self._input.clear()
```

### Example 2: Formatted List with Index

```python
@widget
class NumberedList(Widget):
    _items: Variable[list[str]] = new(["First", "Second", "Third"])
    _labels: list[QLabel] = new(
        bind="_items",
        format="#{#index + 1}: {#self}"  # "1: First", "2: Second", etc.
    )
```

### Example 3: Validation Errors

```python
@widget
class ValidatedForm(Widget):
    _name: Variable[str] = new("")
    _email: Variable[str] = new("")

    # Show all validation errors in red labels
    _errors: list[QLabel] = new(
        bind="validation_error_messages",
        styleSheet="color: red; font-weight: bold;"
    )

    def __setup__(self) -> None:
        self._name.add_validator("required", lambda v: "Name required" if not v else None)
        self._email.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
```

### Example 4: Complex Objects

```python
@dataclass
class Task:
    title: str
    done: bool = False

@widget
class TaskList(Widget):
    _tasks: Variable[list[Task]] = new([
        Task("Buy milk"),
        Task("Walk dog", done=True)
    ])

    _task_labels: list[QLabel] = new(
        bind="_tasks",
        format="{'✓' if done else '☐'} {title}"
    )
```

### Example 5: Manual Styling

```python
@widget
class ColoredList(Widget):
    _items: Variable[list[str]] = new(["Red", "Green", "Blue"])
    _labels: list[QLabel] = new(bind="_items")

    def __setup__(self) -> None:
        colors = ["red", "green", "blue"]
        for label, color in zip(self._labels, colors):
            label.setStyleSheet(f"color: {color};")
```

### Example 6: Excluding from Layout

```python
@widget
class CustomLayout(Widget):
    _header: QLabel = new("Items:")
    _items: Variable[list[str]] = new(["A", "B", "C"])
    _labels: list[QLabel] = new(bind="_items", layout=False)
    _footer: QLabel = new("End")

    def __setup__(self) -> None:
        # Manually position the labels
        custom_layout = QHBoxLayout()
        for label in self._labels:
            custom_layout.addWidget(label)
        # Add custom_layout to parent, etc.
```

---

## Cross-References

### Pages That Should Link Here

1. **`state/bindings.md`**
   - "For binding to lists of items, see [List Bindings](list-bindings.md)"

2. **`data/validation.md`**
   - "To display validation errors in a list of labels, see [List Bindings - Validation Error Display](../state/list-bindings.md#validation-error-display)"

3. **`state/format-expressions.md`**
   - "List bindings support special placeholders like `{#index}`. See [List Bindings](list-bindings.md)"

4. **`start/concepts.md`**
   - Add list bindings to "Reactive State" concept overview

### Pages This Should Link To

1. **`state/bindings.md`** - For simple single-widget binding
2. **`state/format-expressions.md`** - For format string syntax details
3. **`state/property-bindings.md`** - For combining with visible/enabled
4. **`data/validation.md`** - For validation error patterns
5. **`data/lists-dicts.md`** - For dict bindings (similar concept)
6. **`basics/layouts.md`** - For understanding layout behavior

---

## Key Points to Emphasize

### 1. Automatic Synchronization

Make it crystal clear that this is automatic - users don't call any update methods.

### 2. Type Safety

Show how IDE autocomplete works, emphasize pyright support.

### 3. Common Patterns

Highlight validation error display as a killer feature.

### 4. Performance

Brief note about performance with large lists (consider virtualization for 1000+ items).

### 5. Comparison to Other Frameworks

Brief mention of React/Vue equivalents for web devs learning QtPie.

---

## Tone & Style

- **Clear & Practical**: Focus on real-world use cases
- **Progressive Disclosure**: Start simple, build to advanced
- **Example-Driven**: Show, don't just tell
- **Cross-Referenced**: Guide users to related features
- **Type-Focused**: Emphasize type safety throughout

---

## Success Criteria

Users should be able to:

1. Implement a basic list binding in under 2 minutes
2. Understand when to use vs not use list bindings
3. Display validation errors using list bindings
4. Access and style individual widget instances
5. Know where to look for advanced format expression syntax
6. Troubleshoot common issues independently

---

## Optional Enhancements

### Interactive Examples

If using mkdocs-material with code playground support:

- Live editable examples users can modify
- Side-by-side code/result view

### Video Tutorial

Short 2-3 minute screencast showing:

1. Creating a todo list
2. Adding validation errors
3. Styling items

### Comparison Table

| Use Case | Plain Qt | QtPie List Binding |
|----------|----------|-------------------|
| Add item | Create widget, add to layout | `items.append(item)` |
| Remove item | Find widget, remove, delete | `items.remove(item)` |
| Clear all | Loop through widgets | `items.clear()` |
| Show errors | Manual label management | `bind="validation_error_messages"` |

---

## Migration Notes

### From CLAUDE.md

These examples currently in CLAUDE.md should move to the new page:

- Lines 216-233: List Binding with WidgetRepeater
- Lines 235-247: List with Custom Format
- Lines 249-261: Dict Binding (this might go to `data/lists-dicts.md`)

Update CLAUDE.md to reference the new docs page instead of duplicating content.

---

## Timeline Estimate

- Writing: 2-3 hours
- Code examples & testing: 1-2 hours
- Review & cross-reference updates: 1 hour
- **Total: 4-6 hours**

---

## Dependencies

- Ensure `data/validation.md` exists and covers validation basics
- Ensure `state/format-expressions.md` is comprehensive
- Ensure `state/bindings.md` covers simple binding first

---

## Questions for Review

1. Should dict bindings be in the same page or separate?
   - **Recommendation**: Separate page (`data/lists-dicts.md`) since dict syntax is different enough

2. Should we cover Observable[list[T]] vs Variable[list[T]]?
   - **Recommendation**: Only mention Variable; Observable is implementation detail

3. How much detail on performance/virtualization?
   - **Recommendation**: Brief note with external link to Qt QListWidget virtualization docs

4. Should examples use public or private field names?
   - **Recommendation**: Mix of both - private for internal state, public for child widgets
