# Documentation Proposal: Observable Validation (Observant Library)

## Overview

The test file `test_validation.md` describes validation features for the **observant library** (`Observable[T]`, `ObservableList[T]`, `ObservableDict[K, V]`, `ObservableProxy[T]`). This is distinct from the existing validation documentation at `docs/data/validation.md`, which focuses on **QtPie Widget-level validation**.

The current documentation structure does not include dedicated pages for the underlying observant library primitives. This proposal addresses where and how to document the low-level observable validation API.

---

## Scope Analysis

The feature summary covers:

1. **Named validators** on `Observable[T]` (add_validator with name + callable)
2. **Validation errors** (structured dict by validator name + flat list of messages)
3. **Reactive validation** (`is_valid` as an `Observable[bool]`, auto-runs on value change)
4. **List validation** (`ObservableList[T]` validators receive entire list)
5. **Dict validation** (`ObservableDict[K, V]` validators receive entire dict)
6. **Proxy field validation** (`ObservableProxy[T]` fields can have individual validators)
7. **Proxy object validation** (`ObservableProxy[T]` can validate the entire object)
8. **Invalid fields list** (`ObservableProxy[T]` exposes which fields are currently invalid)

---

## Current Documentation Gaps

### What Exists
- **`docs/data/validation.md`**: Widget-level validation using `validate=` parameter in QtPie
- **`docs/reference/classes/variable.md`**: Brief mention of `.add_validator()` method on Variable

### What's Missing
- **No observant library documentation**: The underlying `Observable`, `ObservableList`, `ObservableDict`, `ObservableProxy` classes are not documented anywhere in the public docs
- **No low-level validation docs**: The test summary describes validation on raw observables, but users only see the Widget-level abstraction

### Should This Be Documented Publicly?

**Decision Point**: Is the observant library an **internal implementation detail** or a **public API**?

- **If internal**: Minimal or no public docs needed (internal developer reference only)
- **If public**: Needs full reference documentation

**Current Evidence**:
- `CLAUDE.md` describes observant as part of the project structure
- `docs/reference/classes/variable.md` mentions `.observable` property for "advanced operations"
- The Variable API exposes observables directly via `.observable`

**Recommendation**: **Semi-public API** - users who want advanced features will reach for `.observable`, so basic reference docs are valuable, but they belong in an "Advanced" or "Reference" section, not the main learning path.

---

## Files to Add

### 1. `docs/advanced/observant.md`
**New section in nav**: "Advanced" (between "Guides" and "Reference")

**Purpose**: Overview page for the observant library

**Content Outline**:
- What is observant? (reactive primitives underlying QtPie)
- When to use observant directly vs QtPie Variable
- Link to individual observable type pages
- Brief code example showing `.observable` access from Variable

### 2. `docs/advanced/observable.md`
**Purpose**: Reference for `Observable[T]` (single reactive value)

**Content Outline**:
- Basic usage (create, get, set)
- Change callbacks (`on_change`)
- Validation:
  - `add_validator(name, callable)` - add named validator
  - `remove_validator(name)` - remove validator by name
  - `is_valid` - reactive boolean observable
  - `validation_errors` - dict of {validator_name: [errors]}
  - `validation_error_messages` - flat list of error strings
- Dirty tracking (`.is_dirty`, `.reset_dirty()`)
- Code examples from test summary

### 3. `docs/advanced/observable-list.md`
**Purpose**: Reference for `ObservableList[T]`

**Content Outline**:
- List operations (append, insert, remove, etc.)
- Granular callbacks (`on_insert`, `on_remove`, `on_clear`)
- Validation:
  - Validators receive entire list
  - Example: max length validation
- Dirty tracking

### 4. `docs/advanced/observable-dict.md`
**Purpose**: Reference for `ObservableDict[K, V]`

**Content Outline**:
- Dict operations (set, delete, update)
- Granular callbacks (`on_set`, `on_delete`, `on_clear`)
- Validation:
  - Validators receive entire dict
  - Example: required keys validation
- Dirty tracking

### 5. `docs/advanced/observable-proxy.md`
**Purpose**: Reference for `ObservableProxy[T]` (reactive object wrapper)

**Content Outline**:
- Field access (reactive get/set)
- Field-level validation:
  - Individual field validators
  - `invalid_fields` property - list of currently invalid field names
- Object-level validation:
  - Validators on entire object
  - Example: cross-field validation
- Aggregated validity (valid only if all fields + object validators pass)
- Dirty tracking (`.is_dirty`, `.dirty_fields`)

---

## Files to Update

### 1. `docs/data/validation.md`
**Section to add**: "Advanced: Observable Validation" (at end of document)

**Content**:
- Brief paragraph explaining that Widget validation uses observables under the hood
- Link to `docs/advanced/observable.md` for low-level validation API
- Example of accessing `.observable` for custom validation scenarios
- Code snippet:
  ```python
  def __setup__(self):
      # Widget-level validation
      self._email.add_validator("format", lambda v: ...)

      # Advanced: Access underlying observable
      self._email.observable.add_validator("async_check", async_validator)
      self._email.observable.is_valid.on_change(lambda valid: ...)
  ```

### 2. `docs/reference/classes/variable.md`
**Section to update**: "Validation" (lines 436-483)

**Changes**:
- Keep existing content
- Add note: "For advanced validation scenarios, see [Observable Validation](../../advanced/observable.md)"
- Update broken link at line 246 from `../../features/validation.md` to `../../data/validation.md`
- Update broken links at line 594 (observable-list, observable-dict, observable-proxy) to point to new advanced docs

### 3. `docs/data/dirty-tracking.md` (if exists - not yet read)
**Changes**:
- Add link to `docs/advanced/observable.md` for low-level dirty tracking API

### 4. `mkdocs.yml`
**Navigation updates**:
```yaml
nav:
  # ... existing sections ...
  - Guides:
      # ... existing guides ...
  - Advanced:  # NEW SECTION
      - Observant Library: advanced/observant.md
      - Observable: advanced/observable.md
      - ObservableList: advanced/observable-list.md
      - ObservableDict: advanced/observable-dict.md
      - ObservableProxy: advanced/observable-proxy.md
  - Reference:
      # ... existing reference ...
```

---

## Suggested Location in Nav

**Position**: Between "Guides" and "Reference"

**Rationale**:
- **Not in "Getting Started"**: Too advanced for beginners
- **Not in "Basics"**: Users don't need to know about observables to use QtPie
- **Not in "Reactive State"**: That section covers Variable (the high-level API)
- **Not in "Data & Forms"**: That's about Widget-level features
- **Not in "Guides"**: These are reference pages, not tutorials
- **Before "Reference"**: Advanced users will look here before diving into full API reference

**Alternative**: Could go in "Reference" under a new "Observant" subsection, but "Advanced" signals "you probably don't need this" better.

---

## Content Outline Details

### New Page: `docs/advanced/observable.md`

#### Sections:
1. **What is Observable?**
   - Wrapper around a single reactive value
   - Underlying primitive for `Variable[T]`
   - When to use directly (advanced scenarios)

2. **Basic Operations**
   - Creating: `Observable[T](default_value)`
   - Getting: `.get()`
   - Setting: `.set(value)`
   - Change callbacks: `.on_change(callback)`

3. **Validation**
   - **Add Validator**:
     ```python
     obs = Observable("")
     obs.add_validator("required", lambda v: None if v else "Required")
     obs.add_validator("min_len", lambda v: None if len(v) >= 3 else "Too short")
     ```
   - **Check Validity**:
     ```python
     if obs.is_valid.get():  # Observable[bool]
         print("Valid!")
     ```
   - **Get Errors (Structured)**:
     ```python
     errors = obs.validation_errors.get()
     # {"required": ["Required"], "min_len": ["Too short"]}
     ```
   - **Get Errors (Flat)**:
     ```python
     messages = obs.validation_error_messages.get()
     # ["Required", "Too short"]
     ```
   - **Remove Validator**:
     ```python
     obs.remove_validator("required")
     ```
   - **Reactive Validation**:
     ```python
     obs.is_valid.on_change(lambda valid: print(f"Valid: {valid}"))
     obs.set("hello")  # Triggers validation, fires callback
     ```

4. **Dirty Tracking**
   - `.is_dirty` - Observable[bool]
   - `.reset_dirty()` - mark as clean

5. **Use with Variable**
   ```python
   @widget
   class MyWidget(Widget):
       _email: Variable[str] = new("")

       def __setup__(self):
           # Access underlying observable
           obs = self._email.observable
           obs.add_validator("custom", my_validator)
   ```

6. **See Also**
   - Link to Variable docs
   - Link to other observable types

### New Page: `docs/advanced/observable-proxy.md`

#### Sections:
1. **What is ObservableProxy?**
   - Wraps any object, making fields reactive
   - Used by `Widget[T]` for record types
   - Used by `Variable[T]` for complex objects

2. **Field-Level Validation**
   ```python
   from dataclasses import dataclass

   @dataclass
   class Person:
       name: str = ""
       age: int = 0

   proxy = ObservableProxy(Person())
   proxy.name.add_validator("required", lambda v: None if v else "Required")
   proxy.age.add_validator("positive", lambda v: None if v > 0 else "Must be positive")

   # Check which fields are invalid
   invalid = proxy.invalid_fields  # ["name", "age"]
   ```

3. **Object-Level Validation**
   ```python
   proxy.add_validator(
       "adult_named",
       lambda p: None if p.name and p.age >= 18 else "Must be named adult"
   )
   ```

4. **Aggregated Validity**
   - `proxy.is_valid.get()` returns True only if:
     - All field validators pass
     - All object validators pass

5. **Dirty Tracking**
   - `.is_dirty` - true if any field changed
   - `.dirty_fields` - list of changed field names

6. **Use with Widget[T]**
   ```python
   @widget(record=Person())
   class PersonEditor(Widget[Person]):
       name: QLineEdit = new()

       def __setup__(self):
           # Access proxy
           proxy = self.record  # ObservableProxy[Person]
           proxy.name.add_validator("min_len", ...)
   ```

---

## Code Examples Needed

From test summary, include these code snippets:

1. **Named validators** (from "Named Validators" section)
2. **Validation errors dict + list** (from "Validation Errors")
3. **Reactive validation** (from "Reactive Validation")
4. **List validation** (from "List Validation")
5. **Dict validation** (from "Dict Validation")
6. **Proxy field validation** (from "Proxy Field Validation")
7. **Proxy object validation** (from "Proxy Object Validation")
8. **Invalid fields list** (from "Invalid Fields List")

All examples should be adapted to:
- Remove `assert_that` test syntax
- Add docstring-style comments
- Show expected behavior clearly

---

## Cross-References

### From New Pages To:
- `docs/data/validation.md` - "For Widget-level validation, see..."
- `docs/reference/classes/variable.md` - "Variable wraps Observable, see..."
- `docs/data/records.md` - "ObservableProxy is used by Widget[T], see..."

### From Existing Pages To New Pages:
- `docs/data/validation.md` → Link to advanced observable validation
- `docs/reference/classes/variable.md` → Fix broken links, add advanced references
- `docs/data/dirty-tracking.md` → Link to observable dirty tracking
- `docs/data/records.md` → Link to ObservableProxy docs

---

## Priority

**Priority: Medium-Low**

**Rationale**:
- **Not urgent for beginners**: Users can be productive with QtPie without ever knowing about observables
- **Important for advanced users**: Power users who need fine-grained control will want this
- **Improves overall completeness**: Fills a documentation gap, makes the library feel more polished
- **Clarifies architecture**: Helps users understand the layered design (observant → Variable → Widget)

**Suggested Timeline**:
- **Phase 1 (Core Docs)**: Focus on Widget-level features (validation, dirty tracking, etc.) - already done
- **Phase 2 (Advanced)**: Add observant library docs (this proposal)
- **Phase 3 (Polish)**: Add architecture diagrams, advanced guides, etc.

---

## Alternative Approaches

### Option A: Don't Document Observant Publicly
**Pros**:
- Keeps docs focused on QtPie (the main product)
- Reduces maintenance burden
- Avoids confusing beginners with low-level details

**Cons**:
- Leaves advanced users without reference
- Makes `.observable` property seem mysterious
- Inconsistent with exposing it in the public API

### Option B: Single "Advanced" Page Instead of Multiple
**Pros**:
- Simpler nav structure
- All advanced info in one place

**Cons**:
- Very long page (all 4 observable types + validation)
- Harder to navigate/search
- Less granular cross-referencing

### Option C: Fold Into Existing Reference Pages
Update `docs/reference/classes/variable.md` with full observable details

**Pros**:
- No new nav structure
- Keeps related info together

**Cons**:
- Variable docs would become extremely long
- Mixes high-level (Variable) and low-level (Observable) APIs
- Harder to find observable-specific info

**Recommendation**: Stick with **original proposal** (new "Advanced" section) for clarity and organization.

---

## Summary

**New Files** (5):
1. `docs/advanced/observant.md` - Overview
2. `docs/advanced/observable.md` - Observable[T] reference
3. `docs/advanced/observable-list.md` - ObservableList[T] reference
4. `docs/advanced/observable-dict.md` - ObservableDict[K, V] reference
5. `docs/advanced/observable-proxy.md` - ObservableProxy[T] reference

**Updated Files** (3-4):
1. `docs/data/validation.md` - Add "Advanced" section linking to observable validation
2. `docs/reference/classes/variable.md` - Fix broken links, add advanced references
3. `mkdocs.yml` - Add "Advanced" nav section
4. `docs/data/dirty-tracking.md` - Add observable references (if applicable)

**Nav Location**: New "Advanced" section between "Guides" and "Reference"

**Priority**: Medium-Low (important for completeness, not critical for initial users)

**Key Principle**: Keep the main learning path focused on QtPie (Variable, Widget). Observables are for power users who explicitly seek them via `.observable` access.
