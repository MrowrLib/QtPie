# Documentation Proposal for Widget Feature

## Overview

Based on the current state of QtPie v2 documentation, nearly all pages defined in `mkdocs.yml` are missing. This proposal outlines what needs to be created to properly document the Widget feature and related functionality.

---

## Files to Add/Update

### HIGH PRIORITY (Core Documentation)

1. **`docs/start/install.md`** - NEW
   - Installation instructions (uv/poetry/pip)
   - PySide6 vs PyQt6 setup
   - Quick verification that installation worked

2. **`docs/start/hello-world.md`** - NEW
   - First QtPie app walkthrough
   - Explain @widget decorator, new(), Variable[T]
   - Run the app with @entrypoint
   - What happens behind the scenes

3. **`docs/start/concepts.md`** - NEW
   - Core concepts: declarative vs imperative
   - Widget fields and the new() factory
   - Layouts (automatic)
   - Signal connections
   - Reactive state with Variable[T]
   - When to use QtPie vs plain Qt

4. **`docs/basics/widgets.md`** - NEW
   - Basic widget creation with @widget
   - Field declarations and types
   - The new() factory in detail
   - __setup__() lifecycle hook
   - Widget composition (nesting widgets)

5. **`docs/basics/layouts.md`** - NEW
   - Layout types: vertical, horizontal, form, grid, None
   - Layout margins and spacing
   - Excluding widgets from layout (layout=False)
   - Custom layout control

6. **`docs/basics/signals.md`** - NEW
   - Declarative signal connections
   - String-based connections (clicked="method_name")
   - Lambda connections
   - Multiple signals on one widget
   - Signal forwarding patterns

7. **`docs/basics/styling.md`** - NEW
   - objectName and CSS classes (name=, classes=)
   - StyleSheet basics (stylesheet= alias)
   - Widget properties via decorator kwargs
   - Child widget properties via new() kwargs

8. **`docs/state/variables.md`** - NEW
   - Variable[T] - reactive state
   - Variable[T, W] - state + widget
   - Direct assignment (self._count += 1)
   - Accessing .value and .widget
   - Variable lifecycle

9. **`docs/state/bindings.md`** - NEW
   - bind= parameter for widgets
   - Simple variable bindings (bind="_name")
   - Format string basics (bind="Hello, {_name}!")
   - Binding to Variable[T, W]
   - Reactivity - how updates propagate

10. **`docs/state/format-expressions.md`** - NEW
    - Complex Python expressions in format strings
    - Function calls, methods, math
    - Format specs (:.2f)
    - Special placeholders (#self, #var, #widget, #index, #key, #value)
    - Using instance methods in bindings

11. **`docs/state/property-bindings.md`** - NEW
    - Reactive visible= and enabled= properties
    - Expression-based conditions
    - Combining with Variable[T]

12. **`docs/data/records.md`** - NEW
    - Widget[T] and Window[T] generic types
    - record= decorator parameter
    - Auto-binding fields to record properties
    - ObservableProxy behavior
    - Accessing self.record and self.record_state

13. **`docs/data/lists-dicts.md`** - NEW
    - list[QWidget] with bind= (WidgetRepeater)
    - Custom format strings for lists
    - Dict bindings with #key/#value
    - Reactivity with lists and dicts
    - Complex object lists

14. **`docs/data/validation.md`** - NEW
    - add_validator() API
    - Named validators
    - is_valid property
    - validation_errors structure
    - validation_error_messages
    - on_valid_changed() lifecycle hook

15. **`docs/data/dirty-tracking.md`** - NEW
    - view_model.is_dirty
    - dirty_fields tracking
    - reset_dirty()
    - on_dirty_changed() lifecycle hook

16. **`docs/guides/windows-menus.md`** - NEW
    - Window vs Widget
    - @window decorator
    - @menu decorator and QMenu
    - Auto-adding menus to menu bar
    - Window[T] record types

17. **`docs/guides/translations.md`** - NEW
    - t() function for marking translatable strings
    - Translation YAML format
    - @entrypoint translation setup
    - set_language() runtime switching
    - CLI commands (qtpie tr compile, etc.)
    - Disambiguation and plurals

18. **`docs/guides/app.md`** - NEW
    - @entrypoint decorator
    - QApplication lifecycle
    - When to use vs manual QApplication setup

19. **`docs/reference/decorators/widget.md`** - NEW
    - Complete @widget API reference
    - All decorator parameters
    - layout, margins, name, classes
    - Dynamic properties (title=, windowTitle=, etc.)
    - record= parameter

20. **`docs/reference/factories/new.md`** - NEW
    - Complete new() API reference
    - Positional vs keyword args
    - QtPie-specific kwargs (bind=, name=, classes=, layout=, signal connections)
    - Qt passthrough kwargs
    - Chaining calls for Variable[T, W]

21. **`docs/reference/classes/widget.md`** - NEW
    - Widget base class API
    - Properties: is_dirty, dirty_fields, is_valid, validation_errors, etc.
    - Methods: add_validator(), reset_dirty()
    - Lifecycle hooks: __setup__(), on_dirty_changed(), on_valid_changed()

22. **`docs/reference/classes/variable.md`** - NEW
    - Variable[T] and Variable[T, W] API
    - Properties: .value, .widget, .observable
    - Assignment behavior
    - Integration with observant library

### MEDIUM PRIORITY

23. **`docs/guides/forms.md`** - NEW
    - @widget(layout="form")
    - label= parameter on fields
    - Form validation patterns
    - Common form widgets

24. **`docs/guides/grids.md`** - NEW
    - @widget(layout="grid")
    - grid= parameter (row, col, rowspan, colspan)
    - Grid layout patterns

25. **`docs/guides/async.md`** - NEW
    - @slot decorator for async handlers
    - Background operations
    - Updating UI from async code

26. **`docs/guides/testing.md`** - NEW
    - Testing QtPie widgets
    - QApplication setup in tests
    - Mocking signals
    - Testing reactive bindings

27. **`docs/reference/decorators/window.md`** - NEW
    - @window decorator API
    - Window-specific parameters

28. **`docs/reference/decorators/menu.md`** - NEW
    - @menu decorator API
    - QAction creation
    - Signal connections

29. **`docs/reference/decorators/slot.md`** - NEW
    - @slot decorator for async
    - Error handling

30. **`docs/reference/decorators/entrypoint.md`** - NEW
    - @entrypoint decorator API
    - All parameters (translations, language, watch_translations)

31. **`docs/reference/classes/window.md`** - NEW
    - Window base class API
    - Differences from Widget

### LOW PRIORITY

32. **`docs/examples.md`** - UPDATE
    - Comprehensive real-world examples
    - Full apps with multiple features
    - Common patterns and recipes

33. **`docs/reference/styles/color-schemes.md`** - NEW
    - If QtPie provides color scheme helpers

34. **`docs/reference/styles/class-helpers.md`** - NEW
    - If QtPie provides CSS class utilities

---

## Suggested Nav Location

The current `mkdocs.yml` nav structure is well-organized. All files should be created as already specified in the nav tree. No structural changes needed.

---

## Content Outline by Section

### Getting Started (Priority 1)

**Installation** (`start/install.md`):
- Prerequisites (Python 3.13+)
- Package installation (uv/poetry/pip)
- PySide6 vs PyQt6
- Verifying installation

**Hello World** (`start/hello-world.md`):
- Minimal counter example
- Line-by-line explanation
- Running the app
- What happens behind the scenes (decorator magic)

**Key Concepts** (`start/concepts.md`):
- Declarative vs imperative
- The @widget decorator
- Fields and new() factory
- Automatic layouts
- Reactive state (Variable)
- Signal connections
- Composition patterns

### Basics (Priority 1)

**Widgets** (`basics/widgets.md`):
- Creating widgets with @widget
- Field type annotations
- The new() factory
- Widget vs non-widget fields
- __setup__() hook
- Widget composition
- When to use @widget decorator

**Layouts** (`basics/layouts.md`):
- Layout types (vertical, horizontal, form, grid, None)
- Default behavior (vertical)
- margins parameter (int or tuple)
- spacing control
- layout=False on fields
- Manual layout control when needed

**Signals** (`basics/signals.md`):
- String-based: clicked="on_click"
- Lambda-based: clicked=lambda: ...
- Multiple signals
- Signal parameters
- Best practices

**Styling** (`basics/styling.md`):
- objectName (name= parameter)
- CSS classes (classes= parameter)
- styleSheet / stylesheet
- Decorator kwargs for widget properties
- new() kwargs for child properties
- Property aliases (title, stylesheet)

### Reactive State (Priority 1)

**Variables** (`state/variables.md`):
- Variable[T] - reactive value only
- Variable[T, W] - reactive value + widget
- Direct assignment (+=, =)
- .value property
- .widget property
- .observable property (observant integration)

**Bindings** (`state/bindings.md`):
- bind= parameter
- Simple variable reference (bind="_name")
- Format strings (bind="Hello, {_name}!")
- How reactivity works
- Binding to Variable[T, W]
- Performance considerations

**Format Expressions** (`state/format-expressions.md`):
- Full Python expressions
- Built-in functions (len, max, etc.)
- String methods (.upper(), .lower())
- Math expressions
- Format specs (:.2f, :03d)
- Instance method calls
- Special placeholders table
- Variable[T, W] context (#self vs #var vs #widget)
- List/dict context (#index, #key, #value)

**Property Bindings** (`state/property-bindings.md`):
- visible= reactive property
- enabled= reactive property
- Expression-based conditions
- Combining multiple Variables

### Data & Forms (Priority 1)

**Record Widgets** (`data/records.md`):
- Widget[T] generic type
- record= decorator parameter
- Setting record in __setup__()
- Auto-binding by field name
- ObservableProxy[T] behavior
- self.record vs self.record_state
- Accessing .is_dirty, .value, .observable

**Lists & Dicts** (`data/lists-dicts.md`):
- list[QWidget] with bind=
- WidgetRepeater behavior
- Custom format= strings
- #index placeholder
- Dict bindings (#key, #value)
- Reactivity (auto-add/remove widgets)
- Complex object lists

**Validation** (`data/validation.md`):
- add_validator(field, name, func) API
- Validator functions (return None or error string)
- Named validators (replace/remove)
- is_valid property
- validation_errors structure
- validation_error_messages list
- Binding to error messages
- on_valid_changed() hook

**Dirty Tracking** (`data/dirty-tracking.md`):
- view_model.is_dirty property
- dirty_fields list
- reset_dirty() method
- on_dirty_changed() hook
- Use cases (enable Save button)

### Guides (Priority 2)

**Windows & Menus** (`guides/windows-menus.md`):
- @window decorator
- Window vs Widget
- @menu decorator
- QAction creation
- Auto-adding menus to menu bar
- Window[T] record types

**Translations** (`guides/translations.md`):
- t() function usage
- Translation YAML format
- @entrypoint setup
- set_language() runtime switching
- Disambiguation (context=)
- Plurals (%n)
- CLI tools (qtpie tr compile/list)

**App & Entry Points** (`guides/app.md`):
- @entrypoint decorator
- QApplication lifecycle
- When to use
- Manual QApplication setup

**Form Layouts** (`guides/forms.md`):
- layout="form"
- label= parameter
- Form validation patterns
- Common widgets

**Grid Layouts** (`guides/grids.md`):
- layout="grid"
- grid=(row, col, rowspan, colspan)
- Grid patterns

**Async** (`guides/async.md`):
- @slot decorator (if implemented)
- Background tasks
- UI updates from async

**Testing** (`guides/testing.md`):
- QApplication in tests
- Testing widgets
- Testing bindings
- Mocking signals

### Reference (Priority 3)

API reference pages for:
- Decorators (@widget, @window, @menu, @slot, @entrypoint)
- Factories (new())
- Classes (Widget, Window, Variable)
- Styles (if applicable)

---

## Code Examples Needed

### Must-Have Examples

1. **Basic widget** - Label + button
2. **Counter with Variable[T]** - Reactive state
3. **Variable[T, W] inline** - QLineEdit with reactive value
4. **Format string expressions** - Math, functions, methods
5. **Record binding** - Person editor with Widget[Person]
6. **List binding** - Todo list with WidgetRepeater
7. **Dict binding** - Scoreboard with #key/#value
8. **Validation** - Form with validators
9. **Dirty tracking** - Enable Save button when dirty
10. **Window with menu** - @window + @menu
11. **Translations** - Basic t() usage
12. **Conditional visibility** - visible="{expression}"
13. **Signal connections** - clicked="method" vs lambda
14. **Nested widgets** - Parent passing Variable to child
15. **Layout types** - vertical, horizontal, form, grid
16. **Layout exclusion** - layout=False

### Nice-to-Have Examples

17. **Complex form** - Multi-field validation
18. **Master-detail** - List selection updates detail view
19. **Settings panel** - Tabs with different widget types
20. **Dynamic lists** - Add/remove items
21. **Async operations** - Long-running task with progress
22. **Testing** - Unit test examples

---

## Cross-References

### Within Documentation

- **Hello World** → link to: Concepts, Variables, Bindings, Signals
- **Concepts** → link to: Widgets, Layouts, Variables, Signals
- **Widgets** → link to: Layouts, new(), @widget reference
- **Variables** → link to: Bindings, Format Expressions, Validation
- **Bindings** → link to: Variables, Format Expressions, Property Bindings
- **Format Expressions** → link to: Bindings, Lists & Dicts
- **Records** → link to: Dirty Tracking, Validation, Widget[T] reference
- **Lists & Dicts** → link to: Format Expressions, Variables
- **Validation** → link to: Variables, Records, Forms guide
- **Dirty Tracking** → link to: Records, Validation
- **Windows & Menus** → link to: @window/@menu reference
- **Translations** → link to: @entrypoint reference
- **App** → link to: Hello World, @entrypoint reference

### External Links

- Link to PySide6 docs for Qt types (QLabel, QPushButton, etc.)
- Link to observant library docs (if separate)
- Link to Qt QSS documentation for styling
- Link to Python format string spec for format= syntax

---

## Priority Rationale

### High Priority (Complete First)

These cover the core Widget functionality that users will encounter immediately:
- Getting Started section (install, hello world, concepts)
- Basics section (widgets, layouts, signals, styling)
- Reactive State section (variables, bindings, expressions, property bindings)
- Data & Forms section (records, lists/dicts, validation, dirty tracking)
- Essential guides (windows/menus, translations, app)
- Core reference (decorators, factories, classes)

Users cannot effectively use QtPie without these docs.

### Medium Priority (Complete Second)

Advanced guides that help with specific use cases:
- Form layouts
- Grid layouts
- Async operations
- Testing strategies
- Additional reference pages

### Low Priority (Nice to Have)

- Examples page (partially exists)
- Style helpers (may not exist yet)
- Advanced patterns and recipes

---

## Special Considerations

### Type Safety Documentation

Given QtPie's focus on pyright strict compliance, documentation should:
- Show correct type annotations in examples
- Explain when/why type parameters are needed
- Document the typing of public APIs
- Explain Variable[T] vs Variable[T, W] type inference

### Beginner-Friendly Approach

- Start simple, add complexity gradually
- Explain "why" not just "how"
- Compare to plain Qt to show benefits
- Use realistic examples (not just toy apps)

### Code Snippet Quality

All code snippets must:
- Be complete and runnable
- Include necessary imports
- Follow QtPie conventions (private fields with _, etc.)
- Pass pyright strict type checking
- Include comments explaining non-obvious parts

### Observant Integration

Some features depend on the observant library. Document:
- What observant provides (Observable[T], ObservableList, etc.)
- How Variable[T] wraps Observable[T]
- When to use .observable property
- Link to observant docs for deep dives

---

## Documentation Structure Best Practices

### Page Layout

Each page should follow this structure:

1. **Title** - Clear, concise
2. **Brief description** - One paragraph explaining what this page covers
3. **Quick example** - Show the feature in action (2-5 lines)
4. **Core concepts** - Explain how it works
5. **Detailed examples** - Multiple use cases
6. **API reference** - If applicable
7. **Common patterns** - Best practices
8. **Gotchas** - Things to watch out for
9. **See also** - Links to related pages

### Code Example Format

```python
# imports at top
from PySide6.QtWidgets import QLabel
from qtpie import Widget, new, widget

# Complete example
@widget
class Example(Widget):
    label: QLabel = new("Hello")

# Usage/explanation if needed
w = Example()
w.show()
```

### Admonitions

Use MkDocs admonitions for:
- !!! tip - Helpful hints
- !!! warning - Common mistakes
- !!! note - Additional info
- !!! example - Highlight patterns

---

## Implementation Checklist

Before marking documentation as "done":

- [ ] All HIGH priority pages created
- [ ] All code examples tested (run with uv run python)
- [ ] All cross-references verified (no broken links)
- [ ] All examples pass pyright strict
- [ ] All examples follow QtPie conventions
- [ ] mkdocs build succeeds with no warnings
- [ ] Navigation structure works (prev/next links)
- [ ] Search works for key terms
- [ ] Mobile-friendly (MkDocs Material theme handles this)

---

## Notes

- The current docs (index.md, why-qtpie.md) are excellent starting points
- CLAUDE.md has comprehensive examples that can be adapted
- test_widget.md shows what features are implemented
- Focus on user-facing docs, not internal architecture
- Keep examples short and focused on one concept
- Progressive disclosure: basic → intermediate → advanced
