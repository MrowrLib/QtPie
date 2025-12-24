# Testing

Testing QtPie widgets is easy with **qtpie.testing** - a strongly-typed wrapper around pytest-qt.

## Why qtpie.testing?

pytest-qt is great but has typing issues. Its methods use `*args, **kwargs` which breaks strict type checking. qtpie.testing wraps pytest-qt with fully-typed methods that work perfectly with pyright.

```python
# pytest-qt - no type safety
qtbot.mouseClick(button, Qt.LeftButton)  # pyright errors

# qtpie.testing - fully typed
qt.click(button)  # clean, typed, works
```

## Setup

Install qtpie with the `test` extra:

=== "uv"

    ```bash
    uv add "qtpie[test]"
    ```

=== "poetry"

    ```bash
    poetry add "qtpie[test]"
    ```

=== "pip"

    ```bash
    pip install "qtpie[test]"
    ```

Write tests using pytest. The `qt` fixture is automatically available:

```python
from qtpie.testing import QtDriver

def test_my_widget(qt: QtDriver) -> None:
    # Your test here
    pass
```

## Running Tests

Use `python -m pytest` (not just `pytest`):

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_counter.py -v

# Run specific test
python -m pytest tests/test_counter.py::test_increment -v
```

With uv:

```bash
uv run python -m pytest tests/ -v
```

## The qt Fixture

Every test gets a `qt: QtDriver` fixture automatically. No imports or configuration needed.

```python
from qtpie.testing import QtDriver
from qtpie import widget, make
from qtpy.QtWidgets import QLabel, QPushButton, QWidget

@widget
class Counter(QWidget):
    count: int = 0
    label: QLabel = make(QLabel, "Count: 0")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")

    def increment(self) -> None:
        self.count += 1
        self.label.setText(f"Count: {self.count}")

def test_counter_increments(qt: QtDriver) -> None:
    w = Counter()
    qt.track(w)  # Register for cleanup

    qt.click(w.button)

    assert w.count == 1
    assert w.label.text() == "Count: 1"
```

## Widget Cleanup: qt.track()

Always track widgets with `qt.track()` to ensure proper cleanup after tests.

```python
def test_widget_cleanup(qt: QtDriver) -> None:
    widget = MyWidget()
    qt.track(widget)  # Cleaned up automatically

    # Test your widget
    ...
```

Track multiple widgets at once:

```python
def test_multiple_widgets(qt: QtDriver) -> None:
    main = MainWindow()
    dialog = SettingsDialog()
    qt.track(main, dialog)
```

**Note:** QAction is not a QWidget, so you cannot track it. But you still need the `qt` fixture to ensure QApplication exists:

```python
def test_action(qt: QtDriver) -> None:
    _ = qt  # Ensures QApplication exists

    @action("Test")
    class TestAction(QAction):
        pass

    a = TestAction()
    # Test action without tracking
```

## Mouse Interactions

### qt.click()

Click on widgets. Defaults to left-click.

```python
def test_button_click(qt: QtDriver) -> None:
    w = MyWidget()
    qt.track(w)

    qt.click(w.button)  # Left click

    assert w.button_clicked
```

Right-click:

```python
qt.click(w.button, button=Qt.MouseButton.RightButton)
```

Ctrl+click:

```python
qt.click(w.button, modifiers=Qt.KeyboardModifier.ControlModifier)
```

### qt.double_click()

Double-click on widgets.

```python
def test_double_click(qt: QtDriver) -> None:
    w = FileList()
    qt.track(w)

    qt.double_click(w.file_item)

    assert w.file_opened
```

## Testing Signal Connections

QtPie makes signal testing easy since signals connect automatically.

```python
def test_signal_connection(qt: QtDriver) -> None:
    """Test that clicked signal connects to method."""

    @widget
    class ClickCounter(QWidget):
        button: QPushButton = make(QPushButton, "Click", clicked="on_click")
        clicks: int = 0

        def on_click(self) -> None:
            self.clicks += 1

    w = ClickCounter()
    qt.track(w)

    qt.click(w.button)
    assert w.clicks == 1

    qt.click(w.button)
    qt.click(w.button)
    assert w.clicks == 3
```

Test lambda connections:

```python
def test_lambda_signal(qt: QtDriver) -> None:
    """Test signals connected to lambdas."""
    captured = []

    @widget
    class MyWidget(QWidget):
        button: QPushButton = make(
            QPushButton,
            "Click",
            clicked=lambda: captured.append(True)
        )

    w = MyWidget()
    qt.track(w)

    qt.click(w.button)

    assert len(captured) == 1
```

## Testing Reactive State

Test that state updates trigger UI updates.

```python
def test_state_updates_label(qt: QtDriver) -> None:
    """State changes should update bound widgets."""

    @widget
    class Counter(QWidget):
        count: int = state(0)
        label: QLabel = make(QLabel, bind="count")

    w = Counter()
    qt.track(w)

    # Initial value
    assert w.label.text() == "0"

    # Update state
    w.count = 42
    assert w.label.text() == "42"
```

Test two-way binding:

```python
def test_two_way_binding(qt: QtDriver) -> None:
    """Widget changes should update state."""

    @widget
    class Editor(QWidget):
        name: str = state("")
        name_edit: QLineEdit = make(QLineEdit, bind="name")

    w = Editor()
    qt.track(w)

    # State -> Widget
    w.name = "Alice"
    assert w.name_edit.text() == "Alice"

    # Widget -> State
    w.name_edit.setText("Bob")
    assert w.name == "Bob"
```

## Testing Format Expressions

Test that format string bindings update correctly.

```python
def test_format_binding(qt: QtDriver) -> None:
    """Format expressions should update automatically."""

    @widget
    class Counter(QWidget):
        count: int = state(0)
        label: QLabel = make(QLabel, bind="Count: {count}")
        button: QPushButton = make(QPushButton, "+1", clicked="increment")

        def increment(self) -> None:
            self.count += 1

    w = Counter()
    qt.track(w)

    # Initial
    assert w.label.text() == "Count: 0"

    # Click button
    qt.click(w.button)
    assert w.label.text() == "Count: 1"
```

Test expressions with multiple variables:

```python
def test_multi_var_format(qt: QtDriver) -> None:
    """Format with multiple variables."""

    @widget
    class Calculator(QWidget):
        a: int = state(10)
        b: int = state(20)
        label: QLabel = make(QLabel, bind="{a} + {b} = {a + b}")

    w = Calculator()
    qt.track(w)

    assert w.label.text() == "10 + 20 = 30"

    w.a = 5
    assert w.label.text() == "5 + 20 = 25"
```

## Testing Model Widgets

Test Widget[T] with model/model_observable_proxy.

```python
def test_model_widget(qt: QtDriver) -> None:
    """Widget[T] should auto-bind fields."""

    @dataclass
    class Dog:
        name: str = ""
        age: int = 0

    @widget
    class DogEditor(QWidget, Widget[Dog]):
        name_edit: QLineEdit = make(QLineEdit, bind="name")
        age_spin: QSpinBox = make(QSpinBox, bind="age")

    w = DogEditor()
    qt.track(w)

    # Model -> Widget
    w.model_observable_proxy.observable(str, "name").set("Buddy")
    assert w.name_edit.text() == "Buddy"

    # Widget -> Model
    w.age_spin.setValue(3)
    assert w.model.age == 3
```

## Testing Lifecycle Hooks

Test that setup hooks are called.

```python
def test_setup_called(qt: QtDriver) -> None:
    """setup() should be called on initialization."""
    calls = []

    @widget
    class MyWidget(QWidget):
        def setup(self) -> None:
            calls.append("setup")

    w = MyWidget()
    qt.track(w)

    assert calls == ["setup"]
```

Test that setup has access to child widgets:

```python
def test_setup_access_to_children(qt: QtDriver) -> None:
    """setup() can modify child widgets."""

    @widget
    class MyWidget(QWidget):
        label: QLabel = make(QLabel, "Initial")

        def setup(self) -> None:
            self.label.setText("Modified in setup")

    w = MyWidget()
    qt.track(w)

    assert w.label.text() == "Modified in setup"
```

## Testing Layouts

Test that widgets are added to layouts correctly.

```python
def test_vertical_layout(qt: QtDriver) -> None:
    """Widgets should be added to vertical layout in order."""

    @widget
    class MyWidget(QWidget):
        first: QLabel = make(QLabel, "First")
        second: QPushButton = make(QPushButton, "Second")

    w = MyWidget()
    qt.track(w)

    layout = w.layout()
    assert layout is not None
    assert layout.count() == 2

    item0 = layout.itemAt(0)
    item1 = layout.itemAt(1)
    assert item0 is not None and item1 is not None
    assert item0.widget() is w.first
    assert item1.widget() is w.second
```

## Using assertpy

QtPie tests use assertpy for fluent assertions.

```python
from assertpy import assert_that

def test_with_assertpy(qt: QtDriver) -> None:
    """Use assertpy for readable assertions."""

    @widget
    class Counter(QWidget):
        count: int = state(0)
        label: QLabel = make(QLabel, bind="count")

    w = Counter()
    qt.track(w)

    assert_that(w.count).is_equal_to(0)
    assert_that(w.label.text()).is_equal_to("0")

    w.count = 42

    assert_that(w.count).is_equal_to(42)
    assert_that(w.label.text()).is_equal_to("42")
```

Common assertpy methods:

```python
# Equality
assert_that(value).is_equal_to(expected)
assert_that(value).is_not_equal_to(other)

# Type checks
assert_that(obj).is_instance_of(QWidget)
assert_that(obj).is_not_none()
assert_that(obj).is_none()

# Boolean
assert_that(value).is_true()
assert_that(value).is_false()

# Numbers
assert_that(count).is_greater_than(0)
assert_that(count).is_less_than(10)

# Collections
assert_that(items).is_length(3)
assert_that(items).is_empty()
assert_that(items).contains("item")

# Strings
assert_that(text).starts_with("Hello")
assert_that(text).ends_with("World")
assert_that(text).matches(r"\d+")

# Identity
assert_that(obj1).is_same_as(obj2)
```

## Test Organization

Organize tests by class:

```python
class TestWidgetDecorator:
    """Tests for @widget decorator."""

    def test_creates_widget(self, qt: QtDriver) -> None:
        @widget
        class MyWidget(QWidget):
            pass

        w = MyWidget()
        qt.track(w)

        assert_that(w).is_instance_of(QWidget)

    def test_vertical_layout_default(self, qt: QtDriver) -> None:
        @widget
        class MyWidget(QWidget):
            pass

        w = MyWidget()
        qt.track(w)

        assert_that(w.layout()).is_instance_of(QVBoxLayout)


class TestMakeFactory:
    """Tests for make() factory."""

    def test_creates_widget(self, qt: QtDriver) -> None:
        @widget
        class MyWidget(QWidget):
            label: QLabel = make(QLabel, "Hello")

        w = MyWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Hello")
```

## Full Example: Testing a Counter

```python
from assertpy import assert_that
from qtpie import widget, make, state
from qtpie.testing import QtDriver
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    inc_button: QPushButton = make(QPushButton, "+1", clicked="increment")
    dec_button: QPushButton = make(QPushButton, "-1", clicked="decrement")
    reset_button: QPushButton = make(QPushButton, "Reset", clicked="reset")

    def increment(self) -> None:
        self.count += 1

    def decrement(self) -> None:
        self.count -= 1

    def reset(self) -> None:
        self.count = 0


class TestCounter:
    """Tests for Counter widget."""

    def test_initial_state(self, qt: QtDriver) -> None:
        """Counter should start at 0."""
        w = Counter()
        qt.track(w)

        assert_that(w.count).is_equal_to(0)
        assert_that(w.label.text()).is_equal_to("Count: 0")

    def test_increment(self, qt: QtDriver) -> None:
        """Increment button should increase count."""
        w = Counter()
        qt.track(w)

        qt.click(w.inc_button)

        assert_that(w.count).is_equal_to(1)
        assert_that(w.label.text()).is_equal_to("Count: 1")

    def test_decrement(self, qt: QtDriver) -> None:
        """Decrement button should decrease count."""
        w = Counter()
        qt.track(w)

        w.count = 5
        qt.click(w.dec_button)

        assert_that(w.count).is_equal_to(4)
        assert_that(w.label.text()).is_equal_to("Count: 4")

    def test_reset(self, qt: QtDriver) -> None:
        """Reset button should set count to 0."""
        w = Counter()
        qt.track(w)

        w.count = 100
        qt.click(w.reset_button)

        assert_that(w.count).is_equal_to(0)
        assert_that(w.label.text()).is_equal_to("Count: 0")

    def test_multiple_increments(self, qt: QtDriver) -> None:
        """Multiple clicks should accumulate."""
        w = Counter()
        qt.track(w)

        qt.click(w.inc_button)
        qt.click(w.inc_button)
        qt.click(w.inc_button)

        assert_that(w.count).is_equal_to(3)
        assert_that(w.label.text()).is_equal_to("Count: 3")
```

## Best Practices

### 1. Always track widgets

```python
def test_my_widget(qt: QtDriver) -> None:
    w = MyWidget()
    qt.track(w)  # Don't forget!
```

### 2. Test one thing per test

```python
# Good - focused test
def test_increment_increases_count(qt: QtDriver) -> None:
    w = Counter()
    qt.track(w)

    qt.click(w.inc_button)

    assert w.count == 1

# Bad - testing too many things
def test_counter_everything(qt: QtDriver) -> None:
    w = Counter()
    qt.track(w)
    qt.click(w.inc_button)
    assert w.count == 1
    qt.click(w.dec_button)
    assert w.count == 0
    qt.click(w.reset_button)
    assert w.count == 0
```

### 3. Use descriptive test names

```python
# Good - describes what it tests
def test_increment_button_increases_count_by_one(qt: QtDriver) -> None:
    ...

# Bad - vague name
def test_button(qt: QtDriver) -> None:
    ...
```

### 4. Use assertpy for readability

```python
# Good - clear and readable
assert_that(w.count).is_equal_to(1)

# Works but less readable
assert w.count == 1
```

### 5. Test real user interactions

```python
# Good - simulates user action
qt.click(w.button)

# Bad - bypasses UI
w.on_click()
```

## See Also

- [Reactive State](../data/state.md) - Testing state() fields
- [Model Widgets](../data/model-widgets.md) - Testing Widget[T]
- [Signals](../basics/signals.md) - Signal connection patterns
- [Format Expressions](../data/format.md) - Testing format bindings
