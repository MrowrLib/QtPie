from forc.app.widgets.requests import RequestAddressBarWidget
from forc.app.widgets.requests.request_tabs_widget import RequestTabsWidget
from forc.domain.models.core import Request
from qtpie import Widget, new, widget


@widget
class RequestEditorWidget(Widget[Request]):
    _address_bar: RequestAddressBarWidget = new(bind="record")
    _tabs: RequestTabsWidget = new(bind="record")
