# QtPie v2 Documentation Proposal

## Current State Analysis

**Existing Documentation:**
- `docs/index.md` - Landing page with basic overview
- `docs/why-qtpie.md` - Feature comparison and design philosophy
- `mkdocs.yml` - Nav structure with comprehensive outline (most pages don't exist yet)

**Current Nav Structure:**
- Home / Why QtPie (exist)
- Getting Started (3 pages planned)
- Basics (4 pages planned)
- Reactive State (4 pages planned)
- Data & Forms (4 pages planned)
- Guides (7 pages planned)
- Reference (decorators, factories, classes, styles - multiple pages planned)
- Examples / Qt Resources (planned)

**Gap:** Most documentation pages are outlined in nav but don't exist yet.

---

## Priority: HIGH

### 1. Getting Started Section

**Files to Add:**
- `docs/start/install.md`
- `docs/start/hello-world.md`
- `docs/start/concepts.md`

**Nav Location:** Already in nav under "Getting Started"

**Content Outline:**

#### `install.md`
- Installation via uv/poetry/pip
- PySide6/PyQt6 choice (qtpy abstraction)
- Verify installation
- IDE setup (pyright, type stubs)
- First test run

#### `hello-world.md`
- Minimal counter example (already in index.md)
- Explanation of each line
- Running the app
- Adding more features step-by-step
- Common beginner mistakes

#### `concepts.md`
- Declarative vs imperative
- The `@widget` decorator
- The `new()` factory
- Automatic layouts
- Field naming conventions (underscore prefix)
- Widget lifecycle (`__setup__`)
- Overview of key types: `Widget`, `Variable`, `Window`, `Menu`

**Code Examples Needed:**
- Basic widget with label + button
- Widget with Variable reactive state
- Widget with layout options
- Annotated diagram showing field → widget mapping

**Cross-References:**
- Link to `basics/widgets.md` for deep dive
- Link to `state/variables.md` for reactivity
- Link to `why-qtpie.md` for motivation

**Priority:** HIGH - Users need this to start

---

## Priority: HIGH

### 2. Basics Section

**Files to Add:**
- `docs/basics/widgets.md`
- `docs/basics/layouts.md`
- `docs/basics/signals.md`
- `docs/basics/styling.md`

**Nav Location:** Already in nav under "Basics"

**Content Outline:**

#### `widgets.md`
- Widget class anatomy
- Field declarations with `new()`
- Positional vs keyword args to `new()`
- Field types: plain widgets vs Variables vs lists
- Naming conventions (underscore prefix for private)
- objectName auto-assignment
- Accessing widgets at runtime

#### `layouts.md`
- Default vertical layout
- `layout="horizontal"` / `"form"` / `"grid"`
- Form layouts with `label=` parameter
- Grid layouts with `grid=(row, col, rowspan, colspan)`
- Nested widgets as containers
- Layout parameters (margins, spacing)

#### `signals.md`
- Declarative signal connections: `clicked="method_name"`
- Lambda connections: `clicked=lambda: ...`
- Multiple signal types (clicked, textChanged, etc.)
- Signal forwarding: `clicked="my_signal"`
- Programmatic connections in `__setup__`
- Disconnecting signals

#### `styling.md`
- objectName and CSS classes
- `name=` parameter to set objectName
- `classes=[]` parameter for CSS classes
- QSS stylesheet loading
- Class name selectors (e.g., `#StyledWidget`)
- Dynamic styling based on state
- Decorator-level styling: `@widget(name="...", classes=[...])`

**Code Examples Needed:**
- All layout types side-by-side
- Signal connection patterns
- Styled widget with QSS
- Complex nested layout example

**Cross-References:**
- Link to `state/variables.md` for reactive widgets
- Link to `guides/forms.md` for form-specific patterns
- Link to `reference/decorators/widget.md` for all decorator options

**Priority:** HIGH - Foundation knowledge

---

## Priority: HIGH

### 3. Reactive State Section

**Files to Add:**
- `docs/state/variables.md`
- `docs/state/bindings.md`
- `docs/state/format-expressions.md`
- `docs/state/property-bindings.md`

**Nav Location:** Already in nav under "Reactive State"

**Content Outline:**

#### `variables.md`
- What is `Variable[T]`?
- Creating variables: `_count: Variable[int] = new(0)`
- Reading/writing: `.value` property or direct assignment
- Variable with widget: `Variable[T, W]`
- Accessing inline widget: `.widget` property
- Observable pattern under the hood
- When to use Variable vs plain fields

#### `bindings.md`
- Basic text binding: `bind="_variable_name"`
- String interpolation: `bind="Value: {_var}"`
- Binding to widget properties beyond text
- Two-way bindings (QLineEdit to Variable)
- Auto-binding in `Widget[T]` record types
- Composability: passing Variables to child widgets

#### `format-expressions.md`
- Expression syntax in `{}` placeholders
- Math: `{_x + _y}`, `{(_x + _y) * _z}`
- String methods: `{_name.upper()}`, `{_name.strip()}`
- Built-in functions: `{len(_items)}`, `{abs(_value)}`
- Format specs: `{_price:.2f}`
- Method calls: `{compute()}`, `{repeat(_name, 3)}`
- Special placeholders table:
  - `{#self}` - variable value or widget
  - `{#var}` - explicit variable value
  - `{#widget}` - parent widget instance
  - `{#app}` - QApplication instance
  - `{#index}` - list item index
  - `{#key}` / `{#value}` - dict items
- Reactivity: auto-updates when dependencies change

#### `property-bindings.md`
- `visible=` binding: `visible="_show_flag"`
- `enabled=` binding: `enabled="_can_submit"`
- Expression-based: `visible="{len(_name) > 0}"`
- Boolean Variable binding
- Combining multiple conditions
- Reactive decorator properties: `@widget(windowTitle="{_title}")`

**Code Examples Needed:**
- Variable lifecycle (create, read, write, react)
- Variable[T, W] with chained `new()` calls
- Format expression cookbook (all placeholder types)
- Reactive visibility/enabled scenarios
- Parent-child Variable passing example

**Cross-References:**
- Link to `data/records.md` for record binding
- Link to `data/lists-dicts.md` for collection binding
- Link to observant library docs (if exists)

**Priority:** HIGH - Core feature

---

## Priority: HIGH

### 4. Data & Forms Section

**Files to Add:**
- `docs/data/records.md`
- `docs/data/lists-dicts.md`
- `docs/data/validation.md`
- `docs/data/dirty-tracking.md`

**Nav Location:** Already in nav under "Data & Forms"

**Content Outline:**

#### `records.md`
- `Widget[T]` generic type
- Dataclass/NamedTuple as record types
- `record=` decorator parameter
- `self.record` ObservableProxy
- `self.record_state` accessor
- Auto-binding by field name
- Nested record widgets
- `Window[T]` and `Menu[T]` variants
- `record="parent_field"` binding from parent

#### `lists-dicts.md`
- List field syntax: `_items: list[QLabel] = new(bind="_source")`
- WidgetRepeater internals
- Custom format strings for list items
- Dict binding with `{#key}` / `{#value}`
- Dynamic updates (insert, remove, reorder)
- Complex object lists
- Performance considerations

#### `validation.md`
- `add_validator(field, name, func)` method
- Validator function signature: `value -> None | str`
- Named validators (replaceable, removable)
- `is_valid` Observable[bool]
- `validation_errors` structure
- `validation_error_messages` flat list
- `on_valid_changed()` lifecycle hook
- Validator timing (immediate vs on-submit)
- UI feedback patterns

#### `dirty-tracking.md`
- `view_model.is_dirty` Observable[bool]
- `dirty_fields` list
- `reset_dirty()` method
- `on_dirty_changed()` lifecycle hook
- Use case: enable Save button
- Combining with validation
- Per-field dirty tracking

**Code Examples Needed:**
- Full CRUD form with Person record
- Dynamic list example (todo list)
- Dict binding example (scoreboard)
- Validated form with all validator types
- Dirty tracking with save/reset buttons

**Cross-References:**
- Link to `state/bindings.md` for binding fundamentals
- Link to `guides/forms.md` for complete form patterns
- Link to observant ObservableProxy docs

**Priority:** HIGH - Key differentiator

---

## Priority: MEDIUM

### 5. Guides Section

**Files to Add:**
- `docs/guides/windows-menus.md`
- `docs/guides/forms.md`
- `docs/guides/grids.md`
- `docs/guides/translations.md`
- `docs/guides/app.md`
- `docs/guides/async.md`
- `docs/guides/testing.md`

**Nav Location:** Already in nav under "Guides"

**Content Outline:**

#### `windows-menus.md`
- `@window` decorator
- `Window` base class
- Menu declaration with `@menu`
- QAction fields auto-added to menu
- Menu added to menu bar
- Menu separators: `___: Separator`
- Menu sections: `___section___: Section`
- Window with record type: `Window[T]`
- Status bar, toolbars (if supported)

#### `forms.md`
- Form layout pattern: `layout="form"`
- `label=` parameter for row labels
- Form validation patterns
- Submit/reset buttons
- Read-only vs editable modes
- Multi-step forms (wizard pattern)
- Form with record type

#### `grids.md`
- Grid layout: `layout="grid"`
- `grid=(row, col)` parameter
- Spanning: `grid=(row, col, rowspan, colspan)`
- Alignment in grid cells
- Dynamic grid (if possible)
- Common grid patterns (calculator, color picker)

#### `translations.md`
- `t()` function for marking strings
- `@entrypoint(translations="file.yml", language="en")`
- YAML translation file format
- `:global:` vs widget-specific translations
- Disambiguation: `context=` parameter
- Plurals: `t("%n item(s)")(count)`
- `set_language()` runtime switching
- CLI commands: `qtpie tr compile`, `qtpie tr list`
- Hot-reload in dev: `watch_translations=True`

#### `app.md`
- `@entrypoint` decorator
- `App` class (if exists in v2 - check test_app.md suggests AppBase)
- `AppBase` vs `Widget` vs `Window` for root
- `app()` decorator (from test_app.md)
- System tray support
- QAction fields auto-added to tray
- Application-level state
- Lifecycle hooks
- Multiple windows

#### `async.md`
- `@slot` decorator for async handlers
- Threading considerations
- Progress indicators
- Cancellation patterns
- Error handling in async slots
- Background tasks
- Integration with asyncio/Qt event loop

#### `testing.md`
- Testing QtPie widgets
- pytest fixtures for QApplication
- Testing reactive state
- Testing signal connections
- Testing validation
- Testing bindings
- Mocking strategies
- Example test suite

**Code Examples Needed:**
- Complete window with menu bar example
- Multi-page form wizard
- Grid-based calculator
- Translation setup end-to-end
- App with system tray
- Async operation with progress bar
- Test suite for validated form

**Cross-References:**
- All guides should cross-reference basics and state docs
- Link app.md to entrypoint reference
- Link testing.md to pytest docs and Qt testing

**Priority:** MEDIUM - Important but users can start without these

---

## Priority: MEDIUM

### 6. Reference Section

**Files to Add:**
- `docs/reference/decorators/widget.md`
- `docs/reference/decorators/window.md`
- `docs/reference/decorators/menu.md`
- `docs/reference/decorators/slot.md`
- `docs/reference/decorators/entrypoint.md`
- `docs/reference/factories/new.md`
- `docs/reference/classes/widget.md`
- `docs/reference/classes/window.md`
- `docs/reference/classes/variable.md`
- `docs/reference/styles/color-schemes.md`
- `docs/reference/styles/class-helpers.md`

**Nav Location:** Already in nav under "Reference"

**Content Outline:**

All reference pages should follow this structure:
- Function/class signature
- Parameter table with types and descriptions
- Return type
- Behavior description
- Common patterns
- Edge cases and gotchas
- Complete code examples

#### Decorator Pages
- **@widget**: All parameters (layout, name, classes, record, windowTitle, etc.)
- **@window**: Window-specific parameters (title, record, etc.)
- **@menu**: Menu title, icons, enabled state
- **@slot**: Async handler decoration
- **@entrypoint**: App initialization (translations, language, watch_translations, etc.)

#### Factory Pages
- **new()**: Complete parameter reference
  - Positional args → widget constructor
  - QtPie special kwargs: bind, name, classes, visible, enabled, label, grid
  - Signal connections: clicked, textChanged, etc.
  - Qt constructor kwargs pass-through
  - Chaining for `Variable[T, W]`

#### Class Pages
- **Widget**: Base class members
  - Properties: record, record_state, is_dirty, is_valid, view_model
  - Methods: add_validator, reset_dirty
  - Hooks: __setup__, on_dirty_changed, on_valid_changed
- **Window**: Extends Widget for QMainWindow
- **Variable**: Type parameters, properties (.value, .widget, .observable)

#### Style Pages
- **color-schemes.md**: Predefined QSS themes (if exists)
- **class-helpers.md**: CSS class utilities (if exists)

**Code Examples Needed:**
- Full parameter examples for each decorator
- new() parameter matrix
- Widget lifecycle diagram

**Cross-References:**
- Each reference page links to tutorial/guide that uses it
- Cross-link related APIs (Widget ↔ Variable)

**Priority:** MEDIUM - Reference, not tutorial

---

## Priority: LOW

### 7. Examples & Resources

**Files to Add:**
- `docs/examples.md`
- `docs/qt-resources.md`

**Nav Location:** Already in nav at top level

**Content Outline:**

#### `examples.md`
- Gallery of complete applications
- Todo list app
- Settings dialog
- Data entry form
- Multi-window app
- Translated app
- Async app with loading
- Each with full source + explanation
- Link to GitHub examples folder

#### `qt-resources.md`
- Link to PySide6/PyQt6 official docs
- Qt widget gallery
- QSS styling references
- Qt Designer (if compatible)
- Useful Qt tools
- Community resources

**Code Examples Needed:**
- 5-10 complete mini-apps

**Cross-References:**
- Link from getting started to examples
- Link from each guide to relevant example

**Priority:** LOW - Nice-to-have

---

## Special Considerations

### 1. Observant Library Integration

**Status:** Integrated in `lib/observant/`, but no dedicated docs

**Recommendation:** Create `docs/advanced/observant.md` explaining:
- Observable[T], ObservableList[T], ObservableDict[K,V], ObservableProxy[T]
- How QtPie uses observant under the hood
- Direct observant usage for advanced scenarios
- Performance characteristics

**Priority:** LOW - Most users won't need this

### 2. ref() and sort= Features

**Status:** Mentioned in CLAUDE.md but no dedicated section

**Current Coverage:**
- `ref()` appears in test_app.md for required bindings
- `sort=` appears in git log but not documented

**Recommendation:** Add to existing pages:
- `ref()` → `state/bindings.md` section on forward references
- `sort=` → `data/lists-dicts.md` section on list ordering

**Priority:** MEDIUM - Important features

### 3. signal=<expression> Feature

**Status:** In git log (recent commit) but not in CLAUDE.md

**Recommendation:**
- Document in `basics/signals.md` as "Signal Forwarding"
- Show how to expose child widget signals: `clicked = signal("_button.clicked")`
- Include `#value`, `#index`, `#args` special references

**Priority:** MEDIUM - Composability feature

### 4. Migration Guide

**Status:** Doesn't exist

**Recommendation:** Add `docs/migration-v1-v2.md`
- What changed from v1 to v2
- API differences
- Migration checklist
- Common pitfalls

**Priority:** LOW (unless v1 users exist)

---

## Documentation Writing Guidelines

### For All Pages:

1. **Start with a practical example** (code-first)
2. **Explain the "why"** before the "how"
3. **Use type annotations** in all examples
4. **Show common patterns** and anti-patterns
5. **Link to reference docs** for full API details
6. **Include a "See Also" section** at the end

### Code Style in Examples:

- Use PySide6 imports (note that PyQt6 works via qtpy)
- Use underscore prefix for private fields
- Show full imports (don't assume `from qtpie import *`)
- Add type hints
- Keep examples runnable (include `@entrypoint` if standalone)

### Admonitions to Use:

```markdown
!!! tip "Naming Convention"
    Use underscore prefix for private fields that shouldn't be accessed externally.

!!! warning "Common Mistake"
    Don't access `._value` directly—use `.value` property.

!!! info "Under the Hood"
    Variable[T] wraps observant.Observable[T] for reactivity.

!!! example "Recipe: Form with Validation"
    [Complete working example]
```

---

## Suggested Writing Order

To maximize usefulness as docs are written:

1. **Phase 1: Get Users Started** (Week 1)
   - install.md
   - hello-world.md
   - concepts.md
   - basics/widgets.md
   - state/variables.md

2. **Phase 2: Core Features** (Week 2)
   - basics/layouts.md
   - basics/signals.md
   - state/bindings.md
   - state/format-expressions.md
   - data/records.md

3. **Phase 3: Advanced Data** (Week 3)
   - data/lists-dicts.md
   - data/validation.md
   - data/dirty-tracking.md
   - state/property-bindings.md
   - guides/forms.md

4. **Phase 4: Application Features** (Week 4)
   - guides/windows-menus.md
   - guides/app.md
   - guides/translations.md
   - basics/styling.md

5. **Phase 5: Reference & Examples** (Week 5+)
   - All reference pages
   - guides/async.md
   - guides/testing.md
   - examples.md

---

## Maintenance Plan

### On Feature Addition:
1. Update CLAUDE.md first
2. Add to appropriate doc page
3. Add example to examples.md
4. Add to reference if new API

### On Bug Fix:
1. Check if docs have incorrect info
2. Add anti-pattern note if common mistake

### On Version Release:
1. Update changelog
2. Update migration guide (if breaking)
3. Review all examples for compatibility

---

## Metrics to Track

Once docs are live:
- Page views (which pages are most accessed)
- Search queries (what users look for)
- GitHub issues referencing docs
- Time-to-first-PR for new contributors

---

## Open Questions

1. **App vs AppBase**: test_app.md uses `AppBase` but CLAUDE.md doesn't mention it. Which is the public API?
2. **Widget[T] vs record= decorator**: CLAUDE.md says "use record= to avoid pyright errors" but is Widget[T] still the primary pattern?
3. **Observant visibility**: Should observant be public API or internal implementation detail?
4. **V1 compatibility**: Do we need migration docs or is v2 a clean break?
5. **Menu class**: test_app.md shows `Menu` base class but CLAUDE.md only shows `@menu` with QMenu. What's the pattern?

---

## Summary

**Total Pages to Create:** ~40 pages

**Effort Estimate:**
- Phase 1-3 (core docs): ~2-3 weeks full-time
- Phase 4-5 (guides + reference): ~2-3 weeks full-time
- **Total: ~4-6 weeks** for comprehensive documentation

**Highest Priority:**
1. Getting Started (3 pages) - Unblock new users
2. Basics (4 pages) - Foundation knowledge
3. Reactive State (4 pages) - Core value prop
4. Data & Forms (4 pages) - Key differentiator

**Quick Win:** Start with `hello-world.md` → immediate value for new users.
