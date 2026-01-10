# Documentation Proposal: ObservableSet

## Priority
**Medium** - ObservableSet is a core observant primitive alongside Observable, ObservableList, ObservableDict, and ObservableProxy. While not used in the main QtPie examples yet, it completes the collection types trilogy and should be documented for completeness.

## Files to Add/Update

### New Files
1. **`docs/observant/observable-set.md`** - Main ObservableSet documentation
2. **`docs/observant/index.md`** - Overview/index page for observant library primitives

### Update Files
1. **`docs/index.md`** - Add brief mention of observant library under "Key Features" if not already present
2. **`mkdocs.yml`** - Add new "Observant Library" nav section with Observable primitives

## Suggested Nav Location

Insert a new top-level section after "Reactive State" and before "Data & Forms":

```yaml
nav:
  # ... existing sections ...
  - Reactive State:
      - Variables: state/variables.md
      - Bindings: state/bindings.md
      - Format Expressions: state/format-expressions.md
      - Property Bindings: state/property-bindings.md
  - Observant Library:                              # NEW SECTION
      - Overview: observant/index.md                # NEW
      - Observable: observant/observable.md         # NEW
      - ObservableList: observant/observable-list.md   # NEW
      - ObservableDict: observant/observable-dict.md   # NEW
      - ObservableSet: observant/observable-set.md     # NEW
      - ObservableProxy: observant/observable-proxy.md # NEW
  - Data & Forms:
      # ... existing ...
```

**Rationale:** The observant library is foundational to QtPie's reactivity but operates at a lower level than the QtPie-specific features. Placing it between "Reactive State" (which uses Variable[T]) and "Data & Forms" provides natural progression from high-level to low-level concepts.

## Content Outline

### `docs/observant/observable-set.md`

```markdown
# ObservableSet

## Overview
- What it is: reactive set wrapper around Python's set
- When to use: tracking unique items, tags, permissions, selections
- Part of the observant library (low-level reactive primitives)

## Basic Usage
- Creating empty/initialized sets
- Standard set operations (add, remove, discard, clear, pop)
- Containment checks, iteration, length
- Converting to regular set with to_set()

## Set Algebra
- Immutable operations: union(), intersection(), difference(), symmetric_difference()
- In-place operations: update(), intersection_update(), difference_update(), symmetric_difference_update()
- Tests: issubset(), issuperset(), isdisjoint()

## Reactivity & Callbacks

### Generic Change Callback
- on_change() for any mutation
- Only fires on actual changes (not duplicate adds)
- Multiple callbacks supported

### Granular Callbacks
- on_add(callback) - fires when item added, receives item
- on_remove(callback) - fires when item removed, receives item
- on_clear(callback) - fires when set cleared, receives removed items set
- All fire alongside on_change()

## Dirty Tracking
- is_dirty property (Observable[bool])
- Tracks changes since creation or reset_dirty()
- Reverts to clean if restored to original state
- Reactive: can bind to is_dirty.on_change()

## Validation
- add_validator(name, fn) - named validators
- Validators return None (valid) or str/list[str] (errors)
- is_valid property (Observable[bool])
- validation_errors property (Observable[dict[str, list[str]]])
- validation_error_messages property (Observable[list[str]])
- All properties are reactive and bindable

## Type Safety
- Generic type ObservableSet[T]
- Full pyright strict compliance
- Behaves like regular set for type checking

## Comparison & Equality
- Can compare with other ObservableSet or regular set
- Equality based on set contents, not identity
```

### `docs/observant/index.md`

```markdown
# Observant Library

## Overview
The observant library provides low-level reactive primitives that power QtPie's reactivity system. While QtPie users typically work with Variable[T], the observant library offers fine-grained control for advanced use cases.

## Primitives

### Observable[T]
Single reactive value with change callbacks. The foundation for Variable[T].

### ObservableList[T]
Reactive list with granular callbacks for insert, remove, replace, move, and clear operations.

### ObservableDict[K, V]
Reactive dictionary with callbacks for set, delete, and clear operations.

### ObservableSet[T]
Reactive set with callbacks for add, remove, and clear operations.

### ObservableProxy[T]
Wraps any object, making field access/assignment reactive. Powers Widget[T] record binding.

## When to Use Observant Directly
- Building custom reactive data structures
- Integrating with non-Qt frameworks
- Performance-critical code needing fine-grained callbacks
- Testing reactive logic without Qt dependencies

## When to Use QtPie Wrappers
- Building Qt/PySide6 applications (use Variable[T])
- Automatic UI binding and updates
- Declarative widget development
```

## Code Examples Needed

### Basic Operations
```python
from observant import ObservableSet

# Create and populate
tags = ObservableSet[str]({"python", "qt"})
tags.add("desktop")
assert "python" in tags
```

### Reactivity Example
```python
tags = ObservableSet[str]()
changes: list[str] = []

tags.on_add(lambda item: print(f"Added: {item}"))
tags.on_change(lambda: changes.append("changed"))

tags.add("python")  # Prints "Added: python", appends "changed"
```

### Dirty Tracking Example
```python
tags = ObservableSet[str]({"python"})
tags.reset_dirty()

tags.add("qt")
assert tags.is_dirty.get() is True

tags.remove("qt")  # Back to original
assert tags.is_dirty.get() is False
```

### Validation Example
```python
tags = ObservableSet[str]()
tags.add_validator("required", lambda s: None if len(s) > 0 else "Must have at least one tag")

assert tags.is_valid.get() is False
tags.add("python")
assert tags.is_valid.get() is True
```

### Set Algebra Example
```python
allowed = ObservableSet[str]({"read", "write", "delete"})
user_perms = ObservableSet[str]({"read", "write"})

missing = allowed.difference(user_perms.to_set())  # {"delete"}
user_perms.update(missing)  # Grant missing permissions
```

### Integration with QtPie (aspirational)
```python
from qtpie import Widget, new, widget
from observant import ObservableSet

@widget
class TagEditor(Widget):
    # Hypothetical future binding - not currently implemented
    _tags: ObservableSet[str] = ObservableSet({"python", "qt"})
    _tag_labels: list[QLabel] = new(bind="_tags")  # One label per tag
```

## Cross-References

### Within Observant Library
- Link to Observable - the foundation primitive
- Link to ObservableList - similar collection type
- Link to ObservableDict - similar collection type
- Link to ObservableProxy - for object field reactivity

### To QtPie Features
- **From ObservableSet docs:**
  - Link to `state/variables.md` - Variable[T] is the high-level wrapper
  - Link to `data/dirty-tracking.md` - similar dirty tracking at Widget level
  - Link to `data/validation.md` - similar validation at Widget level

- **From QtPie docs to ObservableSet:**
  - `state/variables.md` should mention observant library as underlying implementation
  - `data/lists-dicts.md` should mention ObservableList/Dict/Set as the backing types
  - Consider adding "Advanced: Using Observant Directly" section in relevant guides

### External References
- Python's built-in `set` documentation
- Reactive programming concepts

## Special Considerations

### Documentation Style
- **Beginner-friendly intro** - Start with simple examples, show clear use cases
- **Progressive disclosure** - Basic operations first, then callbacks, then advanced features
- **Compare to regular set** - Show side-by-side examples where helpful
- **Type annotations everywhere** - Reinforce QtPie's type-safety culture

### API Stability Warning
Consider adding a note if the API is still evolving:

!!! warning "Low-Level API"
    This is a low-level observant library primitive. Most QtPie users should use Variable[T] instead. The observant API is stable but more verbose and Qt-agnostic.

### Feature Gaps
Document any differences from Python's set:
- Missing operators (`|`, `&`, `-`, `^`, `|=`, etc.) - users must use named methods
- No `__ior__`, `__iand__` operator support
- If these are important, consider noting them as "Future Enhancement" or explaining the design decision

### Performance Notes
- Callbacks fire synchronously
- Each mutation operation fires callbacks once (even if multiple items affected)
- update() batches notifications efficiently

## Related Test Files
- `tests/observant/test_observable_set.py` - reference for code examples
- `tests/observant/test_observable_set.md` - literate test suite (source of truth for behavior)

## Implementation Status
- **Status:** ✅ Fully implemented and tested
- **Version:** Available in v2 rewrite
- **Tests:** Complete coverage in test_observable_set.py

## Future Enhancements to Document
If/when these are added:
1. **QtPie integration** - Binding ObservableSet directly in widgets
2. **Operator overloads** - If `|`, `&`, `-` operators added for convenience
3. **Frozen set support** - If ObservableFrozenSet variant is added
4. **Batch operations** - If context manager for suppressing callbacks is added
5. **Custom equality** - If key function support is added
