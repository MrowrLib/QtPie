from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableView,
    QTabWidget,
)

from forc.domain.models import (
    API_KEY_LOCATION_LABELS,
    AUTH_TYPE_LABELS,
    BODY_TYPE_LABELS,
    ApiKeyLocation,
    AuthType,
    BodyType,
    KeyValue,
    Request,
)
from forc.domain.models.auth import ApiKeyAuth
from qtpie import Stretch, Widget, new, widget


@widget(title="Actions")
class DeleteWidget(Widget[KeyValue]):
    delete: QPushButton = new(
        "🗑️", clicked="{on_delete(record)}", styleSheet="background: none; border: none; padding: 0;"
    )


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget[Request]):
    _method: QLabel = new(bind="method?.name")
    _url: QLineEdit = new(bind="url", placeholderText="Enter request URL...")
    _send: QPushButton = new("Send", clicked="{on_send_request(record)}")


@widget(title="Params", on_delete="_on_delete")
class ParamsTabContent(Widget[Request]):
    ### Signals ###
    on_delete = Signal(KeyValue)

    ### Widgets ###
    header: QLabel = new("Query Parameters:")
    add_button: QPushButton = new("+ Add", clicked="_on_add")
    table: QTableView = new(bind="record.query_params", columns=["key", "value", DeleteWidget])

    ### Methods ###
    def _on_delete(self, param: KeyValue):
        self.record.query_params.remove(param)

    def _on_add(self):
        self.record.query_params.append(KeyValue())


@widget(title="Headers")
class HeadersTabContent(Widget[Request]):
    _table: QTableView = new(bind="headers")  # , editable=True)


# class AuthType(Enum):
#     NONE = "none"
#     BASIC = "basic"
#     BEARER = "bearer"
#     API_KEY = "api_key"


@widget(title="Auth")
class AuthTabContent(Widget[Request]):
    ### Variables ###
    # _api_key_locations: Variable[list[str]] = new(["header", "query"])

    # _api_key_locations: dict[str, str] = new({ "header": "Header", "query": "Query Parameter" })

    ### Widgets ###
    _auth_type: QComboBox = new(bind=AuthType, format=AUTH_TYPE_LABELS.get, selectedItem="auth?.type")
    _auth_fields_layout: QFormLayout
    _stretch: Stretch

    ### Basic Auth ###
    _basic_username: QLineEdit = new(
        bind="auth?.username", layout="_auth_fields_layout", label="Username:", visible="{auth?.type == AuthType.BASIC}"
    )
    _basic_password: QLineEdit = new(
        bind="auth?.password",
        layout="_auth_fields_layout",
        label="Password:",
        visible="{auth?.type == AuthType.BASIC}",
    )

    ### Bearer Auth ###
    _bearer_token: QLineEdit = new(
        bind="auth?.token", layout="_auth_fields_layout", label="Token:", visible="{auth?.type == AuthType.BEARER}"
    )

    ### API Key Auth ###
    _api_key_key: QLineEdit = new(
        bind="auth?.key", layout="_auth_fields_layout", label="Key:", visible="{auth?.type == AuthType.API_KEY}"
    )
    _api_key_value: QLineEdit = new(
        bind="auth?.value", layout="_auth_fields_layout", label="Value:", visible="{auth?.type == AuthType.API_KEY}"
    )
    _api_key_location: QComboBox = new(
        bind=ApiKeyLocation,
        format=API_KEY_LOCATION_LABELS.get,
        layout="_auth_fields_layout",
        label="Location:",
        selectedItem="auth?.location",
        visible="{auth?.type == AuthType.API_KEY}",
        currentIndexChanged="_on_api_key_location_changed",
    )
    # ... more API key stuff ...

    def _on_api_key_location_changed(self) -> None:
        if self.record.auth is not None and isinstance(self.record_value.auth, ApiKeyAuth):
            print(f"API Key location changed to: {self.record_value.auth.location}")


@widget(title="Body", on_delete="_on_delete")
class BodyTabContent(Widget[Request]):
    ### Signals ###
    on_delete = Signal(KeyValue)

    ### Widgets ###
    _body_type: QComboBox = new(bind=BodyType, format=BODY_TYPE_LABELS.get, selectedItem="body_type")
    _body_content: QPlainTextEdit = new(
        bind="body",
        visible="{body_type in [BodyType.TEXT, BodyType.JSON, BodyType.XML]}",
    )
    _body_fields_add_button: QPushButton = new(
        "+ Add Field",
        clicked="_on_add_body_field",
        visible="{body_type in [BodyType.FORM_DATA, BodyType.FORM_URLENCODED]}",
    )
    _body_fields: QTableView = new(
        bind="body_fields",
        visible="{body_type in [BodyType.FORM_DATA, BodyType.FORM_URLENCODED]}",
        columns=["key", "value", DeleteWidget],
    )
    _stretch: Stretch

    ### Methods ###
    def _on_add_body_field(self) -> None:
        self.record.body_fields.append(KeyValue())

    def _on_delete(self, field: KeyValue) -> None:
        self.record.body_fields.remove(field)


@widget
class RequestEditorWidget(Widget[Request]):
    ### Widgets ###
    _address_bar: RequestAddressBarWidget
    _tabs: QTabWidget = new(tabs=[ParamsTabContent, BodyTabContent, AuthTabContent, HeadersTabContent])
