from qtpy.QtWidgets import QLabel

from forc2.domain.response import Response
from qtpie import Widget, new, widget


@widget
class ResponseViewerWidget(Widget[Response]):
    label: QLabel = new(bind="Response Viewer Placeholder for {status_code}")
