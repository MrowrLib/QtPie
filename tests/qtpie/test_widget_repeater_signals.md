# WidgetRepeater Signal Connections

This document covers how to connect signals from child widgets in a `WidgetRepeater` to handlers on the parent widget.

## Child Widget with Custom Signals

Define child widgets with custom `Signal` instances that can be emitted and connected to parent handlers.

```python
@widget
class TodoRow(Widget[TodoItem]):
    on_delete = Signal()
    on_edit = Signal(str)  # Signal with argument

    delete_btn: QPushButton = new("X", clicked="on_delete")
```

## Basic Signal Connection

Connect child widget signals to parent methods using `signal_name="handler_name"` syntax in `new()`.

```python
@widget
class TodoApp(Widget):
    _items: Variable[list[TodoItem]] = new([TodoItem("Task 1")])
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted")

    def on_item_deleted(self) -> None:
        print("Item deleted!")
```

## Index Placeholder (#index)

Pass the item's current index to the handler using `#index` placeholder.

```python
_todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#index)")

def on_item_deleted(self, index: int) -> None:
    del self._items[index]
```

## Value Placeholder (#value)

Pass the item value itself to the handler using `#value` placeholder.

```python
_todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value)")

def on_item_deleted(self, item: TodoItem) -> None:
    self._items.remove(item)
```

## Widget Placeholder (#widget)

Pass the child widget instance to the handler using `#widget` placeholder.

```python
_todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#widget)")

def on_item_deleted(self, widget: TodoRow) -> None:
    print(f"Widget {widget} deleted")
```

## Multiple Placeholders

Combine multiple placeholders in a single handler connection.

```python
_todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value, #index)")

def on_item_deleted(self, item: TodoItem, index: int) -> None:
    print(f"Deleted {item.text} at index {index}")
```

## Signal Args Placeholder (#args)

Spread the signal's own arguments using `#args` placeholder.

```python
@widget
class EditRow(Widget[EditItem]):
    value_changed = Signal(int)  # Emits an integer

@widget
class App(Widget):
    _rows: list[EditRow] = new(bind="_items", value_changed="on_change(#index, #args)")

    def on_change(self, index: int, signal_value: int) -> None:
        print(f"Row {index} changed to {signal_value}")
```

## Empty Parentheses (No Args)

Explicitly pass nothing with empty parentheses.

```python
_todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted()")

def on_item_deleted(self) -> None:
    pass  # No arguments received
```

## Callable Handler

Pass a direct callable instead of a method name string.

```python
def handler() -> None:
    print("Deleted!")

_todo_list: list[TodoRow] = new(bind="_items", on_delete=handler)
```

## Placeholder Reference

| Placeholder | Description |
|-------------|-------------|
| `#index` | Current index of the item in the list |
| `#value` | The item value from the bound list |
| `#widget` | The child widget instance |
| `#args` | Spread the signal's emitted arguments |
