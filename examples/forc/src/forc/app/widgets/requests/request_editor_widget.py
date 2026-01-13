from qtpy.QtWidgets import QLabel

from forc.app.widgets.requests import RequestAddressBarWidget
from forc.domain.models.core import Request
from qtpie import Widget, new, widget


@widget
class RequestEditorWidget(Widget[Request]):
    """Central widget for editing a request. Contains address bar and tabs."""

    # This works...
    label: QLabel = new(bind="Request {name}")

    # This isn't working ...
    _address_bar: RequestAddressBarWidget = new(bind="record")

    # _select_request_header: QLabel = new(
    #     "Requests",
    #     visible="{not isinstance(collection_item, Request)}",
    #     stylesheet="font-size: 18pt; font-weight: bold;",
    # )
    # _select_request_message: QLabel = new(
    #     "Select a request from the collections tree to view or edit it.",
    #     visible="{not isinstance(collection_item, Request)}",
    #     stylesheet="font-size: 12pt; font-style: italic;",
    # )
    # _tabs: RequestTabsWidget = new(
    #     visible="{isinstance(collection_item, Request)}",
    # )
