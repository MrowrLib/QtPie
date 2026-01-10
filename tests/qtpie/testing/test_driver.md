# QtDriver Test Harness

## Widget Tracking and Interaction

`QtDriver` provides a test harness for Qt widgets. Use `qt.track()` to register widgets for cleanup and `qt.click()` to simulate button clicks.

```python
def test_raw_widget_click(qt: QtDriver) -> None:
    """Verify QtDriver.click() works with raw QPushButton."""
    widget = RawWidgetExample()
    qt.track(widget)

    qt.click(widget.button)

    assert_that(widget.click_count).is_equal_to(1)
    assert_that(widget.label.text()).is_equal_to("Count: 1")
```

```python
def test_raw_widget_multiple_clicks(qt: QtDriver) -> None:
    """Verify multiple clicks accumulate correctly."""
    widget = RawWidgetExample()
    qt.track(widget)

    qt.click(widget.button)
    qt.click(widget.button)
    qt.click(widget.button)

    assert_that(widget.click_count).is_equal_to(3)
    assert_that(widget.label.text()).is_equal_to("Count: 3")
```
