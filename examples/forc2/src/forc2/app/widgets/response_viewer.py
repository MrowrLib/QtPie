from qtpy.QtWidgets import QLabel, QPlainTextEdit, QTableView, QTabWidget

from forc2.domain.response import Response
from qtpie import Stretch, Widget, new, widget

# TODO --> copy the response_viewer stuff from forc1


@widget(layout="horizontal")
class ResponseStatsWidget(Widget[Response]):
    _status: QLabel = new(bind="Status: {status_code} {status_text}", classes=["status-badge", "status-{status_code // 100}xx"])
    _time: QLabel = new(bind="Time: {time_ms:.2f} ms")
    _size: QLabel = new(bind="Size: {size_bytes} bytes")


# @dataclass
# class Response:
#     """HTTP response - runtime only, not persisted."""

#     status_code: int
#     status_text: str
#     headers: dict[str, str]
#     body: bytes
#     time_ms: float
#     size_bytes: int
#     cookies: list[Cookie] = field(default_factory=lambda: [])


@widget(title="Body")
class ResponseBodyWidget(Widget[Response]):
    ### Widgets ###
    content_type_label: QLabel = new(bind="Content-Type: {headers['content-type']}")
    body_text: QPlainTextEdit = new(bind="{body.decode('utf-8', errors='ignore')}", readOnly=True, content_type="{headers['content-type']}")


@widget(title="Headers")
class ResponseHeadersWidget(Widget[Response]):
    ### Widgets ###
    _headers: QTableView = new(bind="headers")


@widget(title="Cookies")
class ResponseCookiesWidget(Widget[Response]):
    ### Widgets ###
    _cookies: QTableView = new(bind="cookies")


@widget
class ResponseViewerWidget(Widget[Response]):
    ### Widgets ###
    _stats: ResponseStatsWidget
    _tabs: QTabWidget = new(tabs=[ResponseBodyWidget, ResponseHeadersWidget, ResponseCookiesWidget], visible="{record_value is not None}")
    _send_request_message: QLabel = new("Send a request to see the response.", visible="{record_value is None}")
    _stretch: Stretch
