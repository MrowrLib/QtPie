# Sort by Method Name in Repeaters

## String Method Name Resolution

The `sort=` parameter accepts method names as strings. When you pass `sort="method_name"`, the repeater resolves it to a method on the parent widget and uses it as the sort key function.

```python
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3), Dog("Buddy", 5), Dog("Ace", 1)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="sort_by_name")

    def sort_by_name(self, dog: Dog) -> str:
        return dog.name
```

```python
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3), Dog("Buddy", 5), Dog("Ace", 1)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="sort_by_age")

    def sort_by_age(self, dog: Dog) -> int:
        return dog.age
```

## Works with All Repeater Types

String method resolution works with list repeaters, dict repeaters (sorts keys), and set repeaters.

```python
@widget
class ScoreBoard(Widget):
    _scores: dict[str, int] = {"Zara": 100, "Buddy": 85, "Ace": 90}
    _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", sort="sort_by_key")

    def sort_by_key(self, key: str) -> str:
        return key
```

```python
@widget
class TagList(Widget):
    _tags: set[str] = {"zebra", "apple", "mango"}
    _labels: set[QLabel] = new(bind="_tags", sort="sort_tags")

    def sort_tags(self, tag: str) -> str:
        return tag
```

## Error Handling

If the method name doesn't exist on the parent widget, raises `AttributeError`. If no parent widget is provided when constructing repeaters directly, raises `AttributeError`.

```python
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="nonexistent_method")

# Raises: AttributeError: nonexistent_method
```

## Backward Compatibility

All existing `sort=` modes still work: `sort=callable`, `sort=True` (default sorted), `sort=False` (preserve order).

```python
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3), Dog("Ace", 1)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort=lambda d: d.name)
```

```python
@widget
class NumberList(Widget):
    _nums: list[int] = [3, 1, 4, 1, 5]
    _labels: list[QLabel] = new(bind="_nums", sort=True)
```
