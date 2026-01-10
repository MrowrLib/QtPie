# WidgetRepeater Signal Connections

## Signal Placeholders

Connect child widget signals to parent handlers using special placeholders in the handler string.

### #index - Item Index

Pass the current index of the item in the list:

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#index)")

    def on_item_deleted(self, index: int) -> None:
        deleted_indices.append(index)
```

### #value - Item Value

Pass the actual item from the list:

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value)")

    def on_item_deleted(self, item: TodoItem) -> None:
        deleted_items.append(item)
```

### #widget - Child Widget

Pass the child widget instance:

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#widget)")

    def on_item_deleted(self, widget: TodoRow) -> None:
        deleted_widgets.append(widget)
```

### #args - Signal Arguments

Spread the signal's own arguments into the handler:

```python
@widget
class App(Widget):
    _items: list[EditItem] = [EditItem("a"), EditItem("b")]
    _rows: list[EditRow] = new(bind="_items", value_changed="on_change(#index, #args)")

    def on_change(self, index: int, signal_value: int) -> None:
        received_args.append((index, signal_value))
```

### Multiple Placeholders

Combine multiple placeholders in one handler call:

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value, #index)")

    def on_item_deleted(self, item: TodoItem, index: int) -> None:
        received_args.append((item, index))
```

## Handler Formats

### String Handler Name

Default behavior passes signal's own arguments (if any):

```python
_todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted")

def on_item_deleted(self) -> None:
    # No args passed if signal has no args
    pass
```

### Empty Parens

Explicitly pass nothing:

```python
_todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted()")

def on_item_deleted(self) -> None:
    call_count += 1
```

### Direct Callable

Pass a function or lambda directly:

```python
def handler() -> None:
    call_count += 1

_todo_list: list[TodoRow] = new(bind="_items", on_delete=handler)
```

## Dynamic Index Updates

Index placeholder reflects current position after list modifications:

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("A"), TodoItem("B"), TodoItem("C")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#index)")

    def on_item_deleted(self, index: int) -> None:
        deleted_indices.append(index)
        del self._items[index]  # Indices update for remaining items
```
