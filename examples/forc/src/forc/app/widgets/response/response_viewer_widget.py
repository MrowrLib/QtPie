from qtpy.QtWidgets import QLabel, QPlainTextEdit, QTableView

from forc.domain.models import Response
from qtpie import Widget, new, widget


@widget(layout="horizontal")
class ResponseStatusBarWidget(Widget[Response]):
    _status: QLabel = new(bind="Status: {status_code} {status_text}")
    _time: QLabel = new(bind="Time: {time_ms:.2f} ms")
    _size: QLabel = new(bind="Size: {size_bytes} bytes")


@widget(title="Body")
class ResponseBodyTabContent(Widget[Response]):
    _body: QPlainTextEdit = new(
        bind="{body.decode('utf-8', errors='ignore')}",
        content_type="{headers['content-type']}",
        readOnly=True,
    )


@widget(title="Headers")
class ResponseHeadersTabContent(Widget[Response]):
    _headers_label: QLabel = new(bind="{headers}")  # binds to the headers successfully

    _label_above: QLabel = new("ABOVE")
    _headers_xxx: list[QLabel] = new(bind="headers", format="HEADER: {#key}: {#value}")  # THIS WORKS NOW
    _label_below: QLabel = new("BELOW")

    _headers_table: QTableView = new(bind="headers")  # DOES NOT WORK


@widget(title="Cookies")
class ResponseCookiesTabContent(Widget[Response]):
    _placeholder: QLabel = new("Response cookies placeholder")


@widget
class ResponseViewerWidget(Widget[Response]):
    # _lbl1: QLabel = new("OUTSIDE OF TABS")
    _headers_outside_of_tab: ResponseHeadersTabContent
    # _lbl2: QLabel = new("INSIDE OF TABS")
    _headers_xxx: list[QLabel] = new(bind="headers", format="HEADER: {#key}: {#value}")  # nothing shows up!
    # _status_bar: ResponseStatusBarWidget
    # _tabs: QTabWidget = new(tabs=[ResponseBodyTabContent, ResponseHeadersTabContent, ResponseCookiesTabContent])
