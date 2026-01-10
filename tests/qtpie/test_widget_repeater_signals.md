# WidgetRepeater Signal Connections

## Signal Connections with Placeholders

WidgetRepeater supports connecting child widget signals to parent handlers with special placeholders: `#index`, `#value`, `#widget`, and `#args`.

### #index - Item Index

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#index)")

    def on_item_deleted(self, index: int) -> None:
        deleted_indices.append(index)
```

### #value - Item Value

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value)")

    def on_item_deleted(self, item: TodoItem) -> None:
        deleted_items.append(item)
```

### #widget - Child Widget Instance

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#widget)")

    def on_item_deleted(self, widget: TodoRow) -> None:
        deleted_widgets.append(widget)
```

### #args - Signal Arguments

```python
@widget
class App(Widget):
    _items: list[EditItem] = [EditItem("a"), EditItem("b")]
    _rows: list[EditRow] = new(bind="_items", value_changed="on_change(#index, #args)")

    def on_change(self, index: int, signal_value: int) -> None:
        received_args.append((index, signal_value))
```

### Multiple Placeholders

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value, #index)")

    def on_item_deleted(self, item: TodoItem, index: int) -> None:
        received_args.append((item, index))
```

## Default Signal Behavior

Without placeholders, signals pass their original arguments (or none if the signal has no args).

```python
@widget
class TodoApp(Widget):
    _items: Variable[list[TodoItem]] = new([TodoItem("Task 1"), TodoItem("Task 2")])
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted")

    def on_item_deleted(self) -> None:
        # Signal has no args, so handler receives none
        deleted_indices.append(-1)
```

## Empty Parens

Empty parens `()` explicitly pass no arguments, even if the signal has args.

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task 1")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted()")

    def on_item_deleted(self) -> None:
        call_count += 1
```

## Callable Handlers

Direct callable references work instead of method names.

```python
def handler() -> None:
    call_count += 1

@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("Task")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete=handler)
```

## Dynamic Index Updates

The `#index` placeholder reflects the current index after list modifications.

```python
@widget
class TodoApp(Widget):
    _items: list[TodoItem] = [TodoItem("A"), TodoItem("B"), TodoItem("C")]
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#index)")

    def on_item_deleted(self, index: int) -> None:
        deleted_indices.append(index)
        del self._items[index]  # Index updates for remaining widgets
```
