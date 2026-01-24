# Bug Reproduction Tests - QtPie Usage Patterns

This file documents patterns from `test_bug_reproductions.py`, which demonstrates how to write tests that reproduce known bugs before fixing them.

## Testing Infrastructure

QtPie provides a `QtDriver` fixture for testing widgets:

```python
from qtpie.testing import QtDriver

def test_example(self, qt: QtDriver) -> None:
    w = qt.track(MyWidget())  # Track widget for cleanup
```

## Variable with Collection Types

### Variable with Set Type

`Variable[set[T], WidgetType]` creates a reactive set bound to repeating widgets:

```python
@widget
class Test(Widget):
    _numbers: Variable[set[int], QSpinBox] = new({1, 2, 3})
    _names: Variable[set[str], QLineEdit] = new({"alice", "bob"})
```

### Variable with List Type

`Variable[list[T], WidgetType]` creates a reactive list bound to repeating widgets:

```python
@widget
class Test(Widget):
    _numbers: Variable[list[int], QSpinBox] = new([1, 2, 3])
```

## Widget Repeaters

### SetWidgetRepeater

Access the repeater from a set-bound Variable:

```python
repeater: SetWidgetRepeater[int] = w._numbers.widget
repeater.widget_count()           # Number of widgets
repeater.widget_for_item(1)       # Get widget for specific value
```

### WidgetRepeater (List)

Access the repeater from a list-bound Variable:

```python
repeater: WidgetRepeater[int] = w._numbers.widget
repeater.widget_at(1)             # Get widget at index
```

## Menu with Record Type

### Basic Menu with Record

Use `Menu[T]` with `record=` parameter for typed menu state:

```python
@dataclass
class EditState:
    can_undo: bool = False

@menu(text="&Edit", record=EditState())
class EditMenu(Menu[EditState]):
    pass
```

### Accessing Menu Record

```python
m = EditMenu()
m.record.can_undo = True  # Modify record fields
```

## Widget with Record Type

### Basic Widget with Record

Use `Widget[T]` with `record=` parameter for typed widget state:

```python
@dataclass
class Person:
    name: str = ""

@widget(record=Person())
class PersonWidget(Widget[Person]):
    _label: QLabel = new("test")
```

## Dirty Tracking

### Observable-based Dirty Tracking

Subscribe to the `is_dirty` Observable:

```python
w.is_dirty.on_change(lambda v: dirty_notifications.append(v))
w.is_dirty.get()  # Check current dirty state
```

### Lifecycle Hook for Dirty Changes

Override `on_dirty_changed` to respond to dirty state transitions:

```python
@widget(record=Person())
class PersonWidget(Widget[Person]):
    def on_dirty_changed(self, is_dirty: bool) -> None:
        dirty_states.append(is_dirty)
```

## Two-Way Binding

### Primitive Two-Way Sync

When using primitive types (int, str) with editable widgets, changes sync back:

```python
# Spinbox value change updates the underlying list
spin.setValue(99)
assert w._numbers.observable[1] == 99
```

## Testing Pattern: Bug Reproduction

The file demonstrates a pattern for bug reproduction tests:

1. **Document the bug** in class/method docstrings
2. **Create control tests** that show working behavior
3. **Create bug repro tests** that fail initially, pass after fix
4. **Use assertions** to verify expected vs actual behavior

```python
class TestSomeBug:
    """Bug: Description of the bug.

    Expected behavior: ...
    Actual behavior (BUG): ...
    """

    def test_bug_repro(self, qt: QtDriver) -> None:
        """BUG REPRO: What should happen."""
        # Test that fails with bug, passes after fix

    def test_control_case(self, qt: QtDriver) -> None:
        """CONTROL: Similar case that works (for comparison)."""
        # Test showing working behavior
```
