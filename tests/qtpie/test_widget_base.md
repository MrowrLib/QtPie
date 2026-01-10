# WidgetBase Tests

## `__setup__` Lifecycle Hook

Runs after `__init__` completes, allowing post-initialization setup with full access to initialized fields.

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
        # Qt widget is fully initialized
        self.setWindowTitle("Test")
```

## Variable Fields Without Decorator

`Variable[T]` fields work reactively on any class using `WidgetBase`, no `@widget` decorator required.

```python
class MyWidget(MockWidget, WidgetBase):
    _name: Variable[str] = new("")

obj = MyWidget()
obj._name.value = "hello"
assert_that(obj._name.value).is_equal_to("hello")
```

```python
class MyWidget(MockWidget, WidgetBase):
    _count: Variable[int] = new(0)

obj = MyWidget()
received: list[int] = []
observable = cast(Observable[int], obj._count.observable)
observable.on_change(lambda v: received.append(v))

obj._count.value = 1
obj._count.value = 2

assert_that(received).is_equal_to([1, 2])
```

## Qt Widget Instantiation

Non-Variable `new()` fields instantiate Qt widgets (or other objects).

```python
class MyWidget(QWidget, WidgetBase):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click me")

w = qt.track(MyWidget())
assert_that(w._label.text()).is_equal_to("Hello")
assert_that(w._button.text()).is_equal_to("Click me")
```

## Works with Any Qt Subclass

`WidgetBase` can be mixed into any Qt widget class, not just `QWidget`.

```python
class MyListView(QListView, WidgetBase):
    _items: Variable[list[str]] = new([])

    def __setup__(self) -> None:
        self._items.value = ["one", "two", "three"]

view = qt.track(MyListView())
assert_that(view._items.value).is_equal_to(["one", "two", "three"])
```
