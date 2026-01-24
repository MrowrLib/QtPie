from qtpy.QtWidgets import QLabel, QTabWidget

from forc2.domain.response import Response
from qtpie import Stretch, Widget, new, widget

# TODO --> copy the response_viewer stuff from forc1


@widget(layout="horizontal")
class ResponseStatsWidget(Widget[Response]):
    _status: QLabel = new(bind="Status: {status_code} {status_text}", classes=["status-badge", "status-{status_code // 100}xx"])
    _time: QLabel = new(bind="Time: {time_ms:.2f} ms")
    _size: QLabel = new(bind="Size: {size_bytes} bytes")


@widget
class ResponseHeadersWidget(Widget[Response]):
    ### Widgets ###
    _headers: QLabel = new(bind="{headers}")


@widget
class ResponseViewerWidget(Widget[Response]):
    ### Widgets ###
    _stats: ResponseStatsWidget
    _tabs: QTabWidget = new(tabs=[ResponseHeadersWidget])
    _stretch: Stretch
