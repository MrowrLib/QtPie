# Repeater `sort=` String Method Name Resolution

## Sort by Method Name (String)

Repeaters support `sort="method_name"` which resolves to a method on the parent widget. This works for list, dict, and set repeaters.

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
class ScoreBoard(Widget):
    _scores: dict[str, int] = {"Zara": 100, "Buddy": 85, "Ace": 90}
    _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", sort="sort_by_key")

    def sort_by_key(self, key: str) -> str:
        return key
```

## Error Handling

If the method name doesn't exist, raises `AttributeError`:

```python
@widget
class DogList(Widget):
    _dogs: list[Dog] = [Dog("Zara", 3)]
    _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="nonexistent_method")

# Raises: AttributeError: nonexistent_method
```

Direct repeater construction without a parent widget also raises:

```python
obs_list = ObservableList([1, 2, 3])

WidgetRepeater(
    observable_list=obs_list,
    item_type=int,
    widget_type=QLabel,
    sort="some_method",
    parent_widget=None,
)
# Raises: AttributeError: cannot resolve method name without parent widget
```

## Other Sort Options Still Work

Lambda functions:

```python
_labels: list[QLabel] = new(bind="_dogs", format="{name}", sort=lambda d: d.name)
```

Boolean `True` (default sorting):

```python
_labels: list[QLabel] = new(bind="_nums", sort=True)
```

Boolean `False` (preserve order):

```python
_labels: list[QLabel] = new(bind="_nums", sort=False)
```
