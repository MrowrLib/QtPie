# State Callback Bubbling - Usage Patterns

This document describes the callback bubbling feature in QtPie's State system, where change callbacks can propagate up through parent-child hierarchies.

## Basic onChange Callback

Register a callback method on a Variable that fires when the value changes.

```python
@state
class MyState(State):
    count: Variable[int] = new(0, onChange="_on_count")

    def _on_count(self, value: int) -> None:
        print(f"Count changed to {value}")
```

## Callback Bubbling to Parent

When `onChange` references a method not found on the current State, it bubbles up to the parent State.

```python
@state
class ChildState(State):
    name: Variable[str] = new("", onChange="on_child_changed")
    # No on_child_changed here - bubbles to parent!

@state
class ParentState(State):
    children: Variable[list[Any]] = new([])

    def on_child_changed(self) -> None:
        print("Child changed!")

parent = ParentState()
child = ChildState()
parent.children.append(child)  # Establishes parent-child relationship
child.name.value = "new"       # Triggers parent.on_child_changed()
```

## Multi-Level Bubbling

Callbacks bubble through multiple ancestor levels until a handler is found.

```python
@state
class GrandparentState(State):
    children: Variable[list[Any]] = new([])

    def on_deep_change(self) -> None:
        print("Grandparent notified!")
```

Child and parent States can omit the handler - it will bubble up to grandparent.

## Event Annotation (Auto-Creation)

Annotating a field as `Event` without assignment auto-creates an Event instance.

```python
@state
class MyState(State):
    on_save: Event  # No = Event() needed - auto-created
```

## Bubbling to Parent Events

When `onChange` finds an Event on a parent, it emits that Event.

```python
@state
class ChildState(State):
    data: Variable[str] = new("", onChange="on_save")

@state
class ParentState(State):
    on_save: Event = Event()
    children: Variable[list[Any]] = new([])

parent = ParentState()
parent.on_save.connect(lambda: print("Saved!"))
child = ChildState()
parent.children.append(child)
child.data.value = "new"  # Emits parent.on_save
```

## Decorator-Based Event Wiring

The `@state` decorator can auto-wire Events to handlers.

```python
@state(on_save="_persist")
class MyState(State):
    on_save: Event  # Auto-created
    data: Variable[str] = new("")

    def _persist(self) -> None:
        print("Persisted!")
```

## Full Chain: Child Change -> Parent Event -> Handler

Combine bubbling with decorator wiring for clean event propagation.

```python
@state
class ChildState(State):
    value: Variable[int] = new(0, onChange="on_save")

@state(on_save="_persist")
class ParentState(State):
    on_save: Event
    children: Variable[list[Any]] = new([])

    def _persist(self) -> None:
        print("Save triggered by child!")
```

## List Callbacks (onInsert)

List-specific callbacks like `onInsert` also bubble to parents.

```python
@state
class ChildState(State):
    items: Variable[list[str]] = new([], onInsert="on_item_added")

@state
class ParentState(State):
    children: Variable[list[Any]] = new([])

    def on_item_added(self, item: str) -> None:
        print(f"Item added: {item}")
```

## Key Conventions

1. **Parent-child via lists**: Adding a State to a parent's `Variable[list]` establishes the hierarchy
2. **String references**: Callbacks use string names (`onChange="method_name"`)
3. **Bubbling order**: Self first, then parent, then grandparent, etc.
4. **Event annotation**: `on_something: Event` auto-creates; no `= Event()` needed
5. **Decorator wiring**: `@state(event_name="handler")` connects Event to method
