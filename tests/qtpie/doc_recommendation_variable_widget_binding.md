# Documentation Proposal: Variable[T, Widget[T]] Binding

## Overview

The `Variable[T, Widget[T]]` binding feature enables powerful nested widget composition by allowing Variables to instantiate and bind to custom `Widget[T]` subclasses. This creates automatic two-way synchronization between parent and child widget records via shared `ObservableProxy` instances.

## Priority

**HIGH** - This is a powerful composition pattern that differentiates QtPie from other frameworks. It enables building complex, reusable form components.

---

## Files to Add/Update

### New Files to Create

1. **`docs/state/widget-bindings.md`** (Primary documentation)
   - Comprehensive guide to `Variable[T, Widget[T]]` pattern
   - Single widget binding
   - List widget binding (repeaters)
   - Nested widget records
   - Type safety and IDE support notes

2. **`docs/guides/nested-editors.md`** (Optional - could be combined with above)
   - Practical guide for building nested record editors
   - Common patterns and use cases
   - Best practices

### Files to Update

1. **`docs/state/variables.md`**
   - Add section on `Variable[T, Widget[T]]` syntax
   - Link to new detailed page

2. **`docs/state/bindings.md`**
   - Add cross-reference to widget binding feature
   - Brief mention with link to detailed page

3. **`docs/data/records.md`**
   - Add section on nested widget editors
   - Link to Variable[T, Widget[T]] docs

4. **`docs/index.md`**
   - Add "Nested Widget Editors" or similar to feature list
   - Could mention in composability section

5. **`docs/start/concepts.md`** (if it exists, create if not)
   - Add to "Key Concepts" section if discussing composition patterns

## Suggested Nav Location

```yaml
nav:
  - Reactive State:
      - Variables: state/variables.md
      - Bindings: state/bindings.md
      - Format Expressions: state/format-expressions.md
      - Property Bindings: state/property-bindings.md
      - Widget Bindings: state/widget-bindings.md  # NEW
```

**Alternative location:**

Could also fit under "Data & Forms" as `data/widget-binding.md` since it's about composing nested editors.

**Recommended:** Under "Reactive State" as it's fundamentally about Variable bindings.

---

## Content Outline

### Page Title: "Variable Widget Binding"

#### 1. **Introduction** (2-3 paragraphs)
   - What is `Variable[T, Widget[T]]`
   - Why this matters (reusable form components, nested editors)
   - Comparison to React: "like passing props to child components"

#### 2. **Single Widget Binding**
   - Syntax: `Variable[Dog, DogEditor]`
   - How proxy sharing works
   - Bidirectional sync explanation
   - Code example: parent widget with nested editor

#### 3. **List Widget Binding**
   - `Variable[list[T], Widget[T]]` syntax
   - WidgetRepeater behavior
   - Add/remove operations
   - Accessing individual widget instances

#### 4. **Nested Widget Records**
   - `Widget[T]` containing `Variable[U, Widget[U]]`
   - Multi-level composition patterns

### Code Examples Needed

1. **Basic Single Binding** (like CLAUDE.md lines 264-275)
   ```python
   @widget
   class DogEditor(Widget[Dog]):
       _name: QLineEdit = new(label="Dog's Name")
       _age: QSpinBox = new(label="Dog's Age")

   @widget
   class App(Widget):
       dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))
       # Changes flow both ways automatically
   ```

2. **List of Custom Widgets** - Showing `Variable[list[T], Widget[T]]`
   - Creating repeaters of custom widget editors
   - How list operations sync with widget instances
   - Accessing individual widget editors

3. **Nested Widget Records** - Complex compositions with nested editors

4. **Comparison with Record Widgets** - When to use `Variable[T, Widget[T]]` vs just `Widget[T]`

5. **Type Safety** - How pyright understands the shared ObservableProxy

6. **Real-World Use Case** - Multi-step form with nested editors

## Code Examples Needed

1. **Basic nested editor**:
   ```python
   @widget
   class AddressEditor(Widget[Address]):
       street: QLineEdit = new()
       city: QLineEdit = new()

   @widget
   class PersonForm(Widget):
       _person: Variable[Person, PersonEditor] = new(Person("Alice", 30))
       # Automatic bidirectional sync
   ```

2. **List of nested widgets**:
   ```python
   _dogs: Variable[list[Dog], DogEditor] = new([...])
   # Creates WidgetRepeater with one DogEditor per item
   ```

3. **Deep nesting** (Widget[T] containing Variable[U, Widget[U]]):
   ```python
   @widget
   class PetEditor(Widget[Pet]):
       owner: Variable[Owner, OwnerEditor] = new(Owner())
   ```

4. **Compared to simple `bind=` on regular widgets**:
   - `Variable[T, QLineEdit]` + `bind=` → text display/edit
   - `Variable[T, Widget[T]]` → full custom editor widget

## Content Outline

1. **Introduction**
   - What is Variable widget binding
   - When to use it vs. regular Variable bindings
   - Core concept: shared ObservableProxy

2. **Single Widget Binding**
   - Syntax: `Variable[T, Widget[T]]`
   - Observable sharing between Variable and Widget.record
   - Bidirectional sync examples
   - Accessing the widget instance via `.widget`

3. **List Widget Binding**
   - `Variable[list[T], Widget[T]]` creates WidgetRepeater
   - Automatic widget creation/removal
   - Editing individual items
   - When to use vs list[QWidget]

4. **Nested Widget Records**
   - `Variable[T, Widget[T]]` inside `Widget[U]`
   - Multi-level composition
   - Record binding flows

5. **Use Cases**
   - Complex nested editors (address editor with multiple fields)
   - List of custom editors (todo items with metadata)
   - Reusable form components with record types
   - Multi-level forms (person with addresses with details)

## Code Examples Needed

```python
# Basic single widget binding
@widget(layout="form")
class AddressEditor(Widget[Address]):
    street: QLineEdit = new(label="Street")
    city: QLineEdit = new(label="City")

@widget
class PersonForm(Widget):
    name: Variable[str, QLineEdit] = new("")
    address: Variable[Address, AddressEditor] = new(Address())
```

```python
# List of custom widgets
@widget
class ContactList(Widget):
    contacts: Variable[list[Contact], ContactEditor] = new([...])
    # Creates WidgetRepeater with ContactEditor for each item
```

### Cross-References

- [Record Widgets](data/records.md) - Understanding `Widget[T]` pattern
- [Variables](state/variables.md) - `Variable[T]` basics
- [Bindings](state/bindings.md) - General binding concepts
- [Lists & Dicts](data/lists-dicts.md) - `WidgetRepeater` with list bindings
- [Key Concepts](start/concepts.md) - Composition patterns

### Priority

**HIGH**

**Rationale:**
- `Variable[T, Widget[T]]` binding is a powerful composition pattern (like React props + components)
- Enables nested editor widgets with automatic data sync
- This is a distinguishing feature not covered in existing docs
- Critical for building complex forms and CRUD interfaces
- Complements the existing `Widget[T]` record binding documentation
- The test file shows complete, working examples ready to be adapted for docs