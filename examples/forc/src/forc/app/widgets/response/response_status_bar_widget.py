from qtpy.QtWidgets import QLabel

from qtpie import Widget, new, widget


@widget(layout="horizontal")
class ResponseStatusBarWidget(Widget):
    """Status code, response time, and size display."""

    _status: QLabel = new("---")
    _time: QLabel = new("0 ms")
    _size: QLabel = new("0 B")
