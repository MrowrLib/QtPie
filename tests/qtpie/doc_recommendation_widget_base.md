# Documentation Proposal: WidgetBase Mixin

## Summary

`WidgetBase` is a foundational mixin that adds reactive Variable support and lifecycle hooks to any Python class, including Qt widgets. This is the core primitive that powers the declarative Widget/Window/Menu classes but can be used standalone for more granular control.

## 1. Files to Add

### `docs/advanced/widget-base.md`

New page documenting the `WidgetBase` mixin for advanced users who want:
- To add reactive Variables to existing Qt widget subclasses
- More control than the `@widget` decorator provides
- To understand how QtPie's internals work
- To extend custom Qt widgets with QtPie features

## 2. Files to Update

### `docs/start/concepts.md`
- Add brief mention of `WidgetBase` in "Under the Hood" or "Architecture" section
- Explain that `Widget`, `Window`, `Menu` all inherit from `WidgetBase`
- Position it as "you don't usually need this, but it's there if you want it"

### `docs/reference/classes/widget.md`
- Add note that `Widget` inherits from `WidgetBase`
- Link to advanced/widget-base.md for users who need more control

### `docs/basics/widgets.md`
- Brief mention that the `@widget` decorator is sugar over `WidgetBase` mixin
- Keep it simple, link to advanced docs for details

## 3. Suggested Location in Nav

Under a new "Advanced" section (after Guides, before Reference):

```yaml
nav:
  # ... existing sections ...
  - Advanced:
      - WidgetBase Mixin: advanced/widget-base.md
      - Custom Descriptors: advanced/descriptors.md  # future
      - Internals: advanced/internals.md  # future
  - Reference:
      # ... existing reference sections ...
```

Alternatively, could go under Reference > Classes as "WidgetBase (Advanced)".

## 4. Content Outline

### `docs/advanced/widget-base.md`

**Introduction**
- What WidgetBase is: foundational mixin for reactive Variables
- When to use it vs `@widget` decorator
- Prerequisites: understanding of Python mixins

**Basic Usage**
- Minimal example with custom class
- Show `Variable[T]` field declaration
- Explain `new()` factory works automatically

**The `__setup__()` Lifecycle Hook**
- Called after `__init__()` completes
- Safe to access fully-initialized objects
- Example: mixing with QWidget and calling Qt methods in setup
- When to use `__setup__()` vs `__init__()`

**With Qt Widgets**
- Example: QListView with Variables
- Example: QWidget with both Variables and instantiated child widgets
- How to mix reactive state with imperative Qt code

**Variable Field Mechanics**
- How Variables are auto-initialized
- Accessing `.value` and `.observable`
- Reactivity example (on_change subscription)

**Non-Variable Fields with `new()`**
- Using `new()` to instantiate regular classes
- Passing constructor arguments
- Example with custom non-Qt, non-Variable class

**When to Use WidgetBase**
- Extending existing Qt widget subclasses
- Incrementally adding QtPie features to legacy code
- Building custom base classes
- When you need fine-grained control

**When NOT to Use WidgetBase**
- Use `@widget` for new widgets (simpler, more features)
- Use plain Qt for one-off custom widgets
- Don't mix WidgetBase with `@widget` decorator (they overlap)

**Comparison Table**

| Feature | `@widget` Decorator | `WidgetBase` Mixin |
|---------|--------------------|--------------------|
| Variable fields | Yes | Yes |
| `__setup__()` hook | Yes | Yes |
| Automatic layouts | Yes | No |
| Signal auto-connect | Yes | No |
| Record binding | Yes | No |
| Data binding | Yes | No |
| Validation | Yes | No |
| Dirty tracking | Yes | No |
| Complexity | Low | Medium |
| Control | Medium | High |

**Architecture Notes**
- How descriptors work behind the scenes
- Where Variables are stored (`_qtpie` instance state)
- Link to source code for curious developers

**See Also**
- Link to reference/classes/widget.md
- Link to start/concepts.md
- Link to basics/widgets.md

### Minor updates to existing files

**`docs/start/concepts.md`** - Add section:
- "Under the Hood: WidgetBase"
- 2-3 sentences explaining Widget/Window/Menu inherit from WidgetBase
- "For most users, use @widget. See Advanced > WidgetBase for details."

**`docs/reference/classes/widget.md`** - Add callout:
- "Note: Widget inherits from WidgetBase. For advanced usage, see [WidgetBase Mixin](../../advanced/widget-base.md)."

**`docs/basics/widgets.md`** - Add note in introduction:
- Brief mention: "The @widget decorator builds on the WidgetBase mixin, which can also be used standalone for advanced scenarios."

## 5. Code Examples Needed

From the test summary, include:

1. **Basic `__setup__()` example**
   ```python
   class MyWidget(QWidget, WidgetBase):
       def __setup__(self) -> None:
           self.setWindowTitle("Test")
   ```

2. **Variable field example**
   ```python
   class MyWidget(QWidget, WidgetBase):
       _name: Variable[str] = new("")

   obj = MyWidget()
   obj._name.value = "hello"
   ```

3. **Reactive Variable subscription**
   ```python
   class MyWidget(QWidget, WidgetBase):
       _count: Variable[int] = new(0)

   obj = MyWidget()
   obj._count.observable.on_change(lambda v: print(f"Count: {v}"))
   obj._count.value = 1  # Prints: Count: 1
   ```

4. **Non-Variable field instantiation**
   ```python
   class Counter:
       def __init__(self, start: int = 0) -> None:
           self.value = start

   class MyWidget(QWidget, WidgetBase):
       _counter: Counter = new(start=10)
   ```

5. **Real-world Qt integration**
   ```python
   class MyWidget(QWidget, WidgetBase):
       _label: QLabel = new("Hello")
       _button: QPushButton = new("Click me")
       _clicked_count: Variable[int] = new(0)

       def __setup__(self) -> None:
           self._button.clicked.connect(self._on_click)

       def _on_click(self) -> None:
           self._clicked_count.value += 1
           self._label.setText(f"Clicks: {self._clicked_count.value}")
   ```

6. **QListView example**
   ```python
   class MyListView(QListView, WidgetBase):
       _items: Variable[list[str]] = new([])

       def __setup__(self) -> None:
           self._items.value = ["one", "two", "three"]
           # Set up model, etc.
   ```

## 6. Cross-References

**From WidgetBase docs, link to:**
- `docs/reference/classes/widget.md` - The high-level Widget class
- `docs/reference/classes/variable.md` - Variable reference
- `docs/reference/factories/new.md` - new() factory reference
- `docs/start/concepts.md` - Core concepts
- `docs/basics/widgets.md` - Standard widget usage

**From other docs, link to WidgetBase:**
- `docs/start/concepts.md` - Mention as foundation
- `docs/reference/classes/widget.md` - Link to advanced usage
- `docs/basics/widgets.md` - Brief mention for curious users
- `docs/guides/testing.md` - May be useful for testing custom widgets

## 7. Priority

**Priority: Low to Medium (Advanced Feature)**

**Rationale:**
- This is NOT a core concept users need early
- Most users will use `@widget`, not `WidgetBase` directly
- This is for advanced users who need more control or are extending existing code
- Document it, but don't promote it heavily to beginners
- Belongs in "Advanced" section, not in Getting Started flow

**Recommended Documentation Order:**
1. Document all user-facing `@widget` features first
2. Document all reactive state features (Variables, bindings, etc.)
3. Document guides (forms, windows, etc.)
4. Then document advanced topics like WidgetBase

**User Journey:**
- Beginner: Use `@widget`, never touch WidgetBase
- Intermediate: Aware WidgetBase exists, understand the architecture
- Advanced: Use WidgetBase to extend legacy Qt code or build custom abstractions

## Notes

- WidgetBase is infrastructure, not a user-facing API
- It's important to document for completeness and advanced users
- Keep it out of the main learning path
- Emphasize when to use it vs when to use `@widget`
- This is about "escape hatches" and understanding how things work under the hood
- Could be combined with other advanced/internals documentation in the future
