# Documentation Proposal: ref() - Deferred Attribute References

## Files to Add/Update

### New Files to Create

1. **`docs/reference/factories/ref.md`** - Main reference documentation
2. **`docs/state/references.md`** - User guide for references in reactive state context

### Files to Update

1. **`docs/state/bindings.md`** - Add section comparing `ref()` vs `bind=`
2. **`docs/basics/widgets.md`** - Add section on forward/backward widget references
3. **`docs/index.md`** - Add `ref()` to feature list (brief mention)
4. **`mkdocs.yml`** - Add nav entries for new pages

## Suggested Nav Location

```yaml
nav:
  # ... existing nav ...
  - Reactive State:
      - Variables: state/variables.md
      - Bindings: state/bindings.md
      - References: state/references.md           # NEW - user guide
      - Format Expressions: state/format-expressions.md
      - Property Bindings: state/property-bindings.md
  # ... existing nav ...
  - Reference:
      - Decorators:
          # ... existing ...
      - Factories:
          - "new()": reference/factories/new.md
          - "ref()": reference/factories/ref.md   # NEW - API reference
      # ... existing ...
```

## Content Outline

### `docs/reference/factories/ref.md` (API Reference)

```markdown
# ref() - Deferred Attribute References

**Function signature:**
```python
def ref(path: str) -> Ref
```

## Overview

Returns a `Ref` object that resolves widget/variable references at runtime, enabling:
- Forward references (reference fields declared later)
- Backward references (reference fields declared earlier)
- Parent widget access
- Nested attribute traversal
- Optional chaining for None-safe access
- Expression evaluation with Python syntax

## Sections

1. **Basic Usage**
   - Sibling field references
   - Forward vs backward references
   - When refs are resolved (widget initialization)

2. **Reference Syntax**
   - Simple field names: `ref("_field")`
   - Parent references: `ref("#parent._field")`
   - Nested attributes: `ref("_config.theme.name")`
   - Optional chaining: `ref("_config.theme?.name")`
   - Expression syntax: `ref("Hello {_name}")`

3. **Variable Resolution**
   - Automatic `.value` extraction from Variables
   - Example: `ref("_text")` on `Variable[str]` gives the string

4. **Expression Features**
   - Math: `ref("{_x + _y}")`
   - Method calls: `ref("{_name.upper()}")`
   - Function calls: `ref("{len(_items)}")`
   - Format specs: `ref("{_price:.2f}")`
   - Multiple variables: `ref("{_a} + {_b} = {_a + _b}")`

5. **Special Placeholders**
   - `#self` - The widget instance
   - `#parent` - Parent widget
   - Underscore fallback (tries `_field` if `field` not found)

6. **Comparison with bind=**
   - `ref()` - single-shot resolution at init
   - `bind=` - reactive, updates on changes
   - When to use each

7. **API Reference**
   - `Ref.resolve(widget)` - manual resolution
   - Thread safety considerations
   - Type hints

8. **Common Patterns**
   - Sharing menus between widgets
   - Label buddy relationships
   - Computed initial values
   - Parent-child widget connections
```

### `docs/state/references.md` (User Guide)

```markdown
# Widget References

Learn how to reference other widget fields using `ref()`.

## Sections

1. **Why References?**
   - Problem: can't reference widgets before they're declared
   - Solution: `ref()` defers resolution until runtime
   - Use cases: menus, buddies, widget relationships

2. **Basic References**
   - Forward and backward refs with examples
   - Best practices for field naming

3. **Parent-Child Communication**
   - Accessing parent widget state
   - `#parent` syntax
   - When to use vs Variable bindings

4. **Nested Attributes**
   - Traversing object hierarchies
   - Optional chaining for None safety
   - Working with dataclasses/configs

5. **Expressions in References**
   - When you need computed initial values
   - Combining multiple fields
   - Calling methods/functions

6. **ref() vs bind=**
   - Key difference: one-time vs reactive
   - Decision flowchart
   - Can you use both? (Yes, on different fields)

7. **Advanced Patterns**
   - Shared resources (menus, dialogs)
   - Complex widget relationships
   - Dynamic widget trees

8. **Troubleshooting**
   - "AttributeError" - field doesn't exist
   - "TypeError" - wrong type after resolution
   - Debugging ref resolution
```

## Code Examples Needed

### Basic Forward Reference
```python
@widget
class MyWidget(Widget):
    _label: QLabel = new(buddy=ref("_input"))  # Forward ref
    _input: QLineEdit = new()
```

### Backward Reference (Shared Menu)
```python
@widget
class MyWidget(Widget):
    _menu: QMenu = new()
    _button1: QPushButton = new("File", menu=ref("_menu"))
    _button2: QPushButton = new("Edit", menu=ref("_menu"))
```

### Variable Resolution
```python
@widget
class MyWidget(Widget):
    _title: Variable[str] = new("Welcome")
    _label: QLabel = new(text=ref("_title"))  # Gets "Welcome"
    _button: QPushButton = new(clicked="update_title")

    def update_title(self) -> None:
        self._title.value = "Updated"  # _label text does NOT update!
```

### Parent Reference
```python
@widget
class ChildWidget(Widget):
    _btn: QPushButton = new(menu=ref("#parent._shared_menu"))

@widget
class ParentWidget(Widget):
    _shared_menu: QMenu = new()
    _child1: ChildWidget = new()
    _child2: ChildWidget = new()
```

### Nested Attributes with Optional Chaining
```python
@dataclass
class Theme:
    name: str

@dataclass
class Config:
    theme: Theme | None

@widget
class MyWidget(Widget):
    _config: Variable[Config] = new(Config(theme=Theme("dark")))
    _label: QLabel = new(text=ref("Theme: {_config.theme?.name}"))
```

### Expression Syntax
```python
@widget
class MathWidget(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _result: QLabel = new(text=ref("{_x} + {_y} = {_x + _y}"))  # "10 + 20 = 30"
```

### Method Calls in Expressions
```python
@widget
class StringWidget(Widget):
    _name: Variable[str] = new("alice")
    _upper: QLabel = new(text=ref("Name: {_name.upper()}"))  # "Name: ALICE"
    _len: QLabel = new(text=ref("Length: {len(_name)}"))     # "Length: 5"
```

### Format Specs
```python
@widget
class FormattedWidget(Widget):
    _price: Variable[float] = new(19.9)
    _label: QLabel = new(text=ref("Price: ${_price:.2f}"))  # "Price: $19.90"
```

### ref() vs bind() Comparison
```python
@widget
class ComparisonWidget(Widget):
    _count: Variable[int] = new(0)

    # ref() - resolved once at init, does NOT update when _count changes
    _static: QLabel = new(text=ref("Initial: {_count}"))

    # bind= - reactive, DOES update when _count changes
    _reactive: QLabel = new(bind="Current: {_count}")

    _button: QPushButton = new("Increment", clicked="increment")

    def increment(self) -> None:
        self._count += 1
        # _static still shows "Initial: 0"
        # _reactive shows "Current: 1", "Current: 2", etc.
```

### Special Placeholder (#self)
```python
@widget
class SelfRefWidget(Widget):
    name: str = "MyWidget"
    _label: QLabel = new(text=ref("Widget: {type(#self).__name__}"))  # "Widget: SelfRefWidget"
```

## Cross-References

### Link from ref() docs to:
- [Variables](../state/variables.md) - Variable resolution behavior
- [Bindings](../state/bindings.md) - Reactive alternative to ref()
- [Format Expressions](../state/format-expressions.md) - Expression syntax
- [new()](../factories/new.md) - Where ref() is used
- [Parent-child composition](../basics/widgets.md#composition) - Using #parent

### Link to ref() docs from:
- `docs/state/bindings.md` - "For one-time resolution, use ref() instead"
- `docs/reference/factories/new.md` - "Parameters can accept ref() for deferred resolution"
- `docs/basics/widgets.md` - "Forward references with ref()"
- `docs/guides/windows-menus.md` - "Sharing menus with ref()"
- `docs/start/concepts.md` - Brief mention in core concepts

## Priority

**HIGH**

### Reasoning:
1. **Core Feature** - `ref()` is fundamental for widget composition patterns
2. **Not Obvious** - Users coming from React/Vue won't expect this (they have JSX/templates)
3. **Confusion Risk** - Easy to confuse with `bind=` without clear docs
4. **Already Implemented** - Feature exists, tests are comprehensive, just needs docs
5. **Enables Patterns** - Required for advanced widget relationships (shared menus, buddies, etc.)

## Additional Recommendations

### 1. Add Warning Callout
In both docs, include prominent warning:

```markdown
!!! warning "ref() is NOT reactive"
    Unlike `bind=`, `ref()` resolves **once** at widget initialization.
    Changes to referenced Variables will NOT update widgets using ref().

    Use `bind=` for reactive updates, `ref=` for one-time initialization.
```

### 2. Decision Tree Diagram
Add visual flowchart in `docs/state/references.md`:

```
Need to reference another field?
├─ Is it reactive state (Variable)?
│  ├─ Need updates when it changes? → Use bind=
│  └─ Just need initial value? → Use ref()
└─ Is it a widget/object?
   ├─ Forward reference? → Must use ref()
   └─ Backward reference? → Can use ref() or direct access
```

### 3. Migration Note
For v1 users (if applicable), explain what changed about references.

### 4. Performance Note
Briefly mention that ref() has minimal overhead (one-time resolution).

### 5. Examples Page
Add a complete working example to `docs/examples.md`:
- Multi-widget app using shared menus via ref()
- Parent-child state coordination
- Complex nested attribute access

## Implementation Notes

- Keep reference docs (`reference/factories/ref.md`) concise and API-focused
- Keep user guide (`state/references.md`) tutorial-style with motivation
- Use tabs/accordions for comparing ref() vs bind= examples
- Include type signatures in API reference
- Test all code examples (add to test suite if not already covered)
