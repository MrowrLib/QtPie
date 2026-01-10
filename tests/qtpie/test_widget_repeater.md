# WidgetRepeater Tests

## Basic WidgetRepeater Creation

Creates one widget per list item. Empty lists create no widgets.

```python
@widget
class Test(Widget):
    _numbers: Variable[list[int], QLineEdit] = new([1, 2, 3])

w = qt.track(Test())

# Should create a WidgetRepeater
assert isinstance(w._numbers.widget, WidgetRepeater)

# Should have 3 widgets
repeater: WidgetRepeater[int] = w._numbers.widget
assert repeater.widget_count() == 3
```

## Granular List Synchronization

Supports insert, remove, replace, and clear operations with automatic widget management.

```python
@widget
class Test(Widget):
    _items: Variable[list[str], QLineEdit] = new(["a", "b"])

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._items.widget

# Append to list
w._items.observable.append("c")
assert repeater.widget_count() == 3

# Insert at index 1
w._items.observable.insert(1, "b")

# Remove from list
w._items.observable.remove("b")

# Replace via index assignment
w._items.observable[0] = "new"

# Clear the list
w._items.observable.clear()
assert repeater.widget_count() == 0
```

## Primitive Type Binding

Two-way binding between widgets and list items for primitives (int, str, etc.).

```python
@widget
class Test(Widget):
    _numbers: Variable[list[int], QSpinBox] = new([1, 2, 3])

w = qt.track(Test())
repeater: WidgetRepeater[int] = w._numbers.widget

# Change spinbox value
spin = repeater.widget_at(1)
spin.setValue(99)

# List should be updated
assert w._numbers.observable[1] == 99

# Change list item
w._numbers.observable[0] = 50

# Widget updates automatically
```

```python
@widget
class Test(Widget):
    _names: Variable[list[str], QLineEdit] = new(["Alice", "Bob"])

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._names.widget

# Edit widget
edit = repeater.widget_at(0)
edit.setText("Charlie")

# List updated
assert w._names.observable[0] == "Charlie"

# Change list
w._names.observable[1] = "Diana"

# Widget updated
assert repeater.widget_at(1).text() == "Diana"
```

## Object Property Binding

Bind specific properties of complex objects using format strings.

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    _dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3), Dog("Snoopy", 5)])(bind="{name}")

w = qt.track(Test())
repeater: WidgetRepeater[Dog] = w._dogs.widget

assert repeater.widget_at(0).text() == "Rover"
assert repeater.widget_at(1).text() == "Snoopy"
```

```python
@widget
class Test(Widget):
    _dogs: Variable[list[Dog], QLineEdit] = new([Dog("Rover", 3)])(bind="{name}")

w = qt.track(Test())
repeater: WidgetRepeater[Dog] = w._dogs.widget

# Edit widget → updates object
edit = repeater.widget_at(0)
edit.setText("Max")
assert w._dogs.observable[0].name == "Max"
```

## Multi-Property Format Strings

Combine multiple properties in display strings.

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    _dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3), Dog("Snoopy", 5)])(bind="{name} is {age} years old")

w = qt.track(Test())
repeater: WidgetRepeater[Dog] = w._dogs.widget

assert repeater.widget_at(0).text() == "Rover is 3 years old"
assert repeater.widget_at(1).text() == "Snoopy is 5 years old"
```

## Special Placeholders

Special placeholders `{#index}`, `{#self}` for advanced formatting.

```python
@widget
class Test(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b", "c"])(bind="{#index}")

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._items.widget

assert repeater.widget_at(0).text() == "0"
assert repeater.widget_at(1).text() == "1"
assert repeater.widget_at(2).text() == "2"
```

```python
@widget
class Test(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "b"])(bind="Index {#index}: {#self}")

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._items.widget

assert repeater.widget_at(0).text() == "Index 0: a"
assert repeater.widget_at(1).text() == "Index 1: b"
```

## Index Management After Mutations

Widgets remain bound to correct items after insert/remove operations.

```python
@widget
class Test(Widget):
    _items: Variable[list[str], QLabel] = new(["a", "c"])

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._items.widget

# Insert "b" at index 1
w._items.observable.insert(1, "b")

# Now change item at index 2 (was index 1 before)
w._items.observable[2] = "C"

# Third widget should show "C"
assert repeater.widget_at(2).text() == "C"
# Second widget should still show "b"
assert repeater.widget_at(1).text() == "b"
```

## Widget Configuration

Widget kwargs applied to all repeater children, including newly added ones.

```python
@widget
class Test(Widget):
    _names: Variable[list[str], QLineEdit] = new(["a", "b"])(maxLength=5)

w = qt.track(Test())
repeater: WidgetRepeater[str] = w._names.widget

# Each QLineEdit should have maxLength=5
edit1 = repeater.widget_at(0)
edit2 = repeater.widget_at(1)
assert edit1.maxLength() == 5
assert edit2.maxLength() == 5

# Also newly added widgets get kwargs
w._names.observable.append("c")
edit3 = repeater.widget_at(2)
assert edit3.maxLength() == 5
```

## Dict Binding with list[QWidget]

Bind `list[QWidget]` to dict variables using `DictWidgetRepeater`.

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    _dogs_dict: Variable[dict[str, Dog]] = new({"Fido": Dog("Fido", 3), "Rex": Dog("Rex", 5)})
    _labels: list[QLabel] = new(bind="_dogs_dict", format="{#key} is {age} years old")

w = qt.track(Test())

from qtpie import DictWidgetRepeater
assert isinstance(w._labels, DictWidgetRepeater)
assert w._labels.widget_count() == 2
```

```python
@widget
class Test(Widget):
    _dogs: Variable[dict[str, Dog]] = new({"Fido": Dog("Fido", 3)})
    _labels: list[QLabel] = new(bind="_dogs", format="{#key}: {name} is {age}")

w = qt.track(Test())

label = w._labels.widget_for_key("Fido")
assert label.text() == "Fido: Fido is 3"
```

## Format Parameter for list[QWidget]

Use `format=` with string templates or callables for list widget bindings.

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
    _labels: list[QLabel] = new(bind="_dogs", format="{name} is {age} years old")

w = qt.track(Test())

from qtpie import WidgetRepeater
assert isinstance(w._labels, WidgetRepeater)
assert w._labels.widget_at(0).text() == "Fido is 3 years old"
assert w._labels.widget_at(1).text() == "Rex is 5 years old"
```

```python
@widget
class Test(Widget):
    _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
    _labels: list[QLabel] = new(bind="_dogs", format=lambda d: f"{d.name.upper()} - {d.age}")

w = qt.track(Test())

assert w._labels.widget_at(0).text() == "FIDO - 3"
```
