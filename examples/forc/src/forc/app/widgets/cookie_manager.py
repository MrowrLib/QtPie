from qtpy.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView

from forc.services import HttpClientService
from qtpie import Dialog, DialogButton, Stretch, Variable, Widget, dialog, new, widget


@widget
class CookieManagerWidget(Widget):
    ### Services ###
    http_client_service: Variable[HttpClientService]

    ### Widgets ###
    tool_row: QHBoxLayout
    cookies_table: QTableView = new(
        bind="http_client_service.cookies",
        filter="not {cookie_search} or {cookie_search.lower()} in {name.lower()}",
        visible="{len(http_client_service.cookies) > 0}",
    )
    cookie_count_label: QLabel = new(bind="Cookies stored: {len(http_client_service.cookies)}")

    ### Tool Row Widgets ###
    cookie_search: Variable[str, QLineEdit] = new("")(
        placeholderText="Search cookies...",
        enabled="{len(http_client_service.cookies) > 0}",
        layout="tool_row",
    )
    add_button: QPushButton = new(
        "+ Add Cookie",
        clicked="{http_client_service.add_cookie()}",
        layout="tool_row",
    )
    delete_all_button: QPushButton = new(
        "Delete All",
        clicked="{http_client_service.clear_cookies()}",
        enabled="{len(http_client_service.cookies) > 0}",
        layout="tool_row",
    )


@dialog(size=(900, 600), title="Cookie Manager")
class CookieManagerDialog(Dialog):
    _header: QLabel = new("Cookie Manager")
    _cookie_manager: CookieManagerWidget
    _stretch: Stretch
    _ok: DialogButton
