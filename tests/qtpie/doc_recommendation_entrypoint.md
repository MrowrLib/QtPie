# Documentation Proposal: @entrypoint Decorator

## Priority
**HIGH** - This is a core feature that every QtPie app should use. It appears in the main README example and simplifies app bootstrapping significantly.

## Files to Add/Update

### 1. Update: `docs/index.md`
- Already shows `@entrypoint` in the main example (good!)
- No changes needed

### 2. Update: `docs/start/hello-world.md`
- Add explanation of `@entrypoint` after first example
- Show with/without comparison
- Explain auto-run behavior

### 3. **NEW**: `docs/reference/decorators/entrypoint.md`
- Full reference documentation (main deliverable)
- This file is listed in nav but doesn't exist yet

### 4. Update: `docs/guides/app.md`
- This page should cover app lifecycle and entrypoint patterns
- File likely doesn't exist yet - create it
- Show advanced entrypoint usage (translations, stylesheets, etc.)

## Suggested Nav Location

Already correctly placed in `mkdocs.yml`:
```yaml
- Reference:
    - Decorators:
        - "@entrypoint": reference/decorators/entrypoint.md
```

Also referenced in:
```yaml
- Guides:
    - App & Entry Points: guides/app.md
```

## Content Outline

### `docs/reference/decorators/entrypoint.md` (NEW - Full Reference)

```markdown
# @entrypoint

Decorator that handles QApplication setup and automatic app execution.

## Purpose
Eliminates boilerplate for creating and running Qt applications.

## Basic Usage
[Minimal example with function/class]

## Parameters
- title: str | None
- size: tuple[int, int] | None
- icon: str | None
- dark_mode: bool
- stylesheet: str | None
- watch_stylesheet: bool
- translations: str | None
- language: str | None
- watch_translations: bool
- organization_name: str | None
- organization_domain: str | None
- application_name: str | None

## Behavior
- Creates QApplication if none exists
- Auto-runs app ONLY if module is __main__
- Preserves decorated function/class for testing
- Returns widget/window from function

## With Functions
[Example: function returning Widget/Window]

## With Classes
[Example: @entrypoint @widget class]

## Stylesheets
- QSS file support
- SCSS compilation
- QRC resource loading (:/path)
- Hot-reload with watch_stylesheet

## Translations
[Brief overview, link to guides/translations.md]

## Application Metadata
- organization_name
- organization_domain
- application_name
[Explain Qt's settings/config usage]

## Testing
[How to test entrypoint-decorated code]

## Notes
- Function/class remains callable
- Config stored on decorated object
- Auto-run only in __main__ module
```

### `docs/guides/app.md` (NEW - Practical Guide)

```markdown
# Application & Entry Points

How to structure and run QtPie applications.

## The @entrypoint Decorator
[Quick intro, link to reference]

## Entry Point Patterns

### Function-Based Entry
[When to use, example]

### Class-Based Entry
[When to use, example, show @widget stacking]

## Window Configuration
[title, size, icon examples]

## Styling Your App
### Loading Stylesheets
[QSS, SCSS, QRC examples]

### Hot-Reload in Development
[watch_stylesheet demo]

### Dark Mode
[dark_mode parameter]

## Internationalization Setup
[translations parameter, link to guides/translations.md]

## Application Metadata
[organization_name, etc., explain Qt settings]

## Running Your App
[python myapp.py, testing, packaging]

## Multiple Windows
[How to show additional windows]

## Without @entrypoint
[Manual QApplication setup for advanced cases]
```

### `docs/start/hello-world.md` (UPDATE - Add Section)

Add after first working example:

```markdown
## Understanding @entrypoint

The `@entrypoint` decorator handles Qt application setup:

```python
# Without @entrypoint - manual setup
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
widget = MyWidget()
widget.show()
sys.exit(app.exec())

# With @entrypoint - automatic
@entrypoint
@widget
class MyWidget(Widget):
    ...

# Just run: python myapp.py
```

The decorator:
- Creates QApplication automatically
- Shows the widget/window
- Runs app.exec() if module is __main__
- Lets you test the widget without running the app

[Link to full reference]
```

## Code Examples Needed

### 1. Minimal Function Entry
```python
from qtpie import entrypoint
from PySide6.QtWidgets import QLabel

@entrypoint
def main() -> QLabel:
    return QLabel("Hello, World!")
```

### 2. Minimal Class Entry
```python
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Hello!")
```

### 3. With Configuration
```python
@entrypoint(
    title="My Application",
    size=(800, 600),
    icon="app.png",
    dark_mode=True
)
@widget
class MyApp(Widget):
    ...
```

### 4. With Stylesheet (QSS)
```python
@entrypoint(stylesheet="styles/app.qss")
@widget
class MyApp(Widget):
    ...
```

### 5. With Stylesheet (SCSS + Watch)
```python
@entrypoint(
    stylesheet="styles/app.scss",
    watch_stylesheet=True  # Hot-reload during dev
)
@widget
class MyApp(Widget):
    ...
```

### 6. With QRC Resource
```python
@entrypoint(stylesheet=":/styles/app.qss")
@widget
class MyApp(Widget):
    ...
```

### 7. With Translations
```python
@entrypoint(
    translations="i18n/translations.yml",
    language="en",
    watch_translations=True
)
@widget
class MyApp(Widget):
    label: QLabel = new(t("Hello"))
```

### 8. With App Metadata
```python
@entrypoint(
    organization_name="MyCompany",
    organization_domain="mycompany.com",
    application_name="MyApp"
)
@widget
class MyApp(Widget):
    ...
# Settings now stored in proper OS location
```

### 9. Testing Pattern
```python
@entrypoint
@widget
class MyApp(Widget):
    label: QLabel = new("Test")

# Test without running app
def test_my_app(qtbot):
    widget = MyApp()  # Just instantiate, doesn't run app
    assert widget.label.text() == "Test"
```

### 10. Without @entrypoint (Advanced)
```python
# For when you need full control
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

# Custom app setup here
app.setStyle("Fusion")

widget = MyWidget()
widget.show()

sys.exit(app.exec())
```

## Cross-References

### From entrypoint docs, link to:
- [Translations Guide](../../../guides/translations.md) - For i18n setup
- [Styling Guide](../../../basics/styling.md) - For QSS/SCSS details
- [Testing Guide](../../../guides/testing.md) - For pytest patterns
- [@widget decorator](./widget.md) - Often used together
- [@window decorator](./window.md) - Often used together

### From other docs, link to entrypoint:
- `start/hello-world.md` - Add explanation section
- `guides/app.md` - Main practical guide
- `guides/translations.md` - Show entrypoint with translations
- `basics/styling.md` - Show entrypoint with stylesheets
- `guides/testing.md` - Show testing entrypoint-decorated code

## Implementation Notes

### Key Points to Emphasize
1. **Auto-run behavior** - Only runs in `__main__`, safe for testing
2. **Decorator stacking** - Use with `@widget` or `@window`
3. **Function vs. class** - Both patterns supported
4. **Stylesheet formats** - QSS, SCSS, QRC all work
5. **Hot-reload** - Development feature for stylesheets/translations
6. **Preserved callability** - Decorated object still works normally
7. **Config storage** - Uses ENTRY_CONFIG_ATTR internally

### Common Pitfalls to Document
1. Order matters: `@entrypoint` goes FIRST (outermost)
2. Function must return Widget/Window (if using function pattern)
3. watch_stylesheet only for dev, not production
4. QRC paths need resource file compiled first
5. Translations require YAML format (link to spec)

### API Surface from Test File
Based on test_entrypoint.md:
- EntryConfig dataclass (internal)
- ENTRY_CONFIG_ATTR constant (internal)
- _apply_stylesheet() helper (internal)
- _load_qrc_stylesheet() helper (internal)
- _is_main_module() check (internal)
- _should_auto_run() check (internal)

Users mainly interact with decorator parameters, not internals.

## Visual Aids

Consider adding diagrams for:
1. Decision tree: When does @entrypoint auto-run?
2. Lifecycle: What @entrypoint does behind the scenes
3. File structure: Where to put stylesheets/translations

## Related Features

- Window configuration (size, title, icon)
- Stylesheet loading and watching
- Translation system integration
- Qt application metadata (for settings storage)
- Testing without running the event loop
