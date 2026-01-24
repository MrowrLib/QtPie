# Focus Events in QtPie

QtPie provides `onFocus` and `onBlur` pseudo-signals for handling widget focus events. These are implemented via event filters and work on any focusable widget.

## onFocus - Handle Focus In

Connect a handler when a widget gains focus using the `onFocus` parameter in `new()`.

### Method Name Connection

```python
@widget
class MyWidget(Widget):
    line_edit: QLineEdit = new(onFocus="on_focus_in")

    def on_focus_in(self) -> None:
        print("Widget gained focus")
```

### Lambda Connection

```python
@widget
class MyWidget(Widget):
    line_edit: QLineEdit = new(onFocus=lambda: print("Focused!"))
```

## onBlur - Handle Focus Out

Connect a handler when a widget loses focus using the `onBlur` parameter.

```python
@widget
class MyWidget(Widget):
    line_edit: QLineEdit = new(onBlur="on_blur")

    def on_blur(self) -> None:
        print("Widget lost focus")
```

## Combined Focus and Blur

Both handlers can be set on the same widget.

```python
@widget
class MyWidget(Widget):
    line_edit: QLineEdit = new(onFocus="on_focus_in", onBlur="on_focus_out")

    def on_focus_in(self) -> None:
        print("Gained focus")

    def on_focus_out(self) -> None:
        print("Lost focus")
```

## Accessing Widget State in Handlers

Focus handlers have full access to `self` and can modify Variables or widgets.

```python
@widget
class MyWidget(Widget):
    _focused: Variable[bool] = new(False)
    line_edit: QLineEdit = new(onFocus="on_focus_in")

    def on_focus_in(self) -> None:
        self._focused.value = True
```

## Blur for Auto-Save Pattern

A common pattern is saving data when a field loses focus.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    line_edit: QLineEdit = new(bind="_name", onBlur="on_blur")

    def on_blur(self) -> None:
        self.save_name(self._name.value)
```

## Focus Events on Different Widget Types

Focus events work on any focusable widget, including buttons.

```python
@widget
class MyWidget(Widget):
    button: QPushButton = new("Click", onFocus="on_focus")

    def on_focus(self) -> None:
        print("Button focused")
```

## Hierarchy Resolution

Focus handler method names are resolved up the parent widget hierarchy, allowing child widgets to trigger parent methods.

```python
@widget
class Child(Widget):
    line_edit: QLineEdit = new(onFocus="on_parent_focus")

@widget
class Parent(Widget):
    child: Child = new()

    def on_parent_focus(self) -> None:
        print("Child triggered parent handler")
```

## Connecting to Parent Signals

Focus handlers can also emit parent Signals.

```python
@widget
class Child(Widget):
    line_edit: QLineEdit = new(onFocus="on_focused")

@widget
class Parent(Widget):
    on_focused = Signal()
    child: Child = new()
```

## Key Points

- `onFocus` triggers on `FocusIn` event
- `onBlur` triggers on `FocusOut` event
- Handlers are not called during widget initialization
- Method name strings are resolved up the parent hierarchy
- Works with any focusable Qt widget
