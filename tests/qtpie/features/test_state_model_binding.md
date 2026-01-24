# State Model Binding - QtPie Feature Documentation

This document describes how to bind Qt model views (QListView, QTreeView, QTableView) to State objects with reactive Variable fields.

## Overview

State objects use `Variable[T]` fields instead of plain Python values. When binding these to Qt views, QtPie automatically unwraps Variable values for display and maintains reactivity.

---

## Defining State Classes

Use the `@state` decorator with `State` base class. Fields are declared as `Variable[T]` with `new()` defaults.

```python
@state
class StateDog(State):
    name: Variable[str] = new("")
    age: Variable[int] = new(0)
```

### Tree Nodes with Children

For hierarchical data, use a list Variable for children:

```python
@state
class StateTreeNode(State):
    name: Variable[str] = new("")
    items: Variable[list[Any]] = new([])  # Use Any for recursive types
```

### State with Events (Non-Data Fields)

Event fields are automatically excluded from table columns:

```python
@state
class StateItemWithEvent(State):
    name: Variable[str] = new("")
    count: Variable[int] = new(0)
    on_change: Event  # NOT included in table columns
```

---

## QListView Binding

Bind a list of State objects to QListView using `bind=` and `format=`.

### Basic List Display

```python
_dogs: Variable[list[StateDog]] = new([])
_list: QListView = new(bind="_dogs", format="{name} ({age})")
```

### Populating State Objects

Create instances and set Variable fields directly:

```python
dog = StateDog()
dog.name = "Fido"
dog.age = 3
self._dogs.append(dog)
```

### Reactive Updates

List modifications automatically update the view:

```python
instance._dogs.append(new_dog)  # Adds row
del instance._dogs[1]           # Removes row
instance._dogs.clear()          # Clears all
```

---

## QTreeView Binding

Use `children=` to specify the field containing child nodes.

### Tree with Children

```python
_nodes: Variable[list[StateTreeNode]] = new([])
_tree: QTreeView = new(bind="_nodes", children="items", format="{name}")
```

### Building Hierarchical Data

```python
child = StateTreeNode()
child.name = "Child"

root = StateTreeNode()
root.name = "Root"
root.items.append(child)  # Add to Variable[list]

self._nodes.append(root)
```

### Dynamic Child Updates

Appending children updates the tree model:

```python
instance._nodes[0].items.append(new_child)  # Adds child node
```

---

## QTableView Binding

QTableView auto-detects columns from State Variable fields.

### Basic Table

```python
_dogs: Variable[list[StateDog]] = new([])
_table: QTableView = new(bind="_dogs")
```

### Column Auto-Detection Rules

- `Variable[T]` fields become columns
- `Event` fields are excluded
- `state_parent` is excluded

---

## Checkable Items

Enable checkboxes with `checkable=` pointing to a boolean Variable field.

```python
@state
class StateTask(State):
    title: Variable[str] = new("")
    done: Variable[bool] = new(False)

_tasks: Variable[list[StateTask]] = new([])
_list: QListView = new(bind="_tasks", checkable="done")
```

---

## Selection Binding

### Bind Selected Item

```python
_selected: Variable[StateDog | None] = new(None)
_list: QListView = new(bind="_dogs", format="{name}", selectedItem="_selected")
```

### Bind Selected Index

```python
_idx: Variable[int] = new(0)
_list: QListView = new(bind="_dogs", format="{name}", selectedIndex="_idx")

# Programmatic selection:
instance._idx.value = 2  # Selects row 2
```

---

## Format Expressions

Format strings evaluate expressions on State objects, automatically unwrapping Variables.

### Simple Field Access

```python
format="{name}"  # Unwraps Variable to get value
```

### Multiple Fields

```python
format="{name} is {age} years old"
```

### Method Calls

```python
format="{name.upper()}"  # Calls method on unwrapped value
```

### Built-in Functions

```python
format="{len(name)} chars"
```

### #self Placeholder

```python
format="Dog: {#self.name}"  # #self refers to the State item
```

---

## Key Conventions

1. **State class definition**: Use `@state` decorator + `State` base + `Variable[T]` fields
2. **Variable assignment**: Assign directly (`dog.name = "Fido"`) - no `.value` needed for setting
3. **List operations**: Use standard list methods on Variable lists (`append`, `extend`, `clear`, `del`)
4. **Format unwrapping**: Format expressions automatically unwrap Variables - access fields directly
5. **Event exclusion**: `Event` fields are never included in table columns
