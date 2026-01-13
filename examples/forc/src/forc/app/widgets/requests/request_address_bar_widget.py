from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton

from qtpie import Widget, new, widget


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget):
    """HTTP method selector, URL input, and Send button."""

    # Placeholder - will use Variable[HttpMethod] later
    _method: QLabel = new("[GET v]")
    _url: QLineEdit = new(placeholderText="Enter request URL...")
    _send: QPushButton = new("Send")
