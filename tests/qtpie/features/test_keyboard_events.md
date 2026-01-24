# Keyboard Events in QtPie

QtPie provides declarative keyboard event handling via pseudo-signals on widgets. These handlers are connected through Qt's event filter mechanism.

## onKeyPress - Generic Key Press Handler

Fires when any key is pressed on the widget. Handler receives a `QKeyEvent` with full key and modifier information.

```python
line_edit: QLineEdit = new(onKeyPress="on_key")

def on_key(self, event: QKeyEvent) -> None:
    print(f"Key pressed: {event.key()}, modifiers: {event.modifiers()}")
```

Lambda syntax also supported:

```python
line_edit: QLineEdit = new(onKeyPress=lambda e: print(e.key()))
```

## onKeyRelease - Generic Key Release Handler

Fires when a key is released. Same signature as `onKeyPress`.

```python
line_edit: QLineEdit = new(onKeyRelease="on_key_up")

def on_key_up(self, event: QKeyEvent) -> None:
    print(f"Key released: {event.key()}")
```

## onEnterKey - Enter/Return Key Shortcut

Convenience handler that fires specifically for Enter key (both Return and numpad Enter). The event parameter is optional.

```python
# Without event parameter
line_edit: QLineEdit = new(onEnterKey="on_submit")

def on_submit(self) -> None:
    print("Enter pressed!")
```

```python
# With event parameter (for accessing modifiers)
line_edit: QLineEdit = new(onEnterKey="on_submit")

def on_submit(self, event: QKeyEvent) -> None:
    if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
        print("Shift+Enter!")
```

## onDeleteKey - Delete Key Shortcut

Convenience handler for the Delete key. Event parameter is optional.

```python
line_edit: QLineEdit = new(onDeleteKey="on_delete")

def on_delete(self) -> None:
    print("Delete pressed!")
```

## Combining Multiple Handlers

Multiple keyboard handlers can be set on the same widget.

```python
line_edit: QLineEdit = new(
    onKeyPress="on_key",
    onEnterKey="on_submit",
    onDeleteKey="on_remove"
)
```

Both press and release can be handled together:

```python
line_edit: QLineEdit = new(onKeyPress="on_press", onKeyRelease="on_release")
```

## Event Consumption (Stop Propagation)

Handlers can return `True` to consume the event and prevent further handling.

```python
def on_key(self, event: QKeyEvent) -> bool:
    if event.key() == Qt.Key.Key_Escape:
        return True  # Consume - event stops here
    return False  # Don't consume - continue propagation
```

When `onKeyPress` consumes an event, shortcut handlers like `onEnterKey` will not fire:

```python
line_edit: QLineEdit = new(onKeyPress="on_key", onEnterKey="on_enter")

def on_key(self, event: QKeyEvent) -> bool:
    return True  # Consumes all keys - on_enter never called

def on_enter(self) -> None:
    pass  # Never reached if on_key returns True
```

## Handler Signatures

All keyboard handlers support flexible signatures:

| Handler | Without Event | With Event | With Event + Return |
|---------|--------------|------------|---------------------|
| `onKeyPress` | N/A (requires event) | `def on_key(self, event: QKeyEvent)` | `def on_key(self, event: QKeyEvent) -> bool` |
| `onKeyRelease` | N/A (requires event) | `def on_key(self, event: QKeyEvent)` | `def on_key(self, event: QKeyEvent) -> bool` |
| `onEnterKey` | `def on_enter(self)` | `def on_enter(self, event: QKeyEvent)` | `def on_enter(self, event: QKeyEvent) -> bool` |
| `onDeleteKey` | `def on_delete(self)` | `def on_delete(self, event: QKeyEvent)` | `def on_delete(self, event: QKeyEvent) -> bool` |

Lambdas follow the same pattern:

```python
# No-arg lambda
onEnterKey=lambda: print("enter")

# Event-arg lambda
onEnterKey=lambda e: print(e.key())
```
