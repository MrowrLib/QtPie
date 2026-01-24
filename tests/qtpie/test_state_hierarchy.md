# State Hierarchy Feature Documentation

This document describes the State hierarchy feature in QtPie, which enables States to resolve Variables and Events by walking up the `state_parent` chain.

## Overview

States in QtPie can form hierarchical relationships via the `state_parent` property. Child states can access Variables and Events from ancestor states using `var()`, `event()`, and `emit_event()` methods.

## Defining States with Variables and Events

Use the `@state` decorator with `Variable` and `Event` fields:

```python
@state
class RootState(State):
    config_value: Variable[str] = new("root_config")
    on_data_changed: Event[str]
```

## Building State Hierarchies

Link states using the `state_parent` property:

```python
root = RootState()
middle = MiddleState()
leaf = LeafState()

middle.state_parent = root
leaf.state_parent = middle
```

## Resolving Variables with `var()`

The `var()` method resolves Variables by walking up the state hierarchy.

### Basic Resolution

```python
s = MyState()
result = s.var("count")  # Returns unwrapped value (e.g., 42)
```

### Resolution from Parent

```python
leaf.state_parent = root
result = leaf.var("config_value")  # Finds root's Variable
```

### Underscore Prefix Flexibility

Variables with underscore prefixes can be accessed with or without the prefix:

```python
_private_value: Variable[str] = new("secret")

s.var("_private_value")  # Works
s.var("private_value")   # Also works
```

### Type Hints for var()

Use type parameters for compile-time type checking:

```python
x: int = s.var("count", int)
z: int | str = s.var("count", int, str)
w: int | None = s.var("count", int, None)
```

## Resolving Events with `event()`

The `event()` method returns the Event object itself:

```python
evt = s.event("on_action")  # Returns Event instance
evt = leaf.event("on_root_event")  # Finds from parent
```

## Emitting Events with `emit_event()`

The `emit_event()` method finds and emits an Event in one call.

### Basic Emission

```python
s.emit_event("on_action")
```

### Emission with Arguments

```python
s.emit_event("on_data", "hello")  # Passes "hello" to handlers
```

### Emission from Child to Parent Event

```python
leaf.state_parent = root
leaf.emit_event("on_root_event")  # Fires root's event
```

## Hierarchy Shadowing

When the same name exists at multiple levels, the nearest (most local) one is used:

```python
@state
class ParentState(State):
    theme: Variable[str] = new("parent_theme")

@state
class ChildState(State):
    theme: Variable[str] = new("child_theme")

child.state_parent = parent
child.var("theme")  # Returns "child_theme"
```

## Combined Usage Pattern

Child states commonly read parent config and emit parent events:

```python
@state
class ChildFeature(State):
    def do_work(self) -> None:
        app = self.var("app_name", str)
        self.emit_event("on_action_completed", f"Work done for {app}")
```

## Key Conventions

- `var()` returns unwrapped values, not Variable objects
- `event()` returns the Event object for direct manipulation
- `emit_event()` finds and fires in one step
- Resolution walks up `state_parent` chain until found
- Nearest ancestor takes precedence (shadowing)
- Underscore prefixes are flexible - can be omitted in lookups
- AttributeError raised if name not found in hierarchy
