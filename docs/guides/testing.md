# Testing QtPie Applications

QtPie provides `qtpie.testing`, a strongly-typed testing library built on top of pytest-qt. It offers a cleaner, fully-typed API through the `QtDriver` class and the `qt` fixture.

## Quick Start

Install the testing dependencies:

```bash
pip install qtpie[test]
```

Write tests using the `qt` fixture:

```python
from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QPushButton

from qtpie import Widget, new, widget
from qtpie.testing import QtDriver


@widget
class Counter(Widget):
    _count_label: QLabel = new("Count: 0")
    _increment_btn: QPushButton = new("Increment", clicked="on_increment")

    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    def on_increment(self) -> None:
        self.count += 1
        self._count_label.setText(f"Count: {self.count}")


def test_counter_increments(qt: QtDriver) -> None:
    """Test that clicking the button increments the counter."""
    widget = qt.track(Counter())

    assert_that(widget.count).is_equal_to(0)
    assert_that(widget._count_label.text()).is_equal_to("Count: 0")

    qt.click(widget._increment_btn)

    assert_that(widget.count).is_equal_to(1)
    assert_that(widget._count_label.text()).is_equal_to("Count: 1")
```

## The `qt` Fixture

The `qt` fixture is the main entry point for QtPie testing. It provides a `QtDriver` instance for each test.

```python
def test_my_widget(qt: QtDriver) -> None:
    # qt is automatically provided by pytest
    widget = qt.track(MyWidget())
    # ... test your widget
```

### Automatic Setup

QtPie automatically configures pytest-qt to use the QtPie `App` class. You don't need to configure anything - just install the dependencies and start testing.

The `qt` fixture is registered as a pytest plugin in `qtpie.testing.plugin` and is available in all tests without any imports or configuration.

## QtDriver API

The `QtDriver` class wraps pytest-qt's `QtBot` with a strongly-typed, modern API.

### track()

Track a widget for automatic cleanup after the test. This ensures widgets are properly destroyed and prevents memory leaks.

```python
def test_widget_creation(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())
    # Widget will be automatically cleaned up after the test
```

The `track()` method returns the widget for convenience, allowing chaining:

```python
def test_with_chaining(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())
    assert_that(widget).is_not_none()
```

**Type Safety:** `track()` uses generics to preserve the widget's type:

```python
def test_typed_tracking(qt: QtDriver) -> None:
    widget = qt.track(Counter())  # Type: Counter, not QWidget
    widget.count = 10  # IDE autocomplete works perfectly
```

### click()

Simulate a mouse click on a widget.

```python
def test_button_click(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())
    qt.click(widget.button)
    # Button's clicked signal is emitted
```

**Parameters:**

- `widget: QWidget` - The widget to click
- `button: Qt.MouseButton` - Mouse button to use (default: `Qt.MouseButton.LeftButton`)
- `modifiers: Qt.KeyboardModifier` - Keyboard modifiers held during click (default: `Qt.KeyboardModifier.NoModifier`)

**Examples:**

```python
# Left click (default)
qt.click(widget.button)

# Right click
from qtpy.QtCore import Qt
qt.click(widget.button, button=Qt.MouseButton.RightButton)

# Click with modifier keys
qt.click(
    widget.button,
    modifiers=Qt.KeyboardModifier.ControlModifier
)

# Multiple modifiers
qt.click(
    widget.button,
    modifiers=Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
)
```

### double_click()

Simulate a double-click on a widget.

```python
def test_double_click(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())
    qt.double_click(widget.label)
    # Label's double-click handler is called
```

**Parameters:**

- `widget: QWidget` - The widget to double-click
- `button: Qt.MouseButton` - Mouse button to use (default: `Qt.MouseButton.LeftButton`)
- `modifiers: Qt.KeyboardModifier` - Keyboard modifiers held during click (default: `Qt.KeyboardModifier.NoModifier`)

**Example:**

```python
from qtpy.QtCore import Qt

def test_double_click_with_modifiers(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())
    qt.double_click(
        widget.item,
        button=Qt.MouseButton.LeftButton,
        modifiers=Qt.KeyboardModifier.ControlModifier
    )
```

## Testing QtPie Widgets

### Testing Reactive State (Variable)

Test that Variable changes trigger UI updates:

```python
from qtpie import Variable, Widget, new, widget
from qtpy.QtWidgets import QLabel


@widget
class NameDisplay(Widget):
    _name: Variable[str] = new("Alice")
    _label: QLabel = new(bind="Hello, {_name}!")


def test_variable_updates_label(qt: QtDriver) -> None:
    widget = qt.track(NameDisplay())

    assert_that(widget._label.text()).is_equal_to("Hello, Alice!")

    widget._name.value = "Bob"

    assert_that(widget._label.text()).is_equal_to("Hello, Bob!")
```

### Testing Signal Connections

Test that signal connections work as expected:

```python
@widget
class ButtonWidget(Widget):
    _button: QPushButton = new("Save", clicked="on_save")

    def __init__(self) -> None:
        super().__init__()
        self.save_called = False

    def on_save(self) -> None:
        self.save_called = True


def test_signal_connection(qt: QtDriver) -> None:
    widget = qt.track(ButtonWidget())

    assert_that(widget.save_called).is_false()

    qt.click(widget._button)

    assert_that(widget.save_called).is_true()
```

### Testing Bindings

Test format string bindings:

```python
@widget
class Calculator(Widget):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _result: QLabel = new(bind="Sum: {_x + _y}")


def test_binding_expression(qt: QtDriver) -> None:
    widget = qt.track(Calculator())

    assert_that(widget._result.text()).is_equal_to("Sum: 30")

    widget._x.value = 50

    assert_that(widget._result.text()).is_equal_to("Sum: 70")
```

### Testing Record Types (Widget[T])

Test widgets with record types:

```python
from dataclasses import dataclass


@dataclass
class Person:
    name: str = ""
    age: int = 0


@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QLineEdit = new()


def test_record_binding(qt: QtDriver) -> None:
    widget = qt.track(PersonEditor())

    # Initial values from record
    assert_that(widget.name.text()).is_equal_to("Alice")
    assert_that(widget.age.text()).is_equal_to("30")

    # Changing record updates widgets
    widget.record.name = "Bob"
    assert_that(widget.name.text()).is_equal_to("Bob")

    # Changing widget updates record
    widget.name.setText("Charlie")
    assert_that(widget.record.name).is_equal_to("Charlie")
```

### Testing Validation

Test widget validation:

```python
@widget
class ValidatedForm(Widget):
    _email: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator(
            "_email",
            "required",
            lambda v: None if v else "Email required"
        )
        self.add_validator(
            "_email",
            "format",
            lambda v: None if "@" in v else "Invalid email"
        )


def test_validation(qt: QtDriver) -> None:
    widget = qt.track(ValidatedForm())

    # Empty email - invalid
    assert_that(widget.is_valid).is_false()
    assert_that(widget.validation_error_messages).contains("Email required")

    # Invalid format
    widget._email.value = "notanemail"
    assert_that(widget.is_valid).is_false()
    assert_that(widget.validation_error_messages).contains("Invalid email")

    # Valid email
    widget._email.value = "test@example.com"
    assert_that(widget.is_valid).is_true()
    assert_that(widget.validation_error_messages).is_empty()
```

### Testing Dirty Tracking

Test that dirty tracking works correctly:

```python
@widget
class DirtyForm(Widget):
    _name: Variable[str] = new("Original")
    _age: Variable[int] = new(25)


def test_dirty_tracking(qt: QtDriver) -> None:
    widget = qt.track(DirtyForm())

    # Initially clean
    assert_that(widget.view_model.is_dirty).is_false()

    # Change triggers dirty
    widget._name.value = "Modified"
    assert_that(widget.view_model.is_dirty).is_true()
    assert_that(widget.view_model.dirty_fields).contains("_name")

    # Reset to clean
    widget.view_model.reset_dirty()
    assert_that(widget.view_model.is_dirty).is_false()
```

## Testing Raw Qt Widgets

QtDriver works with any QWidget, not just QtPie widgets:

```python
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class RawQtWidget(QWidget):
    """Plain Qt widget with no QtPie."""

    def __init__(self) -> None:
        super().__init__()
        self.click_count = 0

        layout = QVBoxLayout(self)

        self.label = QLabel("Count: 0")
        layout.addWidget(self.label)

        self.button = QPushButton("Click me")
        self.button.clicked.connect(self._on_click)
        layout.addWidget(self.button)

    def _on_click(self) -> None:
        self.click_count += 1
        self.label.setText(f"Count: {self.click_count}")


def test_raw_qt_widget(qt: QtDriver) -> None:
    """QtDriver works with any QWidget."""
    widget = qt.track(RawQtWidget())

    assert_that(widget.label.text()).is_equal_to("Count: 0")

    qt.click(widget.button)

    assert_that(widget.click_count).is_equal_to(1)
    assert_that(widget.label.text()).is_equal_to("Count: 1")
```

## Testing Windows

Test `Window` widgets the same way as regular widgets:

```python
from qtpie import Window, window


@window(title="My App")
class MainWindow(Window):
    content: QLabel = new("Content")


def test_window(qt: QtDriver) -> None:
    window = qt.track(MainWindow())

    assert_that(window.windowTitle()).is_equal_to("My App")
    assert_that(window.content.text()).is_equal_to("Content")
```

## Testing Menus

Test menu actions and signals:

```python
from qtpy.QtWidgets import QMenu
from qtpy.QtGui import QAction
from qtpie import menu, new


@menu("&File")
class FileMenu(QMenu):
    action_save: QAction = new("&Save", triggered="on_save")

    def __init__(self) -> None:
        super().__init__()
        self.save_called = False

    def on_save(self) -> None:
        self.save_called = True


def test_menu_action(qt: QtDriver) -> None:
    menu = qt.track(FileMenu())

    assert_that(menu.save_called).is_false()

    menu.action_save.trigger()

    assert_that(menu.save_called).is_true()
```

## Best Practices

### Always Track Widgets

Always use `qt.track()` for widgets created in tests. This ensures proper cleanup:

```python
# GOOD
def test_good(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())
    # Widget cleaned up automatically


# BAD - may leak memory
def test_bad(qt: QtDriver) -> None:
    widget = MyWidget()
    # Widget not cleaned up!
```

### Test One Thing at a Time

Keep tests focused on a single behavior:

```python
# GOOD - focused tests
def test_button_click_increments_counter(qt: QtDriver) -> None:
    widget = qt.track(Counter())
    qt.click(widget.increment_btn)
    assert_that(widget.count).is_equal_to(1)


def test_reset_button_clears_counter(qt: QtDriver) -> None:
    widget = qt.track(Counter())
    widget.count = 5
    qt.click(widget.reset_btn)
    assert_that(widget.count).is_equal_to(0)


# BAD - testing too much
def test_everything(qt: QtDriver) -> None:
    widget = qt.track(Counter())
    qt.click(widget.increment_btn)
    assert_that(widget.count).is_equal_to(1)
    qt.click(widget.reset_btn)
    assert_that(widget.count).is_equal_to(0)
    qt.click(widget.decrement_btn)
    assert_that(widget.count).is_equal_to(-1)
```

### Use Descriptive Test Names

Name tests after the behavior they verify:

```python
# GOOD
def test_save_button_is_disabled_when_form_is_invalid(qt: QtDriver) -> None:
    ...

def test_validation_error_message_appears_for_empty_email(qt: QtDriver) -> None:
    ...


# BAD
def test_button(qt: QtDriver) -> None:
    ...

def test_validation(qt: QtDriver) -> None:
    ...
```

### Test Behavior, Not Implementation

Focus on observable behavior rather than internal state:

```python
# GOOD - testing user-visible behavior
def test_clicking_increment_updates_label(qt: QtDriver) -> None:
    widget = qt.track(Counter())
    qt.click(widget.increment_btn)
    assert_that(widget.label.text()).is_equal_to("Count: 1")


# BAD - testing internal implementation details
def test_increment_calls_update_label_method(qt: QtDriver) -> None:
    widget = qt.track(Counter())
    widget.update_label = Mock()
    qt.click(widget.increment_btn)
    widget.update_label.assert_called_once()
```

## Common Patterns

### Testing Multiple Clicks

```python
def test_multiple_clicks(qt: QtDriver) -> None:
    widget = qt.track(Counter())

    for i in range(1, 4):
        qt.click(widget.increment_btn)
        assert_that(widget.count).is_equal_to(i)
```

### Testing Initial State

```python
def test_initial_state(qt: QtDriver) -> None:
    widget = qt.track(LoginForm())

    assert_that(widget.username.text()).is_empty()
    assert_that(widget.password.text()).is_empty()
    assert_that(widget.login_btn.isEnabled()).is_false()
```

### Testing Reactive Updates

```python
def test_reactive_updates(qt: QtDriver) -> None:
    widget = qt.track(SearchWidget())

    # Set search term
    widget._query.value = "test"

    # Verify UI updated
    assert_that(widget.search_input.text()).is_equal_to("test")
    assert_that(widget.results_label.text()).contains("test")
```

## Troubleshooting

### Widget Not Updating

If widgets don't update after changing values, ensure you're modifying the Variable, not the widget directly:

```python
# WRONG - bypasses reactivity
widget.label.setText("New text")

# CORRECT - triggers reactive updates
widget._text.value = "New text"
```

### Clicks Not Working

Ensure the widget is visible and enabled:

```python
def test_click_on_disabled_widget(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())

    # Make sure widget is enabled
    assert_that(widget.button.isEnabled()).is_true()

    qt.click(widget.button)
```

### Memory Leaks in Tests

Always use `qt.track()`. If you see warnings about widgets not being cleaned up, make sure every widget is tracked:

```python
# WRONG
def test_without_tracking(qt: QtDriver) -> None:
    widget = MyWidget()  # Not tracked - may leak!


# CORRECT
def test_with_tracking(qt: QtDriver) -> None:
    widget = qt.track(MyWidget())  # Cleaned up automatically
```

## Summary

- Use the `qt` fixture for all QtPie tests
- Always `track()` widgets for automatic cleanup
- Use `click()` and `double_click()` for user interactions
- Test behavior, not implementation
- Keep tests focused and descriptive
- QtDriver works with any QWidget, not just QtPie widgets
