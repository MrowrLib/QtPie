"""Meta-tests for QtDriver - verify the test harness works with raw Qt."""

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from qtpie.testing import QtDriver


class RawWidgetExample(QWidget):
    """A raw QWidget with no QtPie magic - just plain Qt."""

    def __init__(self) -> None:
        super().__init__()
        self.click_count = 0

        layout = QVBoxLayout(self)

        self.label = QLabel("Count: 0")
        layout.addWidget(self.label)

        self.button = QPushButton("Click me")
        self.button.clicked.connect(self._on_click)
        layout.addWidget(self.button)

    def _on_click(self) -> None:
        self.click_count += 1
        self.label.setText(f"Count: {self.click_count}")


def test_raw_widget_creation(qt: QtDriver) -> None:
    """Verify we can create and track a raw QWidget."""
    widget = RawWidgetExample()
    qt.track(widget)

    assert_that(widget.label.text()).is_equal_to("Count: 0")
    assert_that(widget.click_count).is_equal_to(0)


def test_raw_widget_click(qt: QtDriver) -> None:
    """Verify QtDriver.click() works with raw QPushButton."""
    widget = RawWidgetExample()
    qt.track(widget)

    qt.click(widget.button)

    assert_that(widget.click_count).is_equal_to(1)
    assert_that(widget.label.text()).is_equal_to("Count: 1")


def test_raw_widget_multiple_clicks(qt: QtDriver) -> None:
    """Verify multiple clicks accumulate correctly."""
    widget = RawWidgetExample()
    qt.track(widget)

    qt.click(widget.button)
    qt.click(widget.button)
    qt.click(widget.button)

    assert_that(widget.click_count).is_equal_to(3)
    assert_that(widget.label.text()).is_equal_to("Count: 3")
