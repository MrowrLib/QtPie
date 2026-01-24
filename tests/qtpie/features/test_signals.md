# Signal Connections in QtPie

This document describes signal connection patterns in QtPie based on the test suite.

## Method Name Connection

The most common pattern - connect a signal to a method by name string.

```python
@widget
class MyWidget(Widget):
    button: QPushButton = new("Click", clicked="on_click")

    def on_click(self) -> None:
        print("Button clicked!")
```

The handler has full access to `self` and can modify Variables or other widgets.

## Lambda Connection

Connect signals directly to lambda functions for simple inline handlers.

```python
@widget
class MyWidget(Widget):
    button: QPushButton = new("Click", clicked=lambda: print("clicked"))
```

Lambdas can capture variables from the outer scope.

## Expression Connection

Use curly braces `{...}` for expression-based connections that can pass arguments.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Alice")

    # Literal argument
    button1: QPushButton = new("Click", clicked="{handle(42)}")

    # String argument
    button2: QPushButton = new("Click", clicked="{handle('hello')}")

    # Variable reference (current value passed)
    button3: QPushButton = new("Click", clicked="{handle(_name)}")

    # Multiple arguments
    button4: QPushButton = new("Click", clicked="{handle(1, 2)}")

    def handle(self, *args) -> None:
        print(args)
```

## Multiple Buttons

Multiple buttons can have different handlers or share the same handler.

```python
@widget
class MyWidget(Widget):
    # Different handlers
    button_a: QPushButton = new("A", clicked="on_click_a")
    button_b: QPushButton = new("B", clicked="on_click_b")

    # Same handler
    button_x: QPushButton = new("X", clicked="on_click")
    button_y: QPushButton = new("Y", clicked="on_click")
```

## Signal Hierarchy Resolution

Signal connections search up the Qt parent hierarchy. A child widget can connect to methods or signals defined on parent widgets.

```python
@widget
class Child(Widget):
    button: QPushButton = new("Click", clicked="on_parent_click")

@widget
class Parent(Widget):
    child: Child = new()

    def on_parent_click(self) -> None:
        print("Called on parent!")
```

Key behaviors:
- The closest parent's method takes precedence over further ancestors
- Works through multiple levels (grandparent, etc.)
- Can connect to parent's `Signal` objects for signal-to-signal connections

## Accessing Signals Programmatically

Use `signal()` and `emit_signal()` methods to work with parent signals by name.

```python
@widget
class Child(Widget):
    def on_click(self) -> None:
        # Get signal object from parent hierarchy
        sig = self.signal("on_action")

        # Or emit directly
        self.emit_signal("on_action")

@widget
class Parent(Widget):
    on_action = Signal()
    child: Child = new()
```

If the signal is not found in the hierarchy, `AttributeError` is raised.

## Decorator Signal Connections

Connect signals defined on the widget class via decorator kwargs.

```python
@widget(on_action="_handle_action")
class MyWidget(Widget):
    on_action = Signal()

    def _handle_action(self) -> None:
        print("Action signal emitted!")
```

Works for `@widget`, `@window`, and `@menu` decorators.

### With Signal Arguments

```python
@widget(on_data="_handle_data")
class MyWidget(Widget):
    on_data = Signal(int, str)

    def _handle_data(self, num: int, text: str) -> None:
        print(f"Received: {num}, {text}")
```

### Multiple Signal Connections

```python
@widget(on_reload="_handle_reload", on_save="_handle_save")
class MyWidget(Widget):
    on_reload = Signal()
    on_save = Signal()

    def _handle_reload(self) -> None: ...
    def _handle_save(self) -> None: ...
```

### Mixed with Widget Properties

Non-signal kwargs are treated as widget properties.

```python
@widget(on_action="_handle", windowTitle="Custom Title")
class MyWidget(Widget):
    on_action = Signal()
    def _handle(self) -> None: ...
```
