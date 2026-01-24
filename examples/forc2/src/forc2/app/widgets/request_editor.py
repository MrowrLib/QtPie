from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QTableView, QTabWidget

from forc2.domain.auth import API_KEY_LOCATION_LABELS, AUTH_TYPE_LABELS, ApiKeyLocation, Auth, AuthType
from forc2.domain.body import BODY_TYPE_LABELS, BodyType
from forc2.domain.request import HttpMethod, Request, RequestKeyValue
from qtpie import Event, Stretch, Widget, new, widget
from qtpie.variable import Var

# TODO: update all to use _private names for the widgets, simple names, but private to avoid conflicts with the record's attributes


@widget(classes=["delete-cell"])
class DeleteWidget[T](Widget[T]):
    ### Widgets ###
    _delete_button: QPushButton = new("🗑️", clicked="{on_delete(record)}", classes=["btn-icon", "btn-delete"])


@widget(title="Actions")
class DeleteRequestKeyValueWidget(DeleteWidget[RequestKeyValue]): ...


@widget(layout="horizontal", classes=["address-bar"], styledBackground=True, margins=0)
class RequestAddressBarWidget(Widget[Request]):
    ### Widgets ###
    _request_method_chooser: QComboBox = new(bind=HttpMethod, selectedItem="method", classes=["flat", "method-chooser"])
    _request_url: QLineEdit = new(bind="url", placeholderText="Enter request URL...", classes=["url-input"])
    _send_request_button: QPushButton = new("Send", clicked="on_send_request", enabled="{not is_sending}", classes=["btn-primary", "btn-send"])


@widget(title="Params", classes=["tab-content", "params-tab"])
class RequestParamsWidget(Widget[Request]):
    ### Events ###
    on_delete: Event[RequestKeyValue] = new(on="_on_delete")

    ### Widgets ###
    _header: QLabel = new("Query Parameters:", classes=["section-header"])
    _add_button: QPushButton = new("+ Add", clicked="_on_add", classes=["btn-add"])
    _table: QTableView = new(bind="query_params", appendColumns=[DeleteRequestKeyValueWidget], classes=["key-value-table"])

    ### Methods ###
    def _on_add(self) -> None:
        self.record.query_params.append(RequestKeyValue())

    def _on_delete(self, param: RequestKeyValue) -> None:
        self.record.query_params.remove(param)


@widget(title="Headers", classes=["tab-content", "headers-tab"])
class RequestHeadersWidget(Widget[Request]):
    ### Events ###
    on_delete: Event[RequestKeyValue] = new(on="_on_delete")

    ### Widgets ###
    _header: QLabel = new("Headers:", classes=["section-header"])
    _add_button: QPushButton = new("+ Add", clicked="_on_add", classes=["btn-add"])
    _table: QTableView = new(bind="headers", appendColumns=[DeleteRequestKeyValueWidget], classes=["key-value-table"])
    _stretch: Stretch

    ### Methods ###
    def _on_add(self) -> None:
        self.record.headers.append(RequestKeyValue())

    def _on_delete(self, header: RequestKeyValue) -> None:
        self.record.headers.remove(header)


@widget(layout="form", classes=["auth-form"])
class RequestAuthFormWidget(Widget[Auth]):
    ### Widgets ###
    # Basic Auth
    _basic_username: QLineEdit = new(bind="username", label="Username:", visible="{type.name == 'BASIC'}")
    _basic_password: QLineEdit = new(bind="password", label="Password:", echoMode=QLineEdit.EchoMode.Password, visible="{type.name == 'BASIC'}")
    # Bearer Auth
    _bearer_token: QLineEdit = new(bind="token", label="Token:", visible="{type.name == 'BEARER'}")
    # API Key Auth
    _api_key_name: QLineEdit = new(bind="name", label="Name:", visible="{type.name == 'API_KEY'}")
    _api_key_value: QLineEdit = new(bind="value", label="Value:", visible="{type.name == 'API_KEY'}")
    _api_key_location_chooser: QComboBox = new(
        bind=ApiKeyLocation,
        format=API_KEY_LOCATION_LABELS.get,
        selectedItem="location",
        label="Location:",
        visible="{type.name == 'API_KEY'}",
    )


@widget(title="Auth", classes=["tab-content", "auth-tab"])
class RequestAuthWidget(Widget[Request]):
    ### Widgets ###
    _header: QLabel = new("Authentication:", classes=["section-header"])
    _auth_type: QComboBox = new(bind=AuthType, format=AUTH_TYPE_LABELS.get, selectedItem="auth.type", classes=["auth-type-chooser"])
    _auth_form: RequestAuthFormWidget = new(bind="auth")
    _stretch: Stretch


@widget(title="Body", classes=["tab-content", "body-tab"])
class RequestBodyWidget(Widget[Request]):
    ### Events ###
    on_delete: Event = new(on="_on_delete")

    ### Variables ###
    _content_types: Var[dict[BodyType, str]] = new({BodyType.JSON: "application/json", BodyType.XML: "application/xml"})

    ### Widgets ###
    _body_type_chooser: QComboBox = new(bind=BodyType, format=BODY_TYPE_LABELS.get, selectedItem="body_type")
    _body_text: QPlainTextEdit = new(bind="body", visible="{body_type.name in ['JSON', 'XML', 'TEXT']}", content_type="{content_types[body_type]}", classes=["code-editor"])
    _add_button: QPushButton = new("+ Add Field", clicked="_on_add_field", visible="{body_type.name in ['FORM_URLENCODED', 'FORM_DATA']}", classes=["btn-add"])
    _body_fields_table: QTableView = new(
        bind="body_fields", visible="{body_type.name in ['FORM_URLENCODED', 'FORM_DATA']}", appendColumns=[DeleteRequestKeyValueWidget], classes=["key-value-table"]
    )
    _stretch: Stretch

    ### Methods ###
    def _on_add_field(self) -> None:
        self.record.body_fields.append(RequestKeyValue())

    def _on_delete(self, field: RequestKeyValue) -> None:
        self.record.body_fields.remove(field)


@widget(classes=["request-editor"])
class RequestEditorWidget(Widget[Request]):
    ### Widgets ###
    _address_bar: RequestAddressBarWidget
    _request_tabs: QTabWidget = new(
        tabs=[
            RequestParamsWidget,
            RequestHeadersWidget,
            RequestAuthWidget,
            RequestBodyWidget,
        ],
        classes=["request-tabs"],
    )
    _stretch: Stretch
