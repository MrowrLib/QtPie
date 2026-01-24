# QListView Embedded Widgets Feature

QtPie allows embedding custom Widget subclasses inside QListView items using Qt's `openPersistentEditor()` mechanism. Each list item displays a fully interactive widget instead of plain text.

## Basic Embedded Widget

Define a Widget subclass that receives record data, then use `widget=` to embed it in a QListView.

### Define the embedded widget

```python
@widget
class DogLabel(Widget[Dog]):
    _label: QLabel = new(bind="{record.name} ({record.age})")
```

### Embed in QListView

```python
@widget
class TestClass(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
    _list: QListView = new(bind="_dogs", widget=DogLabel)
```

The `widget=` parameter specifies the Widget class to instantiate for each item. Each widget receives its corresponding list item as `record`.

## Reactive List Updates

The embedded widgets automatically sync with list changes:

```python
# Append - creates new widget
instance._dogs.append(Dog("Rex", 5))

# Remove - removes widget
instance._dogs.remove(Dog("Fido", 3))

# Clear - removes all widgets
instance._dogs.clear()
```

## embed() with Index Injection

Use `embed()` to inject the row index into a bare `Variable[int]` field.

### Define widget with index variable

```python
@widget
class DogLabelWithIndex(Widget[Dog]):
    row_index: Variable[int]  # Bare annotation - injected automatically
    _label: QLabel = new(bind="Row {row_index}: {record.name}")
```

### Use embed() with selectedIndex

```python
_list: QListView = new(
    bind="_dogs",
    widget=embed(DogLabelWithIndex, selectedIndex="row_index")
)
```

The `selectedIndex="row_index"` maps the row number to the child's `row_index` Variable.

## embed() with Signal Connection

Connect child widget signals to parent handler methods.

### Define widget with signal

```python
@widget
class DogLabelWithDelete(Widget[Dog]):
    delete_requested = Signal()
    _delete: QPushButton = new("Delete", clicked="on_delete")

    def on_delete(self) -> None:
        self.delete_requested.emit()
```

### Connect signal to parent method

```python
@widget
class TestClass(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
    _list: QListView = new(
        bind="_dogs",
        widget=embed(DogLabelWithDelete, delete_requested="handle_delete")
    )

    def handle_delete(self) -> None:
        # Handle delete from child widget
        pass
```

## embed() with Variable Pass-Through

Pass a parent Variable to child widgets so they share reactive state.

### Define widget with bare Variable

```python
@widget
class DogLabelWithToggle(Widget[Dog]):
    show_details: Variable[bool]  # Bare - receives parent's Variable
    _label: QLabel = new(bind="{record.name}")
    _age: QLabel = new(bind="{record.age} years", visible="show_details")
```

### Pass parent Variable to child

```python
@widget
class TestClass(Widget):
    _show_details: Variable[bool] = new(True)
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
    _list: QListView = new(
        bind="_dogs",
        widget=embed(DogLabelWithToggle, show_details="_show_details")
    )
```

All child widgets share the same `_show_details` Variable, so toggling it affects all items.

## Combined embed() Features

Use multiple embed() features together:

```python
@widget
class DogCard(Widget[Dog]):
    delete_requested = Signal()
    row_index: Variable[int]        # Injected index
    show_age: Variable[bool]        # Pass-through Variable
    _label: QLabel = new(bind="[{row_index}] {record.name}")
    _age: QLabel = new(bind="{record.age} years", visible="show_age")
    _delete: QPushButton = new("X", clicked="on_delete")

    def on_delete(self) -> None:
        self.delete_requested.emit()

@widget
class TestClass(Widget):
    _show_age: Variable[bool] = new(True)
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
    _list: QListView = new(
        bind="_dogs",
        widget=embed(
            DogCard,
            selectedIndex="row_index",
            show_age="_show_age",
            delete_requested="handle_delete",
        ),
    )

    def handle_delete(self) -> None:
        pass
```

## selectedWidget Binding

Track which embedded widget is currently selected using `selectedWidget=`.

```python
@widget
class TestClass(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
    _selected_widget: Variable[Widget | None] = new(None)
    _list: QListView = new(
        bind="_dogs",
        widget=DogLabel,
        selectedWidget="_selected_widget"
    )
```

The `_selected_widget` Variable:
- Is `None` when nothing is selected
- Updates to the embedded widget instance when a row is selected
- Automatically updates when selection changes

## Summary of new() Parameters for QListView

| Parameter | Type | Description |
|-----------|------|-------------|
| `bind=` | `str` | Variable name containing `list[T]` data |
| `widget=` | `type[Widget]` or `embed(...)` | Widget class to embed for each item |
| `selectedWidget=` | `str` | Variable name to receive currently selected widget |

## Summary of embed() Parameters

| Parameter | Description |
|-----------|-------------|
| First positional | Widget class to embed |
| `selectedIndex=` | Child Variable name to inject row index |
| `signal_name=` | Parent method name to connect child signal |
| `var_name=` | Parent Variable name to pass through to child |
