from qtpy.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView

from forc.services import HttpClientService
from qtpie import Variable, Widget, new, widget


@widget
class CookieManagerWidget(Widget):
    ### Services ###
    http_client_service: Variable[HttpClientService]

    ### Widgets ###
    tool_row: QHBoxLayout
    cookies_table: QTableView = new(
        bind="http_client_service?.cookies",
        filter="not {cookie_search} or {cookie_search.lower()} in {name.lower()}",
        visible="{len(http_client_service?.cookies) > 0}",
    )
    cookie_count_label: QLabel = new(bind="Cookies stored: {len(http_client_service.cookies)}")

    ### Tool Row Widgets ###
    cookie_search: Variable[str, QLineEdit] = new("")(
        placeholderText="Search cookies...",
        visible="{len(http_client_service?.cookies) > 0}",
        layout="tool_row",
    )
    add_button: QPushButton = new(
        "+ Add Cookie",
        clicked="_on_add_cookie",
        layout="tool_row",
    )
    delete_all_button: QPushButton = new(
        "Delete All",
        clicked="_on_delete_all",
        visible="{len(http_client_service?.cookies) > 0}",
        layout="tool_row",
    )

    ### Methods ###
    def _on_add_cookie(self) -> None:
        self.http_client_service().add_cookie()

    def _on_delete_all(self) -> None:
        self.http_client_service().clear_cookies()
