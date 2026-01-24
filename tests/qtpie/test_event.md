# QtPie Event System

This documents the `Event` class - a pure Python event emitter independent of Qt's signal system.

## Event Declaration

Events are typed generics. The type parameter indicates what arguments will be passed to handlers.

```python
event: Event = Event()              # No arguments
event: Event[int] = Event()         # Single argument
event: Event[str] = Event()         # Single argument
event: Event[tuple[int, str]] = Event()  # Multiple arguments
```

## Connecting Handlers

Use `.connect()` to attach handlers. Handlers can be lambdas or named functions.

```python
event.connect(lambda: calls.append(True))
event.connect(lambda x: received.append(x))
event.connect(lambda x, y: received.append((x, y)))
```

## Emitting Events

Use `.emit()` to trigger all connected handlers with the specified arguments.

```python
event.emit()                # No-arg event
event.emit(42)              # Single arg
event.emit(42, "hello")     # Multiple args (for tuple-typed events)
```

## Disconnecting Handlers

Use `.disconnect()` to remove a specific handler.

```python
def handler() -> None:
    calls.append("called")

event.connect(handler)
event.disconnect(handler)
```

## Multiple Handlers

Multiple handlers can be connected; all are called on emit.

```python
event.connect(lambda s: calls.append(f"handler1:{s}"))
event.connect(lambda s: calls.append(f"handler2:{s}"))
event.emit("hello")  # Both handlers called
```

## Helper Functions

### is_event_hint

Checks if a type hint represents an Event type (used internally for field processing).

```python
is_event_hint("Event")           # True
is_event_hint("Event[int]")      # True
is_event_hint(Event)             # True
is_event_hint(Event[int])        # True
is_event_hint("Variable[int]")   # False
```

### extract_event_args

Extracts argument types from an Event type hint (used internally).

```python
extract_event_args("Event")                    # ()
extract_event_args("Event[int]")               # (int,)
extract_event_args("Event[tuple[int, str]]")   # (int, str)
extract_event_args(Event[int])                 # (int,)
```
