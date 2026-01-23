from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QTableView, QTabWidget

from forc2.domain.request import HttpMethod, Request
from qtpie import Stretch, Widget, new, widget


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget[Request]):
    ### Widgets ###
    request_method: QComboBox = new(bind=HttpMethod, selectedItem="method")
    request_url: QLineEdit = new(bind="url", placeholderText="Enter request URL...")
    send_request_button: QPushButton = new("Send", clicked="on_send_request", enabled="{not is_sending}")


@widget(title="Params")
class RequestParamsWidget(Widget[Request]):
    ### Widgets ###
    header: QLabel = new("Query Parameters:")


@widget(title="Headers")
class RequestHeadersWidget(Widget[Request]):
    ### Widgets ###
    header: QLabel = new("Headers:")
    table: QTableView = new(bind="headers")


@widget(title="Auth")
class RequestAuthWidget(Widget[Request]):
    ### Widgets ###
    header: QLabel = new("Authentication:")


@widget(title="Body")
class RequestBodyWidget(Widget[Request]):
    ### Widgets ###
    header: QLabel = new("Body:")


@widget
class RequestEditorWidget(Widget[Request]):
    ### Widgets ###
    address_bar: RequestAddressBarWidget
    request_tabs: QTabWidget = new(
        tabs=[
            RequestParamsWidget,
            RequestHeadersWidget,
            RequestAuthWidget,
            RequestBodyWidget,
        ]
    )
    stretch: Stretch
