# Documentation Proposal: Stylesheet Loader

## Summary

The `load_stylesheet()` function and its test coverage demonstrate a utility for loading QSS stylesheets from either local filesystem paths or Qt Resource (QRC) files, with automatic fallback behavior. This is already documented in `docs/basics/styling.md` but could benefit from expanded examples and clarifications.

## Priority

**Low-Medium** - This is an existing feature that is already documented. The feature is straightforward and the current documentation covers the basics. However, the documentation could be enhanced with better examples and edge case coverage.

## Files to Update

### 1. `docs/basics/styling.md` (Update Existing)

**Section to Enhance:** "External QSS Files" and "QRC Resources" (lines 248-288)

**Current State:**
The documentation covers the basics but lacks detail on:
- Error handling behavior (returns empty string vs raising exceptions)
- Practical use cases for local vs QRC loading
- Build/development workflow recommendations
- When to use which approach

**Content to Add:**

#### Error Handling Details
```python
from qtpie.styles import load_stylesheet

# Graceful handling - no exceptions raised
qss = load_stylesheet(qss_path="./nonexistent.qss")
assert qss == ""  # Returns empty string, not an error

# QRC paths that don't exist also return empty string
qss = load_stylesheet(qrc_path=":/missing/styles.qss")
assert qss == ""
```

#### Development vs Production Pattern
```python
from qtpie.styles import load_stylesheet

# Pattern: Use local during development, QRC in production
# During development: styles/app.qss exists locally (hot-reloadable)
# In production builds: only QRC resource is available
qss = load_stylesheet(
    qss_path="./styles/app.qss",      # Dev: use this
    qrc_path=":/styles/app.qss"       # Prod: fall back to this
)
self.setStyleSheet(qss)
```

#### Use Case Guidance
- **Local paths (`qss_path=`)**: Best for development (hot-reload, easy editing)
- **QRC paths (`qrc_path=`)**: Best for production (bundled into executable, single-file distribution)
- **Both paths**: Recommended pattern - supports both dev and prod workflows seamlessly

#### Integration with SCSS Workflow
```python
# Build script: compile SCSS to local QSS for dev
from qtpie.styles import compile_scss
compile_scss(scss_path="./src/styles.scss", qss_path="./build/app.qss")

# Then compile local QSS into QRC for production
# (using Qt's rcc tool in your build pipeline)

# Widget: works in both dev and prod
@widget
class MyWidget(Widget):
    def __setup__(self) -> None:
        qss = load_stylesheet(
            qss_path="./build/app.qss",    # Dev builds have this
            qrc_path=":/styles/app.qss"    # Prod uses QRC
        )
        self.setStyleSheet(qss)
```

## Files to Add

**None** - This feature is already well-placed in the existing documentation structure.

## Suggested Location in Nav

No changes needed - already in the correct location:
```yaml
nav:
  - Basics:
      - Styling: basics/styling.md  # ← Already here
```

## Code Examples Needed

From the test summary, highlight these practical patterns:

### 1. Basic Local Loading
```python
qss = load_stylesheet(qss_path="./styles/app.qss")
```

### 2. QRC Loading
```python
qss = load_stylesheet(qrc_path=":/styles/app.qss")
```

### 3. Fallback Pattern (Most Important)
```python
# Try local first (dev), fall back to QRC (prod)
qss = load_stylesheet(
    qss_path="./styles/app.qss",
    qrc_path=":/styles/app.qss"
)
```

### 4. Safe Empty String Handling
```python
# No exceptions raised - safe to use anywhere
qss = load_stylesheet(qss_path="/maybe/missing.qss")
if qss:
    self.setStyleSheet(qss)
else:
    # Use default styles
    pass
```

## Cross-References

### Links To Add
- From **External QSS Files** section → SCSS Compilation section (workflow integration)
- From **External QSS Files** section → **Best Practices** section (dev vs prod patterns)

### Links From Other Pages
- **`docs/start/concepts.md`** - Mention stylesheet loading in "Styling" concept overview
- **`docs/guides/app.md`** - Show QRC resource setup for production apps
- **`docs/reference/styles/class-helpers.md`** - Cross-reference stylesheet loading utilities

## Content Outline

### Enhanced "External QSS Files" Section

1. **Basic Local Loading**
   - Simple file path example
   - Returns empty string if missing (no exception)
   - Use case: Development, rapid iteration

2. **QRC Resource Loading**
   - Qt Resource system brief intro
   - `:/ path` syntax
   - Returns empty string if missing
   - Use case: Production builds, single executable

3. **Fallback Pattern** ⭐ *Most Important*
   - Both paths provided
   - Local takes precedence (dev)
   - Falls back to QRC (prod)
   - Recommended workflow for all projects

4. **Error Handling**
   - No exceptions raised
   - Empty string return value
   - Safe to use in any context
   - Optional conditional styling

5. **Integration with SCSS**
   - Compile SCSS → local QSS during dev
   - Bundle local QSS → QRC for production
   - Single `load_stylesheet()` call works for both

6. **Best Practices**
   - Always provide both paths for flexibility
   - Use relative paths for portability
   - Consider build pipeline integration
   - Test both dev and prod paths

## Implementation Notes

### What NOT to Document
- Internal implementation details (QFile, QTextStream usage)
- Test-specific mocking patterns
- Private API behavior

### Keep It Simple
- Focus on the 80% use case (fallback pattern)
- Show one clear recommended approach
- Avoid overcomplicating with edge cases
- Trust that developers will read the function signature if they need details

### Tone
- Practical, workflow-oriented
- "Here's how you'd actually use this in a real project"
- Less API reference, more cookbook

## Maintenance Notes

If this feature evolves to support:
- Multiple fallback paths (beyond just 2)
- Remote URL loading
- Caching or hot-reload
- Async loading

...then consider promoting it to its own page under `reference/styles/` or a dedicated guide page.

For now, keeping it as an enhanced section in `basics/styling.md` is appropriate given the feature's scope and simplicity.
