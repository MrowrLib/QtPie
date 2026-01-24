# Repeater Sort String Feature Documentation

This document covers the `sort=` parameter for widget repeaters, specifically the string-based method name resolution feature.

## Sort by Method Name (String)

The `sort=` parameter accepts a string that references a method on the parent widget. This method is called for each item to determine sort order.

```python
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3), Dog("Buddy", 5), Dog("Ace", 1)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="sort_by_name")

    def sort_by_name(self, dog: Dog) -> str:
        return dog.name
```

The sort method receives an item and returns a sortable value (string, int, etc.).

## Sort by Lambda/Callable

Inline callables work as an alternative to method name strings.

```python
_labels: list[QLabel] = new(bind="_dogs", format="{name}", sort=lambda d: d.name)
```

## Sort by Boolean

- `sort=True` - Uses default Python `sorted()` on items
- `sort=False` - Preserves original insertion order

```python
_labels: list[QLabel] = new(bind="_nums", sort=True)   # Sorted: [1, 1, 3, 4, 5]
_labels: list[QLabel] = new(bind="_nums", sort=False)  # Original: [3, 1, 4, 1, 5]
```

## Dict Repeater Sorting

For dict bindings, the sort method receives the dictionary **key**, not the value.

```python
@widget
class ScoreBoard(Widget):
    _scores: dict[str, int] = {"Zara": 100, "Buddy": 85, "Ace": 90}
    _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", sort="sort_by_key")

    def sort_by_key(self, key: str) -> str:
        return key
```

## Set Repeater Sorting

For set bindings, the sort method receives each set item.

```python
@widget
class TagList(Widget):
    _tags: set[str] = {"zebra", "apple", "mango"}
    _labels: set[QLabel] = new(bind="_tags", sort="sort_tags")

    def sort_tags(self, tag: str) -> str:
        return tag
```

## Supported Collection Types

| Collection Type | Annotation | Sort Method Receives |
|-----------------|------------|---------------------|
| List | `list[QLabel]` | Item value |
| Dict | `list[QLabel]` | Dictionary key |
| Set | `set[QLabel]` | Set item |

## Convention Summary

- Use `sort="method_name"` for readable, reusable sort logic
- Use `sort=lambda x: x.field` for simple one-off sorting
- Use `sort=True` for natural ordering
- Use `sort=False` (or omit) to preserve insertion order
