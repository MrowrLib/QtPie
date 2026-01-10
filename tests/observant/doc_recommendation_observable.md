# Documentation Proposal: Observable[T]

## Overview

`Observable[T]` is a low-level reactive primitive from the `observant` library. It's a foundational building block used internally by QtPie's `Variable[T]`, but can also be used directly for custom reactive patterns.

## 1. Files to Add

### `docs/advanced/observant-primitives.md`

A new page documenting the low-level observant library primitives for advanced users who want to build custom reactive patterns or understand QtPie's internals.

**Rationale:** Observable is an advanced/internal API. Most users should use `Variable[T]` instead. This page serves users who need deeper control or want to understand how QtPie's reactivity works under the hood.

## 2. Files to Update

### `docs/state/variables.md`

Add a brief section at the end linking to the observant primitives page:

- **Section:** "Under the Hood" or "Advanced: Observable[T]"
- **Content:** 2-3 paragraph explanation that `Variable[T]` is built on top of `Observable[T]`, with a link to the advanced docs
- **Why:** Users learning about Variables should know where the reactivity comes from, but it shouldn't distract from the main Variable[T] documentation

### `docs/reference/classes/variable.md`

Add a subsection in the API reference:

- **Section:** "Related Classes"
- **Content:** Link to Observable[T] documentation and explain the relationship
- **Why:** API reference should show the complete picture of class hierarchy

### `docs/index.md`

No changes needed - Observable is too low-level to mention on the homepage.

## 3. Suggested Location in Nav

```yaml
nav:
  # ... existing sections ...
  - Advanced:
      - Observant Primitives: advanced/observant-primitives.md
      - Custom Reactive Patterns: advanced/custom-reactive.md  # future
      - Architecture: advanced/architecture.md  # future
```

**Note:** This creates a new "Advanced" section in the nav. Observable[T] documentation belongs here because:
- It's internal/foundational rather than user-facing
- Most users will use `Variable[T]` instead
- It's for those who want to extend QtPie or build custom reactive patterns

## 4. Content Outline

### `docs/advanced/observant-primitives.md`

```markdown
# Observant Primitives

## Overview
- What is the observant library
- Relationship to QtPie (internal foundation)
- When to use primitives directly vs Variable[T]

## Observable[T]

### What is Observable[T]?
- Lightweight reactive value container
- Foundation for Variable[T]
- Used for building custom reactive patterns

### Basic Usage
- Creating an Observable
- Getting and setting values
- Type parameterization

### Change Callbacks
- Registering callbacks with on_change()
- Multiple callbacks
- Callback execution order (all fire)
- Automatic deduplication

### Type Support
- Works with any Python type
- Type safety with generics
- Examples: int, str, float, list, custom classes

### When to Use Observable[T] vs Variable[T]
- Variable[T]: For UI-bound reactive state (recommended)
- Observable[T]: For non-UI reactive logic, custom patterns

### Performance Characteristics
- Lightweight (minimal overhead)
- No automatic UI updates (that's Variable's job)

## Other Observant Primitives (brief overview)
- ObservableList[T] - reactive lists
- ObservableDict[K, V] - reactive dicts
- ObservableProxy[T] - reactive objects
- Links to their respective docs (when written)

## Building Custom Reactive Patterns
- Example: Creating a computed value
- Example: Chaining observables
- Example: Custom reactive data structure
```

### `docs/state/variables.md` (additions)

```markdown
# Variables

[... existing content ...]

## Under the Hood

`Variable[T]` is built on top of `Observable[T]` from the observant library. Observable provides the low-level reactive primitive (value storage + change callbacks), while Variable adds:

- Integration with QtPie widgets
- Automatic UI updates via bindings
- Widget type parameter (`Variable[T, W]`)
- Format expression evaluation

For most QtPie users, `Variable[T]` is the right choice. However, if you're building custom reactive patterns or need reactivity without UI integration, you can use `Observable[T]` directly. See [Observant Primitives](../advanced/observant-primitives.md) for details.
```

### `docs/reference/classes/variable.md` (additions)

```markdown
# Variable[T] Reference

[... existing content ...]

## Related Classes

### Observable[T]

`Variable[T]` inherits from or wraps `Observable[T]` (implementation detail). Observable provides the core reactive value storage and change notification system.

For advanced use cases requiring custom reactive patterns without UI integration, see [Observable[T]](../../advanced/observant-primitives.md#observablet).
```

## 5. Code Examples Needed

### From test_observable.md:

1. **Basic value storage** (get/set):
   ```python
   from observant import Observable

   obs = Observable[int](42)
   print(obs.get())  # 42

   obs.set(100)
   print(obs.get())  # 100
   ```

2. **Change callbacks**:
   ```python
   obs = Observable[int](0)
   received: list[int] = []

   obs.on_change(lambda v: received.append(v))
   obs.set(1)
   obs.set(2)

   print(received)  # [1, 2]
   ```

3. **Multiple callbacks**:
   ```python
   obs = Observable[int](0)
   results: list[str] = []

   obs.on_change(lambda v: results.append(f"a:{v}"))
   obs.on_change(lambda v: results.append(f"b:{v}"))
   obs.set(5)

   print(results)  # ["a:5", "b:5"]
   ```

4. **Callback deduplication**:
   ```python
   count = [0]

   def increment(_: int) -> None:
       count[0] += 1

   obs = Observable[int](0)
   obs.on_change(increment)
   obs.on_change(increment)  # Same callback - deduplicated
   obs.set(1)

   print(count[0])  # 1 (not 2!)
   ```

5. **Type support examples**:
   ```python
   str_obs = Observable[str]("hello")
   float_obs = Observable[float](3.14)
   list_obs = Observable[list[int]]([1, 2, 3])

   # Even custom types
   @dataclass
   class Person:
       name: str
       age: int

   person_obs = Observable[Person](Person("Alice", 30))
   ```

### Additional examples to create:

1. **Comparison with Variable[T]**:
   ```python
   # Observable - no UI integration
   obs = Observable[int](0)
   obs.on_change(lambda v: print(f"Value changed: {v}"))

   # Variable - automatic UI updates
   @widget
   class Example(Widget):
       _count: Variable[int] = new(0)
       _label: QLabel = new(bind="Count: {_count}")
       # No manual on_change needed - binding handles it!
   ```

2. **Custom reactive pattern** (computed value):
   ```python
   from observant import Observable

   x = Observable[int](5)
   y = Observable[int](10)
   sum_obs = Observable[int](x.get() + y.get())

   # Update sum when either x or y changes
   def update_sum(_):
       sum_obs.set(x.get() + y.get())

   x.on_change(update_sum)
   y.on_change(update_sum)

   print(sum_obs.get())  # 15
   x.set(20)
   print(sum_obs.get())  # 30
   ```

## 6. Cross-References

### Links TO Observable[T]:
- From `docs/state/variables.md` - "Under the Hood" section
- From `docs/reference/classes/variable.md` - "Related Classes"
- From future `docs/advanced/architecture.md` - QtPie internals
- From future `docs/advanced/custom-reactive.md` - Building custom patterns

### Links FROM Observable[T]:
- To `docs/state/variables.md` - Recommend Variable for UI use cases
- To future `docs/advanced/observant-primitives.md#observablelist` - Other primitives
- To future `docs/advanced/observant-primitives.md#observabledict`
- To future `docs/advanced/observant-primitives.md#observableproxy`
- To `docs/start/concepts.md` - Back to core concepts if user is lost

## 7. Priority

**Priority: LOW** (defer until core docs are complete)

**Reasoning:**

1. **Internal API**: Observable[T] is a foundational primitive, not a user-facing feature. Most QtPie users will never need to use it directly.

2. **Variable[T] is sufficient**: The vast majority of use cases are covered by `Variable[T]`, which has Observable's functionality plus UI integration.

3. **Documentation sequence**: Users should learn:
   1. Basic widgets (high priority)
   2. Variables and bindings (high priority)
   3. Advanced patterns (medium priority)
   4. Internal primitives (low priority)

4. **Advanced audience**: Only users building custom reactive patterns or wanting to understand QtPie internals need this documentation.

5. **Complete the pyramid first**: Before documenting low-level primitives, ensure all high-level user-facing features are documented.

**Recommended timeline:**
- Phase 1 (now): Document Widget, Variable, bindings, records, validation
- Phase 2 (later): Document advanced guides, async, testing
- Phase 3 (much later): Document internal primitives like Observable[T]

## 8. Notes

### Documentation Style

- Use **admonition boxes** to warn users:
  ```markdown
  !!! note "Most users don't need this"
      If you're building a QtPie widget, use `Variable[T]` instead.
      Observable[T] is for custom reactive patterns and internal use.
  ```

- Emphasize the **distinction** between Observable (general reactivity) and Variable (UI-integrated reactivity)

- Provide **practical examples** showing when Observable is useful vs overkill

### Testing Note

The test file `test_observable.md` provides excellent coverage of the basic API surface. The documentation should mirror this structure but add context about:
- Why you'd use Observable vs Variable
- How it fits into QtPie's architecture
- Real-world use cases beyond simple examples

### Future Considerations

When writing this documentation, leave room for:
- ObservableList[T] documentation
- ObservableDict[K, V] documentation
- ObservableProxy[T] documentation
- "Building Custom Observables" tutorial
- Performance comparison between primitives
