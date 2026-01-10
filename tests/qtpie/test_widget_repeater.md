# WidgetRepeater Tests

## Basic Creation and Layout

`WidgetRepeater` automatically creates one widget per list item and integrates into parent layouts.

```python
@widget
class Test(Widget):
    _numbers: Variable[list[int], QLineEdit] = new([1, 2, 3])

w = qt.track(Test())
repeater: WidgetRepeater[int] = w._numbers.widget
assert repeater.widget_count() == 3
```

```python
@widget
class Test(Widget):
    _label: QLabel = new("Before")
    _numbers: Variable[list[int], QLabel] = new([1, 2])
    _label2: QLabel = new("After")

w = qt.track(Test())
# Repeater is added to layout between the two labels
assert layout.itemAt(1).widget() isinstance WidgetRepeater
```

## Granular List Synchronization

Append, insert, remove, replace, and clear operations on the underlying `ObservableList` automatically sync to widgets.

```python
@widget
class Test(Widget):
    _items: Variable[list[str], QLineEdit] = new(["a", "b"])

w = qt.track(Test())
w._items.observable.append("c")  # Adds widget
assert repeater.widget_count() == 3

w._items.observable.insert(1, "x")  # Inserts at position
w._items.observable.remove("b")    # Removes widget
w._items.observable[0] = "new"     # Updates widget
w._items.observable.clear()        # Removes all widgets
```

## Two-Way Binding with Primitives

Primitives (int, str) support two-way binding: list changes update widgets, widget edits update list.

```python
@widget
class Test(Widget):
    _names: Variable[list[str], QLineEdit] = new(["Alice", "Bob"])

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._names.widget

# List to widget
assert repeater.widget_at(0).text() == "Alice"

# Widget to list
edit = repeater.widget_at(0)
edit.setText("Charlie")
assert w._names.observable[0] == "Charlie"
```

## Complex Object Binding

Bind object properties to widgets using format strings. Single property binding supports two-way sync.

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    # Single property - two-way binding
    _dogs: Variable[list[Dog], QLineEdit] = new([Dog("Rover", 3)])(bind="{name}")

w = qt.track(Test())
edit = repeater.widget_at(0)
assert edit.text() == "Rover"
edit.setText("Max")
assert w._dogs.observable[0].name == "Max"
```

```python
@widget
class Test(Widget):
    # Multiple properties - display only
    _dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3)])(bind="{name} is {age} years old")

assert repeater.widget_at(0).text() == "Rover is 3 years old"
```

## Bind Expression Placeholders

Special placeholders provide access to index, item value, and parent context.

```python
@widget
class Test(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b"])(bind="Index {#index}: {#self}")

w = qt.track(Test())
assert repeater.widget_at(0).text() == "Index 0: a"
assert repeater.widget_at(1).text() == "Index 1: b"
```

## Dict Binding with list[QWidget]

Bind `list[QWidget]` to dict variables with `{#key}` and `{#value}` placeholders.

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    _dogs: Variable[dict[str, Dog]] = new({"Fido": Dog("Fido", 3)})
    _labels: list[QLabel] = new(bind="_dogs", format="{#key}: {name} is {age}")

w = qt.track(Test())
label = w._labels.widget_for_key("Fido")
assert label.text() == "Fido: Fido is 3"

# Dict changes sync to widgets
w._items["Rex"] = Dog("Rex", 5)
assert w._labels.widget_count() == 2
```

## Format Parameter for list[QWidget]

Use `format=` with string templates or callables for standalone list bindings.

```python
@widget
class Test(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
    _labels: list[QLabel] = new(bind="_dogs", format="{name} is {age} years old")

assert w._labels.widget_at(0).text() == "Fido is 3 years old"
```

```python
@widget
class Test(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
    _labels: list[QLabel] = new(bind="_dogs", format=lambda d: f"{d.name.upper()} - {d.age}")

assert w._labels.widget_at(0).text() == "FIDO - 3"
```

## Widget Kwargs Propagation

Kwargs passed to `new()` are applied to every child widget, including newly created ones.

```python
@widget
class Test(Widget):
    _names: Variable[list[str], QLineEdit] = new(["a", "b"])(maxLength=5)

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._names.widget

assert repeater.widget_at(0).maxLength() == 5
assert repeater.widget_at(1).maxLength() == 5

# Newly added widgets also get kwargs
w._names.observable.append("c")
assert repeater.widget_at(2).maxLength() == 5
```

## Index Management After Operations

Widgets remain bound to correct list items after insert/remove operations.

```python
@widget
class Test(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "c"])

w = qt.track(Test())
w._items.observable.insert(1, "b")  # ["a", "b", "c"]

# Modify item at new index 2 (was index 1 before insert)
w._items.observable[2] = "C"
assert repeater.widget_at(2).text() == "C"
assert repeater.widget_at(1).text() == "b"
```
