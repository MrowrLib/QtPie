# Signal Connections

QtPie provides declarative signal connection for Qt signals, allowing you to wire up event handlers directly in your widget definition without manual `connect()` calls.

## Basic Signal Connection

### Method Name String

Connect a signal to a widget method by passing the method name as a string:

```python
from PySide6.QtWidgets import QPushButton
from qtpie import Widget, new, widget

@widget
class MyWidget(Widget):
    _save_btn: QPushButton = new("Save", clicked="on_save")

    def on_save(self) -> None:
        print("Saved!")
```

When the button is clicked, QtPie automatically calls `self.on_save()`.

**Important:** If the method name doesn't exist, QtPie raises an `AttributeError` at instantiation time:

```python
@widget
class BrokenWidget(Widget):
    # This will raise AttributeError: nonexistent_method not found
    _btn: QPushButton = new("Click", clicked="nonexistent_method")
```

### Lambda Functions

Connect a signal to an inline lambda or function:

```python
@widget
class MyWidget(Widget):
    _cancel_btn: QPushButton = new("Cancel", clicked=lambda: print("Cancelled"))
```

You can also reference external functions:

```python
def on_click() -> None:
    print("Button clicked")

@widget
class MyWidget(Widget):
    _btn: QPushButton = new("Click", clicked=on_click)
```

## Multiple Signals

Connect multiple signals on the same widget by passing additional signal parameters:

```python
from PySide6.QtWidgets import QPushButton
from qtpie import Widget, new, widget

@widget
class MultiSignalWidget(Widget):
    _btn: QPushButton = new(
        "Click",
        pressed=lambda: print("Pressed"),
        released=lambda: print("Released"),
        clicked="on_clicked"
    )

    def on_clicked(self) -> None:
        print("Clicked")
```

Each signal parameter must match a Qt signal name (e.g., `clicked`, `pressed`, `released`, `toggled`, `textChanged`).

## Common Signal Patterns

### QPushButton Signals

```python
from PySide6.QtWidgets import QPushButton
from qtpie import Widget, new, widget

@widget
class ButtonSignals(Widget):
    _btn: QPushButton = new(
        "Action",
        clicked="on_clicked",      # Most common
        pressed="on_pressed",       # When mouse button goes down
        released="on_released",     # When mouse button comes up
        toggled="on_toggled"        # For checkable buttons
    )

    def on_clicked(self) -> None:
        print("Clicked")

    def on_pressed(self) -> None:
        print("Pressed")

    def on_released(self) -> None:
        print("Released")

    def on_toggled(self, checked: bool) -> None:
        print(f"Toggled: {checked}")
```

### QLineEdit Signals

```python
from PySide6.QtWidgets import QLineEdit
from qtpie import Widget, new, widget

@widget
class LineEditSignals(Widget):
    _input: QLineEdit = new(
        textChanged="on_text_changed",
        returnPressed="on_return_pressed",
        editingFinished="on_editing_finished"
    )

    def on_text_changed(self, text: str) -> None:
        print(f"Text: {text}")

    def on_return_pressed(self) -> None:
        print("Return key pressed")

    def on_editing_finished(self) -> None:
        print("Editing finished")
```

### QAction Signals

```python
from PySide6.QtGui import QAction
from qtpie import Widget, new, widget

@widget
class ActionSignals(Widget):
    _action: QAction = new("Open File", triggered="on_triggered")

    def on_triggered(self) -> None:
        print("Action triggered")
```

## Signal Connection with Variable[T, W]

When using `Variable[T, W]`, pass signal connections in the second call (the widget configuration):

```python
from PySide6.QtWidgets import QLineEdit
from qtpie import Variable, Widget, new, widget

@widget
class VariableSignals(Widget):
    _name: Variable[str, QLineEdit] = new("")(
        textChanged="on_name_changed",
        returnPressed="on_submit"
    )

    def on_name_changed(self, text: str) -> None:
        print(f"Name changed to: {text}")

    def on_submit(self) -> None:
        print(f"Submitted: {self._name.value}")
```

## How It Works

QtPie processes signal parameters during widget initialization:

1. For each `signal_name=handler` pair in `new()`
2. QtPie looks for `widget.signal_name` (e.g., `button.clicked`)
3. If the handler is a string, QtPie looks up `self.handler_name`
4. If the handler is callable (lambda/function), QtPie uses it directly
5. QtPie calls `signal.connect(handler)`

This happens automatically during `__init__`, so signals are connected before `__setup__()` runs.

## Best Practices

### Use Method Names for Complex Logic

For anything beyond a single line, use a method:

```python
@widget
class GoodExample(Widget):
    _btn: QPushButton = new("Process", clicked="on_process")

    def on_process(self) -> None:
        # Multiple steps, error handling, etc.
        self.validate_data()
        self.save_to_database()
        self.show_success_message()
```

### Use Lambdas for Simple Actions

For trivial one-liners, lambdas are fine:

```python
@widget
class SimpleActions(Widget):
    _close_btn: QPushButton = new("Close", clicked=lambda: self.close())
    _toggle_btn: QPushButton = new("Toggle", clicked=lambda: self.toggle_view())
```

### Naming Conventions

Method names typically start with `on_`:

```python
@widget
class ConventionalNaming(Widget):
    _save_btn: QPushButton = new("Save", clicked="on_save")
    _cancel_btn: QPushButton = new("Cancel", clicked="on_cancel")
    _input: QLineEdit = new(textChanged="on_text_changed")
```

### Don't Mix Declarative and Imperative

Avoid manually calling `.connect()` when using QtPie's declarative approach:

```python
# BAD - mixing styles
@widget
class MixedStyles(Widget):
    _btn: QPushButton = new("Click", clicked="on_click")

    def __setup__(self) -> None:
        self._btn.clicked.connect(self.on_other_thing)  # Don't do this
```

Instead, use multiple signals or call both methods from one handler:

```python
# GOOD - consistent declarative style
@widget
class ConsistentStyle(Widget):
    _btn: QPushButton = new("Click", clicked="on_click")

    def on_click(self) -> None:
        self.do_thing_one()
        self.do_thing_two()
```

## Gotchas

### Signal Names Must Match Qt Signal Names

QtPie doesn't validate signal names at class definition time. Typos will raise `AttributeError` at runtime:

```python
@widget
class TypoExample(Widget):
    # AttributeError: 'QPushButton' object has no attribute 'cliked'
    _btn: QPushButton = new("Click", cliked="on_click")  # Typo: cliked
```

### Signal Handler Signatures Must Match

Qt requires signal handlers to accept the correct parameters:

```python
@widget
class SignatureExample(Widget):
    _input: QLineEdit = new(textChanged="on_text_changed")

    # CORRECT - accepts str parameter
    def on_text_changed(self, text: str) -> None:
        print(text)

    # WRONG - missing parameter (will raise TypeError at runtime)
    # def on_text_changed(self) -> None:
    #     print("changed")
```

### Can't Connect to Properties

Signal parameters only work with actual Qt signals, not properties or custom attributes:

```python
@widget
class PropertyExample(Widget):
    # This doesn't work - 'text' is a property, not a signal
    # _label: QLabel = new("Hello", text="on_change")  # Won't connect

    # Use the actual signal instead:
    _input: QLineEdit = new(textChanged="on_change")
```
