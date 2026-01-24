# Dock Tab Context Menu Feature

This document describes the dock tab context menu feature in QtPie Windows, which provides right-click menus on tabbed dock widgets.

## Basic Dock Setup with Groups

Docks in the same `group` are tabified together, creating a tab bar:

```python
@window
class TestWindow(Window):
    _props: Dock[PropertiesPanel] = new(dock="right", group="inspector", title="Properties")
    _inspector: Dock[InspectorPanel] = new(group="inspector", title="Inspector")
```

## Context Menu Configuration

### Enabling/Disabling the Menu

The context menu is **enabled by default**. Disable it with `dockMenu=False`:

```python
@window(dockMenu=False)
class TestWindow(Window):
    _props: Dock[PropertiesPanel] = new(dock="right", group="g", title="Properties")
```

### Built-in Menu Actions

By default, the context menu includes:

- **Close** - Close the current tab
- **Close Others** - Close all tabs except the current one (only if multiple tabs)
- **Close to the Right** - Close tabs to the right (only if tabs exist to the right)
- **Close to the Left** - Close tabs to the left (only if tabs exist to the left)
- **Close All** - Close all tabs in the group (only if multiple tabs)

### Disabling Individual Actions

Each action can be individually disabled via decorator kwargs:

```python
@window(dockMenuClose=False)           # Hide "Close"
class W1(Window): ...

@window(dockMenuCloseOthers=False)     # Hide "Close Others"
class W2(Window): ...

@window(dockMenuCloseRight=False)      # Hide "Close to the Right"
class W3(Window): ...

@window(dockMenuCloseLeft=False)       # Hide "Close to the Left"
class W4(Window): ...

@window(dockMenuCloseAll=False)        # Hide "Close All"
class W5(Window): ...
```

Disable all actions:

```python
@window(
    dockMenuClose=False,
    dockMenuCloseOthers=False,
    dockMenuCloseRight=False,
    dockMenuCloseLeft=False,
    dockMenuCloseAll=False,
)
class EmptyMenuWindow(Window): ...
```

## Custom Context Menus

### Per-Dock Custom Menu

Provide a custom QMenu subclass via `contextMenu=`:

```python
class CustomDockMenu(QMenu):
    def __init__(self) -> None:
        super().__init__()
        self.addAction("Custom Action 1")
        self.addAction("Custom Action 2")

@window
class TestWindow(Window):
    _props: Dock[PropertiesPanel] = new(
        dock="right",
        group="g",
        title="Properties",
        contextMenu=CustomDockMenu,  # Custom menu replaces built-in
    )
    _inspector: Dock[InspectorPanel] = new(group="g", title="Inspector")  # Uses built-in
```

### Prepending Built-in Actions to Custom Menu

Use `dockMenuPrependActions=True` to add built-in actions before custom actions:

```python
@window(dockMenuPrependActions=True)
class TestWindow(Window):
    _props: Dock[PropertiesPanel] = new(
        dock="right",
        group="g",
        title="Properties",
        contextMenu=CustomDockMenu,
    )
```

Results in menu order: Close, Close Others, ..., separator, Custom Action 1, Custom Action 2

## Dock Methods for Tab Operations

Docks provide methods for programmatic tab operations:

```python
# Close all other tabs in the group
win._props.close_others()

# Close tabs to the right in the tab bar
win._props.close_to_right()

# Close tabs to the left in the tab bar
win._console.close_to_left()

# Close all tabs in the group (including self)
win._props.close_all()
```

### Tab Position Properties

```python
win._props.has_tabs_to_right  # True if tabs exist to the right
win._props.has_tabs_to_left   # True if tabs exist to the left
win._props.tab_count          # Total number of tabs in the group
```

## Variable List Dock Repeaters

Context menus also work with dynamically created docks from `Variable[list[T], Dock[W]]`:

```python
@dataclass
class EditorItem:
    name: str = "Untitled"

@window
class TestWindow(Window):
    _editors: Variable[list[EditorItem], Dock[EditorWidget]] = new(
        group="editors",
        dock="right",
        title="{name}",
        contextMenu=CustomDockMenu,  # Optional: custom menu for all created docks
    )
```

Adding/removing items creates/destroys docks:

```python
win._editors.append(EditorItem(name="File1"))  # Creates dock tab
win._editors.widget[0].close()                  # Removes item from list
```
