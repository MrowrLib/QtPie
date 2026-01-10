# Documentation Proposal: CSS Classes Feature

## Overview

The test file `test_styles_classes.md` describes the CSS class manipulation API for QtPie widgets. This is already documented in the existing documentation, so this proposal focuses on **ensuring completeness and consistency** rather than creating new pages.

## Analysis

The CSS class helper functions are **already documented** in:

1. **C:\Code\mrowr\MrowrLib\QtPie-v2\docs\basics\styling.md** (lines 130-183)
   - Comprehensive section on "Runtime Class Manipulation"
   - Documents all 8 functions: `get_classes()`, `set_classes()`, `add_class()`, `add_classes()`, `has_class()`, `has_any_class()`, `remove_class()`, `replace_class()`, `toggle_class()`
   - Includes examples and refresh behavior notes

2. **C:\Code\mrowr\MrowrLib\QtPie-v2\docs\reference\styles\class-helpers.md** (entire file)
   - Dedicated reference page for class helper functions
   - Clean, focused documentation with examples for each function

The test summary confirms these functions work as documented. **No new documentation pages are needed.**

## Files to Update

### 1. C:\Code\mrowr\MrowrLib\QtPie-v2\docs\reference\styles\class-helpers.md

**Status**: Already complete and accurate

**Recommended additions** (minor refinements):

- Add a "Quick Reference" table at the top showing all functions at a glance
- Add a note about the `refresh=` parameter that appears in the main styling doc (line 178)
- Add cross-reference to the main styling guide for context

**Proposed additions**:

```markdown
## Quick Reference

| Function | Purpose |
|----------|---------|
| `get_classes(widget)` | Get list of CSS classes |
| `set_classes(widget, classes)` | Replace all classes |
| `add_class(widget, cls)` | Add single class (no duplicates) |
| `add_classes(widget, classes)` | Add multiple classes (no duplicates) |
| `has_class(widget, cls)` | Check if class exists |
| `has_any_class(widget, classes)` | Check if any class exists |
| `remove_class(widget, cls)` | Remove a class |
| `replace_class(widget, old, new)` | Replace class (preserves position) |
| `toggle_class(widget, cls)` | Toggle class on/off |

## Performance Considerations

Most class functions automatically refresh the widget's stylesheet. For bulk operations, use `refresh=False`:

```python
# Efficient bulk updates
for widget in widgets:
    add_class(widget, "active", refresh=False)
# Manual refresh once
widget.style().unpolish(widget)
widget.style().polish(widget)
```

See [Styling Guide](../../basics/styling.md) for more context on CSS classes in QtPie.
```

### 2. C:\Code\mrowr\MrowrLib\QtPie-v2\docs\basics\styling.md

**Status**: Already comprehensive

**Recommended verification**:

- Confirm all 9 functions from the reference are mentioned (currently line 130-177)
- Ensure consistency with reference page examples

**No major changes needed** - the styling guide already documents runtime class manipulation thoroughly with practical examples.

## Files to Add

**None** - All necessary documentation already exists.

## Suggested Location in Nav

**Current location is appropriate**:

```yaml
nav:
  - Reference:
      - Styles:
          - Color Schemes: reference/styles/color-schemes.md
          - Class Helpers: reference/styles/class-helpers.md  # Already here
```

No changes to navigation needed.

## Content Outline

Since the documentation already exists, here's a **completeness checklist**:

### Existing Coverage (Already Complete)

- [x] Basic usage of `classes=` parameter
- [x] Getting classes with `get_classes()`
- [x] Setting classes with `set_classes()`
- [x] Adding classes with `add_class()` and `add_classes()`
- [x] Checking classes with `has_class()` and `has_any_class()`
- [x] Removing classes with `remove_class()`
- [x] Replacing classes with `replace_class()`
- [x] Toggling classes with `toggle_class()`
- [x] Using classes with `Variable[T, W]`
- [x] Using classes with list/dict repeaters
- [x] Performance notes about refresh behavior

### Potential Gaps (Minor)

- [ ] Quick reference table in reference doc
- [ ] Explicit documentation of `refresh=` parameter (mentioned but not detailed)
- [ ] Cross-references between basics/styling.md and reference/styles/class-helpers.md

## Code Examples Needed

The existing documentation already has excellent examples. The test summary confirms these patterns work:

### Examples Already Documented

1. **Basic class manipulation** (styling.md lines 147-176)
2. **Variable[T, W] with classes** (styling.md lines 184-198)
3. **List/dict repeater classes** (styling.md lines 200-222)
4. **Reference examples** (class-helpers.md entire file)

### No new examples needed

All test scenarios are already covered in the docs.

## Cross-References

### Already Present

- `basics/styling.md` is the main guide for styling concepts
- `reference/styles/class-helpers.md` is the API reference

### Recommended Additions

Add to **reference/styles/class-helpers.md**:
```markdown
See also:
- [Styling Guide](../../basics/styling.md) - Complete guide to QtPie styling including CSS classes
- [Color Schemes](color-schemes.md) - Dark/light mode support
```

Add to **basics/styling.md** (in the Runtime Class Manipulation section):
```markdown
For detailed API documentation, see [Class Helpers Reference](../reference/styles/class-helpers.md).
```

## Priority

**Priority: LOW** (Maintenance/Polish)

**Reasoning:**
- Feature is already fully documented
- Test summary confirms existing docs are accurate
- Only minor refinements suggested (quick reference table, cross-links)
- Not a new feature requiring user education

This is a **completeness audit** rather than a documentation gap.

## Action Items

If implementing refinements:

1. Add quick reference table to `reference/styles/class-helpers.md`
2. Document `refresh=` parameter explicitly in reference page
3. Add cross-reference links between styling.md and class-helpers.md
4. Consider adding a note about duplicate handling (already implied, make explicit)

## Summary

The CSS class helpers are already well-documented in QtPie. The test summary confirms the documentation is accurate. Only minor polish items remain:

- Quick reference table for easy scanning
- Explicit cross-references
- Document `refresh=` parameter more clearly

**No new pages or major updates required.**
