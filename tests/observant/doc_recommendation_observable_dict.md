# Documentation Proposal: ObservableDict

## Overview

`ObservableDict` is a core reactive primitive from the observant library that provides a dictionary with granular change callbacks and dirty tracking. While currently mentioned in passing in QtPie docs, it deserves comprehensive standalone documentation as users may interact with it directly via `Variable[dict[K, V]].observable`.

## 1. Files to Add

### `docs/reference/observant/observable-dict.md`

A comprehensive reference page dedicated to `ObservableDict[K, V]`.

**Rationale**: This is a foundational reactive primitive with rich functionality (insert/replace/remove/clear callbacks, dirty tracking, standard dict interface). Users working with dict-based state need clear documentation, especially when using `.observable` for advanced operations.

## 2. Files to Update

### `docs/reference/classes/variable.md`

**Updates needed**:
- Fix broken reference link at line 591: `[ObservableDict](./observable-dict.md)` currently points to non-existent page
- Expand the `ObservableDict[K, V]` section (lines 165-167) with more detailed examples of granular callbacks
- Add cross-reference to new standalone `observable-dict.md` page

### `docs/data/lists-dicts.md`

**Updates needed**:
- Add section "Advanced: Direct ObservableDict Access" after line 477
- Document granular callbacks (`on_insert`, `on_replace`, `on_remove`, `on_clear`) for users who need fine-grained control
- Link to new `docs/reference/observant/observable-dict.md` for complete API reference
- Add example showing when/why to use `.observable` vs direct Variable access

### `docs/index.md` or `docs/start/concepts.md`

**Updates needed**:
- Add brief mention of observant library primitives in "Key Features" or "Key Concepts"
- Link to observant reference documentation for users who want to understand the underlying reactivity system

## 3. Suggested Location in Nav

Add new section to `mkdocs.yml`:

```yaml
nav:
  # ... existing sections ...
  - Reference:
      # ... existing decorator/factory/class sections ...
      - Observant Library:
          - Overview: reference/observant/index.md
          - Observable: reference/observant/observable.md
          - ObservableList: reference/observant/observable-list.md
          - ObservableDict: reference/observant/observable-dict.md
          - ObservableProxy: reference/observant/observable-proxy.md
```

**Rationale**: Place observant docs under Reference since they are lower-level primitives. Most users interact with `Variable`, but advanced users need to access `.observable` for granular control.

## 4. Content Outline

### `docs/reference/observant/observable-dict.md`

1. **Introduction**
   - What is ObservableDict
   - When to use it directly (via `Variable[dict[K, V]].observable`)
   - Key features: standard dict interface, granular callbacks, dirty tracking

2. **Basic Usage**
   - Construction: `ObservableDict[str, int]()` and `ObservableDict[str, int]({"a": 1})`
   - Standard dict operations: `[]`, `del`, `get()`, `update()`, `setdefault()`
   - Iteration and utility methods: `keys()`, `values()`, `items()`, `len()`, `in`

3. **Change Callbacks**
   - Generic `on_change()` - fires on any modification
   - When `on_change` fires vs doesn't fire (e.g., `setdefault` on existing key)

4. **Granular Callbacks**
   - `on_insert(callback)` - new keys only (not updates)
     - Works with `[]`, `setdefault()`, `update()`
     - Callback signature: `(key: K, value: V) -> None`
   - `on_replace(callback)` - existing keys only (not inserts)
     - Provides old and new values
     - Callback signature: `(key: K, old_value: V, new_value: V) -> None`
   - `on_remove(callback)` - deletion events
     - Works with `del`, `pop()`, `popitem()`
     - Not fired for `pop()` with default on missing key
     - Callback signature: `(key: K, value: V) -> None`
   - `on_clear(callback)` - clearing the dict
     - Passes dict of all removed items (even if already empty)
     - Callback signature: `(removed_items: dict[K, V]) -> None`

5. **Dirty Tracking**
   - `is_dirty` property (returns `Observable[bool]`)
   - When dict becomes dirty (any modification)
   - `reset_dirty()` - mark current state as clean
   - Automatic clean state when reverted to original state
   - Subscribing to dirty state changes

6. **Callback Management**
   - Multiple callbacks supported
   - Duplicate callbacks ignored
   - Both granular and generic callbacks fire together

7. **Type Safety**
   - Generic types: `ObservableDict[K, V]`
   - Full pyright strict compliance
   - Type inference examples

8. **Common Patterns**
   - Score tracking with insert/replace callbacks
   - Undo/redo with dirty tracking
   - Live search/filter with change callbacks
   - Cache invalidation on specific key changes

9. **API Reference Table**
   - Method signatures
   - Callback signatures
   - Properties

10. **See Also**
    - `Variable[dict[K, V]]` - Higher-level wrapper
    - `Observable[T]` - Single-value primitive
    - `ObservableList[T]` - List equivalent
    - Data & Forms: Lists & Dicts guide

### `docs/reference/observant/index.md` (Overview page)

1. **What is Observant**
   - Reactive primitives library integrated into QtPie
   - Similar to MobX, Vue reactivity, etc.
   - Accessed via `Variable[T].observable`

2. **When to Use Observant Directly**
   - Most users only need `Variable[T]`
   - Direct observant access for granular callbacks
   - Performance-critical scenarios
   - Custom reactive patterns

3. **Observable Types**
   - Brief description of each with links to detail pages
   - Type selection flowchart

4. **Links to Detail Pages**

## 5. Code Examples Needed

### From Test Summary - Good Examples to Include:

1. **Basic dict operations** (lines 7-20 of test summary)
   - Shows standard Python dict interface
   - Good for "Basic Usage" section

2. **on_change callback** (lines 43-63)
   - Generic change detection
   - Good example of when it fires vs doesn't fire

3. **Dirty tracking with revert** (lines 86-97)
   - Shows automatic clean state detection
   - Excellent for dirty tracking section

4. **is_dirty subscription** (lines 100-112)
   - Shows reactive dirty state tracking
   - Good for demonstrating Observable[bool] return type

5. **on_insert granular callback** (lines 118-147)
   - Shows distinction between insert and replace
   - Works with setdefault and update
   - Perfect for granular callbacks section

6. **on_replace granular callback** (lines 153-182)
   - Old/new value tracking
   - Complement to on_insert

7. **on_remove callback** (lines 188-217)
   - del, pop, popitem
   - Edge case: pop with default on missing key

8. **on_clear callback** (lines 223-241)
   - Passes all removed items
   - Fires even on empty dict

9. **Multiple callbacks** (lines 247-271)
   - Shows callback ordering
   - Granular + generic both fire

### Additional Examples to Create:

1. **Real-world score tracking**
```python
scores = ObservableDict[str, int]()
scores.on_insert(lambda name, score: print(f"New player: {name}"))
scores.on_replace(lambda name, old, new: print(f"{name}: {old} → {new}"))
```

2. **QtPie integration via Variable**
```python
@widget
class Scoreboard(Widget):
    _scores: Variable[dict[str, int]] = new({})

    def __setup__(self):
        # Access underlying ObservableDict for granular callbacks
        self._scores.observable.on_insert(self.on_new_player)
        self._scores.observable.on_replace(self.on_score_update)

    def on_new_player(self, name: str, score: int):
        print(f"Welcome {name}!")
```

3. **Dirty tracking for save detection**
```python
data = ObservableDict[str, str]({"title": "Doc", "author": "Alice"})
data.is_dirty.on_change(lambda dirty: save_button.setEnabled(dirty))
```

## 6. Cross-References

### Link TO (pages that should link to ObservableDict):

- `docs/reference/classes/variable.md` - Fix existing broken link, expand section
- `docs/data/lists-dicts.md` - Add "Advanced" section linking to granular callbacks
- `docs/state/variables.md` - Brief mention in "Under the hood" section
- Future `docs/reference/observant/index.md` - Overview of all primitives

### Link FROM (ObservableDict should link to):

- `Variable[dict[K, V]]` - Primary way users encounter dicts
- `ObservableList[T]` - Sister primitive with similar callback model
- `Observable[T]` - Simpler single-value primitive
- `docs/data/lists-dicts.md` - High-level guide to dict bindings in QtPie

## 7. Priority

**Medium-High Priority**

**Reasoning**:
- **Not blocking for beginners**: Most users can use `Variable[dict[K, V]]` without touching `.observable`
- **Important for intermediate/advanced users**: Those who need granular callbacks (e.g., insert vs replace) must access `.observable`
- **Currently has broken links**: `variable.md` already references non-existent pages
- **Foundation for completeness**: Part of completing the observant library documentation (Observable, ObservableList, ObservableDict, ObservableProxy)

**Suggested implementation order**:
1. First: Create `docs/reference/observant/observable-dict.md` (fixes broken link)
2. Second: Update `docs/reference/classes/variable.md` (expand examples, fix link)
3. Third: Update `docs/data/lists-dicts.md` (add advanced section)
4. Fourth: Create `docs/reference/observant/index.md` (overview page tying it all together)
5. Fifth: Create remaining observant pages (Observable, ObservableList, ObservableProxy) for completeness

## 8. Additional Notes

### Scope Considerations

- **This is library-level documentation**, not QtPie-specific. ObservableDict exists independently in the observant library.
- However, it should be documented in QtPie's docs because:
  1. Observant is bundled with QtPie
  2. Users access it via `Variable[dict[K, V]].observable`
  3. QtPie users need this for advanced scenarios

### Consistency with Existing Docs

- Follow same structure as existing `docs/reference/classes/variable.md`
- Use similar code style (pyright strict, type annotations)
- Include both standalone examples and QtPie integration examples
- Maintain "See Also" sections for cross-linking

### Future Work

After ObservableDict documentation:
- Document remaining observant primitives (Observable, ObservableList, ObservableProxy)
- Create observant overview/architecture page
- Add observant migration/integration guide for users coming from other reactive systems
- Consider advanced topics: performance tuning, custom observables, callback ordering guarantees
