from qtpy.QtWidgets import QSplitter

from forc2.app.widgets.request_editor import RequestEditorWidget
from forc2.app.widgets.response_viewer import ResponseViewerWidget
from forc2.domain.request import Request
from forc2.domain.response import Response
from qtpie import Event, Var, Widget, new, widget


@widget
class RequestWidget(Widget[Request]):
    ### Events ###
    on_send_request: Event = new(on="_on_send_request")

    ### Variables ###
    response: Var[Response | None] = new(None)
    is_sending: Var[bool] = new(False)

    ### Widgets ###
    splitter: QSplitter = new(bind="request_splitter_orientation")
    request_editor: RequestEditorWidget = new(splitter="splitter")
    response_viewer: ResponseViewerWidget = new(bind="response", splitter="splitter")

    ### Methods ###
    def __setup__(self) -> None:
        self.splitter.setSizes([1000, 1000])

    def _on_send_request(self) -> None:
        print("Sending request...", self.record_value)
        self.is_sending = True
        ...
        self.is_sending = False
