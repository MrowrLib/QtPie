# QtPie v2 Documentation Proposal

## Current State

**Existing Files:**
- `docs/index.md` - Landing page with quick overview
- `docs/why-qtpie.md` - Before/after comparison
- `docs/qt-resources.md` - Qt reference links

**Missing from mkdocs.yml nav:** All "Getting Started", "Basics", "Reactive State", "Data & Forms", "Guides", and "Reference" sections are defined in nav but files don't exist.

## Recommendations by Priority

---

### Priority: HIGH

#### 1. Getting Started Section

**Files to Add:**

- `docs/start/install.md`
- `docs/start/hello-world.md`
- `docs/start/concepts.md`

**Nav Location:** Already defined under "Getting Started"

**Content Outline:**

**install.md:**
- Installation with uv/poetry/pip
- PySide6 vs PyQt6 support
- Optional dependencies (qasync for async, pytest-qt for testing)
- Verify installation with `import qtpie`

**hello-world.md:**
- Minimal counter example from index.md expanded
- Step-by-step breakdown of each line
- Running the app (`python app.py`)
- Common first-time issues (QApplication, imports)
- Link to Key Concepts for deeper dive

**concepts.md:**
- The three core primitives: `@widget`, `Widget`, `new()`
- What is declarative UI?
- Reactive state (`Variable[T]`)
- The `new()` factory and field descriptors
- Lifecycle: class definition → `__init_subclass__` → `__init__` → `__setup__`
- Quick comparison table: Qt vs QtPie patterns

**Code Examples Needed:**
- Basic widget with label/button (hello-world.md)
- Widget with reactive Variable (concepts.md)
- Side-by-side Qt vs QtPie comparison (concepts.md)

**Cross-References:**
- hello-world → concepts, basics/widgets
- concepts → state/variables, basics/widgets
- install → hello-world

---

#### 2. Basics Section

**Files to Add:**

- `docs/basics/widgets.md`
- `docs/basics/layouts.md`
- `docs/basics/signals.md`
- `docs/basics/styling.md`

**Nav Location:** Already defined under "Basics"

**Content Outline:**

**widgets.md:**
- The `@widget` decorator and `Widget` base class
- Field annotations: `field: QLabel = new("text")`
- The `new()` factory parameters (positional args, Qt kwargs, QtPie kwargs)
- Public vs private fields (naming conventions)
- Widget composition (nesting widgets)
- The `__setup__()` lifecycle hook
- Accessing child widgets

**layouts.md:**
- `layout="vertical"` (default), `"horizontal"`, `"form"`, `"grid"`
- Layout-specific parameters: `label=` for form, `grid=` for grid
- Manual layout control (when/why to use plain Qt layouts)
- Spacing and margins (using Qt properties)
- Stretch factors and alignment

**signals.md:**
- Declarative signal connections: `clicked="method_name"`
- Lambda connections: `clicked=lambda: print("hi")`
- Signal forwarding: `clicked="my_signal"` (define `my_signal = Signal()`)
- Multiple connections to same signal
- Disconnecting signals (when needed)
- Common Qt signals reference table (clicked, textChanged, etc.)

**styling.md:**
- `name="my-widget"` for objectName
- `classes=["primary", "large"]` for CSS class-like selectors
- Widget-level QSS with `setStyleSheet()`
- Application-level QSS
- QSS selectors: `#objectName`, `.className`, `WidgetType`
- Common QSS patterns (buttons, inputs, colors)
- Dark mode example

**Code Examples Needed:**
- Basic widget with multiple fields (widgets.md)
- Each layout type with 3-4 widgets (layouts.md)
- Signal connection patterns (signals.md)
- Styled widget with QSS (styling.md)

**Cross-References:**
- widgets → layouts, signals, state/variables
- layouts → guides/forms, guides/grids
- signals → qt-resources (Qt signals reference)
- styling → reference/styles/*

---

#### 3. Reactive State Section

**Files to Add:**

- `docs/state/variables.md`
- `docs/state/bindings.md`
- `docs/state/format-expressions.md`
- `docs/state/property-bindings.md`

**Nav Location:** Already defined under "Reactive State"

**Content Outline:**

**variables.md:**
- `Variable[T]` - single reactive value
- Creating variables: `_count: Variable[int] = new(0)`
- Reading: `_count.get()` or `_count.value`
- Writing: `_count.set(5)` or `_count.value = 5` or `_count += 1`
- `.observable` for subscribing to changes
- `Variable[T, W]` - variable + auto-created widget
- Accessing the widget: `_name.widget`
- Variable composition (passing variables to child widgets)

**bindings.md:**
- `bind="_variable_name"` - simple binding
- `bind="static text {_variable}"` - interpolation
- `bind="{_x + _y}"` - computed bindings
- Reactivity: auto-updates when any referenced variable changes
- Multiple bindings to same variable
- Performance considerations (avoid expensive computations)

**format-expressions.md:**
- Full Python expressions in `{...}`: math, methods, functions
- Special placeholders: `{#self}`, `{#var}`, `{#widget}`, `{#index}`, `{#key}`, `{#value}`
- Format specs: `{_price:.2f}`
- Method calls: `{_name.upper()}`, `{len(_items)}`
- Instance methods: `{compute()}`
- List context: `{#index}`, `{#self}`
- Dict context: `{#key}`, `{#value}`
- Expression dependency tracking (how QtPie knows what to watch)

**property-bindings.md:**
- `visible="{expression}"` - reactive visibility
- `enabled="{expression}"` - reactive enabled state
- Boolean expressions: `{len(_name) > 0}`
- Combining multiple variables: `{is_valid and is_dirty}`
- Common patterns: conditional UI, validation-gated buttons

**Code Examples Needed:**
- Variable[T] and Variable[T, W] usage (variables.md)
- Simple/interpolated/computed bindings (bindings.md)
- Each special placeholder with examples (format-expressions.md)
- visible/enabled use cases (property-bindings.md)

**Cross-References:**
- variables → bindings, reference/classes/variable
- bindings → format-expressions
- format-expressions → data/lists-dicts (for #index/#key/#value)
- property-bindings → bindings

---

#### 4. Data & Forms Section

**Files to Add:**

- `docs/data/records.md`
- `docs/data/lists-dicts.md`
- `docs/data/validation.md`
- `docs/data/dirty-tracking.md`

**Nav Location:** Already defined under "Data & Forms"

**Content Outline:**

**records.md:**
- `Widget[T]` - generic widget bound to record type
- Using `record=` decorator parameter: `@widget(record=Person(...))`
- Alternative: setting `self.record` in `__setup__()`
- Auto-binding: field names matching record properties
- `self.record` - ObservableProxy[T]
- `self.record_state` - access to `.is_dirty`, `.value`, `.observable`
- Reading record fields: `self.record.name`
- Writing record fields: `self.record.name = "new"`
- Nested records (record with record fields)
- Best practices for type safety

**lists-dicts.md:**
- `list[QWidget]` with `bind=` creates WidgetRepeater
- List binding: `_labels: list[QLabel] = new(bind="_items")`
- Custom format: `format="Item #{#index}: {#self}"`
- Dict binding: `bind="_scores"`, format with `{#key}` and `{#value}`
- Adding/removing items (reactive updates)
- Complex objects in lists: `list[Dog]` with `{name}` access
- Performance with large lists
- Manual control (when needed)

**validation.md:**
- `add_validator(field, name, validator_fn)`
- Validator signature: `Callable[[T], str | None]`
- Named validators (replace/remove by name)
- `self.is_valid` - Observable[bool]
- `self.validation_errors` - structured error dict
- `self.validation_error_messages` - flat list
- Binding error messages to labels
- `on_valid_changed(is_valid)` lifecycle hook
- Built-in validators (ideas for common patterns)
- Field-level vs widget-level validation

**dirty-tracking.md:**
- What is dirty tracking? (changed from initial value)
- `self.is_dirty` - Observable[bool]
- `self.dirty_fields` - list of changed field names
- `self.reset_dirty()` - mark all as clean
- `on_dirty_changed(is_dirty)` lifecycle hook
- Common pattern: enable Save button when dirty
- Combining with validation: `{is_valid and is_dirty}`
- Record dirty tracking: `self.record_state.is_dirty`

**Code Examples Needed:**
- Person dataclass with PersonEditor widget (records.md)
- List of strings, list of objects, dict binding (lists-dicts.md)
- Form with multiple validators (validation.md)
- Save button enabled when dirty and valid (dirty-tracking.md)

**Cross-References:**
- records → data/validation, data/dirty-tracking
- lists-dicts → state/format-expressions (#index/#key/#value)
- validation → data/dirty-tracking (combining is_valid and is_dirty)
- dirty-tracking → data/validation

---

### Priority: MEDIUM

#### 5. Guides Section

**Files to Add:**

- `docs/guides/windows-menus.md`
- `docs/guides/forms.md`
- `docs/guides/grids.md`
- `docs/guides/translations.md`
- `docs/guides/app.md`
- `docs/guides/async.md`
- `docs/guides/testing.md`

**Nav Location:** Already defined under "Guides"

**Content Outline:**

**windows-menus.md:**
- `@window` decorator and `Window` base class
- Window parameters: `title=`, `record=`
- `Window[T]` for record-bound windows
- The `@menu` decorator
- Menu structure: actions, separators, submenus
- Auto-adding menus to menu bar
- Menu signals: `triggered="on_action"`
- Keyboard shortcuts
- Standard menus (File, Edit, Help patterns)

**forms.md:**
- `@widget(layout="form")` for form layouts
- `label="Field Name:"` parameter
- Label alignment and colon handling
- Multi-column forms (using nested widgets)
- Form with validation + dirty tracking
- Required field indicators
- Form submission pattern
- Reset form to defaults

**grids.md:**
- `@widget(layout="grid")` for grid layouts
- `grid=(row, col)` or `grid=(row, col, rowspan, colspan)`
- Grid alignment and spanning
- Empty cells
- Dynamic grids (when to use manual GridLayout)
- Common grid patterns (calculator, color picker)

**translations.md:**
- `t("text")` for translatable strings
- `@entrypoint(translations="file.yml", language="en")`
- Translation YAML format: `:global:` and widget contexts
- Disambiguation: `t("Open", context="menu")`
- Plurals: `t("%n file(s)")(count)`
- `set_language("fr")` for runtime switching
- CLI commands: `qtpie tr compile`, `qtpie tr list`
- Hot-reload with `watch_translations=True`
- Best practices: when to disambiguate, translator notes

**app.md:**
- `@entrypoint` decorator
- QApplication setup and teardown
- Application-level settings (icon, stylesheet)
- Multiple windows
- Main window show/hide/close patterns
- System tray integration (if supported)
- Exit handling

**async.md:**
- `@slot` decorator for async methods
- qasync integration
- Async signal handlers: `clicked="async_handler"`
- Updating UI from async code
- Progress indicators with async operations
- Error handling in async slots
- Background tasks
- Cancellation patterns

**testing.md:**
- Using qtpie.testing module (wrapper for pytest-qt)
- `qtbot` fixture usage
- Creating widgets in tests
- Simulating user input (clicks, text entry)
- Waiting for signals/conditions
- Testing reactive updates
- Mocking
- Testing validation/dirty tracking
- CI integration

**Code Examples Needed:**
- MainWindow with FileMenu (windows-menus.md)
- Registration form with labels (forms.md)
- Calculator-style grid layout (grids.md)
- Multi-language app with t() (translations.md)
- Complete app with @entrypoint (app.md)
- Button that loads data asynchronously (async.md)
- Test for counter widget (testing.md)

**Cross-References:**
- windows-menus → basics/widgets
- forms → basics/layouts, data/validation
- grids → basics/layouts
- translations → guides/app (@entrypoint)
- app → guides/async, guides/testing
- async → guides/testing (testing async code)
- testing → all feature pages (how to test each feature)

---

### Priority: LOW

#### 6. Reference Section

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

**Nav Location:** Already defined under "Reference"

**Content Outline:**

**Decorators:**
- Each decorator on its own page
- Signature with all parameters
- Parameter descriptions (types, defaults, purpose)
- Return type
- Usage examples (minimal and comprehensive)
- Related decorators/classes

**new.md:**
- `new(*args, **kwargs)` signature
- Positional args → widget constructor
- QtPie keyword args: `bind=`, `name=`, `classes=`, signals, `visible=`, `enabled=`, `label=`, `grid=`
- Qt keyword args → passed to constructor
- Variable[T, W] chaining: `new(value)(widget_kwargs)`
- Return type (NewField descriptor)
- Examples for each parameter type

**Classes:**
- Class reference for Widget, Window, Variable
- Constructor signatures
- Properties (readable/writable)
- Methods
- Lifecycle hooks (`__setup__`, `on_dirty_changed`, etc.)
- Type parameters (`Widget[T]`, `Window[T]`)
- Inheritance patterns

**Styles:**
- color-schemes.md: Pre-built color schemes (if any), how to create custom
- class-helpers.md: Utility functions for styling (if any), best practices

**Code Examples Needed:**
- Minimal and full usage for each decorator/factory/class
- All parameters demonstrated

**Cross-References:**
- Decorators → corresponding Classes
- new → all pages (used everywhere)
- Classes → guides that use them extensively

---

#### 7. Examples Page

**File to Add:**

- `docs/examples.md`

**Nav Location:** Already defined as "Examples" (top-level)

**Content Outline:**
- Complete runnable examples
- Each example as collapsible section or link to GitHub
- Examples:
  - Todo List (add/remove items, list binding)
  - Calculator (grid layout, reactive computation)
  - User Registration Form (validation, dirty tracking)
  - Settings Dialog (record binding, checkboxes)
  - Multi-window App (main window + dialogs)
  - Translated App (i18n)
  - Async Data Loader (progress bar, async/await)
  - Custom Styled App (QSS theming)

**Code Examples Needed:**
- 5-8 complete apps (50-200 lines each)

**Cross-References:**
- Link to relevant guide/reference pages for each feature used

---

## Missing Features to Document

Based on CLAUDE.md but not in mkdocs.yml nav:

1. **Observant library** - The reactive primitives (`Observable[T]`, `ObservableList`, `ObservableDict`, `ObservableProxy`)
   - Suggestion: Add "Advanced" section with `docs/advanced/observant.md`
   - Explain how QtPie uses these internally
   - When/why to use them directly (rare, but possible)

2. **Lifecycle hooks** - `__setup__()`, `on_dirty_changed()`, `on_valid_changed()`
   - Partially covered in various pages
   - Suggestion: Add `docs/reference/lifecycle-hooks.md` with complete list

3. **view_model** - Reference to `self.view_model.is_dirty` in dirty tracking
   - Clarify in `data/dirty-tracking.md` what view_model is

4. **Reactive decorator properties** - `@widget(windowTitle="{_title}")`
   - Covered in CLAUDE.md but should be in `basics/widgets.md` or separate page

5. **Signal forwarding** - `clicked="my_signal"` where `my_signal = Signal()`
   - Mentioned in CLAUDE.md but not in outline
   - Add to `basics/signals.md`

---

## Documentation Gaps to Address

1. **Type safety guidance**
   - How to maintain pyright strict compliance
   - Common typing patterns with QtPie
   - Suggestion: Add `docs/guides/type-safety.md`

2. **Performance considerations**
   - When reactive bindings might be expensive
   - List rendering performance
   - Suggestion: Add "Performance" section to relevant pages

3. **Debugging**
   - How to debug reactive bindings
   - Inspecting variable dependencies
   - Common pitfalls
   - Suggestion: Add `docs/guides/debugging.md`

4. **Migration guide**
   - From plain Qt to QtPie
   - From v1 to v2
   - Suggestion: Add `docs/guides/migration.md`

5. **Architecture deep-dive**
   - How descriptors work
   - `__init_subclass__` magic
   - For contributors/advanced users
   - Suggestion: Add `docs/advanced/architecture.md`

---

## Style Guide for Writing Docs

1. **Code examples first** - Show working code, then explain
2. **Progressive disclosure** - Simple example, then variations
3. **Consistent example domain** - Use todo/counter/person examples consistently
4. **Runnable snippets** - Every example should be copy-paste runnable
5. **Type annotations** - Always show full types in examples
6. **Imports** - Show imports in first example per page
7. **Cross-reference liberally** - Link to related pages
8. **Admonitions** - Use for tips, warnings, notes
9. **Before/after** - Show Qt vs QtPie when introducing concepts
10. **Why, not just how** - Explain the reasoning

---

## Tooling Recommendations

1. **Add code block testing** - Ensure examples actually run
2. **API reference generator** - Consider sphinx/mkdocstrings for auto-generating reference from docstrings
3. **Example repo** - Separate repo with full examples that are tested in CI
4. **Search optimization** - Add keywords/aliases for common searches
5. **Diagrams** - Consider mermaid for lifecycle/architecture diagrams

---

## Estimated Effort

- **HIGH priority** (Getting Started + Basics + State + Data): ~20-30 pages, 2-3 weeks
- **MEDIUM priority** (Guides): ~7 pages, 1-2 weeks
- **LOW priority** (Reference + Examples): ~15 pages, 1-2 weeks

Total: ~40-50 pages of documentation, 4-7 weeks at steady pace.

Recommend starting with Getting Started → Basics → State, as these build on each other and unblock most use cases.
