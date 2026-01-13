from qtpy.QtWidgets import QLabel

from forc.domain.models.core import Request
from qtpie import Widget, new, widget

from .request_address_bar_widget import RequestAddressBarWidget
from .request_tabs_widget import RequestTabsWidget

_ = Request  # to avoid unused import removal


@widget
class RequestEditorWidget(Widget):
    """Central widget for editing a request. Contains address bar and tabs."""

    _select_request_header: QLabel = new("Requests", visible="{not isinstance(selected_collection_item, Request)}", stylesheet="font-size: 18pt; font-weight: bold;")
    _select_request_message: QLabel = new(
        "Select a request from the collections tree to view or edit it.", visible="{not isinstance(selected_collection_item, Request)}", stylesheet="font-size: 12pt; font-style: italic;"
    )
    _address_bar: RequestAddressBarWidget = new(visible="{isinstance(selected_collection_item, Request)}")
    _tabs: RequestTabsWidget = new(visible="{isinstance(selected_collection_item, Request)}")
