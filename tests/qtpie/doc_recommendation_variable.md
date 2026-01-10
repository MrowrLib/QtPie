# Documentation Recommendation: Variable Feature Coverage

## Overview

The test summary file `test_variable.md` documents low-level technical behaviors of the `Variable[T]` class. Most of these features are **already well-documented** in `docs/state/variables.md`, which is comprehensive and user-friendly. This recommendation focuses on identifying any gaps and ensuring completeness.

## Current Documentation Status

The existing `docs/state/variables.md` (556 lines) is **excellent** and covers:
- Variable[T] basic usage
- Direct assignment
- Per-instance state
- Reactivity with `.observable`
- Variable[list[T]], Variable[dict[K,V]], Variable[MyClass]
- Variable[T, W] with widgets
- Augmented assignment operators (+=, -=, etc.)
- Dirty tracking
- Type conversion in bindings

## Files to Update

### 1. `docs/state/variables.md` - Minor additions

**Current status**: Already comprehensive, but could add small clarifications.

**Additions needed**:

- **Section on using `new()` with regular types** (non-Variable)
  - Location: Add as subsection after "Variable[T] - Basic Reactive State" section
  - Content: Document that `new()` also works for instantiating regular classes (not just Variables)
  - Code example from test:
    ```python
    class Greeter:
        def __init__(self, name: str) -> None:
            self.name = name

    @new_fields
    class MyClass:
        _greeter: Greeter = new("Alice")

    obj = MyClass()
    assert obj._greeter.name == "Alice"
    ```
  - Rationale: This is a core `new()` capability that applies to all fields, not just Variables. Currently mentioned implicitly but not explicitly documented.

- **Clarify reactivity triggers for augmented assignment**
  - Location: Update existing "Augmented Assignment Operators" section
  - Add explicit note: "All augmented assignments trigger change callbacks, just like `.value` assignment."
  - Already present in current docs, but could emphasize with example showing callback being triggered

### 2. `docs/reference/factories/new.md` - Document non-Variable usage

**Current status**: Likely focuses on Variable usage primarily.

**Addition needed**:
- Add section "Using new() with Regular Classes"
- Explain that `new()` is a general factory for instantiating any type, not just Variables
- Show examples of instantiating custom classes with positional and keyword args
- Code examples:
  ```python
  class Config:
      def __init__(self, *, host: str, port: int) -> None:
          self.host = host
          self.port = port

  @widget
  class MyWidget(Widget):
      _config: Config = new(host="localhost", port=8080)
  ```

## Files to Add

**None** - All Variable functionality is appropriately documented in existing files.

## Files NOT Needing Updates

The following pages are complete as-is:
- `docs/state/bindings.md` - Already covers binding Variables to widgets
- `docs/data/dirty-tracking.md` - Already covers Variable dirty tracking
- `docs/state/format-expressions.md` - Already covers expressions with Variables
- `docs/state/property-bindings.md` - Already covers Variable usage in property bindings

## Suggested Location in Nav

No changes needed - `state/variables.md` is already correctly placed under "Reactive State" section in the navigation.

## Content Outline

### For `docs/state/variables.md` additions:

#### New subsection: "Using new() with Regular Classes" (after intro)

- Explain `new()` works for any type, not just Variables
- Show instantiation with positional args
- Show instantiation with keyword args
- Brief note that QtPie-specific kwargs (bind=, clicked=, etc.) only apply to widgets
- Position: After "Variable[T] - Basic Reactive State" intro, before "Creating Variables"

### For `docs/reference/factories/new.md` additions:

#### New section: "Instantiating Regular Classes"

- Purpose: Document that `new()` is a universal field factory
- Distinguish Variable vs non-Variable behavior
- Show custom class examples
- Explain args/kwargs forwarding to constructor
- Cross-reference to Variable docs for Variable-specific behavior

## Code Examples Needed

From test summary, include these examples:

1. **Regular class instantiation** (both docs):
   ```python
   class Greeter:
       def __init__(self, name: str) -> None:
           self.name = name

   @widget
   class MyWidget(Widget):
       _greeter: Greeter = new("Alice")
   ```

2. **Kwargs instantiation** (both docs):
   ```python
   class Config:
       def __init__(self, *, host: str, port: int) -> None:
           self.host = host
           self.port = port

   @widget
   class MyWidget(Widget):
       _config: Config = new(host="localhost", port=8080)
   ```

3. **Augmented assignment with callback** (variables.md only):
   ```python
   @widget
   class Counter(Widget):
       _count: Variable[int] = new(0)

       def __setup__(self) -> None:
           self._count.observable.on_change(self._on_change)

       def _on_change(self, value: int) -> None:
           print(f"Count changed to: {value}")

       def increment(self) -> None:
           self._count += 1  # Triggers _on_change callback
   ```

## Cross-References

### Variables page should link to:
- `reference/factories/new.md` - When introducing `new()` for non-Variable usage
- Already has good links to bindings, dirty tracking, format expressions

### new() reference should link to:
- `state/variables.md` - For Variable-specific behavior
- `basics/widgets.md` - For general widget field usage

## Priority

**Low Priority** - The test file documents implementation details and edge cases that are already well-covered in user-facing documentation. The main gaps are:

1. **Minor gap**: Explicit documentation of `new()` working with regular (non-Variable) classes
2. **Already covered**: Everything else (reactivity, augmented assignment, dirty tracking, per-instance state, Observable wrappers)

The current documentation is production-ready and comprehensive for end users. These additions would provide completeness for power users who want to understand all capabilities of `new()`, but are not critical for typical usage.

## Summary

The Variable feature is **already excellently documented**. The test summary primarily validates implementation details that are transparent to users. The only documentation gap is explicitly showing that `new()` works for regular class instantiation (not just Variables), which is a 5-minute addition to two existing pages.

**Recommendation**: Make the minor additions to `variables.md` and `new.md` to explicitly document regular class instantiation with `new()`, but no major documentation work is needed for the Variable feature.
