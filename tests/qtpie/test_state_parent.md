# State Parent Hierarchy - Usage Patterns

This document covers the `state_parent` feature in QtPie, which enables hierarchical relationships between State objects.

## State Definition with @state Decorator

States are defined using the `@state` decorator on classes extending `State`. Variables are declared using the `new()` factory.

```python
from qtpie import State, Variable, new, state

@state
class MyState(State):
    count: Variable[int] = new(0)
```

## Manual Parent Assignment

State objects have a `state_parent` property that can be set manually to establish parent-child relationships.

```python
parent = ParentState()
child = ChildState()

child.state_parent = parent  # Establish relationship
child.state_parent = None    # Clear relationship
```

## Parent Chain Traversal

States can form multi-level hierarchies. Access ancestors by chaining `.state_parent` calls.

```python
parent.state_parent = grandparent
child.state_parent = parent

# Traverse up the chain
child.state_parent              # -> parent
child.state_parent.state_parent # -> grandparent
```

## Auto-Parenting with Variable[list[State]]

When a `Variable` holds a list of State objects, appending or inserting automatically sets the `state_parent`.

```python
@state
class ParentState(State):
    children: Variable[list[ChildState]] = new([])

parent = ParentState()
child = ChildState()

parent.children.append(child)  # child.state_parent is now parent
```

## List Operations That Auto-Parent

Both `append()` and `insert()` trigger auto-parenting.

```python
parent.children.append(child1)     # Auto-parents child1
parent.children.insert(0, child2)  # Auto-parents child2
```

## Non-State Items Unaffected

Auto-parenting only applies to State subclasses. Primitive types in lists work normally without any parenting logic.

```python
@state
class ParentState(State):
    items: Variable[list[str]] = new([])

parent.items.append("hello")  # Just adds string, no parenting
```
