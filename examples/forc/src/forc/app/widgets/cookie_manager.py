from qtpy.QtWidgets import QLabel, QLineEdit, QTableView

from forc.services import HttpClientService
from qtpie import Variable, Widget, new, widget


@widget
class CookieManagerWidget(Widget):
    ### Services ###
    http_client_service: Variable[HttpClientService]

    ### Widgets ###
    cookie_search: Variable[str, QLineEdit] = new(placeholderText="Search cookies...")
    cookies_table: QTableView = new(bind="http_client_service?.cookies")  # , filter="{name} in {cookie_search}")
    cookie_count_label: QLabel = new(bind="Cookies stored: {len(http_client_service.cookies)}")

    label2: QLabel = new("Not Optional:")
    cookies_table_two: QTableView = new(bind="http_client_service.cookies")
