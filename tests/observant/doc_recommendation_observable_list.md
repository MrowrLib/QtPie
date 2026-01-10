# Documentation Proposal: ObservableList

## Executive Summary

**ObservableList** is a foundational reactive primitive from the `observant` library. It provides a reactive list implementation with granular callbacks, dirty tracking, and full Python list API compatibility. This is an **internal implementation detail** that powers `Variable[list[T]]` in QtPie.

**Recommendation**: This feature requires **minimal new documentation** since it's already covered indirectly through the existing `Variable[list[T]]` docs. However, we should add a **reference page** in the observant library section for advanced users and library maintainers.

---

## Priority

**Low-Medium Priority** - This is infrastructure documentation:
- Most users will use `Variable[list[T]]` and don't need to know about ObservableList internals
- Advanced users and contributors need reference documentation
- Should be documented for completeness, but not critical for beginner workflow

---

## Files to Add

### 1. `docs/reference/observant/observable-list.md` (NEW)

**Purpose**: Complete API reference for ObservableList

**Content Outline**:
- **Overview**
  - What ObservableList is and why it exists
  - Relationship to `Variable[list[T]]`
  - When to use it directly vs. through Variable

- **Creating ObservableLists**
  - Basic instantiation: `ObservableList[T]()`
  - With initial data: `ObservableList[int]([1, 2, 3])`
  - Type parameter usage

- **Standard List Operations**
  - Full Python list API compatibility table
  - `append()`, `extend()`, `insert()`, `remove()`, `pop()`, `clear()`
  - Indexing: `obs[0]`, `obs[0] = value`, `del obs[0]`
  - Slicing behavior (if supported)
  - Iteration, `len()`, `in` operator
  - `index()`, `count()` methods

- **Generic Change Callbacks**
  - `on_change(callback)` - fires on any mutation
  - Multiple callback registration
  - Callback signature (no arguments)
  - Duplicate handling

- **Granular Callbacks**
  - `on_insert(callback: Callable[[int, T], None])`
    - Fires when items are added
    - Callback receives `(index, item)`
  - `on_remove(callback: Callable[[int, T], None])`
    - Fires when items are removed
    - Callback receives `(index, item)`
  - `on_replace(callback: Callable[[int, T, T], None])`
    - Fires when items are replaced via indexing
    - Callback receives `(index, old_value, new_value)`
  - `on_clear(callback: Callable[[list[T]], None])`
    - Fires when list is cleared
    - Callback receives the list of removed items

- **Dirty Tracking**
  - `.is_dirty` property (Observable[bool])
  - `.reset_dirty()` method
  - How dirty state is calculated (content-based comparison)
  - Automatic clean state when reverted to original
  - `is_dirty.on_change()` for dirty state transitions only

- **Type Safety**
  - Generic type parameter `T`
  - Type inference with pyright
  - No `Any` leakage

- **Performance Notes**
  - Callback overhead
  - When granular callbacks are more efficient than `on_change`

- **Advanced Patterns**
  - Using multiple callback types together
  - Combining with other observables
  - Direct usage outside of QtPie

**Code Examples Needed** (from test summary):
```python
# Basic operations
obs = ObservableList[int]([1, 2, 3])
obs.append(4)
obs.extend([5, 6])
obs.insert(1, 99)
obs.remove(2)
item = obs.pop(0)

# Generic change callback
changes: list[str] = []
obs.on_change(lambda: changes.append("changed"))

# Granular callbacks
inserts: list[tuple[int, str]] = []
obs.on_insert(lambda idx, item: inserts.append((idx, item)))

replaces: list[tuple[int, str, str]] = []
obs.on_replace(lambda idx, old, new: replaces.append((idx, old, new)))

clears: list[list[str]] = []
obs.on_clear(lambda items: clears.append(items))

# Dirty tracking
obs.reset_dirty()
assert not bool(obs.is_dirty)
obs.append(3)
assert bool(obs.is_dirty)
obs.pop()  # back to original
assert not bool(obs.is_dirty)

# Dirty change notifications
dirty_states: list[bool] = []
obs.is_dirty.on_change(lambda d: dirty_states.append(d))
obs.append(1)  # clean -> dirty
obs.append(2)  # stays dirty (no callback)
obs.reset_dirty()  # dirty -> clean
assert dirty_states == [True, False]
```

---

## Files to Update

### 2. `docs/state/variables.md` (UPDATE - Minor)

**Current State**: Already documents `Variable[list[T]]` extensively

**Updates Needed**:
- Add a cross-reference in the "Variable[list[T]] - Observable Lists" section
- Add link to the new ObservableList reference page for advanced users

**Suggested Addition** (around line 130):
```markdown
## Variable[list[T]] - Observable Lists

When the type parameter is a list, Variable wraps an `ObservableList` that tracks insertions, removals, and other list operations.

> **Advanced**: For details on the underlying `ObservableList` implementation, granular callbacks, and direct usage, see the [ObservableList Reference](../../reference/observant/observable-list.md).

[... rest of existing content ...]
```

### 3. `docs/reference/classes/variable.md` (UPDATE - Minor)

**Current State**: Comprehensive Variable reference with brief ObservableList mentions

**Updates Needed**:
- Add cross-reference to ObservableList in the "Type Selection" table
- Add link in the ".observable" property section

**Suggested Updates**:

Around line 50 (in the Type Selection table):
```markdown
| `Variable[list[T]]` | `ObservableList[T]` | Lists with granular callbacks ([ref](../observant/observable-list.md)) |
```

Around line 161 (in the .observable section):
```python
# Lists → ObservableList[T]
items_obs: ObservableList[str] = self._items.observable
items_obs.on_insert(lambda idx, item: print(f"Inserted {item} at {idx}"))
items_obs.on_remove(lambda idx, item: print(f"Removed {item} from {idx}"))

# See [ObservableList Reference](../observant/observable-list.md) for all callback types
```

### 4. `mkdocs.yml` (UPDATE - Add Nav Entry)

**Current State**: No "Observant Library" section in nav

**Updates Needed**:
- Add new "Observant Library" section under Reference
- Add ObservableList page (and placeholder for other observables)

**Suggested Location in Nav** (after "Classes" section, around line 97):
```yaml
  - Reference:
      - Decorators:
          # ... existing ...
      - Factories:
          # ... existing ...
      - Classes:
          - Widget: reference/classes/widget.md
          - Window: reference/classes/window.md
          - Variable: reference/classes/variable.md
      - Observant Library:  # NEW SECTION
          - ObservableList: reference/observant/observable-list.md
          # Future:
          # - Observable: reference/observant/observable.md
          # - ObservableDict: reference/observant/observable-dict.md
          # - ObservableSet: reference/observant/observable-set.md
          # - ObservableProxy: reference/observant/observable-proxy.md
      - Styles:
          # ... existing ...
```

**Rationale**: The Observant Library section belongs in Reference because:
- These are low-level primitives most users won't directly interact with
- Advanced users and contributors need complete API documentation
- It's separate from the main QtPie classes for clarity

---

## Cross-References

### Links TO ObservableList:
- `docs/state/variables.md` - Variable[list[T]] section
- `docs/reference/classes/variable.md` - Type selection table
- `docs/data/lists-dicts.md` - Could add note about underlying implementation

### Links FROM ObservableList:
- Link back to `Variable[list[T]]` as the recommended high-level API
- Link to Observable (when that page is written)
- Link to ObservableDict (when that page is written) for comparison

---

## Related Features to Document

Since ObservableList is part of the `observant` library, we should plan for documenting the other reactive primitives:

1. **Observable[T]** - Single reactive value (powers `Variable[T]` for primitives)
2. **ObservableDict[K, V]** - Reactive dictionary (powers `Variable[dict[K, V]]`)
3. **ObservableSet[T]** - Reactive set (if implemented)
4. **ObservableProxy[T]** - Reactive object wrapper (powers `Variable[MyClass]`)

These should all follow the same documentation pattern and live in `docs/reference/observant/`.

---

## Documentation Architecture Notes

### Separation of Concerns

1. **User-Facing Docs** (`docs/state/`, `docs/data/`):
   - Focus on `Variable[T]` API
   - Show practical QtPie usage patterns
   - Minimal mention of underlying observables

2. **Reference Docs** (`docs/reference/observant/`):
   - Complete API documentation for each observable type
   - Direct usage examples (without QtPie)
   - Advanced patterns and performance considerations
   - For library maintainers and power users

### Progressive Disclosure

- **Beginners**: Use Variable[list[T]], never need to know about ObservableList
- **Intermediate**: Might use `.observable.on_insert()` for granular callbacks, can click through to reference
- **Advanced**: Read complete ObservableList docs for direct usage or contributing

---

## Content Warnings & Notes

### Important Clarifications:

1. **ObservableList is not a direct user API** - Most users should use `Variable[list[T]]`
2. **Don't over-document in beginner sections** - Keep state/variables.md focused on Variable usage
3. **Reference docs should be comprehensive** - Complete API surface for contributors
4. **Avoid duplication** - Reference the ObservableList page, don't copy content

### Style Consistency:

- Match the tone and structure of existing reference pages
- Use the same code example format (type hints, pyright compliance)
- Include "See Also" sections for cross-referencing
- Add admonition blocks for important notes (use `!!! note` or `!!! warning`)

---

## Implementation Checklist

When implementing this proposal:

- [ ] Create `docs/reference/observant/observable-list.md` with complete API reference
- [ ] Add "Observant Library" section to `mkdocs.yml` nav
- [ ] Add cross-reference link in `docs/state/variables.md`
- [ ] Add cross-reference link in `docs/reference/classes/variable.md`
- [ ] Verify all code examples are tested and accurate
- [ ] Check all internal links work (run `mkdocs serve` locally)
- [ ] Consider adding a brief note in `docs/data/lists-dicts.md` about the underlying implementation (optional)
- [ ] Plan documentation for other observant primitives (Observable, ObservableDict, ObservableProxy)

---

## Future Considerations

### Complete Observant Documentation Suite

Once ObservableList is documented, we should create similar pages for:
- `Observable[T]` - The foundation (single reactive value)
- `ObservableDict[K, V]` - Reactive dictionaries
- `ObservableProxy[T]` - Reactive object wrappers
- `ObservableSet[T]` - Reactive sets (if implemented)

### Observant Library Overview Page

Consider adding `docs/reference/observant/index.md` as an overview:
- What is the observant library
- When to use each primitive
- How they integrate with QtPie's Variable system
- Architecture diagram showing relationships
- Migration guide from direct observable usage to Variable

### Examples Page

The existing `docs/examples.md` could include an advanced section showing:
- Direct ObservableList usage
- Building custom reactive patterns
- Integrating observables with non-Qt code

---

## Conclusion

ObservableList is important infrastructure that deserves complete documentation, but as a **reference page** rather than beginner-focused content. The existing Variable[list[T]] documentation already covers the user-facing API well. This proposal adds the technical depth needed for advanced users and contributors while maintaining the progressive disclosure principle of the overall documentation structure.
