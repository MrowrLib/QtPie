from qtpy.QtWidgets import QLabel

from forc2.domain.response import Response
from qtpie import Widget, new, widget

# TODO --> copy the response_viewer stuff from forc1


@widget
class ResponseViewerWidget(Widget[Response]):
    label: QLabel = new(bind="Response Viewer Placeholder for {status_code}")
