from qtpy.QtWidgets import QLabel, QPlainTextEdit, QTableView, QTabWidget

from forc2.domain.response import Response
from qtpie import Computed, Stretch, Widget, new, widget


@widget(layout="horizontal")
class ResponseStatsWidget(Widget[Response]):
    ### Widgets ###
    _status: QLabel = new(bind="Status: {status_code} {status_text}", classes=["status-badge", "status-{status_code // 100}xx"])
    _time: QLabel = new(bind="Time: {time_ms:.2f} ms")
    _size: QLabel = new(bind="Size: {size_bytes} bytes")


@widget(title="Body")
class ResponseBodyWidget(Widget[Response]):
    ### Variables ###
    _content_type: Computed[str] = new("{headers['content-type'].split(';')[0] if 'content-type' in headers else ''}")

    ### Widgets ###
    _content_type_label: QLabel = new(bind="Content-Type: {_content_type}")
    _body_text: QPlainTextEdit = new(readOnly=True, content_type="{_content_type}")


@widget(title="Headers")
class ResponseHeadersWidget(Widget[Response]):
    ### Widgets ###
    _headers: QTableView


# TODO: only make this tab appear if there are cookies in the response
@widget(title="Cookies")
class ResponseCookiesWidget(Widget[Response]):
    ### Widgets ###
    _cookies: QTableView


@widget
class ResponseViewerWidget(Widget[Response]):
    ### Widgets ###
    _stats: ResponseStatsWidget
    _tabs: QTabWidget = new(tabs=[ResponseBodyWidget, ResponseHeadersWidget, ResponseCookiesWidget], visible="{record_value is not None}")
    _send_request_message: QLabel = new("Send a request to see the response.", visible="{record_value is None}")
    _stretch: Stretch
