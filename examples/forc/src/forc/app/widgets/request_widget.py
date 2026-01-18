from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QSplitter

from forc.app.widgets.response_viewer_widget import ResponseViewerWidget
from forc.domain.models import Request, Response
from forc.services import HttpClientService
from qtpie import Variable, Widget, new, widget

from .request_editor_widget import RequestEditorWidget


@widget(on_send_request="_on_send_request")
class RequestWidget(Widget[Request]):
    ### Signals ###
    on_send_request = Signal(Request)

    ### Services ###
    http_client_service: Variable[HttpClientService]

    ### Variables ###
    response: Variable[Response | None] = new(None)

    ### Widgets ###
    _splitter: QSplitter = new(Qt.Orientation.Horizontal)
    request_editor: RequestEditorWidget = new(splitter="_splitter")
    response_viewer: ResponseViewerWidget = new(bind="response", splitter="_splitter")

    ### Methods ###
    def __setup__(self) -> None:
        self._splitter.setSizes([1000, 1000])

    def _on_send_request(self, request: Request) -> None:
        self.response = self.http_client_service.value.send(request)
