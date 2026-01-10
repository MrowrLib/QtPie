# Documentation Proposal: WidgetRepeater

## Overview

The `WidgetRepeater` feature is a core reactive pattern in QtPie that automatically creates and synchronizes widgets with list/dict data. This is demonstrated extensively in CLAUDE.md but lacks dedicated documentation explaining the underlying mechanism and advanced use cases.

## 1. Files to Add

### `docs/data/widget-repeater.md`

**New comprehensive page** explaining WidgetRepeater as a standalone concept, including:
- What WidgetRepeater is and how it works
- When it's created (automatically vs explicitly)
- The underlying ObservableList/ObservableDict synchronization
- Advanced patterns and best practices

## 2. Files to Update

### `docs/data/lists-dicts.md` (Priority Update)

Currently this file should cover list/dict binding basics. Needs to be updated to:
- Add a clear "How It Works" section explaining WidgetRepeater
- Reference the new dedicated widget-repeater.md page for deep dive
- Show the two syntaxes side by side:
  - `Variable[list[T], QWidget]` (inline widget type)
  - `list[QWidget]` with `bind=` parameter (standalone binding)

### `docs/state/format-expressions.md`

Update to include:
- Section on repeater-specific placeholders (`{#index}`, `{#key}`, `{#value}`)
- Examples showing these placeholders in list/dict contexts
- Cross-reference to widget-repeater.md

### `docs/reference/classes/variable.md`

Add section explaining:
- How `Variable[list[T], W]` creates a WidgetRepeater
- The `.widget` property returns a WidgetRepeater instance
- Cross-reference to widget-repeater.md

### `docs/start/concepts.md`

Add brief mention in reactive state section:
- "Lists and dicts can be bound to widget repeaters that auto-sync"
- Link to data/lists-dicts.md for full explanation

### `docs/basics/widgets.md`

Add note about `list[QWidget]` field types:
- Special handling for list-typed fields with `bind=` parameter
- Briefly mention WidgetRepeater creation
- Link to data/widget-repeater.md

## 3. Suggested Location in Nav

Insert in the "Data & Forms" section (already has Lists & Dicts):

```yaml
- Data & Forms:
    - Record Widgets: data/records.md
    - Lists & Dicts: data/lists-dicts.md
    - Widget Repeater: data/widget-repeater.md  # NEW
    - Validation: data/validation.md
    - Dirty Tracking: data/dirty-tracking.md
```

**Rationale**: WidgetRepeater is fundamentally about data binding for collections, so it belongs in "Data & Forms" alongside Records and Lists & Dicts. It's more specialized than the general lists-dicts overview, so it follows that page.

## 4. Content Outline

### `docs/data/widget-repeater.md` (New File)

#### Section 1: Introduction
- What is WidgetRepeater?
- Automatic widget creation and synchronization
- When WidgetRepeater is created (two syntaxes)
- Basic example showing both syntaxes

#### Section 2: Two Ways to Create WidgetRepeaters
- **Inline Widget Type**: `Variable[list[T], QWidget]`
  - Clean syntax for simple cases
  - Widget type is part of Variable declaration
  - Example with primitives
- **Standalone Binding**: `list[QWidget]` with `bind=`
  - Separation of data and presentation
  - Useful when data is complex or shared
  - Example binding to existing Variable

#### Section 3: Synchronization Behavior
- Granular list operations (append, insert, remove, replace, clear)
- Widget creation/destruction timing
- Layout integration
- Index management after operations
- Code examples from test_widget_repeater.md lines 29-46

#### Section 4: Two-Way Binding
- Primitives (int, str, bool) support two-way sync
- Widget edits update the list
- List changes update widgets
- Example from test_widget_repeater.md lines 48-67

#### Section 5: Complex Object Binding
- Binding object properties with format strings
- Single property binding enables two-way sync
- Multiple properties are display-only
- Examples from test_widget_repeater.md lines 69-98

#### Section 6: Format Expressions and Placeholders
- Special placeholders: `{#self}`, `{#index}`, `{#key}`, `{#value}`
- Format parameter variations (string template vs callable)
- Examples from test_widget_repeater.md lines 100-159

#### Section 7: Dict Binding
- Using `list[QWidget]` with dict variables
- `{#key}` and `{#value}` placeholders
- Accessing widgets by key with `widget_for_key()`
- Example from test_widget_repeater.md lines 114-136

#### Section 8: Widget Configuration
- Kwargs propagation to all child widgets
- Configuration applies to existing and future widgets
- Example from test_widget_repeater.md lines 160-178

#### Section 9: WidgetRepeater API Reference
- `widget_count() -> int`
- `widget_at(index: int) -> QWidget`
- `widget_for_key(key: K) -> QWidget` (dict binding only)
- `clear()` - remove all widgets
- Internal methods (marked as advanced/internal)

#### Section 10: Best Practices
- When to use inline vs standalone syntax
- Performance considerations (widget creation cost)
- Avoid deeply nested repeaters
- Consider custom composite widgets for complex items
- Testing strategies

#### Section 11: Common Patterns
- Todo lists
- Settings/preferences lists
- Directory/file browsers
- Chat message displays
- Score boards / leaderboards

#### Section 12: Troubleshooting
- "Widget not updating" - check if using ObservableList methods
- "Index out of range" after operations - index management
- "Two-way binding not working" - check if using primitives or single property

### `docs/data/lists-dicts.md` (Update)

Add these sections:

#### "How It Works: WidgetRepeater"
- Brief explanation of the WidgetRepeater mechanism
- Link to data/widget-repeater.md for full details

#### Update existing examples
- Show both syntax variations side by side
- Add note about when each is appropriate

## 5. Code Examples Needed

From `test_widget_repeater.md`:

1. **Basic creation** (lines 7-14): Shows minimal WidgetRepeater usage
2. **Layout integration** (lines 18-27): Shows repeater in parent layout
3. **Granular sync** (lines 33-45): All list operations demonstrated
4. **Two-way binding** (lines 52-67): Primitive type bidirectional sync
5. **Complex objects single property** (lines 80-89): Two-way with objects
6. **Complex objects multi-property** (lines 93-98): Display-only binding
7. **Placeholders** (lines 105-112): Index and self placeholders
8. **Dict binding** (lines 118-136): Dict with key/value placeholders
9. **Format parameter string** (lines 144-149): Template format
10. **Format parameter callable** (lines 153-158): Lambda format
11. **Widget kwargs** (lines 166-178): Configuration propagation
12. **Index management** (lines 184-196): Correctness after operations

Additional examples to create:

1. **Todo list app** - practical end-to-end example
2. **Settings editor** - dict binding with complex values
3. **Custom widget repeater** - using custom widgets instead of QLabel/QLineEdit
4. **Comparison: manual vs WidgetRepeater** - show plain Qt approach vs QtPie

## 6. Cross-References

### Pages that should link TO widget-repeater.md:
- `data/lists-dicts.md` - "For details on how WidgetRepeater works, see..."
- `state/format-expressions.md` - "Repeater placeholders are explained in..."
- `reference/classes/variable.md` - "When Variable wraps a list/dict..."
- `start/concepts.md` - "QtPie automatically creates widget repeaters..."
- `basics/widgets.md` - "List-typed fields create WidgetRepeaters..."
- `examples.md` - Include todo list or similar example

### Pages that widget-repeater.md should link TO:
- `state/variables.md` - For Variable[T] basics
- `state/format-expressions.md` - For bind expression syntax
- `data/lists-dicts.md` - For basic list/dict concepts
- `reference/factories/new.md` - For new() parameter reference
- `basics/layouts.md` - For layout behavior

## 7. Priority

**HIGH PRIORITY - Core Concept**

### Reasoning:

1. **Fundamental Feature**: WidgetRepeater is one of QtPie's killer features that differentiates it from plain Qt. It's heavily used in CLAUDE.md examples.

2. **Currently Undocumented**: While CLAUDE.md shows usage, there's no dedicated explanation of:
   - How WidgetRepeater actually works under the hood
   - The relationship to ObservableList/ObservableDict
   - The two different syntaxes and when to use each
   - Advanced features like two-way binding rules

3. **User Confusion Risk**: Without proper docs, users might:
   - Not understand the difference between `Variable[list[T], W]` and `list[W]` with `bind=`
   - Struggle with why two-way binding works sometimes but not others
   - Miss dict binding capabilities entirely
   - Not know about kwargs propagation

4. **Enables Other Features**: Understanding WidgetRepeater is prerequisite for:
   - Complex form builders
   - Dynamic UI patterns
   - Reactive collections

### Suggested Documentation Order:

1. **First**: Update `data/lists-dicts.md` with a "How It Works" section
2. **Second**: Create comprehensive `data/widget-repeater.md`
3. **Third**: Update cross-references in other pages
4. **Fourth**: Add practical examples to `examples.md`

This ensures users get a gentle introduction in lists-dicts.md, then can deep-dive into widget-repeater.md when needed.

## 8. Additional Recommendations

### Interactive Examples

Consider adding runnable examples in the docs that users can copy-paste:

- Simple todo list (add/remove items)
- Editable contact list with two-way binding
- Settings panel with dict binding
- Chat message display (append-only pattern)

### Diagrams

Visual diagrams would help explain:

1. **Synchronization flow**: `ObservableList` ↔ `WidgetRepeater` ↔ `QWidget[]` ↔ `QLayout`
2. **Two-way binding**: User edits widget → Signal → Update list → Notify observers
3. **Index management**: How indices shift during insert/remove operations

### Comparison Table

Create a comparison table for the two syntaxes:

| Feature | `Variable[list[T], W]` | `list[W]` with `bind=` |
|---------|------------------------|------------------------|
| Syntax complexity | More concise | More explicit |
| Data ownership | Variable owns data | Data can be shared |
| Format parameter | Via chained `()` call | Via `format=` param |
| When to use | Simple, self-contained | Complex, shared data |
| Type inference | Excellent | Good |

### Performance Notes

Add performance guidance:

- Widget creation is not free - avoid 1000+ item lists
- Use `QListWidget`/`QTableWidget` for large datasets
- Consider virtualization for huge lists
- WidgetRepeater is best for &lt;100 items

### Migration from v1

If v1 had a similar feature, include migration notes. If not, mention this is new in v2.

## Summary

WidgetRepeater is a high-priority documentation gap that needs dedicated coverage. It's a core feature that users will encounter early and need to understand thoroughly. The documentation should:

- Start with simple examples (lists-dicts.md)
- Provide comprehensive coverage (widget-repeater.md)
- Include practical patterns (examples.md)
- Cross-reference extensively

The proposed structure balances beginner-friendliness (progressive disclosure) with advanced coverage (dedicated deep-dive page) while fitting naturally into the existing documentation navigation.
