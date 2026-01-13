from qtpie import Widget, new, widget

from .request_address_bar_widget import RequestAddressBarWidget
from .request_tabs_widget import RequestTabsWidget


@widget
class RequestEditorWidget(Widget):
    """Central widget for editing a request. Contains address bar and tabs."""

    _address_bar: RequestAddressBarWidget = new()
    _tabs: RequestTabsWidget = new()
