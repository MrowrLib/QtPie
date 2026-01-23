from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QTableView, QTabWidget

from forc2.domain.auth import API_KEY_LOCATION_LABELS, AUTH_TYPE_LABELS, ApiKeyLocation, Auth, AuthType
from forc2.domain.body import BODY_TYPE_LABELS, BodyType
from forc2.domain.request import HttpMethod, Request, RequestKeyValue
from qtpie import Event, Stretch, Widget, new, widget
from qtpie.variable import Var

# TODO: update all to use _private names for the widgets, simple names, but private to avoid conflicts with the record's attributes


@widget
class DeleteWidget[T](Widget[T]):
    ### Widgets ###
    delete: QPushButton = new("🗑️", clicked="{on_delete(record)}", styleSheet="background: none; border: none; padding: 0;")


@widget(title="Actions")
class DeleteRequestKeyValueWidget(DeleteWidget[RequestKeyValue]): ...


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget[Request]):
    ### Widgets ###
    request_method_chooser: QComboBox = new(bind=HttpMethod, selectedItem="method")
    request_url: QLineEdit = new(bind="url", placeholderText="Enter request URL...")
    send_request_button: QPushButton = new("Send", clicked="on_send_request", enabled="{not is_sending}")


@widget(title="Params")
class RequestParamsWidget(Widget[Request]):
    ### Events ###
    on_delete: Event[RequestKeyValue] = new(on="_on_delete")

    ### Widgets ###
    header: QLabel = new("Query Parameters:")
    add_button: QPushButton = new("+ Add", clicked="_on_add", classes=["add-button"])
    table: QTableView = new(bind="query_params", appendColumns=[DeleteRequestKeyValueWidget])

    ### Methods ###
    def _on_add(self) -> None:
        self.record.query_params.append(RequestKeyValue())

    def _on_delete(self, param: RequestKeyValue) -> None:
        self.record.query_params.remove(param)


@widget(title="Headers")
class RequestHeadersWidget(Widget[Request]):
    ### Events ###
    on_delete: Event[RequestKeyValue] = new(on="_on_delete")

    ### Widgets ###
    header: QLabel = new("Headers:")
    add_button: QPushButton = new("+ Add", clicked="_on_add", classes=["add-button"])
    table: QTableView = new(bind="headers", appendColumns=[DeleteRequestKeyValueWidget])

    ### Methods ###
    def _on_add(self) -> None:
        self.record.headers.append(RequestKeyValue())

    def _on_delete(self, header: RequestKeyValue) -> None:
        self.record.headers.remove(header)


@widget(layout="form")
class RequestAuthFormWidget(Widget[Auth]):
    ### Widgets ###
    # Basic Auth
    basic_username: QLineEdit = new(bind="username", label="Username:", visible="{type.name == 'BASIC'}")
    basic_password: QLineEdit = new(bind="password", label="Password:", echoMode=QLineEdit.EchoMode.Password, visible="{type.name == 'BASIC'}")
    # Bearer Auth
    bearer_token: QLineEdit = new(bind="token", label="Token:", visible="{type.name == 'BEARER'}")
    # API Key Auth
    api_key_name: QLineEdit = new(bind="name", label="Name:", visible="{type.name == 'API_KEY'}")
    api_key_value: QLineEdit = new(bind="value", label="Value:", visible="{type.name == 'API_KEY'}")
    api_key_location_chooser: QComboBox = new(
        bind=ApiKeyLocation,
        format=API_KEY_LOCATION_LABELS.get,
        selectedItem="location",
        label="Location:",
        visible="{type.name == 'API_KEY'}",
    )


@widget(title="Auth")
class RequestAuthWidget(Widget[Request]):
    ### Widgets ###
    header: QLabel = new("Authentication:")
    auth_type: QComboBox = new(bind=AuthType, format=AUTH_TYPE_LABELS.get, selectedItem="auth.type")
    auth_form: RequestAuthFormWidget = new(bind="auth")


@widget(title="Body")
class RequestBodyWidget(Widget[Request]):
    ### Events ###
    on_delete: Event = new(on="_on_delete")

    ### Variables ###
    content_types: Var[dict[BodyType, str]] = new({BodyType.JSON: "application/json", BodyType.XML: "application/xml"})

    ### Widgets ###
    body_type_chooser: QComboBox = new(bind=BodyType, format=BODY_TYPE_LABELS.get, selectedItem="body_type")
    body_text: QPlainTextEdit = new(bind="body", visible="{body_type.name in ['JSON', 'XML', 'TEXT']}", content_type="{content_types[body_type]}")
    add_button: QPushButton = new("+ Add Field", clicked="_on_add_field", visible="{body_type.name in ['FORM_URLENCODED', 'FORM_DATA']}", classes=["add-button"])
    body_fields_table: QTableView = new(bind="body_fields", visible="{body_type.name in ['FORM_URLENCODED', 'FORM_DATA']}", appendColumns=[DeleteRequestKeyValueWidget])

    ### Methods ###
    def _on_add_field(self) -> None:
        self.record.body_fields.append(RequestKeyValue())

    def _on_delete(self, field: RequestKeyValue) -> None:
        self.record.body_fields.remove(field)


@widget
class RequestEditorWidget(Widget[Request]):
    ### Widgets ###
    address_bar: RequestAddressBarWidget
    request_tabs: QTabWidget = new(
        tabs=[
            RequestParamsWidget,
            RequestHeadersWidget,
            RequestAuthWidget,
            RequestBodyWidget,
        ]
    )
    stretch: Stretch
