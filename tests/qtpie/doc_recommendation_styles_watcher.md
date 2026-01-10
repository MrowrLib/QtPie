# Documentation Proposal: Stylesheet Hot-Reloading

## Overview

The styles watcher feature provides hot-reloading for QSS and SCSS stylesheets during development, significantly improving the developer experience when styling Qt applications. This is a developer-facing feature that should be prominently documented.

## Files to Add/Update

### New Files to Create

1. **`docs/guides/hot-reload-styles.md`** (Primary documentation)
   - Complete guide to using `watch_qss()`, `watch_scss()`, and `watch_styles()`
   - Development workflow examples
   - Best practices and gotchas

2. **`docs/basics/styling.md`** (New page)
   - Basic QSS usage in QtPie
   - Static stylesheet loading with `load_stylesheet()`
   - CSS class helpers (`add_class`, `set_classes`, etc.)
   - Brief mention of hot-reloading (link to guide)
   - Link to Qt's QSS documentation

### Files to Update

1. **`docs/index.md`**
   - Add hot-reloading to Key Features section (currently missing styling features entirely)

2. **`docs/why-qtpie.md`**
   - Add to Feature Comparison table:
     - Hot-reload styles: Plain Qt (DIY) vs QtPie (Built-in watchers)
     - SCSS support: Plain Qt (External tooling) vs QtPie (Integrated)

3. **`mkdocs.yml`**
   - Add `basics/styling.md` to "Basics" section (currently empty stub in nav)
   - Add `guides/hot-reload-styles.md` to "Guides" section

## Suggested Nav Location

### In mkdocs.yml nav structure:

```yaml
nav:
  - Basics:
      - Styling: basics/styling.md  # UPDATE (currently empty stub)

  - Guides:
      - Hot-Reload Styles: guides/hot-reload-styles.md  # NEW
      - Windows & Menus: guides/windows-menus.md
      - Translations: guides/translations.md
      # ... existing guides

  - Reference:
      - Styles:  # EXISTING SECTION
          - Color Schemes: reference/styles/color-schemes.md
          - Class Helpers: reference/styles/class-helpers.md
          - Stylesheet Watchers: reference/styles/watchers.md  # NEW (API reference)
```

## Content Outline

### 1. `docs/basics/styling.md` (New)

**Purpose**: Introduce styling fundamentals in QtPie

**Sections**:
- **QSS Basics** (2-3 paragraphs)
  - What is QSS (Qt Style Sheets)
  - How it differs from CSS
  - Link to Qt's official QSS reference

- **Setting Object Names** (1 paragraph + code)
  - How `name=` parameter sets objectName
  - Default behavior (field name becomes objectName)
  - Example of targeting with `#objectName` selector

- **Using CSS Classes** (1 paragraph + code)
  - How `classes=["foo", "bar"]` parameter works
  - Example of targeting with `.className` selector
  - Link to Class Helpers reference

- **Loading Static Stylesheets** (1 paragraph + code)
  - Using `load_stylesheet(path)` function
  - When to use static vs hot-reload

- **Hot-Reloading Styles** (1 paragraph + link)
  - Brief mention that QtPie supports hot-reloading
  - Link to full Hot-Reload Styles guide

- **Next Steps** (Links section)
  - Link to Hot-Reload Styles guide
  - Link to Color Schemes reference
  - Link to Class Helpers reference
  - Link to Qt's QSS documentation

### 2. `docs/guides/hot-reload-styles.md` (New)

**Purpose**: Complete guide to development-time stylesheet hot-reloading

**Sections**:

#### **Overview** (1-2 paragraphs)
- What is hot-reloading and why it's useful
- Comparison to manual workflow (restart app every change)

#### **Quick Start: QSS Hot-Reload**
```python
from qtpie import widget, Widget, watch_qss
from PySide6.QtWidgets import QLabel

@widget
class MyWidget(Widget):
    label: QLabel = new("Styled label")

    def __setup__(self) -> None:
        # Watch QSS file - auto-applies on changes
        self._watcher = watch_qss(self, "styles.qss")
```

#### **SCSS Support**
- What is SCSS and advantages (variables, nesting, imports)
- How QtPie compiles SCSS to QSS automatically
- Example with variables and imports

```python
from qtpie import watch_scss

def __setup__(self) -> None:
    # Watches SCSS, compiles to QSS, applies to widget
    self._watcher = watch_scss(
        self,
        scss_path="styles.scss",
        qss_path="output.qss",
        search_paths=["./scss_partials"]  # For @import
    )
```

#### **The Convenience Function**
- `watch_styles()` - automatically chooses watcher based on parameters

#### **Watching the Application**
- Apply styles globally to QApplication
```python
from PySide6.QtWidgets import QApplication

app = QApplication.instance()
watcher = watch_qss(app, "app.qss")  # Styles entire app
```

#### **Important: Keep References**
- **WARNING box**: Must keep watcher reference to prevent garbage collection
- Show correct vs incorrect patterns

#### **Editor Compatibility**
- How watchers handle editor behavior (delete+recreate)
- Works with vim, VSCode, Sublime, etc.
- Debouncing prevents redundant reloads

#### **Watching Non-Existent Files**
- Watchers wait for file creation
- Useful for generated stylesheets

#### **SCSS Partial Watching**
- Watchers detect changes to `@import`ed files
- Use `search_paths` for partial directories

#### **Development vs Production**
- Hot-reloading is for development only
- For production, use `load_stylesheet()` with compiled QSS
- Example production setup

#### **Common Patterns**
- Conditional watching based on environment
```python
import os

def __setup__(self) -> None:
    if os.getenv("DEV_MODE"):
        self._watcher = watch_qss(self, "dev.qss")
    else:
        load_stylesheet("prod.qss")
```

#### **Troubleshooting**
- Watcher not updating → check file path
- Styles not applying → check QSS syntax errors
- SCSS not compiling → check import paths

#### **API Summary Table**

| Function | Purpose | Returns |
|----------|---------|---------|
| `watch_qss(target, path)` | Watch QSS file | `QssWatcher` |
| `watch_scss(target, scss, qss, paths)` | Watch & compile SCSS | `ScssWatcher` |
| `watch_styles(target, qss, scss, paths)` | Auto-detect watcher type | `QssWatcher` or `ScssWatcher` |

### 3. `docs/reference/styles/watchers.md` (New)

**Purpose**: API reference for watcher classes and functions

**Sections**:
- **QssWatcher class**
  - Constructor parameters
  - `stylesheetApplied` signal
  - `stop()` method

- **ScssWatcher class**
  - Constructor parameters
  - `stylesheetApplied` signal
  - `stop()` method

- **watch_qss() function**
  - Parameters with types
  - Return type
  - Example

- **watch_scss() function**
  - Parameters with types
  - Return type
  - Example

- **watch_styles() function**
  - Parameters with types
  - Return type
  - Example

## Code Examples Needed

### Basic Examples
1. **Simple QSS watching** - Widget with QSS hot-reload
2. **SCSS with variables** - Show SCSS compilation with `$color` variable
3. **SCSS with imports** - Show `@import 'variables'` pattern with `search_paths`
4. **Application-level watching** - Global app styles
5. **Conditional dev/prod** - Environment-based loading

### Advanced Examples
1. **Multiple widgets with shared watcher** - One watcher, multiple targets
2. **Watcher with signal connection** - React to `stylesheetApplied` signal
3. **Non-existent file watching** - Create file after watcher starts
4. **Editor delete/recreate simulation** - Show watcher survives file replacement

### Anti-Patterns
1. **Wrong: No reference** - Watcher gets garbage collected
```python
# WRONG - watcher will be garbage collected!
watch_qss(self, "styles.qss")
```

2. **Correct: Store reference**
```python
# CORRECT - keep reference
self._watcher = watch_qss(self, "styles.qss")
```

### Minimal Complete Examples

#### Example 1: Dev Mode Toggle
```python
from qtpie import widget, Widget, entrypoint, watch_qss
from qtpie.styles import load_stylesheet
import os

@entrypoint
@widget
class StyledApp(Widget):
    label: QLabel = new("Check my styles!")

    def __setup__(self) -> None:
        if os.getenv("DEV"):
            # Hot-reload during development
            self._watcher = watch_qss(self, "dev.qss")
        else:
            # Static load for production
            load_stylesheet("prod.qss")
```

#### Example 2: SCSS Workflow
```python
# styles.scss
"""
$primary: #0078d4;
$hover: darken($primary, 10%);

QPushButton {
    background: $primary;
    &:hover { background: $hover; }
}
"""

# widget.py
@widget
class App(Widget):
    button: QPushButton = new("Click Me")

    def __setup__(self) -> None:
        self._watcher = watch_scss(
            self,
            scss_path="styles.scss",
            qss_path="compiled.qss"
        )
```

## Cross-References

### Links TO This Feature (Inbound)
- `docs/basics/styling.md` → Link to hot-reload guide
- `docs/index.md` → Mention hot-reload in features
- `docs/why-qtpie.md` → Feature comparison entry
- `docs/start/concepts.md` → Brief mention in development workflow
- `docs/guides/testing.md` → Note about disabling watchers in tests

### Links FROM This Feature (Outbound)
- Qt's official QSS documentation (external)
- `docs/reference/styles/class-helpers.md` → CSS class manipulation functions
- `docs/reference/styles/color-schemes.md` → Theming with ColorScheme
- `docs/reference/styles/watchers.md` → Detailed API reference
- `docs/basics/styling.md` → Styling fundamentals
- `docs/guides/app.md` → Application-level styling

## Priority

**HIGH**

### Reasoning:
1. **High Developer Value**: Hot-reloading dramatically improves styling workflow
2. **Unique Differentiator**: Not common in Qt tooling, worth highlighting
3. **Currently Undocumented**: Feature exists but has zero user-facing docs
4. **Easy to Implement**: Feature is complete and tested, just needs docs
5. **Blocks Adoption**: Users won't discover this feature without docs
6. **Low Effort, High Impact**: Relatively simple to document, high user satisfaction

### Impact Assessment:
- **Without docs**: Users restart app for every style change (painful workflow)
- **With docs**: Users get instant visual feedback, faster iteration
- **Comparison to other features**: More impactful than niche features like obscure binding edge cases

## Additional Notes

### Style Recommendations
- Use admonitions (warning, tip, note) liberally
  - WARNING for garbage collection issue
  - TIP for SCSS advantages
  - NOTE for production vs dev guidance

### Code Block Languages
- Use `python` for Python code
- Use `css` or `scss` for stylesheet code
- Use `yaml` for config examples

### Tone
- Friendly, practical tone matching existing QtPie docs
- Focus on "here's what this solves" not just "here's how it works"
- Include real-world workflow examples

### Testing Considerations
- Note that watchers should be disabled or mocked in tests
- Show pattern for test fixtures that don't start watchers

### Future Enhancements (Out of Scope)
- These could be follow-up docs if features are added:
  - CLI tool for SCSS compilation (`qtpie scss compile`)
  - Integration with `@entrypoint` for automatic dev mode detection
  - Built-in SCSS syntax validation with error display
