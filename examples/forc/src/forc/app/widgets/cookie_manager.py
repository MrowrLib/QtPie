from qtpy.QtWidgets import QLabel, QLineEdit, QTableView

from forc.domain.models.response import Cookie
from forc.services import HttpClientService
from qtpie import Variable, Widget, new, widget


@widget
class CookieManagerWidget(Widget):
    ### Services ###
    http_client_service: Variable[HttpClientService]

    ### Widgets ###
    cookie_search: Variable[str, QLineEdit] = new()(
        placeholderText="Search cookies...",
        visible="{len(http_client_service?.cookies) > 0}",
    )
    cookies_table: QTableView = new(
        bind="http_client_service?.cookies",
        # filter="not {cookie_search} or {cookie_search.lower()} in {name.lower()}",
        # filter="filter_cookies",
        visible="{len(http_client_service?.cookies) > 0}",
    )
    cookie_count_label: QLabel = new(bind="Cookies stored: {len(http_client_service.cookies)}")

    def filter_cookies(self, cookie: Cookie) -> bool:
        print(f"Filtering cookie: {cookie.name}")
        search_term = self.cookie_search.value.lower()
        if not search_term:
            return True
        return search_term in cookie.name.lower() or search_term in cookie.value.lower()
