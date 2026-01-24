# Dirty Tracking in QtPie

Dirty tracking allows widgets to know when their state has changed from initial values. This is useful for enabling/disabling save buttons, prompting before close, and tracking unsaved changes.

## Core Concepts

### is_dirty Property

The `is_dirty` property is an `Observable[bool]` that tracks whether any Variable has been modified.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

# Check dirty state
if instance.is_dirty.get():
    print("Unsaved changes!")
```

### dirty_fields Property

Returns a `set[str]` of field names that have been modified.

```python
instance._name.value = "changed"
instance._count.value = 42
print(instance.dirty_fields)  # {"_name", "_count"}
```

### reset_dirty() Method

Marks all Variables as clean, resetting the dirty state.

```python
instance.reset_dirty()
assert instance.is_dirty.get() is False
assert instance.dirty_fields == set()
```

## Lifecycle Hook: on_dirty_changed

Override this method to react to dirty state transitions. It only fires on actual state changes (clean->dirty or dirty->clean), not on every value change.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        self.save_btn.setEnabled(is_dirty)
```

Key behavior:
- Called with `True` when first Variable becomes dirty
- Called with `False` when `reset_dirty()` is called
- Does NOT fire repeatedly when already dirty

## Reactive Binding

Since `is_dirty` is an `Observable[bool]`, you can subscribe to changes.

```python
dirty_changes: list[bool] = []
instance.is_dirty.on_change(lambda v: dirty_changes.append(v))
```

## Works with All Class Types

Dirty tracking works identically across `Widget`, `Window`, `Menu`, and `App` classes.

## Collection Types

### List Variables

All list mutations trigger dirty tracking:

```python
_items: Variable[list[str]] = new()

# All of these make the widget dirty:
instance._items.observable.append("a")
instance._items.observable.remove("a")
instance._items.observable.insert(0, "z")
instance._items.observable.pop()
instance._items.observable.clear()
```

### Dict Variables

All dict mutations trigger dirty tracking:

```python
_data: Variable[dict[str, int]] = new()

# All of these make the widget dirty:
instance._data.observable["key"] = 42
del instance._data.observable["key"]
instance._data.observable.update({"a": 1})
instance._data.observable.clear()
```

### Set Variables

All set mutations trigger dirty tracking:

```python
_tags: Variable[set[str]] = new()

# All of these make the widget dirty:
instance._tags.observable.add("tag")
instance._tags.observable.discard("tag")
instance._tags.observable.clear()
```

## Multiple Variables

Dirty tracking aggregates across all Variables in a widget. Each changed field appears once in `dirty_fields`.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)
    _items: Variable[list[str]] = new()
    _data: Variable[dict[str, int]] = new()

instance._name.value = "changed"
instance._items.observable.append("a")
# dirty_fields = {"_name", "_items"}
# _count and _data are not in dirty_fields
```

## Initial State

- New instances start as NOT dirty
- Empty classes (no Variables) are also NOT dirty
- Multiple changes to the same field only appear once in `dirty_fields`
