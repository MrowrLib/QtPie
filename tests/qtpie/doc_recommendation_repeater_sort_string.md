# Documentation Proposal: Repeater Sorting with String Method Names

## Feature Summary

The `sort=` parameter in repeaters now accepts string method names (e.g., `sort="sort_by_name"`) that resolve to methods on the parent widget. This complements the existing support for callables, `True` (default sort), and `False` (preserve order).

## Files to Add/Update

### Primary Documentation

**Create: `docs/data/repeater-sorting.md`**
- Dedicated page covering all repeater sorting options
- Clear examples for list, dict, and set repeaters
- Comparison table of sorting modes

### Updates to Existing Files

**Update: `docs/data/lists-dicts.md`** (create if doesn't exist)
- Add cross-reference to the new sorting page
- Brief mention of sorting capabilities with link to full docs
- Example showing basic `sort=` usage

**Update: `CLAUDE.md`**
- Add sorting examples to "List Binding with WidgetRepeater" section (line 216-233)
- Add sorting examples to "Dict Binding" section (line 249-261)
- Update table of contents if sorting becomes a prominent feature

## Suggested Nav Location

In `mkdocs.yml`, add under the "Data & Forms" section:

```yaml
nav:
  - Data & Forms:
      - Record Widgets: data/records.md
      - Lists & Dicts: data/lists-dicts.md
      - Repeater Sorting: data/repeater-sorting.md  # NEW
      - Validation: data/validation.md
      - Dirty Tracking: data/dirty-tracking.md
```

**Rationale:** Sorting is a data display concern, fitting naturally alongside list/dict/repeater documentation.

## Content Outline

### `docs/data/repeater-sorting.md`

1. **Introduction** (2-3 paragraphs)
   - Why sorting matters for repeaters
   - Overview of four sorting modes

2. **Sorting Modes Table**
   - Quick reference: `sort=False`, `sort=True`, `sort=callable`, `sort="method_name"`
   - When to use each

3. **String Method Name Syntax** (main focus)
   - Basic usage with list repeaters
   - Example with object properties (Dog by name, Dog by age)
   - Dict repeater sorting (sorts keys)
   - Set repeater sorting
   - Method signature requirements

4. **Callable Sorting** (existing feature)
   - Lambda functions
   - Standalone functions
   - Complex sort keys

5. **Default Sorting** (`sort=True`)
   - Uses Python's `sorted()`
   - Works with comparable types

6. **Preserving Order** (`sort=False`)
   - Maintains source order
   - Useful for pre-sorted data

7. **Error Handling**
   - Missing method name → `AttributeError`
   - Missing parent widget → `AttributeError`
   - Clear error messages

8. **Advanced Patterns**
   - Reverse sorting with method names
   - Multi-key sorting strategies
   - Dynamic sort order (user-controlled)

9. **Performance Notes**
   - When sorting happens (on insertion, on change)
   - Considerations for large lists

## Code Examples Needed

### Essential Examples (must include)

```python
# 1. Basic string method sorting (list)
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3), Dog("Ace", 1)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="sort_by_name")

    def sort_by_name(self, dog: Dog) -> str:
        return dog.name

# 2. Numeric sorting
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3), Dog("Ace", 1)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="sort_by_age")

    def sort_by_age(self, dog: Dog) -> int:
        return dog.age

# 3. Dict sorting (by key)
@widget
class ScoreBoard(Widget):
    _scores: dict[str, int] = {"Zara": 100, "Ace": 90}
    _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", sort="sort_by_key")

    def sort_by_key(self, key: str) -> str:
        return key

# 4. Set sorting
@widget
class TagList(Widget):
    _tags: set[str] = {"zebra", "apple"}
    _labels: set[QLabel] = new(bind="_tags", sort="sort_alphabetically")

    def sort_alphabetically(self, tag: str) -> str:
        return tag.lower()

# 5. Comparison of all modes (side-by-side)
_labels1: list[QLabel] = new(bind="_items", sort=False)  # Preserve order
_labels2: list[QLabel] = new(bind="_items", sort=True)   # Default sort
_labels3: list[QLabel] = new(bind="_items", sort=lambda x: x.name)  # Lambda
_labels4: list[QLabel] = new(bind="_items", sort="by_name")  # Method name
```

### Advanced Examples (nice to have)

```python
# 6. Reverse sorting pattern
def sort_by_age_desc(self, dog: Dog) -> int:
    return -dog.age  # Negate for reverse numeric sort

# 7. Case-insensitive string sorting
def sort_ignore_case(self, name: str) -> str:
    return name.lower()

# 8. User-controlled sorting
@widget
class DynamicSort(Widget):
    _sort_by_age: Variable[bool] = new(False)
    _dogs: list[Dog] = new([...])

    def __setup__(self) -> None:
        self._sort_by_age.on_change(self._update_sort)

    def _update_sort(self, by_age: bool) -> None:
        # Manually re-sort or rebuild repeater
        # (document limitations/patterns)
```

## Cross-References

### Links to Related Pages

- **From `repeater-sorting.md`:**
  - → `lists-dicts.md` (overview of list/dict repeaters)
  - → `bindings.md` (how `bind=` works)
  - → `format-expressions.md` (using placeholders like `{#key}`)
  - → Reference: `new()` factory (all parameters)

- **To `repeater-sorting.md`:**
  - ← `lists-dicts.md` ("For sorting options, see Repeater Sorting")
  - ← `CLAUDE.md` (internal dev docs)
  - ← `index.md` or feature overview (if listing all features)

### Related Features

- Format strings (`format=` parameter)
- Special placeholders (`{#index}`, `{#key}`, `{#value}`)
- Widget repeater lifecycle
- Observable list/dict/set reactivity

## Priority

**Medium-High**

### Justification:

**High Impact:**
- Sorting is a common UI need
- String method names are more maintainable than lambdas
- Enables better code organization (methods with business logic)

**Medium Urgency:**
- Feature is complete and tested (44 tests passing)
- Not blocking other work
- Users can currently work around with lambdas
- Documentation gap affects discoverability

**Recommendation:** Document in the next documentation sprint. This is a quality-of-life feature that makes QtPie more ergonomic, but users have workarounds if documentation lags slightly.

## Additional Notes

### Documentation Style

- **Show, don't tell:** Lead with code examples, explain after
- **Progressive disclosure:** Simple examples first, advanced patterns later
- **Real-world context:** Use relatable examples (Dog, ScoreBoard) not Foo/Bar
- **Type hints:** Include in all examples for clarity

### Testing Coverage

The feature has comprehensive test coverage (47 tests in `test_repeater_sort_string.py`):
- All repeater types (list, dict, set)
- Error cases (missing methods, no parent)
- Backward compatibility (callable, True, False modes)
- Direct construction edge cases

No additional test documentation needed beyond code examples.

### Migration Guide

Not needed - this is additive, no breaking changes. Existing `sort=callable`, `sort=True`, and `sort=False` usage remains unchanged.
