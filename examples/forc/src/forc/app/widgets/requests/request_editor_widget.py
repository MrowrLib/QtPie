from forc.app.widgets.requests import RequestAddressBarWidget
from forc.app.widgets.requests.request_tabs_widget import RequestTabsWidget
from forc.domain.models.core import Request
from qtpie import Widget, widget


@widget
class RequestEditorWidget(Widget[Request]):
    ### Widgets ###
    _address_bar: RequestAddressBarWidget
    _tabs: RequestTabsWidget
