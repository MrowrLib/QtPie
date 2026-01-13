from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton

from qtpie import Widget, new, widget


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget):
    _method: QLabel = new(bind="{collection_item?.method?.name}")
    _url: QLineEdit = new(bind="collection_item?.url")
    _send: QPushButton = new("Send")

    # , placeholderText="Enter request URL...")
