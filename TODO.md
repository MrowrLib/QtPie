# QtPie v2 - Game Plan

Build fresh, slow and steady, let the design emerge from actual needs.

---

## Scope

**Phases 0-7 focus on the core reactive DSL:**
- Observable primitives
- `Variable[T]`, `new()`, bindings
- `WidgetBase`, `Widget`, `Widget[T]`
- Auto-layout system
- MVVM features (dirty, validation, save/load, undo)

**Out of scope for now (QtPie v1 has these, we'll integrate later):**
- `@entrypoint` / QApplication management
- QSS/SCSS styling and hot reload
- Translation/i18n support
- Async support
- CSS classes system
- Other QtPie features

Phase 8 is where we make a plan to either:
1. Replace QtPie v1's core with our new stuff, OR
2. Bolt the existing QtPie features onto our new foundation

---

## Phase 0: Sandbox Setup
- [ ] Fresh project structure for v2 prototyping
- [ ] Test harness (pytest)
- [ ] Mock Qt classes for fast iteration before real Qt

---

## Phase 1: Core Reactivity
Build the minimal observable primitives from scratch:
- [ ] `Observable[T]` - single value with change notifications
- [ ] `on_change()` subscription
- [ ] Basic tests: set value → callback fires

**Don't add yet:** dirty tracking, undo, proxy - let needs emerge

---

## Phase 2: `new()` and `Variable[T]`
The DSL foundation:
- [ ] `new()` that captures metadata via `__set_name__`
- [ ] `Variable[T]` descriptor that reads/writes reactively
- [ ] Tests: class-level declarations, access patterns

---

## Phase 3: `WidgetBase`
Minimal mixin:
- [ ] `__setup__` lifecycle hook
- [ ] Wire up `Variable` fields
- [ ] Test with mock widgets first, then real Qt

---

## Phase 4: `Widget` + Auto-Layout
- [ ] Default `QWidget` container
- [ ] Layout types: vertical, horizontal, form, grid, none
- [ ] `layout=False` exclusion
- [ ] `Variable[T, W]` creating child widgets
- [ ] Tests: field order → layout order

---

## Phase 5: Bindings
- [ ] `bind=_variable_ref` (direct reference)
- [ ] `bind="{_name}"` format strings
- [ ] Two-way binding for input widgets
- [ ] Nested paths, optional chaining

---

## Phase 6: View Model
- [ ] `Widget` auto-generates view model from `Variable` fields
- [ ] `Widget[T]` uses explicit dataclass
- [ ] `view_model` property access

---

## Phase 7: MVVM Features (one at a time)
Add incrementally, only when we have a use-case:

### 7a: Dirty Tracking
- [ ] `is_dirty()` - has anything changed?
- [ ] `dirty_fields()` - which fields changed?
- [ ] `reset_dirty()` - mark current state as clean
- [ ] `on_dirty_changed()` lifecycle hook

### 7b: Validation
- [ ] `add_validator(field, validator_fn)`
- [ ] `is_valid()` - observable bool
- [ ] `validation_errors()` - per-field errors
- [ ] `on_valid_changed()` lifecycle hook

### 7c: Save/Load
- [ ] `save_to(model)` - copy values to model instance
- [ ] `load_dict(data)` - update from dictionary

### 7d: Undo/Redo
- [ ] Per-field undo/redo stacks
- [ ] `undo(field)`, `redo(field)`
- [ ] `can_undo(field)`, `can_redo(field)`
- [ ] Debouncing for text input

---

## The Observable Question

As we build, discover:
- [ ] Does `Observable[T]` need dirty tracking baked in? Or is that a layer on top?
- [ ] Does `ObservableList` need its own undo stack? Or is that view-model-level?
- [ ] Is `ObservableProxy` even needed, or can `Variable` handle it directly?

Build what we need, when we need it. At the end:
- If it looks like Observant → use Observant
- If it's QtPie-specific → keep it internal
- If it's better/generic → extract as new Observant

---

## Phase 8: Integration Planning

Once Phases 0-7 are complete, make a new plan for full QtPie v2:

- [ ] Evaluate: replace QtPie v1 core vs. bolt QtPie v1 features onto new foundation
- [ ] `@entrypoint` / QApplication management
- [ ] QSS/SCSS styling system and hot reload
- [ ] CSS classes (`classes=["foo", "bar"]`)
- [ ] Translation/i18n support
- [ ] Async support (`async def` in widgets)
- [ ] Signals beyond `clicked=` (all Qt signals)
- [ ] Any other QtPie v1 features we want to keep

This is a separate planning exercise after we've proven out the core.

---

## Notes

- All fields use leading underscore convention for encapsulation
- `__setup__` instead of `setup()` for pythonic naming
- `new()` uses `__set_name__` to avoid repeating type annotations
- `WidgetBase` = no layout (for custom Qt widget subclasses)
- `Widget` / `Widget[T]` = auto-layout enabled
