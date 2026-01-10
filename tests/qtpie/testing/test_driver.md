# QtDriver Test Harness

## Widget Tracking

Track raw Qt widgets for testing. Ensures proper cleanup after tests.

```python
def test_raw_widget_creation(qt: QtDriver) -> None:
    """Verify we can create and track a raw QWidget."""
    widget = RawWidgetExample()
    qt.track(widget)

    assert_that(widget.label.text()).is_equal_to("Count: 0")
    assert_that(widget.click_count).is_equal_to(0)
```

## Button Click Simulation

Simulate button clicks programmatically. Works with raw QPushButton instances.

```python
def test_raw_widget_click(qt: QtDriver) -> None:
    """Verify QtDriver.click() works with raw QPushButton."""
    widget = RawWidgetExample()
    qt.track(widget)

    qt.click(widget.button)

    assert_that(widget.click_count).is_equal_to(1)
    assert_that(widget.label.text()).is_equal_to("Count: 1")
```
