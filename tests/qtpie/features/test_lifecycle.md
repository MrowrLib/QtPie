# Lifecycle Hooks in QtPie

This document describes the lifecycle hooks available in QtPie widgets, windows, and menus.

## The `__setup__` Hook

The `__setup__` method is a lifecycle hook called during widget initialization, after all fields have been created but before the widget is fully ready.

### Basic Usage

Define a `__setup__` method to perform initialization logic:

```python
@widget
class MyWidget(Widget):
    def __setup__(self) -> None:
        # Initialization code here
        pass
```

### Accessing and Modifying Fields

All fields are available in `__setup__` and can be read or modified:

```python
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)

    def __setup__(self) -> None:
        self._count.value = 42  # Modify initial value
```

### Working with List Variables

```python
@widget
class ItemList(Widget):
    _items: Variable[list[str]] = new([])

    def __setup__(self) -> None:
        self._items.observable.append("first")
        self._items.observable.append("second")
```

### Working with Dict Variables

```python
@widget
class DataStore(Widget):
    _data: Variable[dict[str, int]] = new({})

    def __setup__(self) -> None:
        self._data.observable["key"] = 42
```

### Adding Validators

Use `__setup__` to add field validators:

```python
@widget
class ValidatedForm(Widget):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
```

### Setting Record Data

For typed widgets (`Widget[T]`), set the record in `__setup__`:

```python
@dataclass
class Person:
    name: str = ""

@widget
class PersonEditor(Widget[Person]):
    def __setup__(self) -> None:
        self.record = Person("Alice")
```

### Calling Other Methods

`__setup__` can delegate to other instance methods:

```python
@widget
class MyWidget(Widget):
    _value: Variable[int] = new(0)

    def __setup__(self) -> None:
        self._initialize()

    def _initialize(self) -> None:
        self._value.value = 99
```

## Key Conventions

| Convention | Description |
|------------|-------------|
| `__setup__` is optional | Widgets work fine without defining it |
| Called exactly once | Invoked once per instance during initialization |
| Fields already exist | All declared fields are accessible when `__setup__` runs |
| Initial values set | Field values have their `new()` defaults before `__setup__` |
| Works across all types | Available on Widget, Window, and Menu classes |

## Initialization Order

1. Widget/Window/Menu is instantiated
2. All fields are created with their `new()` default values
3. `__setup__` is called
4. Widget is ready for use
