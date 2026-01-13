from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton

from forc.domain.models import Request
from qtpie import Widget, new, widget


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget[Request]):
    _method: QLabel = new(bind="method?.name")
    _url: QLineEdit = new(bind="url", placeholderText="Enter request URL...")
    _send: QPushButton = new("Send")
