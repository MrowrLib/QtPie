# Documentation Proposal: ObservableProxy Path Traversal

## Overview

This feature adds dot-notation path traversal and optional chaining to `ObservableProxy`, enabling reactive access to deeply nested object properties.

## 1. Files to Add

### `docs/observant/observable-proxy-paths.md`

A new page dedicated to advanced `ObservableProxy` features, specifically path-based observable access.

**Rationale:** This is a distinct, advanced feature that deserves its own page rather than cluttering the basics. Users working with deeply nested data structures will search specifically for this functionality.

## 2. Files to Update

### `docs/data/records.md`

Add a section or callout box mentioning that for deeply nested record structures, `ObservableProxy` supports path-based access (with link to new page).

**Rationale:** Users working with `Widget[T]` and record types will naturally encounter nested objects and need to know how to bind to deeply nested fields.

### Potential new file: `docs/observant/index.md` (if it doesn't exist)

Create an overview page for the observant library explaining:
- What observant is (reactive primitives layer under QtPie)
- When to use it directly vs. through QtPie abstractions
- Links to `Observable`, `ObservableProxy`, `ObservableList`, `ObservableDict`

**Rationale:** The observant library is mentioned in CLAUDE.md but doesn't appear to have user-facing docs yet. Path traversal is an advanced feature that assumes users understand the basics.

## 3. Suggested Location in Nav

```yaml
nav:
  # ... existing sections ...
  - Advanced:
      - Observant Library:
          - Overview: observant/index.md
          - ObservableProxy Paths: observant/observable-proxy-paths.md
          - Observable Primitives: observant/primitives.md  # Future
  # OR, if keeping observant internal:
  - Reference:
      - Classes:
          # ... existing ...
          - ObservableProxy: reference/classes/observable-proxy.md
```

**Rationale:** This is an advanced feature for power users. It should be discoverable but not in the Getting Started flow. Since observant is a sub-library, grouping it under "Advanced" or "Reference" makes sense.

## 4. Content Outline

### For `docs/observant/observable-proxy-paths.md`

1. **Introduction**
   - What is path-based access and why use it?
   - When to use vs. direct property access
   - Note: Primarily for programmatic/dynamic scenarios

2. **Basic Path Traversal**
   - Syntax: `proxy.observable_for_path("field")`
   - Simple nested access: `"address.city"`
   - Returns an `Observable[T]` that reacts to changes at that path
   - Code example from test summary (Person with nested Address)

3. **Optional Chaining (`?.` syntax)**
   - Handling nullable/optional fields safely
   - Syntax: `"address?.city"` or `"ceo?.address?.city"`
   - Returns `Observable(None)` if any intermediate is None
   - No exceptions thrown on None access
   - Code example from test summary (Person with None address)

4. **Reactivity Behavior**
   - What happens when intermediate values change?
   - Does the observable update automatically? (if tested)
   - Memory/lifecycle considerations

5. **Use Cases**
   - Dynamic form builders
   - Configuration editors with variable schemas
   - Generic data viewers/inspectors
   - When field names come from user input or config

6. **Limitations & Caveats**
   - Path segments are parsed at call time
   - Type safety: path strings aren't type-checked (vs direct property access)
   - Performance considerations for deeply nested paths

7. **API Reference**
   - `observable_for_path(path: str) -> Observable[T]`
   - Path syntax: `field.nested.deeply` and `field?.optional?.chain`
   - Internal: `_parse_path_segments(path: str)` (mention as implementation detail)

### For `docs/data/records.md` (Update)

Add a new section or admonition:

**"Working with Deeply Nested Records"**

```python
@dataclass
class Address:
    city: str
    zip_code: str

@dataclass
class Person:
    name: str
    address: Address | None

@widget(record=Person(...))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Simple binding

    # For nested fields, you can:
    # 1. Access via the proxy directly in bindings
    city: QLabel = new(bind="{record.address.city if record.address else 'N/A'}")

    # 2. Use observable_for_path for programmatic access
    def __setup__(self) -> None:
        city_obs = self.record.observable_for_path("address?.city")
        city_obs.subscribe(self.on_city_changed)
```

> For advanced path-based observable access (including optional chaining), see [ObservableProxy Paths](../observant/observable-proxy-paths.md).

## 5. Code Examples Needed

**From test summary:**

1. **Simple traversal example:**
```python
person = Person(name="Alice", age=30)
proxy = ObservableProxy(person)
name_obs = proxy.observable_for_path("name")
assert name_obs.get() == "Alice"
```

2. **Nested object traversal:**
```python
person = Person(name="Bob", address=Address(city="NYC", zip_code="10001"))
proxy = ObservableProxy(person)
city_obs = proxy.observable_for_path("address.city")
assert city_obs.get() == "NYC"
```

3. **Optional chaining with None:**
```python
person = Person(name="Charlie", address=None)
proxy = ObservableProxy(person)
result = proxy.observable_for_path("address?.city")
assert result.get() is None  # No exception!
```

4. **Deep optional chaining:**
```python
company = Company(name="Acme", ceo=None)
proxy = ObservableProxy(company)
result = proxy.observable_for_path("ceo?.address?.city")
assert result.get() is None
```

5. **Path parsing (for reference/advanced section):**
```python
segments = proxy._parse_path_segments("a?.b.c?.d")
# Returns: [("a", True), ("b", False), ("c", True), ("d", False)]
```

**Additional examples to create:**

6. **QtPie integration example:**
```python
@widget(record=Company(...))
class CompanyViewer(Widget[Company]):
    def __setup__(self) -> None:
        # Dynamic binding to optional nested field
        ceo_city = self.record.observable_for_path("ceo?.address?.city")
        self._ceo_location.bind_to(ceo_city)
```

## 6. Cross-References

**Link TO:**
- `docs/data/records.md` (Widget[T] and ObservableProxy intro)
- `docs/state/bindings.md` (how bindings work generally)
- `docs/reference/classes/observable-proxy.md` (if it exists)

**Link FROM:**
- `docs/data/records.md` → Link in "nested records" section
- `docs/state/format-expressions.md` → Mention as alternative to complex expressions
- `docs/observant/index.md` → List this as an advanced capability
- `docs/start/concepts.md` → Brief mention in "Advanced Reactivity" section (if exists)

## 7. Priority

**Priority: Medium-Low (Advanced Feature)**

**Justification:**
- This is an advanced feature for power users
- Most users will work with flat or shallow record structures
- Direct property access (`record.field.nested`) works for known schemas
- Path-based access is most useful for:
  - Dynamic/generic form builders
  - Schema-driven UIs
  - Programmatic observable access
  - Optional chaining edge cases

**Recommended Timeline:**
- Document AFTER core features are covered:
  - Basic widgets, variables, bindings
  - Record types (`Widget[T]`)
  - Format expressions
- Document BEFORE:
  - Internal architecture docs
  - Advanced customization guides

**User Journey Placement:**
Users should discover this when they:
1. Already understand `ObservableProxy` basics (from `Widget[T]` docs)
2. Hit a pain point with deeply nested optionals
3. Are building dynamic/generic data viewers
4. Search for "optional chaining" or "nested observable"

## Notes

- The `_parse_path_segments()` method is internal (leading underscore). Include in docs as "Implementation Detail" or omit entirely from user-facing docs.
- Consider whether to expose observant library directly to users or keep it as an internal implementation detail. If internal, this might belong in a "How QtPie Works" advanced section rather than user-facing API docs.
- The test summary doesn't show reactivity tests (what happens when intermediate values change). Consider adding tests and documenting this behavior before publishing docs.
