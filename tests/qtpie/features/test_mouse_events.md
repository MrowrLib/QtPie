# Mouse Events in QtPie

QtPie provides pseudo-signal handlers for mouse events via event filters. These allow declarative binding of mouse interactions directly in the `new()` field definition.

## Available Mouse Event Handlers

| Handler | Event Type | Callback Signature |
|---------|------------|-------------------|
| `onMouseEnter` | Mouse enters widget | `() -> None` |
| `onMouseLeave` | Mouse leaves widget | `() -> None` |
| `onMousePress` | Mouse button pressed | `(event: QMouseEvent) -> None` |
| `onMouseRelease` | Mouse button released | `(event: QMouseEvent) -> None` |
| `onMouseDoubleClick` | Double click | `(event: QMouseEvent) -> None` |
| `onMouseMove` | Mouse moves over widget | `(event: QMouseEvent) -> None` |
| `onWheel` | Mouse wheel scrolled | `(event: QWheelEvent) -> None` |

## Basic Usage - Method Name String

Connect mouse events to instance methods by passing the method name as a string:

```python
@widget
class HoverLabel(Widget):
    label: QLabel = new("Hover me", onMouseEnter="on_enter", onMouseLeave="on_leave")

    def on_enter(self) -> None:
        self.label.setStyleSheet("background: yellow")

    def on_leave(self) -> None:
        self.label.setStyleSheet("")
```

## Handlers with Event Parameter

Press, release, double-click, move, and wheel handlers receive the Qt event object:

```python
@widget
class ClickTracker(Widget):
    label: QLabel = new("Click me", onMousePress="on_press")

    def on_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            print("Left click!")
```

## Lambda Handlers

Use lambdas for inline event handling:

```python
@widget
class QuickHandler(Widget):
    label: QLabel = new("Click", onMousePress=lambda e: print(f"Pressed at {e.pos()}"))
```

## Multiple Handlers on Same Widget

All mouse event handlers can be combined on a single widget:

```python
@widget
class FullMouseTracking(Widget):
    label: QLabel = new(
        "Interactive",
        onMouseEnter="on_enter",
        onMouseLeave="on_leave",
        onMousePress="on_press",
        onMouseRelease="on_release",
    )
```

## Mouse Move Auto-Enables Tracking

When `onMouseMove` is set, mouse tracking is automatically enabled on the widget:

```python
@widget
class MouseTracker(Widget):
    # hasMouseTracking() will be True automatically
    canvas: QLabel = new("Draw here", onMouseMove="on_move")

    def on_move(self, event: QMouseEvent) -> None:
        print(f"Mouse at: {event.pos()}")
```

## Wheel Events

Handle scroll wheel input:

```python
@widget
class ZoomControl(Widget):
    view: QLabel = new("Scroll to zoom", onWheel="on_scroll")

    def on_scroll(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            print("Zoom in")
        else:
            print("Zoom out")
```

## Works with Widget and Window

Mouse event handlers work identically on both `Widget` and `Window` subclasses.
