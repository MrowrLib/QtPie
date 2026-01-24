# Widget Base Usage Patterns

Analysis of `test_widget_base.py` - documenting QtPie framework usage patterns.

## WidgetBase Mixin Pattern

`WidgetBase` is a mixin class that enables QtPie features when applied to any Qt widget class. Use with the `@widget` decorator.

```python
@widget
class MyWidget(QWidget, WidgetBase):
    _title: Variable[str] = new("default")
```

## Subclassing Any Qt Widget

`WidgetBase` works with any Qt widget class, not just `QWidget`. Useful for custom views.

```python
@widget
class MyListView(QListView, WidgetBase):
    _items: Variable[list[str]] = new([])
```

## Variable Fields

Declare reactive state using `Variable[T]` type hints with `new()` factory.

```python
_name: Variable[str] = new("")
_count: Variable[int] = new(0)
_items: Variable[list[str]] = new([])
```

## Reading and Writing Variables

Access values via `.value` property.

```python
obj._name.value = "hello"
print(obj._name.value)
```

## Reactive Subscriptions

Variables expose an `Observable` for change subscriptions.

```python
observable = cast(Observable[int], obj._count.observable)
observable.on_change(lambda v: received.append(v))
```

## __setup__ Lifecycle Hook

`__setup__` is called after `__init__` completes. Qt widget is fully initialized at this point.

```python
def __setup__(self) -> None:
    self.setWindowTitle("Test")
    self._value.value = 42
```

## Non-Variable Field Instantiation

`new()` can instantiate any class, not just Variables or Qt widgets.

```python
class Counter:
    def __init__(self, start: int = 0) -> None:
        self.value = start

_counter: Counter = new(start=10)
```

## Mixing Qt Widgets and Variables

Combine instantiated Qt widgets with reactive Variables in the same class.

```python
@widget
class MyWidget(QWidget, WidgetBase):
    _label: QLabel = new("Hello")
    _button: QPushButton = new("Click me")
    _clicked_count: Variable[int] = new(0)
```

## Signal Connection in __setup__

Connect Qt signals to methods in `__setup__`.

```python
def __setup__(self) -> None:
    self._button.clicked.connect(self._on_click)

def _on_click(self) -> None:
    self._clicked_count.value += 1
```

## Testing with QtDriver

Use `QtDriver` fixture from `qtpie.testing` for widget tests. Track widgets for proper cleanup.

```python
def test_example(self, qt: QtDriver) -> None:
    w = qt.track(MyWidget())
    qt.click(w._button)
```
