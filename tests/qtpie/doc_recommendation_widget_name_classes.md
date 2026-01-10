# Documentation Proposal: Widget Names and CSS Classes

## Overview

Document the `name=` and `classes=` parameters for setting `objectName` and CSS classes on widgets, fields, and repeater items. This is a foundational styling feature that enables QSS selector targeting.

## Priority

**HIGH** - This is a fundamental feature for styling and must be documented early since users need it to:
- Apply QSS/stylesheets effectively
- Use CSS-like selectors (#id, .class)
- Target specific widgets programmatically
- Organize UI components semantically

## Files to Add/Update

### 1. Create: `docs/basics/styling.md` (NEW)
Primary documentation for styling basics including name/classes parameters.

**Rationale**: Currently missing from docs structure but present in mkdocs nav. This should be the main entry point for styling concepts.

### 2. Update: `docs/basics/widgets.md` (if exists, otherwise CREATE)
Add brief mention of name/classes in the basic widget section with cross-reference to styling.md.

### 3. Create: `docs/reference/styles/class-helpers.md` (NEW)
Document the `get_classes()` and `set_classes()` helper functions from `qtpie.styles`.

**Rationale**: Listed in mkdocs nav but file doesn't exist. Needed for programmatic class manipulation.

### 4. Update: `docs/index.md`
Add styling example to the feature showcase if not already present.

## Suggested Nav Location

Based on existing mkdocs.yml:

```yaml
nav:
  - Basics:
      - Styling: basics/styling.md  # PRIMARY LOCATION
  - Reference:
      - Styles:
          - Class Helpers: reference/styles/class-helpers.md  # API reference
```

The feature spans two locations:
- **Basics/Styling**: User-facing documentation with examples
- **Reference/Styles**: API documentation for helper functions

## Content Outline: `docs/basics/styling.md`

### Structure

```markdown
# Styling

## Object Names and CSS Classes

### Setting Widget Names
- @widget(name="...") for widget class itself
- new(name="...") for individual fields
- Default behavior (class name / field name)
- Use cases for custom names

### Setting CSS Classes
- @widget(classes=[...]) for widget class
- new(classes=[...]) for fields
- Multiple classes
- Semantic naming conventions

### QSS Selectors
- ID selectors: #objectName
- Class selectors: .className
- Combined selectors
- Example stylesheet integration

## Variable Widgets
- Setting name/classes on Variable[T, W] widgets
- Chained new() syntax: new(value)(name="...", classes=[...])

## List and Dict Repeaters
- Applying name/classes to all items in a repeater
- list[QWidget] with new(bind="...", name="...", classes=[...])
- Variable[list[T], W] with new(...)(name="...", classes=[...])
- Variable[dict[K, V], W] same pattern
- Dynamic items inherit name/classes

## Default Object Names
- Widget defaults to class name
- Fields default to field name
- Why this matters for QSS selectors

## Non-QWidget Classes
- name= and classes= passed as constructor kwargs
- Use case: custom components with styling metadata

## Best Practices
- When to use explicit names vs defaults
- CSS class naming conventions
- Organization strategies for large UIs
```

## Content Outline: `docs/reference/styles/class-helpers.md`

```markdown
# Class Helpers

## get_classes()

Get CSS classes from a widget.

**Signature**: `get_classes(widget: QWidget) -> list[str]`

## set_classes()

Set CSS classes on a widget.

**Signature**: `set_classes(widget: QWidget, classes: list[str]) -> None`

## add_class() / remove_class()

If these exist, document them here.

## Usage Examples

Show programmatic class manipulation patterns.
```

## Code Examples Needed

### 1. Basic Widget Name and Classes
```python
@widget(name="main-panel", classes=["panel", "primary"])
class MainPanel(Widget):
    _title: QLabel = new("Title", name="panel-title", classes=["heading"])
    _button: QPushButton = new("Action", classes=["btn", "btn-primary"])
```

### 2. With QSS Stylesheet
```python
@widget(
    name="styled-card",
    classes=["card"],
    stylesheet="""
        #styled-card { background: white; border-radius: 8px; }
        .card { padding: 16px; }
        .heading { font-size: 18px; font-weight: bold; }
        .btn-primary { background: blue; color: white; }
    """
)
class StyledCard(Widget):
    _title: QLabel = new("Card Title", classes=["heading"])
    _action: QPushButton = new("Click", classes=["btn", "btn-primary"])
```

### 3. Variable Widget Names
```python
@widget
class LoginForm(Widget):
    _username: Variable[str, QLineEdit] = new("")(
        name="username-input",
        classes=["input", "required"]
    )
    _password: Variable[str, QLineEdit] = new("")(
        name="password-input",
        classes=["input", "required", "password"]
    )
```

### 4. List Repeater Names/Classes
```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Buy milk", "Walk dog"])
    _labels: list[QLabel] = new(
        bind="_items",
        name="todo-item",
        classes=["item", "clickable"]
    )
```

### 5. Dynamic Items Example
```python
@widget
class DynamicList(Widget):
    _items: Variable[list[str]] = new([])
    _labels: list[QLabel] = new(bind="_items", classes=["list-item"])

    def add_item(self, text: str):
        self._items.append(text)  # New label gets "list-item" class automatically
```

### 6. Default Names Example
```python
@widget
class MyWidget(Widget):
    _button: QPushButton = new("Click")  # objectName = "_button"

# In QSS:
# #MyWidget { background: white; }
# #_button { color: blue; }
```

### 7. Non-QWidget Class Example
```python
class StyledComponent:
    def __init__(self, value: int, name: str = "", classes: list[str] | None = None):
        self.value = value
        self.name = name
        self.classes = classes or []

@widget
class MyWidget(Widget):
    _component: StyledComponent = new(42, name="my-component", classes=["styled"])
```

### 8. Programmatic Class Manipulation
```python
from qtpie.styles import get_classes, set_classes

def highlight_button(self):
    classes = get_classes(self._button)
    classes.append("highlighted")
    set_classes(self._button, classes)
```

## Cross-References

Link to related documentation:

- **From `basics/styling.md`**:
  - Link to `basics/widgets.md` - Basic widget creation
  - Link to `state/property-bindings.md` - Reactive visible/enabled based on state
  - Link to `reference/styles/class-helpers.md` - Programmatic class manipulation
  - Link to `reference/decorators/widget.md` - Full widget decorator API
  - Link to `reference/factories/new.md` - Full new() factory API

- **To `basics/styling.md`** (add references from):
  - `basics/widgets.md` - "See [Styling](../basics/styling.md) for objectName and classes"
  - `start/concepts.md` - Mention styling in key concepts
  - `index.md` - Feature showcase

## Additional Notes

### Integration with Existing Docs

The CLAUDE.md already has a section "Object Name and CSS Classes" (lines 277-288) which should be:
1. Expanded with more examples in the new `docs/basics/styling.md`
2. Kept in CLAUDE.md as reference (it's for Claude context, not user docs)

### QSS Integration

Consider adding a subsection or separate guide about:
- Loading external QSS files
- Global vs widget-specific stylesheets
- Qt stylesheet syntax primer (or link to Qt docs)
- Common styling patterns (themes, dark mode, etc.)

### Example Application

Consider creating a complete example app that demonstrates:
- Semantic naming conventions
- Theme switching via class manipulation
- QSS stylesheet organization
- Real-world styling patterns

This could go in `docs/examples.md` or a separate `examples/styling/` directory.

### Testing Note

All features are thoroughly tested in `tests/qtpie/test_widget_name_classes.py`. The test file can serve as a reference for edge cases and complete feature coverage.

### Comparison to Other Frameworks

Consider adding a comparison section showing how this maps to:
- HTML/CSS: `<div id="name" class="class1 class2">`
- Qt Designer: objectName and styleSheet properties
- Other declarative UI frameworks

This helps users coming from web development or Qt Designer backgrounds.
