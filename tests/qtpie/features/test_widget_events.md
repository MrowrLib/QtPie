# Widget Events Feature

Widget events are pseudo-signals that trigger on widget lifecycle events. QtPie installs event filters to intercept Qt events and route them to your handlers.

## Available Event Handlers

| Handler | Event | Signature |
|---------|-------|-----------|
| `onShow` | Widget becomes visible | `() -> None` |
| `onHide` | Widget becomes hidden | `() -> None` |
| `onResize` | Widget size changes | `(event: QResizeEvent) -> None` |
| `onMove` | Widget position changes | `(event: QMoveEvent) -> None` |
| `onClose` | Widget receives close event | `(event: QCloseEvent) -> None` |

## onShow / onHide Events

Connect to show/hide lifecycle events. Handlers take no parameters.

### Method Reference

```python
label: QLabel = new("Test", onShow="on_shown", onHide="on_hidden")

def on_shown(self) -> None:
    print("Widget is now visible")

def on_hidden(self) -> None:
    print("Widget is now hidden")
```

### Lambda

```python
label: QLabel = new("Test", onShow=lambda: print("shown"))
```

## onResize Event

Triggers when widget size changes. Handler receives the `QResizeEvent`.

```python
label: QLabel = new("Test", onResize="on_resized")

def on_resized(self, event: QResizeEvent) -> None:
    width = event.size().width()
    height = event.size().height()
```

## onMove Event

Triggers when widget position changes. Handler receives the `QMoveEvent`.

```python
label: QLabel = new("Test", onMove="on_moved")

def on_moved(self, event: QMoveEvent) -> None:
    x = event.pos().x()
    y = event.pos().y()
```

## onClose Event

Triggers when widget receives a close event. Handler receives the `QCloseEvent`.

```python
label: QLabel = new("Test", onClose="on_closing")

def on_closing(self, event: QCloseEvent) -> None:
    # Optionally call event.ignore() to prevent closing
    pass
```

## Multiple Events on Same Widget

Multiple event handlers can be attached to a single widget.

```python
label: QLabel = new(
    "Test",
    onShow="on_show",
    onHide="on_hide",
    onResize="on_resize"
)
```

## Handler Patterns

**Method name (string):** Handler is resolved as `self.method_name`
```python
button: QPushButton = new("Click", onShow="handle_show")
```

**Lambda:** Inline handler, receives event parameter for resize/move/close
```python
button: QPushButton = new("Click", onResize=lambda e: print(e.size()))
```
