# Documentation Proposal: WidgetRepeater Signal Connections

## Overview

WidgetRepeater signal connections enable parent widgets to handle signals from dynamically-repeated child widgets with contextual information (index, value, widget instance, signal args). This is critical for interactive lists like todo apps, item pickers, or any repeating UI pattern where user interactions on individual items need to propagate to the parent.

## Priority

**HIGH** - This is a core feature for building interactive lists/grids with repeating widgets. Without documentation, users will struggle to handle clicks/changes in repeated child widgets.

---

## Files to Add/Update

### New File: `docs/data/widget-repeater-signals.md`

Main documentation for WidgetRepeater signal connections with special placeholders.

**Rationale**: This belongs in the "Data & Forms" section since it deals with list/dict data binding and is closely related to `docs/data/lists-dicts.md`.

### Update File: `docs/data/lists-dicts.md` (when created)

Add a cross-reference section at the end:

```markdown
## Handling Child Widget Signals

When child widgets in a repeater need to trigger actions, see [WidgetRepeater Signal Connections](widget-repeater-signals.md) for handling clicks, deletions, and other interactions.
```

### Update File: `mkdocs.yml`

Add to nav structure under "Data & Forms":

```yaml
  - Data & Forms:
      - Record Widgets: data/records.md
      - Lists & Dicts: data/lists-dicts.md
      - WidgetRepeater Signals: data/widget-repeater-signals.md  # NEW
      - Validation: data/validation.md
      - Dirty Tracking: data/dirty-tracking.md
```

---

## Suggested Nav Location

**Section**: Data & Forms
**Position**: After "Lists & Dicts", before "Validation"
**Filename**: `docs/data/widget-repeater-signals.md`

**Reasoning**:
- Natural progression: learn about list bindings first, then learn how to handle interactions
- "Data & Forms" section already covers related reactive data concepts
- Users working with repeaters will likely need signal handling immediately after setup

---

## Content Outline

### 1. Introduction (1 paragraph)

Brief explanation: when using list/dict bindings with child widgets that emit signals, use special placeholders to pass contextual information to parent handlers.

### 2. Special Placeholders (reference table)

| Placeholder | Type Passed | Description |
|------------|-------------|-------------|
| `#index` | `int` | Index of item in list |
| `#value` | `T` | The actual item from list/dict |
| `#widget` | `QWidget` | Child widget instance |
| `#args` | Spread | Signal's own arguments |

### 3. Basic Examples (practical patterns)

#### 3.1 Delete Button Handler

Show common pattern: user clicks delete on a todo item.

```python
@widget
class TodoApp(Widget):
    _items: list[str] = ["Task 1", "Task 2"]
    _rows: list[TodoRow] = new(bind="_items", on_delete="handle_delete(#index)")

    def handle_delete(self, index: int) -> None:
        del self._items[index]
```

#### 3.2 Item Selection

Pass the actual item value to handler.

```python
_items: list[Product] = [...]
_cards: list[ProductCard] = new(bind="_items", clicked="on_select(#value)")

def on_select(self, product: Product) -> None:
    self.selected_product = product
```

#### 3.3 Signal with Arguments

Child widget emits signal with value, parent needs both index and signal value.

```python
_rows: list[EditRow] = new(bind="_items", value_changed="on_change(#index, #args)")

def on_change(self, index: int, new_value: str) -> None:
    self._items[index] = new_value
```

### 4. Multiple Placeholders

Show combining placeholders in one handler call.

```python
on_edit="handle_edit(#index, #value, #widget)"

def handle_edit(self, index: int, item: TodoItem, widget: TodoRow) -> None:
    # Access all context
    pass
```

### 5. Handler Formats

#### 5.1 String Handler (Default)

Default behavior passes signal's own args if any.

```python
on_click="handler"  # Signal args passed through
```

#### 5.2 Empty Parens

Explicitly pass nothing, useful when signal has args but you don't need them.

```python
on_click="handler()"  # No args
```

#### 5.3 Direct Callable

Pass lambda or function reference directly.

```python
on_click=lambda: print("clicked")
on_click=self.my_method
```

### 6. Dynamic Index Updates

Explain that `#index` reflects current position after list modifications.

```python
def handle_delete(self, index: int) -> None:
    del self._items[index]  # Other items' indices update automatically
```

### 7. Common Patterns

#### Pattern 1: Todo List with Delete

Full working example with add/delete functionality.

#### Pattern 2: Editable Items

List of items where each can be edited inline.

#### Pattern 3: Selection & Detail View

Click item to show detail panel.

### 8. Gotchas & Tips

- **Order matters**: Place placeholders in order you want args passed to handler
- **Type safety**: Handler signature must match placeholder types for proper typing
- **Signal args spreading**: `#args` spreads signal's arguments, use at end of parameter list
- **Lambda handlers**: Can't use placeholders with lambdas, lambdas receive no special context

### 9. Cross-References

Link to related features:
- [Lists & Dicts](lists-dicts.md) - How to set up list/dict bindings
- [Format Expressions](../state/format-expressions.md) - Similar placeholder syntax for text binding
- [Signals](../basics/signals.md) - Basic signal connection concepts
- [Variable[T]](../state/variables.md) - Reactive state backing repeaters

---

## Code Examples Needed

### Example 1: Complete Todo App

Full working example showing:
- List of todo items with text and done state
- Delete button per item using `#index`
- Add new item button
- Mark as done checkbox

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QLabel, QPushButton, QCheckBox, QLineEdit
from qtpie import Widget, Variable, new, widget

@dataclass
class TodoItem:
    text: str
    done: bool = False

@widget
class TodoRow(Widget):
    item: Variable[TodoItem]

    _text: QLabel = new(bind="{item.text}")
    _done: QCheckBox = new(bind="item.done")
    _delete: QPushButton = new("Delete", clicked="on_delete")

    on_delete: signal = new()  # Signal to parent

@widget
class TodoApp(Widget):
    _items: Variable[list[TodoItem]] = new([
        TodoItem("Buy milk"),
        TodoItem("Walk dog"),
    ])

    _new_text: Variable[str, QLineEdit] = new("")(placeholderText="New task...")
    _add_btn: QPushButton = new("Add", clicked="add_item")
    _rows: list[TodoRow] = new(bind="_items", on_delete="delete_item(#index)")

    def add_item(self) -> None:
        if self._new_text.value:
            self._items.append(TodoItem(self._new_text.value))
            self._new_text.value = ""

    def delete_item(self, index: int) -> None:
        del self._items[index]
```

### Example 2: Product Picker

Show selection pattern with detail view.

```python
@widget
class ProductPicker(Widget):
    _products: list[Product] = load_products()
    _selected: Variable[Product | None] = new(None)

    _cards: list[ProductCard] = new(
        bind="_products",
        clicked="on_select(#value)"
    )
    _detail: ProductDetail = new(product="_selected", visible="{_selected is not None}")

    def on_select(self, product: Product) -> None:
        self._selected.value = product
```

### Example 3: Inline Editable List

Show bidirectional binding with signal args.

```python
@widget
class EditableList(Widget):
    _items: Variable[list[str]] = new(["Alpha", "Beta", "Gamma"])
    _rows: list[EditRow] = new(
        bind="_items",
        text_changed="on_edit(#index, #args)"
    )

    def on_edit(self, index: int, new_text: str) -> None:
        self._items[index] = new_text
```

---

## Cross-References

### Links TO this page (where to mention it)

1. **docs/data/lists-dicts.md** - "See WidgetRepeater Signals for handling child widget interactions"
2. **docs/state/format-expressions.md** - "Similar placeholder syntax used in signal handlers, see WidgetRepeater Signals"
3. **docs/basics/signals.md** - Brief mention: "For list/dict repeaters, see WidgetRepeater Signals"
4. **docs/index.md** - Consider adding to examples section or key features

### Links FROM this page (references)

1. [Lists & Dicts](lists-dicts.md) - Setting up list/dict bindings
2. [Format Expressions](../state/format-expressions.md) - Similar placeholder concept for text
3. [Signals](../basics/signals.md) - Basic signal concepts
4. [Variables](../state/variables.md) - Reactive state
5. [Widget Reference](../reference/classes/widget.md) - Parent widget class
6. [new() Factory](../reference/factories/new.md) - Field declaration

---

## Visual Aids (Optional)

Consider adding diagrams:

1. **Flow diagram**: User clicks delete → Signal → Placeholder resolution → Parent handler → List update → UI sync
2. **Type flow**: Show how `#index: int`, `#value: T`, `#widget: W` flow into handler signature

---

## Testing Examples

Include pytest snippets showing how to test signal handlers:

```python
def test_delete_item_by_index(qtbot):
    widget = TodoApp()
    initial_count = len(widget._items)

    # Simulate click on second item's delete button
    widget._rows[1]._delete.click()

    assert len(widget._items) == initial_count - 1
```

---

## Notes for Documentation Author

1. **Emphasize type safety**: Show how handler signatures must match placeholder types
2. **Show progression**: Start simple (#index), build to complex (#index, #value, #args)
3. **Real-world examples**: Todo list is relatable, everyone gets it
4. **Gotchas section**: Address common mistakes (placeholder order, lambda limitations)
5. **Link liberally**: Connect to related features so users discover more
6. **Code over prose**: Show working examples, let code speak
7. **Consistency**: Use same placeholder format as format-expressions.md (they share syntax)

---

## Related Implementation Files

For documentation author reference:

- `lib/qtpie/widget_repeater.py` - Core implementation
- `tests/qtpie/test_widget_repeater_signals.md` - Test specification (SOURCE DOC)
- `tests/qtpie/test_widget_repeater.py` - Test suite with examples
- `CLAUDE.md` lines 216-247, 446-475 - Existing context snippets

---

## Completion Checklist

Before marking docs as complete:

- [ ] All code examples run without errors
- [ ] Cross-reference links work in mkdocs build
- [ ] Examples demonstrate all 4 placeholders (#index, #value, #widget, #args)
- [ ] Gotchas section covers lambda limitation
- [ ] At least 2 complete working examples (todo app + one other)
- [ ] nav updated in mkdocs.yml
- [ ] References added in lists-dicts.md and format-expressions.md
