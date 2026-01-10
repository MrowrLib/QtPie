# Documentation Proposal: Observable Dirty Tracking

## Overview

This feature describes dirty state tracking for `Observable[T]` - tracking whether a value has changed from its initial/baseline state. This is a low-level reactive primitive in the `observant` library that powers QtPie's higher-level dirty tracking features.

## Files to Add

### 1. `docs/reference/observables/dirty-tracking.md`

**Rationale:** This is an advanced observant library feature that deserves its own reference page. It's more technical than the QtPie-level dirty tracking and belongs in a dedicated reference section.

**Content Outline:**

- **Overview:** What is dirty tracking and why it matters
- **Basic Usage:**
  - `is_dirty` property returns `Observable[bool]`
  - Setting value to something different marks as dirty
  - Setting value back to original marks as clean
- **Reset Dirty:**
  - `reset_dirty()` sets new baseline
  - Use cases: after saving data, after user confirms changes
- **State Transition Callbacks:**
  - `is_dirty.on_change()` fires only on clean ↔ dirty transitions
  - Contrast with value changes (every change fires)
  - Use case: enabling/disabling save buttons efficiently
- **Boolean Conversion:**
  - `bool(obs)` checks truthiness of wrapped value (not dirty state)
  - `bool(obs.is_dirty)` checks dirty state explicitly
  - Common pitfall: confusion between the two
- **Integration with QtPie:**
  - Brief mention of how Widget uses this
  - Link to Widget-level dirty tracking docs

**Code Examples Needed:**

1. Basic dirty detection (from test: set/change/revert)
2. Reset dirty workflow (from test: reset and new baseline)
3. State transition callbacks (from test: only fires on transitions)
4. Boolean conversion clarification
5. Practical example: form save button enable/disable

## Files to Update

### 1. `docs/data/dirty-tracking.md` (existing Widget-level docs)

**Updates:**

- **Add "Under the Hood" section** at the end:
  - Brief explanation that Widget dirty tracking uses Observable dirty tracking
  - Link to `docs/reference/observables/dirty-tracking.md` for advanced use cases
  - Note: Most users won't need Observable-level dirty tracking directly

- **Add cross-reference** in the introduction:
  - Mention that individual `Variable[T]` fields have their own dirty state
  - Link to Observable dirty tracking for field-level control

**Content to Add:**

```markdown
## Under the Hood

Widget dirty tracking uses the `Observable` dirty tracking feature from the `observant` library. Each `Variable[T]` field tracks its own dirty state via `Observable.is_dirty`.

For advanced scenarios where you need field-level dirty control:

- Access individual field dirty state: `self._name.observable.is_dirty`
- Reset a single field: `self._name.observable.reset_dirty()`
- React to field-level transitions: `self._name.observable.is_dirty.on_change(callback)`

See [Observable Dirty Tracking](../reference/observables/dirty-tracking.md) for details.
```

### 2. `docs/state/variables.md` (existing Variable docs)

**Updates:**

- **Add "Dirty State" subsection** under Variable features:
  - Each Variable tracks if its value changed from initial/baseline
  - Access via `my_var.observable.is_dirty`
  - Link to Observable dirty tracking reference

**Content to Add:**

```markdown
### Dirty State

Each `Variable[T]` tracks whether its value has changed from the initial/baseline:

```python
_name: Variable[str] = new("Alice")

# Later...
self._name.value = "Bob"
print(self._name.observable.is_dirty.get())  # True

self._name.value = "Alice"  # Back to original
print(self._name.observable.is_dirty.get())  # False
```

This is useful for:

- Individual field validation
- Conditional formatting (highlight changed fields)
- Granular save operations (save only changed fields)

For widget-level dirty tracking (all fields), see [Dirty Tracking](../data/dirty-tracking.md).

For advanced Observable dirty features, see [Observable Dirty Tracking](../reference/observables/dirty-tracking.md).
```

### 3. `docs/reference/classes/variable.md` (Variable API reference)

**Updates:**

- **Add to API listing:**
  - `observable.is_dirty: Observable[bool]` - Dirty state tracking
  - `observable.reset_dirty() -> None` - Reset dirty baseline

- **Add code example** showing field-level dirty access

## Suggested Location in Nav

Update `mkdocs.yml`:

```yaml
nav:
  # ... existing sections ...

  - Reference:
      - Decorators: # ... existing
      - Factories: # ... existing
      - Classes:
          - Widget: reference/classes/widget.md
          - Window: reference/classes/window.md
          - Variable: reference/classes/variable.md
      - Observables:  # NEW SECTION
          - Dirty Tracking: reference/observables/dirty-tracking.md
          - Observable: reference/observables/observable.md  # Future
          - ObservableList: reference/observables/observable-list.md  # Future
          - ObservableDict: reference/observables/observable-dict.md  # Future
          - ObservableProxy: reference/observables/observable-proxy.md  # Future
      - Styles: # ... existing
```

**Rationale:**

- Creates new "Observables" section under Reference for low-level reactive primitives
- Keeps it separate from user-facing Variable/Widget APIs
- Provides structure for future Observable* reference docs
- Dirty tracking goes first as it's most commonly needed

## Cross-References

### Pages that should link TO this feature:

1. **`docs/data/dirty-tracking.md`** → Link to Observable dirty tracking in "Under the Hood" section
2. **`docs/state/variables.md`** → Link in "Dirty State" subsection for advanced usage
3. **`docs/reference/classes/variable.md`** → Link from `observable.is_dirty` API documentation
4. **`docs/start/concepts.md`** → If it has a "Reactivity" section, briefly mention Observable primitives with link

### Pages this feature should link TO:

1. **`docs/data/dirty-tracking.md`** → Link from Observable page as "See also: Widget-level dirty tracking"
2. **`docs/state/variables.md`** → Link for context about how Variables use Observables
3. **`docs/reference/classes/variable.md`** → Link to Variable API for accessing `observable` property

## Priority

**Priority: Low/Advanced**

**Reasoning:**

1. **Not a beginner feature:** Most users will use Widget-level `is_dirty` and `reset_dirty()` without needing to understand Observable internals
2. **Advanced use cases only:** Direct Observable dirty tracking is for:
   - Field-level dirty control
   - Custom reactive primitives
   - Library developers extending QtPie
3. **Documentation order:** Should be documented AFTER:
   - Widget/Variable basics
   - Widget-level dirty tracking
   - Basic reactive concepts
4. **Reference material:** Belongs in reference docs, not getting-started guides

**Placement in learning path:**

- **Beginners:** Start with Widget dirty tracking (simple, high-level)
- **Intermediate:** Learn Variable dirty access for field-level control
- **Advanced:** Read Observable dirty tracking for deep understanding or custom implementations

## Implementation Notes

### Documentation Style

- **Reference tone:** Technical, precise, API-focused
- **Contrast with Widget docs:** Widget dirty docs are tutorial-style, Observable docs are reference-style
- **Code examples:** Short, focused on specific API features
- **Avoid duplication:** Don't repeat Widget dirty tracking content - link to it instead

### Common Pitfalls to Document

1. **Boolean confusion:** `bool(obs)` vs `bool(obs.is_dirty)` - very common mistake
2. **State transition callbacks:** Users may expect callbacks on every value change
3. **Reset timing:** When to call `reset_dirty()` (after save, not before)
4. **Direct Observable access:** Most users should use Widget/Variable APIs, not Observable directly

### Future Expansion

This page sets the pattern for other Observable reference docs:

- `docs/reference/observables/observable.md` - Core Observable API
- `docs/reference/observables/observable-list.md` - List reactivity
- `docs/reference/observables/observable-dict.md` - Dict reactivity
- `docs/reference/observables/observable-proxy.md` - Object field reactivity

Keep the structure consistent across all Observable reference pages.

## Summary

**Scope:** Small feature, but important foundation for understanding Widget dirty tracking.

**Documentation approach:**

- Primary: New reference page for Observable dirty tracking
- Secondary: Cross-references from Widget/Variable docs
- Emphasis: This is an advanced/internal feature - most users won't use it directly

**User journey:**

1. User learns Widget dirty tracking (high-level, tutorial-style)
2. User discovers they need field-level control
3. User finds link to Observable dirty tracking (low-level, reference-style)
4. User understands the underlying mechanism and can build custom solutions

This approach keeps beginners from getting overwhelmed while providing advanced users with the details they need.
