# Documentation Proposal: Property Bindings

## Files to Add/Update

### New Files
- **`docs/state/property-bindings.md`** (PRIMARY) - Comprehensive guide to reactive property bindings
  - Already referenced in `mkdocs.yml` nav (line 68) but doesn't exist yet

### Files to Update
- **`docs/state/bindings.md`** - Add cross-reference to property-bindings.md, clarify distinction between content bindings (`bind=`) and property bindings (`visible=`, `enabled=`)
- **`docs/index.md`** - Consider adding property bindings to the key features section if not already present
- **`docs/start/concepts.md`** - Briefly mention property bindings as distinct from content bindings

## Suggested Nav Location

Already exists in `mkdocs.yml` at the correct location:

```yaml
- Reactive State:
    - Variables: state/variables.md
    - Bindings: state/bindings.md
    - Format Expressions: state/format-expressions.md
    - Property Bindings: state/property-bindings.md  # Line 68 - already present!
```

**No nav changes needed** - the structure is already set up correctly.

## Content Outline

### 1. Introduction
- What are property bindings vs content bindings (`bind=`)
- Supported properties: `visible=`, `enabled=`
- Brief mention that decorator properties also support this (covered later)

### 2. Basic Usage

#### 2.1 Simple Variable Binding
- Bind to boolean Variable using field name string
- Example: `visible="_show_panel"`
- Example: `enabled="_can_submit"`

#### 2.2 Expression Bindings
- Use `{...}` syntax for Python expressions
- Boolean expressions: `visible="{_count > 0}"`
- String operations: `enabled="{len(_name) > 0}"`
- Combined conditions: `visible="{_logged_in and _is_admin}"`

### 3. Multiple Properties
- Apply multiple bindings to same widget
- Example: `visible="_show", enabled="_allow"`

### 4. Decorator Properties
- Make `@widget` decorator kwargs reactive
- `@widget(windowTitle="{_title}")`
- Multi-variable expressions: `@widget(windowTitle="{_app_name} - {_filename}")`
- Note: Works with any Qt property that decorator supports

### 5. Advanced: Raw Observables
- Bind to `Observable[T]`, `ObservableList[T]`, `ObservableDict[K,V]`, `ObservableProxy[T]`
- Must use `.get()` for Observable: `enabled="{can_submit.get()}"`
- Direct access for collections: `visible="{len(items) > 0}"`
- Proxy property access: `enabled="{settings.enabled}"`
- Complex expressions combining multiple observables

### 6. Common Patterns

#### 6.1 Conditional UI Sections
- Show/hide advanced settings panel
- Display error messages when validation fails

#### 6.2 Enable/Disable Forms
- Submit button enabled only when form is valid
- Save button enabled when data is dirty

#### 6.3 Dynamic Titles
- Window title showing current document name
- Status bar text with user info

### 7. Comparison with Other Features
- **vs Content Bindings** (`bind=`): Property bindings control widget state (visible/enabled), content bindings control widget display value
- **vs Format Expressions**: Property bindings always evaluate to boolean (or string for decorator props), format expressions produce display strings
- **vs Signal Connections**: Property bindings are for one-way data flow, signals are for events

### 8. Best Practices
- Use simple variable names for clarity when possible
- Complex expressions should be readable - consider extracting to computed properties if too complex
- Property bindings are reactive - no manual updates needed
- Type safety: expressions must evaluate to correct type (bool for visible/enabled)

### 9. Troubleshooting
- Common mistake: Forgetting `{}` for expressions vs plain variable names
- Common mistake: Using `.get()` on Variable (Variables auto-unwrap, only Observable needs `.get()`)
- How to debug: Check expression syntax, verify Variables are defined in class
- Performance note: Expressions re-evaluate when any referenced Variable changes

## Code Examples Needed

### Basic Examples
```python
# Simple variable binding
@widget
class ToggleWidget(Widget):
    _show_panel: Variable[bool] = new(True)
    _panel: QWidget = new(visible="_show_panel")

# Expression binding
@widget
class FormWidget(Widget):
    _name: Variable[str] = new("")
    _submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")

# Multiple properties
@widget
class MultiPropWidget(Widget):
    _show: Variable[bool] = new(True)
    _allow: Variable[bool] = new(True)
    _button: QPushButton = new("Action", visible="_show", enabled="_allow")
```

### Realistic Use Cases
```python
# Login form
@widget
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")
    _is_loading: Variable[bool] = new(False)

    _login_btn: QPushButton = new(
        "Login",
        enabled="{len(_username) > 0 and len(_password) > 0 and not _is_loading}"
    )
    _spinner: QLabel = new(visible="_is_loading")

# Advanced settings toggle
@widget
class SettingsPanel(Widget):
    _show_advanced: Variable[bool] = new(False)
    _toggle_btn: QPushButton = new("Show Advanced", clicked="toggle_advanced")
    _advanced_panel: QWidget = new(visible="_show_advanced")

    def toggle_advanced(self) -> None:
        self._show_advanced.value = not self._show_advanced.value

# Conditional admin panel
@widget
class Dashboard(Widget):
    _logged_in: Variable[bool] = new(False)
    _is_admin: Variable[bool] = new(False)

    _admin_panel: QWidget = new(
        visible="{_logged_in and _is_admin}"
    )
```

### Decorator Properties
```python
# Dynamic window title
@widget(windowTitle="{_app_name} - {_filename}")
class EditorWindow(Widget):
    _app_name: Variable[str] = new("MyEditor")
    _filename: Variable[str] = new("untitled.txt")

    def open_file(self, path: str) -> None:
        self._filename.value = path  # Window title updates automatically

# Status-dependent title
@widget(windowTitle="Editor {_has_changes and '(unsaved)' or ''}")
class DocumentEditor(Widget):
    _has_changes: Variable[bool] = new(False)
```

### Raw Observables
```python
# Observable[T] with .get()
@widget
class ObservableExample(Widget):
    can_submit: Observable[bool] = Observable(False)
    _button: QPushButton = new("Submit", enabled="{can_submit.get()}")

# ObservableList
@widget
class ListExample(Widget):
    items: ObservableList[str] = ObservableList()
    _empty_msg: QLabel = new("No items", visible="{len(items) == 0}")
    _count_label: QLabel = new(bind="Items: {len(items)}")

# ObservableProxy
@dataclass
class Settings:
    dark_mode: bool = False
    notifications: bool = True

@widget
class SettingsWidget(Widget):
    settings: ObservableProxy[Settings] = ObservableProxy(Settings())

    _theme_label: QLabel = new(
        bind="Theme: {settings.dark_mode and 'Dark' or 'Light'}"
    )
    _notif_btn: QPushButton = new(
        "Disable Notifications",
        visible="{settings.notifications}"
    )

# Complex multi-observable expression
@widget
class ComplexWidget(Widget):
    is_ready: Observable[bool] = Observable(False)
    items: ObservableList[str] = ObservableList()
    settings: ObservableProxy[Settings] = ObservableProxy(Settings())

    _submit: QPushButton = new(
        "Submit",
        enabled="{is_ready.get() and len(items) > 0 and settings.notifications}"
    )
```

## Cross-References

### Internal Links (within docs)
- **[Variables](variables.md)** - Understanding Variable[T] reactive state
- **[Bindings](bindings.md)** - Content bindings with `bind=` parameter
- **[Format Expressions](format-expressions.md)** - Complex expression syntax (shared with property bindings)
- **[Validation](../data/validation.md)** - Using `is_valid` with property bindings
- **[Dirty Tracking](../data/dirty-tracking.md)** - Using `is_dirty` with property bindings
- **[@widget decorator](../reference/decorators/widget.md)** - All supported decorator properties
- **[Widget class](../reference/classes/widget.md)** - Widget API reference

### Related Features (in same doc)
- Section 2.2 (Expression Bindings) references Format Expressions page for detailed syntax
- Section 4 (Decorator Properties) references @widget decorator reference
- Section 5 (Raw Observables) references Variables page for comparison
- Section 7 (Comparison) creates clear boundaries between related features

### Example Links
```markdown
For more on expression syntax, see [Format Expressions](format-expressions.md).

To understand the underlying reactive state, see [Variables](variables.md).

For controlling widget *content* rather than properties, see [Bindings](bindings.md).

To use property bindings with form validation, see [Validation](../data/validation.md).
```

## Priority

**HIGH**

### Rationale:
1. **Already in nav structure** - The page is referenced in `mkdocs.yml` (line 68) but doesn't exist, causing a broken link in the docs
2. **Core feature** - Property bindings (`visible=`, `enabled=`) are fundamental to reactive UI patterns in QtPie
3. **User confusion** - Easy to confuse with content bindings (`bind=`); needs clear documentation to distinguish
4. **Test coverage exists** - `test_property_bindings.md` shows the feature is implemented and tested
5. **Mentioned in CLAUDE.md** - Section "Property Bindings (visible=, enabled=)" exists (lines 549-568) but is brief
6. **Practical utility** - Extremely common use case (conditional UI, form validation, etc.)
7. **Decorator properties** - The reactive decorator property pattern is powerful but underdocumented

### User Impact:
- Users trying to create conditional UI will look for this immediately
- Critical for form-based applications (enable submit when valid, show errors conditionally)
- Foundation for building responsive, reactive interfaces
- Decorator property reactivity is a "wow" feature that needs visibility

## Notes

- The test file (`test_property_bindings.md`) is well-structured and can serve as the basis for doc examples
- CLAUDE.md section (lines 549-568) is concise; docs should expand with more use cases
- Consider adding a comparison table between `bind=`, `visible=`, `enabled=`, and signal connections
- Raw Observable support (section 5) might be advanced - consider a callout or "Advanced" heading
- Decorator properties (section 4) deserve emphasis - this is a unique QtPie feature that's very powerful
