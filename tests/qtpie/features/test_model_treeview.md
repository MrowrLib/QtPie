# QTreeView Model Binding - Feature Documentation

This document describes QtPie's declarative QTreeView binding patterns based on test usage.

## Basic Tree Binding

Bind a `Variable[list[T]]` to a QTreeView using `bind=`. The tree auto-displays items using their `__str__` method.

```python
@widget
class TestWidget(Widget):
    _nodes: Variable[list[TreeNode]] = new([TreeNode("Root 1"), TreeNode("Root 2")])
    _tree: QTreeView = new(bind="_nodes")
```

## Hierarchical Data (Nested Children)

By default, QtPie looks for a `children` attribute on each item. For items with nested lists, the tree renders them hierarchically.

```python
@dataclass
class TreeNode:
    name: str
    children: list[TreeNode] = field(default_factory=list)

_nodes: Variable[list[TreeNode]] = new([
    TreeNode("Parent", [TreeNode("Child 1"), TreeNode("Child 2")])
])
_tree: QTreeView = new(bind="_nodes")
```

## Custom Children Attribute

Use `children=` when your items use a different attribute name for children.

```python
@dataclass
class FileNode:
    name: str
    items: list[FileNode] = field(default_factory=list)  # Not "children"

_tree: QTreeView = new(bind="_nodes", children="items")
```

## Format String

Use `format=` to customize how each node is displayed.

```python
_tree: QTreeView = new(bind="_nodes", format="Node: {name}")
# Or with expressions:
_tree: QTreeView = new(bind="_nodes", format="{name} ({age} yrs)")
```

## Selection Binding (Single Item)

Use `selectedItem=` to bind the current selection to a Variable.

```python
@widget
class TestWidget(Widget):
    _nodes: Variable[list[TreeNode]] = new([...])
    _selected: Variable[TreeNode | None] = new(None)
    _tree: QTreeView = new(bind="_nodes", selectedItem="_selected")
```

Bare Variable annotation (no default) is also supported:

```python
_selected: Variable[TreeNode | None]  # No = new(...)
_tree: QTreeView = new(bind="_nodes", selectedItem="_selected")
```

## Selection Binding (Multiple Items)

Use `selectedItems=` for multi-selection binding to a list Variable.

```python
_selected: Variable[list[TreeNode]]
_tree: QTreeView = new(bind="_nodes", selectedItems="_selected")
_count_label: QLabel = new(bind="Selected: {len(_selected)}")
```

Both `selectedItem=` and `selectedItems=` can be used together:

```python
_current: Variable[TreeNode | None]
_selected: Variable[list[TreeNode]]
_tree: QTreeView = new(bind="_nodes", selectedItem="_current", selectedItems="_selected")
```

## Nested Path Binding

Selection bindings support optional chaining for nested paths, useful when the root object may be None.

```python
@widget
class TestWidget(Widget):
    workspace: Variable[Workspace | None] = new(None)
    _tree: QTreeView = new(
        bind="workspace?.items",
        selectedItem="workspace?.selected_item",
    )
```

## Parent Widget Variable Resolution

Selection bindings can reference Variables defined in parent widgets, not just the current widget.

```python
@widget
class ChildTreeWidget(Widget):
    _nodes: Variable[list[TreeNode]] = new([...])
    # "selected_node" is defined on PARENT widget
    _tree: QTreeView = new(bind="_nodes", selectedItem="selected_node")

@widget
class ParentWidget(Widget):
    selected_node: Variable[TreeNode | None] = new(None)
    _child: ChildTreeWidget = new()
```

## Checkable Items

Use `checkable=` to add checkboxes to tree items.

### Field Binding (Two-Way)

```python
@dataclass
class SelectableNode:
    name: str
    selected: bool = False

_tree: QTreeView = new(bind="_nodes", checkable="selected")
```

### Expression (Read-Only)

```python
_tree: QTreeView = new(bind="_nodes", checkable="{len(children) > 0}")
```

### Nested Path

```python
_tree: QTreeView = new(bind="_nodes", checkable="state.selected")
```

### Disable Checkboxes

```python
_tree: QTreeView = new(bind="_nodes", checkable=False)
```

## Editable Items

Use `editable=` to enable inline text editing.

### Field Binding

```python
_tree: QTreeView = new(bind="_nodes", editable="name")
```

### Simple Types

```python
_items: Variable[list[str]] = new(["Apple", "Banana"])
_tree: QTreeView = new(bind="_items", editable=True)
```

### Nested Path

```python
_tree: QTreeView = new(bind="_nodes", editable="info.title")
```

### Combining with Other Options

```python
_tree: QTreeView = new(bind="_nodes", format="[{name}]", editable="name", checkable="selected")
```

## Edit Triggers

Control when inline editing activates.

```python
# Disable double-click editing
_tree: QTreeView = new(bind="_nodes", editable="name", editOnDoubleClick=False)

# Enable click-on-selected editing
_tree: QTreeView = new(bind="_nodes", editable="name", editOnSelect=True)

# Disable F2/Enter key editing
_tree: QTreeView = new(bind="_nodes", editable="name", editOnEditKey=False)
```

## Validators

Add input validation to editable items.

```python
# Callable validator
_tree: QTreeView = new(bind="_nodes", editable="name", validator=lambda s: len(str(s)) <= 10)

# Regex pattern
_tree: QTreeView = new(bind="_nodes", editable="name", validator=r"^[A-Za-z]+$")

# Named function
def alphanumeric_validator(text: str) -> bool:
    return text.isalnum() or text == ""

_tree: QTreeView = new(bind="_nodes", editable="name", validator=alphanumeric_validator)
```

## Edit Callbacks

Use `onEdited=` to receive callbacks after edits.

```python
@widget
class TestWidget(Widget):
    _nodes: Variable[list[EditableNode]] = new([...])
    _tree: QTreeView = new(bind="_nodes", editable="name", onEdited="_on_node_edited")

    def _on_node_edited(self, item: EditableNode, old_value: str, new_value: str) -> None:
        print(f"Changed {item} from {old_value} to {new_value}")
```

Or with a standalone callable:

```python
def on_edited(item: Any, old_value: str, new_value: str) -> None:
    print(f"Edited: {old_value} -> {new_value}")

_tree: QTreeView = new(bind="_nodes", editable="name", onEdited=on_edited)
```

## Signal Handlers

Connect signals like `clicked` to methods.

```python
@widget
class TestWidget(Widget):
    _tree: QTreeView = new(
        bind=list(Location),
        selectedItem="auth?.location",
        clicked="_on_clicked",
    )

    def _on_clicked(self) -> None:
        # Selection is already updated when this fires
        print(f"Selected: {self.record.auth.location}")
```

## Reactive Updates

Tree automatically updates when the bound list changes.

```python
# Append
instance._nodes.append(TreeNode("New"))

# Remove
del instance._nodes[1]

# Clear
instance._nodes.clear()
```

### ObservableList for Child Updates

Use `ObservableList` for children to get reactive updates on nested modifications.

```python
from observant import ObservableList

@dataclass
class ObservableTreeNode:
    name: str
    children: ObservableList[ObservableTreeNode] = field(
        default_factory=lambda: ObservableList()
    )

# Tree updates when you modify children
root.children.append(ObservableTreeNode("New Child"))
```

## Widget[T] Record Integration

QTreeView works with `Widget[T]` record bindings.

```python
@dataclass
class Cat:
    name: str
    kittens: list[Cat] = field(default_factory=list)

@widget(record=cat)
class CatWidget(Widget[Cat]):
    _selected_kittens: Variable[list[Cat]]
    _tree: QTreeView = new(
        bind="kittens",
        format="{name} ({age} yrs)",
        children="kittens",
        selectedItems="_selected_kittens"
    )
    _info: QLabel = new(bind="Selected: {len(_selected_kittens)}")
```

## Summary of `new()` Parameters for QTreeView

| Parameter | Type | Description |
|-----------|------|-------------|
| `bind=` | `str` | Variable name or path to bind data from |
| `children=` | `str` | Attribute name for child items (default: "children") |
| `format=` | `str` | Format string for display (e.g., `"{name}"`) |
| `selectedItem=` | `str` | Variable to bind single selection |
| `selectedItems=` | `str` | Variable to bind multi-selection list |
| `checkable=` | `str\|bool` | Field name or expression for checkbox binding |
| `editable=` | `str\|bool` | Field name for inline editing |
| `validator=` | `Callable\|str` | Validation function or regex pattern |
| `onEdited=` | `str\|Callable` | Callback after edit completes |
| `editOnDoubleClick=` | `bool` | Enable double-click to edit (default: True) |
| `editOnSelect=` | `bool` | Enable click-selected to edit (default: False) |
| `editOnEditKey=` | `bool` | Enable F2/Enter to edit (default: True) |
| `clicked=` | `str` | Signal handler for item clicks |
