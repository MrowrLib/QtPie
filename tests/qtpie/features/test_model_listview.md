# QListView Model Binding in QtPie

This document describes how to use `QListView` with reactive model binding in QtPie.

## Basic List Binding

Bind a `QListView` to a `Variable[list]` for automatic reactive updates.

```python
_items: Variable[list[str]] = new(["A", "B", "C"])
_list: QListView = new(bind="_items")
```

The list view automatically updates when items are appended, removed, replaced, or cleared:

```python
instance._items.append("D")     # Adds row
instance._items.remove("B")     # Removes row
instance._items[0] = "Z"        # Updates row
instance._items.clear()         # Clears all rows
```

## Format Strings

Use `format=` to customize how items are displayed, especially for dataclass items:

```python
@dataclass
class Dog:
    name: str
    age: int

_dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
_list: QListView = new(bind="_dogs", format="{name} ({age})")
# Displays: "Fido (3)", "Rex (5)"
```

## Single Selection Binding

### selectedIndex

Bind the current row index to a Variable:

```python
_items: Variable[list[str]] = new(["A", "B", "C"])
_idx: Variable[int]  # Bare annotation - auto-created
_list: QListView = new(bind="_items", selectedIndex="_idx")

# Change selection programmatically:
instance._idx.value = 2  # Selects row 2
```

### selectedItem

Bind the actual selected item to a Variable:

```python
_dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
_dog: Variable[Dog]  # Bare annotation
_list: QListView = new(bind="_dogs", selectedItem="_dog")

# Access selected item:
print(instance._dog.value.name)  # "Fido"
```

### selectedText

Match selection by display text (useful when display differs from value):

```python
_dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
_name: Variable[str] = new("Rex")
_list: QListView = new(bind="_dogs", format="{name}", selectedText="_name")
# Selects "Rex" by matching the formatted display text
```

## Multi-Selection Binding

### selectedIndexes

Bind to a list of selected row indices:

```python
_items: Variable[list[str]] = new(["A", "B", "C"])
_indexes: Variable[list[int]]
_list: QListView = new(bind="_items", selectedIndexes="_indexes")
```

### selectedItems

Bind to a list of selected items:

```python
_dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
_selected: Variable[list[Dog]]
_list: QListView = new(bind="_dogs", selectedItems="_selected")
```

## Nested Path Bindings

Use optional chaining (`?.`) for nullable nested paths:

```python
@dataclass
class Workspace:
    items: list[Dog]
    selected_item: Dog | None = None

workspace: Variable[Workspace | None] = new(None)
_list: QListView = new(
    bind="workspace?.items",
    selectedItem="workspace?.selected_item",
)
```

## Dict Binding

Bind to dictionaries - keys become selectable values, values become display text:

```python
# Variable[dict]
_headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
_list: QListView = new(bind="_headers", format="{#key}: {#value}")

# Optional chaining with dict
_response: Variable[Response | None] = new(None)
_list: QListView = new(bind="_response?.headers", format="{#key}: {#value}")
```

## Static List/Dict Binding

Bind to static class attributes (non-reactive but useful for fixed options):

```python
# Static list
_locations: list[str] = new(["header", "query", "cookie"])
_list: QListView = new(bind="_locations")

# Static dict (values are display text, keys are selection values)
_options: dict[str, str] = new({"header": "Header", "query": "Query Parameter"})
_list: QListView = new(bind="_options")
```

## Inline List/Dict Binding

Pass literal lists or dicts directly to `bind=`:

```python
_list: QListView = new(bind=["header", "query", "cookie"])
_list: QListView = new(bind={"header": "Header", "query": "Query Parameter"})
```

## Enum Binding

Bind to Python Enums for type-safe option lists:

```python
class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

_priority: Variable[Priority] = new(Priority.LOW)
_list: QListView = new(bind=Priority, selectedItem="_priority")
```

## Checkable Items

Add checkboxes to list items with `checkable=`:

```python
@dataclass
class Task:
    title: str
    done: bool = False

_tasks: Variable[list[Task]] = new([Task("Task A", done=True)])
_list: QListView = new(bind="_tasks", checkable="done")
# Two-way binding: clicking checkbox updates task.done
```

Expression-based checkable (read-only):

```python
_list: QListView = new(bind="_tasks", checkable="{len(title) > 10}")
```

## Editable Items

Enable inline text editing with `editable=`:

```python
@dataclass
class Item:
    name: str

_items: Variable[list[Item]] = new([Item("Original")])
_list: QListView = new(bind="_items", editable="name")
# Double-click to edit, changes propagate to dataclass

# For simple types:
_items: Variable[list[str]] = new(["Apple", "Banana"])
_list: QListView = new(bind="_items", editable=True)

# Nested paths:
_list: QListView = new(bind="_items", editable="info.title")
```

## Combined Features

Use format, selection, checkable, and editable together:

```python
_tasks: Variable[list[Task]] = new([Task("Task A", done=True)])
_list: QListView = new(
    bind="_tasks",
    format="[{title}]",
    checkable="done",
    editable="title",
    selectedItem="_selected_task",
)
```

## Record Field Binding

When using `Widget[T]`, bind to record fields while using local Variables for selection:

```python
@dataclass
class Container:
    dogs: list[Dog]

@widget(record=Container(dogs=[Dog("Fido", 3)]))
class MyWidget(Widget[Container]):
    _dogs: Variable[list[Dog]]  # Local variable for selection
    _list: QListView = new(
        bind="dogs",              # Resolves to record.dogs
        selectedItems="_dogs",    # Resolves to local _dogs Variable
    )
```

## Signal Handlers

Connect signal handlers that see updated values:

```python
_priority: Variable[Priority] = new(Priority.LOW)
_list: QListView = new(
    bind=Priority,
    selectedItem="_priority",
    clicked="_on_clicked",  # Handler sees updated _priority
)

def _on_clicked(self) -> None:
    print(self._priority.value)  # Sees the NEW value
```

## ObservableList and ObservableDict

Direct binding to observant primitives works seamlessly:

```python
from observant import ObservableDict, ObservableList

headers: ObservableDict[str, str]
_list: QListView = new(bind="headers", format="{#key}: {#value}")

def __setup__(self) -> None:
    self.headers = ObservableDict({"Content-Type": "application/json"})
```

## Dirty State Tracking

Selection bindings track dirty state per-item:

```python
_selected: Variable[Person | None] = new(None)
_list: QListView = new(bind="_people", selectedItem="_selected")

# Modify selected item
instance._selected.name = "Modified"

# Check dirty state
if instance._selected.is_dirty.get():
    print("Item has been modified")
```
