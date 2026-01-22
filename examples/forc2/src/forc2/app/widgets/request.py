from qtpy.QtWidgets import QLabel

from forc2.domain.request import Request
from forc2.domain.response import Response
from qtpie import Event, Var, Widget, new, widget


@widget
class RequestWidget(Widget[Request]):
    hello: QLabel = new(bind="Request Widget Placeholder for {name}")

    ### Events ###
    on_send_request: Event

    ### Variables ###
    response: Var[Response | None] = new(None)
    is_sending: Var[bool] = new(False)

    ### Widgets ###
