from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QTableView, QTabWidget

from forc2.domain.auth import API_KEY_LOCATION_LABELS, AUTH_TYPE_LABELS, ApiKeyLocation, Auth, AuthType
from forc2.domain.request import HttpMethod, Request, RequestKeyValue
from qtpie import Event, Stretch, Widget, new, widget


# TODO: can we make this generic for other T than RequestKeyValue?
@widget(title="Actions")
class DeleteRequestKeyValueWidget(Widget[RequestKeyValue]):
    ### Widgets ###
    delete: QPushButton = new("🗑️", clicked="{on_delete(record)}", styleSheet="background: none; border: none; padding: 0;")


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget[Request]):
    ### Widgets ###
    request_method: QComboBox = new(bind=HttpMethod, selectedItem="method")
    request_url: QLineEdit = new(bind="url", placeholderText="Enter request URL...")
    send_request_button: QPushButton = new("Send", clicked="on_send_request", enabled="{not is_sending}")


@widget(title="Params")
class RequestParamsWidget(Widget[Request]):
    ### Events ###
    on_delete: Event[RequestKeyValue] = new(on="_on_delete")

    ### Widgets ###
    header: QLabel = new("Query Parameters:")
    add_button: QPushButton = new("+ Add", clicked="_on_add", classes=["add-button"])
    table: QTableView = new(bind="query_params")  # , columns=["key", "value", "enabled", DeleteRequestKeyValueWidget])

    ### Methods ###
    def _on_add(self) -> None:
        self.record.query_params.append(RequestKeyValue())

    def _on_delete(self, param: RequestKeyValue) -> None:
        self.record.query_params.remove(param)


@widget(title="Headers")
class RequestHeadersWidget(Widget[Request]):
    ### Widgets ###
    table: QTableView = new(bind="headers")  # , columns=["key", "value", "enabled", DeleteRequestKeyValueWidget])


@widget(layout="form")
class RequestAuthFormWidget(Widget[Auth]):
    ### Widgets ###
    # Basic Auth
    basic_username: QLineEdit = new(bind="username", label="Username:", visible="{type.name == 'BASIC'}")
    basic_password: QLineEdit = new(bind="password", label="Password:", echoMode=QLineEdit.EchoMode.Password, visible="{type.name == 'BASIC'}")
    # Bearer Auth
    bearer_token: QLineEdit = new(bind="token", label="Token:", visible="{type.name == 'BEARER'}")
    # API Key Auth
    api_key_name: QLineEdit = new(bind="key", label="API Key:", visible="{type.name == 'API_KEY'}")
    api_key_value: QLineEdit = new(bind="value", label="Value:", visible="{type.name == 'API_KEY'}")
    api_key_location: QComboBox = new(
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
    auth_type_chooser: QComboBox = new(
        bind=AuthType,
        format=AUTH_TYPE_LABELS.get,
        selectedItem="auth.type",
    )
    auth_form: RequestAuthFormWidget = new(bind="auth")
    foo: QLabel = new(bind="AUTH IS: {auth}")


@widget(title="Body")
class RequestBodyWidget(Widget[Request]):
    ### Widgets ###
    header: QLabel = new("Body:")


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
