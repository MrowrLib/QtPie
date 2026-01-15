from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSplitter

from forc.app.widgets.response import ResponseViewerWidget
from forc.domain.models import Request
from qtpie import Widget, new, widget

from .request_editor_widget import RequestEditorWidget


@widget
class RequestWidget(Widget[Request]):
    """Contains both request editor and response viewer for a single request."""

    _splitter: QSplitter = new(Qt.Orientation.Horizontal)
    _editor: RequestEditorWidget = new(bind="record", splitter="_splitter")
    _response: ResponseViewerWidget = new(splitter="_splitter")

    def __setup__(self) -> None:
        self._splitter.setSizes([200, 100])
