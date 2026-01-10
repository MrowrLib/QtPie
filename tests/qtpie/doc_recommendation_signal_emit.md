# Documentation Proposal: Signal-to-Signal Connections

## Priority
**HIGH** - This is a unique feature that differentiates QtPie from plain Qt and enables powerful component composition patterns.

## Files to Add/Update

### New File: `docs/basics/signal-forwarding.md`
Main documentation page for signal-to-signal connections and forwarding.

### Update: `docs/basics/signals.md`
Add a brief mention of signal forwarding with link to the dedicated page.

### Update: `docs/index.md`
Add signal forwarding to the feature highlights section (brief mention).

### Update: `docs/why-qtpie.md`
The comparison table already mentions "Signal forwarding | Manual wiring | `clicked="my_signal"`" - this is good, but could expand slightly with an example.

## Suggested Nav Location

In `mkdocs.yml`, add after `basics/signals.md`:

```yaml
nav:
  - Basics:
      - Widgets: basics/widgets.md
      - Layouts: basics/layouts.md
      - Signals: basics/signals.md
      - Signal Forwarding: basics/signal-forwarding.md  # NEW
      - Styling: basics/styling.md
```

**Rationale:** Signal forwarding is a natural extension of basic signal handling, so it belongs right after the Signals page in the Basics section.

## Content Outline: `docs/basics/signal-forwarding.md`

### 1. Introduction (What & Why)
- What: Connect widget signals directly to custom Signal attributes
- Why: Enables component communication without manual wiring
- Comparison: Traditional Qt approach vs QtPie

### 2. Basic Signal Forwarding
- Syntax: `clicked="my_signal"`
- Declaration: `my_signal = Signal()`
- Complete minimal example

### 3. Argument Forwarding
- Arguments automatically pass through
- Example with `QSlider.valueChanged(int)` → `Signal(int)`
- Type safety note

### 4. Argument Count Mismatch
- Target signals with fewer args ignore extras
- Example: `QPushButton.clicked(bool)` → `Signal()` (no args)
- When this is useful

### 5. Parent-Child Communication
- Child signal → parent method
- Example: `Counter` with `increment_requested` signal
- How to wire: `counter: Counter = new(increment_requested="_on_increment")`

### 6. Signal Chaining
- Child signal → parent signal → grandparent
- Multi-level component hierarchy
- Event bubbling pattern
- Complete example with 3 levels

### 7. Comparison with Traditional Qt
- Before/after code comparison
- Show manual `connect()` calls vs declarative approach
- Highlight reduced boilerplate

### 8. Common Patterns
- Event bubbling up component tree
- Signal aggregation (multiple children → one parent signal)
- Custom events for component APIs

### 9. Combining with Methods
- Can use both: `clicked="_on_click"` (method) and `clicked="my_signal"` (signal)
- Wait, can you? Clarify if this is supported or exclusive

### 10. Best Practices
- When to use signal forwarding vs methods
- Naming conventions for custom signals
- Type annotations for Signal parameters

## Code Examples Needed

### Example 1: Basic Forwarding
```python
@widget
class SimpleForward(Widget):
    action_triggered = Signal()
    _button: QPushButton = new("Click", clicked="action_triggered")

w = SimpleForward()
w.action_triggered.connect(lambda: print("Forwarded!"))
w._button.click()
```

### Example 2: With Arguments
```python
@widget
class ValueForward(Widget):
    value_changed = Signal(int)
    _slider: QSlider = new(valueChanged="value_changed")

w = ValueForward()
w.value_changed.connect(lambda v: print(f"Value: {v}"))
w._slider.setValue(42)
```

### Example 3: Argument Mismatch
```python
@widget
class IgnoreArgs(Widget):
    # QPushButton.clicked emits bool, but we don't care
    simple_clicked = Signal()
    _button: QPushButton = new("Click", clicked="simple_clicked")
```

### Example 4: Parent-Child Method
```python
@widget
class Counter(Widget):
    increment_requested = Signal()
    _button: QPushButton = new("+", clicked="increment_requested")

@widget
class App(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    counter: Counter = new(increment_requested="_on_increment")

    def _on_increment(self) -> None:
        self._count += 1
```

### Example 5: Signal Chaining
```python
@widget
class Button(Widget):
    pressed = Signal()
    _btn: QPushButton = new("Click", clicked="pressed")

@widget
class Panel(Widget):
    panel_action = Signal()
    button: Button = new(pressed="panel_action")

@widget
class App(Widget):
    app_action = Signal()
    panel: Panel = new(panel_action="app_action")

app = App()
app.app_action.connect(lambda: print("Bubbled to app!"))
app.panel.button._btn.click()  # Flows up the chain
```

### Example 6: Before/After Comparison
```python
# Traditional Qt - Manual wiring
class Counter(QWidget):
    increment_requested = Signal()

    def __init__(self):
        super().__init__()
        self.button = QPushButton("+")
        self.button.clicked.connect(self._forward_signal)

    def _forward_signal(self, checked: bool) -> None:
        self.increment_requested.emit()

# QtPie - Declarative
@widget
class Counter(Widget):
    increment_requested = Signal()
    _button: QPushButton = new("+", clicked="increment_requested")
```

## Cross-References

### Links to Include in Signal Forwarding Page
- [Basic Signals](signals.md) - For signal connection fundamentals
- [Widgets](widgets.md) - For component composition basics
- [Variables](../state/variables.md) - Alternative state management approach
- [Widget Reference](../reference/classes/widget.md) - Full Widget API

### Links to Add to Other Pages

**In `docs/basics/signals.md`:**
Add section at the end:
> For advanced signal patterns including signal-to-signal forwarding and component communication, see [Signal Forwarding](signal-forwarding.md).

**In `docs/start/concepts.md`** (if it exists):
Mention signal forwarding as a key concept for component communication.

**In `docs/reference/factories/new.md`:**
Add signal forwarding to the signal connection examples.

## Additional Notes

### Terminology
- Use "signal forwarding" consistently throughout
- Avoid "signal emission" or "signal relay" to keep terminology simple
- "Parent-child communication" for the pattern of passing signals up

### Diagrams
Consider adding simple ASCII/text diagrams showing signal flow:
```
Button clicked → my_signal → parent handler
Widget Signal → Parent Signal → Grandparent Signal
```

### Common Gotchas Section
- Must use Signal attribute name as string: `clicked="my_signal"` not `clicked=my_signal`
- Signal must be declared at class level (not in `__init__` or `__setup__`)
- Can't forward to methods and signals simultaneously from same signal

### Testing Note
Mention that signal forwarding can be tested by connecting to test handlers and triggering source signals.

## Relationship to Other Features

This feature pairs well with:
- **Widget composition** - Child components expose signals for parent to consume
- **Variable bindings** - Alternative to signals for state changes
- **Event handlers** - Can combine method handlers with signal forwarding

Signal forwarding enables the "events up, data down" pattern common in React/Vue.
