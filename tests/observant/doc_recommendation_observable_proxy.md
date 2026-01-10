# Documentation Proposal: ObservableProxy

## Overview

`ObservableProxy[T]` is a **foundational reactive primitive** from the `observant` library that wraps any object and makes its fields reactive. It is already being used extensively in QtPie (as `self.record` in `Widget[T]`), but the implementation details and standalone usage are not documented.

## Priority

**Medium-High Priority** - This is an advanced/internal feature that power users need to understand:
- Users working with `Widget[T]` already interact with ObservableProxy indirectly via `self.record`
- Advanced users may want to use ObservableProxy directly for custom reactive patterns
- Understanding ObservableProxy helps explain how `Widget[T]` works under the hood

## Recommendation

**Add as a section to existing documentation** rather than creating new pages. The feature is already documented indirectly through `Widget[T]`, but lacks technical details.

---

## Files to Update

### 1. **C:\Code\mrowr\MrowrLib\QtPie-v2\docs\data\records.md**

**Why:** This page already documents `Widget[T]` and mentions that `self.record` is an `ObservableProxy[T]`, but doesn't explain what that means or how it works.

**New Section to Add:** "Understanding ObservableProxy" (after "Accessing the Record" section)

**Content Outline:**
- Brief explanation: ObservableProxy wraps objects and makes fields reactive
- How it works with `self.record` in `Widget[T]`
- Field access returns `Observable[T]` objects
- Direct assignment vs `.set()` methods
- Change callbacks at proxy level vs field level
- Automatic wrapping of nested objects, lists, and dicts
- Link to reference documentation for advanced usage

**Code Examples Needed:**
```python
# Show that record.name returns an Observable
editor = PersonEditor()
name_observable = editor.record.name  # Observable[str]
print(name_observable.get())  # "Alice"

# Direct assignment
editor.record.name = "Bob"  # Syntactic sugar for .set()

# Field-level callbacks
editor.record.name.on_change(lambda v: print(f"Name changed to {v}"))

# Proxy-level callbacks (any field change)
def on_any_change():
    print("Something changed!")
editor.record.on_change(on_any_change)
```

---

### 2. **C:\Code\mrowr\MrowrLib\QtPie-v2\docs\data\dirty-tracking.md**

**Why:** Dirty tracking in `Widget[T]` is powered by ObservableProxy's dirty tracking, but this isn't explained.

**New Section to Add:** "Record Dirty Tracking" (after "Basic Dirty Tracking" section, before "Lifecycle Hook")

**Content Outline:**
- Explain that `Widget[T]` records use ObservableProxy's built-in dirty tracking
- How `record_state.is_dirty` relates to the proxy's dirty tracking
- Nested object changes propagate dirty state
- List and dict field modifications mark dirty
- Brief mention that dirty tracking can be disabled (for advanced cases)

**Code Examples Needed:**
```python
@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()

editor = PersonEditor()

# Record modifications track dirty
editor.record.name = "Bob"
print(editor.record_state.is_dirty.get())  # True

# Nested objects propagate dirty state
editor.record.address.city = "NYC"
print(editor.record_state.is_dirty.get())  # Still True

# Reset dirty
editor.record.reset_dirty()
print(editor.record_state.is_dirty.get())  # False
```

---

### 3. **C:\Code\mrowr\MrowrLib\QtPie-v2\docs\start\concepts.md**

**Why:** The "Widget[T] - Record Types" section mentions ObservableProxy but doesn't explain what it is.

**Update Existing Section:** "Widget[T] - Record Types"

**Changes:**
- Add 1-2 sentences explaining ObservableProxy after "Access the record:" code block
- Keep it brief - just enough context so beginners aren't confused by the term
- Link to the detailed explanation in records.md

**New Content:**
```markdown
The `record` property returns an `ObservableProxy[Person]` - a wrapper that makes all fields reactive. This means changes to `person.name` or `person.age` automatically update bound widgets. See [Records](../data/records.md) for full details.
```

---

## Files to Add

### 1. **C:\Code\mrowr\MrowrLib\QtPie-v2\docs\reference\observant\observable-proxy.md** (NEW)

**Why:** Create a dedicated reference page for developers who want to use ObservableProxy directly or understand its API in depth.

**Location in Nav:** Under a new "Reference > Observant" section

**Content Outline:**

#### Introduction
- What is ObservableProxy
- Part of the observant library
- Used internally by QtPie's `Widget[T]`
- Can be used standalone for custom reactive patterns

#### Creating a Proxy
- Basic usage: `ObservableProxy(obj)`
- Optional: `dirty_tracking=False` parameter
- Type parameter: `ObservableProxy[T]`

#### Field Access
- Accessing fields returns `Observable[T]`
- Using `.get()` and `.set()` methods
- Direct assignment (syntactic sugar)
- Type safety with pyright

#### Change Callbacks
- Proxy-level: `proxy.on_change(callback)`
- Field-level: `proxy.field.on_change(callback)`
- When each fires
- Callback signatures

#### Dirty Tracking
- What is tracked
- `is_dirty` property (returns `Observable[bool]`)
- `dirty_fields` property
- `reset_dirty()` method
- Observing dirty state changes
- Disabling dirty tracking

#### Nested Objects
- Automatic recursive wrapping
- Change propagation
- Dirty state propagation

#### Collection Fields
- Automatic wrapping of lists as `ObservableList`
- Automatic wrapping of dicts as `ObservableDict`
- Modifications trigger callbacks and dirty tracking

#### Advanced Usage
- When to use ObservableProxy vs Variable
- Using outside of QtPie widgets
- Performance considerations
- Limitations (frozen dataclasses, __slots__, etc.)

**Code Examples Needed:**
- All examples from test_observable_proxy.md
- Practical standalone usage (non-QtPie context)
- Comparison with Variable[T]

---

## Suggested Location in Nav (mkdocs.yml)

Add a new "Observant" subsection under "Reference":

```yaml
  - Reference:
      - Decorators:
          - "@widget": reference/decorators/widget.md
          - "@window": reference/decorators/window.md
          - "@menu": reference/decorators/menu.md
          - "@slot": reference/decorators/slot.md
          - "@entrypoint": reference/decorators/entrypoint.md
      - Factories:
          - "new()": reference/factories/new.md
      - Classes:
          - Widget: reference/classes/widget.md
          - Window: reference/classes/window.md
          - Variable: reference/classes/variable.md
      - Observant:  # NEW SECTION
          - ObservableProxy: reference/observant/observable-proxy.md
          - Observable: reference/observant/observable.md
          - ObservableList: reference/observant/observable-list.md
          - ObservableDict: reference/observant/observable-dict.md
      - Styles:
          - Color Schemes: reference/styles/color-schemes.md
          - Class Helpers: reference/styles/class-helpers.md
```

**Note:** Only create the ObservableProxy page initially. The other observant types can be added later as needed.

---

## Cross-References

### Pages that should link TO ObservableProxy docs:
- `docs/data/records.md` - In "Understanding ObservableProxy" section
- `docs/start/concepts.md` - Brief mention with link
- `docs/data/dirty-tracking.md` - In "Record Dirty Tracking" section
- `docs/reference/classes/variable.md` - Compare/contrast with Variable[T]

### Pages ObservableProxy docs should link TO:
- Back to `docs/data/records.md` - For Widget[T] usage
- `docs/reference/observant/observable.md` - For Observable[T] reference (if/when created)
- `docs/reference/observant/observable-list.md` - For list field behavior (if/when created)
- `docs/reference/observant/observable-dict.md` - For dict field behavior (if/when created)

---

## Code Examples Summary

**Essential examples from test summary:**

1. **Field access via Observable** - Show `.get()` and `.set()` methods
2. **Direct assignment** - Show syntactic sugar
3. **Proxy-level callbacks** - `proxy.on_change()`
4. **Field-level callbacks** - `proxy.field.on_change()`
5. **Dirty tracking basics** - `is_dirty`, `dirty_fields`, `reset_dirty()`
6. **Dirty state observation** - `is_dirty.on_change()`
7. **Nested objects** - Automatic wrapping and propagation
8. **List fields** - ObservableList wrapping
9. **Dict fields** - ObservableDict wrapping
10. **Disable dirty tracking** - Constructor parameter

**Additional examples needed:**

11. **Using with Widget[T]** - Show how it relates to `self.record`
12. **Standalone usage** - Non-QtPie reactive pattern
13. **When to use vs Variable** - Decision guide

---

## Implementation Sequence

1. **Phase 1 (High Value, Low Effort):**
   - Update `docs/start/concepts.md` with 1-2 sentence explanation
   - Update `docs/data/records.md` with "Understanding ObservableProxy" section
   - Update `docs/data/dirty-tracking.md` with "Record Dirty Tracking" section

2. **Phase 2 (Medium Priority):**
   - Create `docs/reference/observant/observable-proxy.md` full reference page
   - Update nav in `mkdocs.yml`

3. **Phase 3 (Future):**
   - Consider documenting other observant primitives (Observable, ObservableList, ObservableDict)
   - Create observant architecture overview page if warranted

---

## Notes

- **This is not a beginner feature** - Most users will interact with ObservableProxy indirectly through `Widget[T]` without needing to understand the internals
- **Type safety is critical** - All examples must show proper type annotations
- **Focus on the "why"** - Explain when and why someone would use ObservableProxy directly vs using Variable[T] or Widget[T]
- **Relationship to Widget[T]** - Make it clear this is the implementation detail behind `self.record`, not a separate concept
- **Progressive disclosure** - Brief mention in concepts.md, practical usage in records.md, full API reference in reference/observant/
