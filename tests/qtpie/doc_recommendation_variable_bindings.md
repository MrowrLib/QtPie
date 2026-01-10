# Documentation Proposal: Variable Bindings (Parent-Child Widget Communication)

## Priority

**HIGH** - This is a core feature for composable widget architecture and is currently underdocumented.

## Overview

Variable bindings enable React/Vue-style component composition in QtPie, allowing parent widgets to pass reactive state to child widgets. This is currently mentioned briefly in index.md but lacks comprehensive documentation despite being a fundamental feature for building reusable components.

## Files to Add/Update

### New Files to Create

1. **`docs/state/widget-bindings.md`** (Primary documentation)
   - Deep dive into parent-child widget communication via Variable bindings
   - Required vs optional bindings
   - Two-way binding behavior
   - Expression bindings for computed values
   - Literal value bindings
   - Nested widget hierarchies
   - Advanced patterns (diamond dependencies, deep nesting)

### Files to Update

1. **`docs/state/variables.md`**
   - Add "Next: Widget Bindings" navigation link
   - Brief mention that Variables can be bound between widgets (teaser)

2. **`docs/state/bindings.md`**
   - Currently covers format string bindings (`bind=` parameter)
   - Add section distinguishing widget bindings from format bindings
   - Cross-reference to `widget-bindings.md`

3. **`docs/start/concepts.md`**
   - Add section on "Component Composition" explaining Variable bindings at high level
   - Show simple parent-child example

4. **`docs/index.md`**
   - Expand the "Composable Widgets" section with more context
   - Link to full widget-bindings documentation

## Suggested Nav Location

```yaml
nav:
  - Reactive State:
      - Variables: state/variables.md
      - Bindings: state/bindings.md
      - Widget Bindings: state/widget-bindings.md  # NEW - Add here
      - Format Expressions: state/format-expressions.md
      - Property Bindings: state/property-bindings.md
```

**Rationale:** Place after basic bindings but before format expressions, as widget bindings are conceptually simpler than complex expressions and more fundamental to the component model.

## Content Outline: `docs/state/widget-bindings.md`

### 1. Introduction (What & Why)
- What are widget bindings (passing state between parent/child widgets)
- Why they matter (composable, reusable components)
- Comparison to React props / Vue props

### 2. Required vs Optional Bindings
- Variables without `= new()` are required bindings
- Variables with `= new(default)` are optional
- How required bindings are validated at instantiation
- Error messages when missing

### 3. Basic Two-Way Bindings
- Simple parent-child example
- Changes propagate both directions
- Initial value synchronization

### 4. Expression Bindings (One-Way Computed)
- Using format strings for computed bindings: `child: Child = new(enabled="{len(_items) > 0}")`
- When to use vs two-way bindings
- Read-only nature of expression bindings

### 5. Literal Value Bindings
- Passing non-reactive initial values
- String values that don't start with `_` or contain `{}`
- Use cases for static configuration

### 6. Nested Widget Hierarchies
- Passing bindings through multiple levels
- Grandparent → Parent → Child → GrandChild chains
- How to pass down without breaking the chain

### 7. Multiple Bindings
- Widgets with multiple required bindings
- Mixing bound and literal values
- Sibling widgets sharing bindings

### 8. Advanced Patterns
- **Diamond Dependencies**: Multiple branches sharing same root binding
- **Deep Nesting**: Many-level widget hierarchies
- **Mixed Strategies**: Some children bound, some literal

### 9. Integration with Format Expressions
- Using widget bindings in `bind=` parameters
- Example: `_label: QLabel = new(bind="Theme: {theme}")`
- How nested bindings work with format strings

### 10. Best Practices
- When to use required vs optional bindings
- Naming conventions (parent: `_var`, child: `var`)
- Avoiding circular dependencies
- Performance considerations (shallow vs deep hierarchies)

### 11. Troubleshooting
- "requires binding for 'X'" error
- Binding not updating
- Type mismatches between parent/child
- Debugging binding chains

## Code Examples Needed

### Basic Examples

```python
# Required binding
@widget
class ChildWidget(Widget):
    theme: Variable[str]  # Required from parent
    _label: QLabel = new(bind="Theme: {theme}")

@widget
class ParentWidget(Widget):
    _my_theme: Variable[str] = new("dark")
    child: ChildWidget = new(theme="_my_theme")  # Pass binding
```

### Two-Way Binding

```python
# Parent changes affect child, child changes affect parent
parent = Parent()
parent._count.value = 42
assert parent.child.count.value == 42  # Child updated

parent.child.count.value = 100
assert parent._count.value == 100  # Parent updated
```

### Expression Binding (One-Way)

```python
@widget
class SubmitButton(Widget):
    enabled: Variable[bool]

@widget
class Form(Widget):
    _name: Variable[str] = new("")
    submit: SubmitButton = new(enabled="{len(_name) > 0}")  # Computed
```

### Nested Hierarchy

```python
@widget
class GrandChild(Widget):
    theme: Variable[str]
    _display: QLabel = new(bind="Theme: {theme}")

@widget
class Child(Widget):
    theme: Variable[str]  # Pass through from parent
    grandchild: GrandChild = new(theme="theme")

@widget
class Parent(Widget):
    _theme: Variable[str] = new("dark")
    child: Child = new(theme="_theme")

# Changes propagate all the way down
parent._theme.value = "light"
assert parent.child.grandchild._display.text() == "Theme: light"
```

### Multiple Siblings

```python
@widget
class Display(Widget):
    value: Variable[str]
    _label: QLabel = new(bind="{value}")

@widget
class Dashboard(Widget):
    _shared: Variable[str] = new("data")
    display1: Display = new(value="_shared")
    display2: Display = new(value="_shared")
    display3: Display = new(value="_shared")

# All update together
dashboard._shared.value = "updated"
# All three displays show "updated"
```

### Diamond Pattern

```python
@widget
class Leaf(Widget):
    value: Variable[str]

@widget
class BranchA(Widget):
    value: Variable[str]
    leaf: Leaf = new(value="value")

@widget
class BranchB(Widget):
    value: Variable[str]
    leaf: Leaf = new(value="value")

@widget
class Root(Widget):
    _shared: Variable[str] = new("data")
    branch_a: BranchA = new(value="_shared")
    branch_b: BranchB = new(value="_shared")

# Both branches stay in sync
root._shared.value = "new"
# Both branch_a.leaf and branch_b.leaf receive "new"
```

### Mixed Literal and Binding

```python
@widget
class Themed(Widget):
    theme: Variable[str]

@widget
class App(Widget):
    _dynamic_theme: Variable[str] = new("dark")

    # One gets binding (reactive)
    widget1: Themed = new(theme="_dynamic_theme")

    # One gets literal (static)
    widget2: Themed = new(theme="light")
```

### Error Example (Missing Required Binding)

```python
@widget
class Child(Widget):
    required_value: Variable[int]  # No default = required!

@widget
class Parent(Widget):
    child: Child = new()  # ERROR!

# TypeError: Child requires binding for 'required_value'
```

## Cross-References

### Related Documentation Pages

- **[Variables](state/variables.md)** - Understanding Variable[T] basics
- **[Bindings](state/bindings.md)** - Format string bindings (different concept)
- **[Format Expressions](state/format-expressions.md)** - Using bindings in expressions
- **[Record Widgets](data/records.md)** - Widget[T] for binding entire dataclasses
- **[Key Concepts](start/concepts.md)** - High-level overview of composition
- **[Widget Reference](reference/classes/widget.md)** - Technical API details

### Related Features Mentioned

- `Variable[T]` - The reactive primitive powering bindings
- `new()` factory - How bindings are declared: `new(param="variable_name")`
- `Widget[T]` - Another binding pattern (record-level)
- Format expressions - Can reference bound variables
- Property bindings (`visible=`, `enabled=`) - Can use bound variables

### Links to Add FROM Other Pages

- **index.md** → Link "Composable Widgets" section to full widget-bindings docs
- **state/variables.md** → "Next: Learn about Widget Bindings"
- **state/bindings.md** → Distinguish widget bindings from format bindings, link to both
- **start/concepts.md** → Link component composition section to widget-bindings
- **data/records.md** → Mention widget bindings as complementary to record bindings

## Visual Aids / Diagrams

Consider adding diagrams for:

1. **Two-Way Binding Flow**
   ```
   Parent._count = 42
        ↓
   Child.count.value ← 42
        ↓
   Child.count.value = 100
        ↓
   Parent._count ← 100
   ```

2. **Nested Hierarchy**
   ```
   Root._theme = "dark"
     ↓
   L1.theme = "dark"
     ↓
   L2.theme = "dark"
     ↓
   L3.theme = "dark"
   ```

3. **Diamond Dependencies**
   ```
        Root._shared
         /        \
   BranchA      BranchB
      |            |
   LeafA        LeafB
   (Both receive same value)
   ```

## Key Messages to Convey

1. **Widget bindings enable true component composition** - Build reusable widgets that receive state from parents
2. **Two types: Required vs Optional** - Clear contract for what a widget needs
3. **Two-way by default** - Changes propagate both directions (unlike React one-way flow)
4. **Expression bindings are one-way** - Computed values are read-only
5. **Works through any depth** - Bindings propagate through entire widget trees
6. **Type-safe** - Full pyright support, autocomplete works
7. **Different from `bind=`** - Widget bindings (parent→child state) vs format bindings (Variable→text)

## Common Pitfalls to Address

1. Forgetting to declare a Variable without `= new()` when it should be required
2. Trying to pass bindings with wrong type (will fail at runtime)
3. Creating circular binding dependencies
4. Confusing widget bindings with format string bindings
5. Not understanding when to use expression bindings vs two-way bindings
6. Missing required bindings and getting cryptic errors

## Success Criteria

After reading this documentation, users should be able to:

- [ ] Understand the difference between required and optional Variable bindings
- [ ] Create composable widgets that receive state from parents
- [ ] Use two-way bindings for bidirectional communication
- [ ] Use expression bindings for computed one-way values
- [ ] Pass bindings through nested widget hierarchies
- [ ] Share bindings across multiple sibling widgets
- [ ] Debug common binding issues
- [ ] Understand when to use widget bindings vs record bindings (Widget[T])
- [ ] Distinguish widget bindings from format string bindings

## Implementation Notes

- This documentation should come BEFORE format expressions in the learning path
- Include real-world examples (theme systems, form validation, dashboard widgets)
- Emphasize that this is React/Vue-style composition for Qt
- Show both simple and complex examples (progressive disclosure)
- Link to test file for developers wanting to see all edge cases
- Consider a "Binding Cheat Sheet" sidebar with quick reference

## Related Test Coverage

Reference the comprehensive test file for implementation details:
- `tests/qtpie/test_variable_bindings.md` - Full test coverage and behavioral documentation
- `tests/qtpie/test_variable_bindings.py` - Executable test suite
