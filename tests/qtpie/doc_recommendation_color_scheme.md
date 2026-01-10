# Color Scheme Feature - Documentation Proposal

## Priority
**High** - This is a commonly-needed feature for modern desktop applications (dark mode support), and it's a simple quality-of-life feature that should be highlighted.

## Files to Add/Update

### New Files
1. **`docs/reference/styles/color-schemes.md`** (already in mkdocs nav, needs content)
   - Primary documentation for color scheme API
   - Full reference for all functions and enum values

2. **`docs/guides/styling.md`** (create if doesn't exist, or merge with `docs/basics/styling.md`)
   - Practical guide showing how to style apps
   - Should include color schemes as a subsection

### Update Files
1. **`docs/index.md`**
   - Add color scheme support to feature list (brief mention)

2. **`docs/reference/decorators/entrypoint.md`**
   - Document `color_scheme=` parameter for @entrypoint decorator (if it exists/planned)

## Suggested Nav Location

Already correctly placed in mkdocs.yml:
```yaml
Reference:
  - Styles:
      - Color Schemes: reference/styles/color-schemes.md
      - Class Helpers: reference/styles/class-helpers.md
```

Possibly also mention in:
```yaml
Guides:
  - App & Entry Points: guides/app.md  # Mention color_scheme setup
```

## Content Outline

### `docs/reference/styles/color-schemes.md`

```markdown
# Color Schemes

Control your application's light/dark mode appearance.

## Overview
QtPie provides simple helpers for managing Qt's color scheme (dark/light mode).
Works with Qt 6.8+ runtime API when app exists, or sets up environment variables
for Windows when called before app creation.

## Quick Start
[Basic example with enable_dark_mode()]

## API Reference

### ColorScheme Enum
- ColorScheme.Dark
- ColorScheme.Light

### Functions

#### set_color_scheme()
[Signature, parameters, behavior details]
- With app existing (Qt 6.8+ runtime API)
- Without app (deferred + Windows env vars)
- Cross-platform behavior notes

#### enable_dark_mode()
[Convenience wrapper details]

#### enable_light_mode()
[Convenience wrapper details]

## Usage Patterns

### At Application Startup
[Example with @entrypoint or manual QApplication setup]

### Runtime Switching
[Example showing theme toggle in settings]

### Integration with @entrypoint
[If color_scheme parameter exists, document it]

## Platform Notes
- Windows: Uses QT_QPA_PLATFORM env var when set before app creation
- macOS/Linux: Deferred until app creation, then uses Qt API
- Qt 6.8+ required for runtime API

## Complete Example
[Full working app with dark/light toggle button]
```

### `docs/basics/styling.md` or `docs/guides/styling.md`

Add section:
```markdown
## Color Schemes (Dark/Light Mode)

[Brief intro with link to full reference]
[One simple example]
[Link to reference/styles/color-schemes.md]
```

## Code Examples Needed

### Example 1: Basic Usage (Quick Start)
```python
from qtpie import entrypoint, widget, Widget
from qtpie.styles import enable_dark_mode

# Before app creation
enable_dark_mode()

@entrypoint
@widget
class MyApp(Widget):
    ...
```

### Example 2: Runtime Switching
```python
from PySide6.QtWidgets import QPushButton
from qtpie import Widget, Variable, new, widget
from qtpie.styles import set_color_scheme, ColorScheme

@widget
class ThemeSettings(Widget):
    _dark_mode: Variable[bool] = new(False)
    toggle_btn: QPushButton = new("Toggle Theme", clicked="on_toggle")

    def on_toggle(self) -> None:
        self._dark_mode.value = not self._dark_mode.value
        scheme = ColorScheme.Dark if self._dark_mode.value else ColorScheme.Light
        set_color_scheme(scheme)
```

### Example 3: With @entrypoint (if supported)
```python
@entrypoint(color_scheme=ColorScheme.Dark)
@widget
class MyApp(Widget):
    ...
```

### Example 4: Complete App with Toggle
```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, Variable, entrypoint, new, widget
from qtpie.styles import set_color_scheme, ColorScheme

@entrypoint
@widget
class DarkModeDemo(Widget):
    _is_dark: Variable[bool] = new(True)

    _label: QLabel = new(bind="Current mode: {'Dark' if _is_dark else 'Light'}")
    _toggle: QPushButton = new("Toggle Dark/Light", clicked="on_toggle")

    def __setup__(self) -> None:
        # Set initial scheme
        set_color_scheme(ColorScheme.Dark)

    def on_toggle(self) -> None:
        self._is_dark.value = not self._is_dark.value
        scheme = ColorScheme.Dark if self._is_dark.value else ColorScheme.Light
        set_color_scheme(scheme)
```

### Example 5: Early Setup (no app yet)
```python
from qtpie.styles import enable_dark_mode

# Call before any Qt imports or app creation
enable_dark_mode()

# Now import and create app
from qtpie import entrypoint, widget, Widget

@entrypoint
@widget
class MyApp(Widget):
    ...  # Will start in dark mode
```

## Cross-References

### Links TO this feature:
- From `docs/index.md` - Feature list mention
- From `docs/basics/styling.md` - Styling basics guide
- From `docs/guides/app.md` - App initialization patterns
- From `docs/reference/decorators/entrypoint.md` - If color_scheme param exists

### Links FROM this feature:
- To Qt docs on styleHints/colorScheme (external)
- To Qt 6.8 release notes (external, for API reference)
- To `docs/guides/app.md` - For app lifecycle context
- To `docs/basics/styling.md` - For general styling topics

## Additional Notes

### Implementation Notes to Cover
1. **Deferred application pattern**: Explain why/how color scheme is stored when no app exists yet
2. **Platform differences**: Windows env var vs macOS/Linux deferred approach
3. **Qt version requirements**: Mention Qt 6.8+ for runtime API
4. **Limitations**: Note that this doesn't create/modify QSS stylesheets, just sets OS-level color scheme

### Common Use Cases to Highlight
1. Setting dark mode at app startup
2. User preference toggle (runtime switching)
3. Following system theme (may need additional code - document this pattern if available)
4. Persisting user preference (show integration with settings/config file)

### Gotchas to Document
1. Must call before app creation on some platforms for best results
2. Doesn't automatically style custom widgets - they need to respect palette
3. Qt 6.8+ requirement for runtime switching

## Testing Checklist for Docs

Before finalizing, verify docs include:
- [ ] All three functions documented
- [ ] ColorScheme enum values explained
- [ ] Runtime vs pre-app behavior explained
- [ ] Platform differences noted
- [ ] At least one complete working example
- [ ] Links to related features
- [ ] External Qt documentation references
