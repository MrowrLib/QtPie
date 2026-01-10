# test_widget_base.py

Tests for the `WidgetBase` mixin - the foundation for adding reactive Variables to any Python class.

## __setup__ Lifecycle Hook

`__setup__()` is called after `__init__()` completes, allowing safe access to fully-initialized objects.

```python
class MyWidget(MockWidget, WidgetBase):
    def __setup__(self) -> None:
        call_order.append("setup")

MyWidget()
assert_that(call_order).is_equal_to(["init", "setup"])
```

```python
class MyWidget(QWidget, WidgetBase):
    def __setup__(self) -> None:
        # Qt widget is fully initialized, can call Qt methods
        self.setWindowTitle("Test")
```

## Variable Fields

`Variable[T]` fields work automatically without requiring a decorator.

```python
class MyWidget(MockWidget, WidgetBase):
    _name: Variable[str] = new("")

obj = MyWidget()
obj._name.value = "hello"
assert_that(obj._name.value).is_equal_to("hello")
```

Variables are fully reactive:

```python
class MyWidget(MockWidget, WidgetBase):
    _count: Variable[int] = new(0)

obj = MyWidget()
observable = cast(Observable[int], obj._count.observable)
observable.on_change(lambda v: received.append(v))

obj._count.value = 1
obj._count.value = 2
assert_that(received).is_equal_to([1, 2])
```

## Non-Variable Field Instantiation

`new()` instantiates any class, not just Variables.

```python
class Counter:
    def __init__(self, start: int = 0) -> None:
        self.value = start

class MyWidget(MockWidget, WidgetBase):
    _counter: Counter = new(start=10)

obj = MyWidget()
assert_that(obj._counter.value).is_equal_to(10)
```

## Works with Any Qt Widget

`WidgetBase` can be mixed into any Qt widget class.

```python
class MyListView(QListView, WidgetBase):
    _items: Variable[list[str]] = new([])

    def __setup__(self) -> None:
        self._items.value = ["one", "two", "three"]

view = qt.track(MyListView())
assert_that(view._items.value).is_equal_to(["one", "two", "three"])
```

Can mix Variables with instantiated Qt widgets:

```python
class MyWidget(QWidget, WidgetBase):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click me")
    _clicked_count: Variable[int] = new(0)

    def __setup__(self) -> None:
        self._button.clicked.connect(self._on_click)

    def _on_click(self) -> None:
        self._clicked_count.value += 1
```
