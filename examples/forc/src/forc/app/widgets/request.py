from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QSplitter

from forc.app.widgets.response_viewer import ResponseViewerWidget
from forc.domain.models import Request, Response
from forc.services import HttpClientService
from qtpie import Variable, Widget, new, slot, widget

from .request_editor_widget import RequestEditorWidget


@widget(on_send_request="_on_send_request")
class RequestWidget(Widget[Request]):
    ### Signals ###
    on_send_request = Signal(Request)

    ### Services ###
    http_client_service: Variable[HttpClientService]

    ### Variables ###
    response: Variable[Response | None] = new(None)
    is_sending: Variable[bool] = new(False)

    ### Widgets ###
    splitter: QSplitter = new(Qt.Orientation.Horizontal)
    request_editor: RequestEditorWidget = new(splitter="_splitter")
    response_viewer: ResponseViewerWidget = new(bind="response", splitter="_splitter")

    ### Methods ###
    @slot
    async def _on_send_request(self, request: Request) -> None:
        self.is_sending = True
        try:
            self.response = await self.http_client_service.value.send(request)
        finally:
            self.is_sending = False
