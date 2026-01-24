# QtDriver Testing Utility

The `QtDriver` is QtPie's test harness for widget testing. It provides utilities for creating, tracking, and interacting with Qt widgets in tests.

## Importing QtDriver

```python
from qtpie.testing import QtDriver
```

## Using QtDriver as a Pytest Fixture

QtDriver is injected as a pytest fixture named `qt`:

```python
def test_my_widget(qt: QtDriver) -> None:
    widget = MyWidget()
    qt.track(widget)
```

## Tracking Widgets

Use `qt.track()` to register a widget with the test harness. This ensures proper lifecycle management:

```python
widget = RawWidgetExample()
qt.track(widget)
```

## Simulating User Interactions

### Click Events

Use `qt.click()` to simulate button clicks:

```python
qt.click(widget.button)
```

Multiple clicks can be chained:

```python
qt.click(widget.button)
qt.click(widget.button)
qt.click(widget.button)
```

## Works with Raw Qt Widgets

QtDriver works with plain Qt widgets, not just QtPie widgets:

```python
class RawWidgetExample(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.button = QPushButton("Click me")
        self.button.clicked.connect(self._on_click)
```

## Typical Test Pattern

1. Create widget instance
2. Track with `qt.track()`
3. Perform interactions with `qt.click()` etc.
4. Assert on widget state

```python
def test_widget_click(qt: QtDriver) -> None:
    widget = MyWidget()
    qt.track(widget)
    qt.click(widget.button)
    assert_that(widget.label.text()).is_equal_to("Count: 1")
```
