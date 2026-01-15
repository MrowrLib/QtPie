from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableView,
    QTabWidget,
)

from forc.domain.models import AUTH_TYPE_LABELS, BODY_TYPE_LABELS, AuthType, BodyType, KeyValue, Request
from qtpie import Stretch, Widget, new, widget


@widget(layout="horizontal")
class RequestAddressBarWidget(Widget[Request]):
    _method: QLabel = new(bind="method?.name")
    _url: QLineEdit = new(bind="url", placeholderText="Enter request URL...")
    _send: QPushButton = new("Send")


@widget(title="Actions")
class DeleteWidget(Widget[KeyValue]):
    delete: QPushButton = new(
        "🗑️", clicked="{on_delete(record)}", styleSheet="background: none; border: none; padding: 0;"
    )


@widget(title="Params", on_delete="_on_delete")
class ParamsTabContent(Widget[Request]):
    ### Signals ###
    on_delete = Signal(KeyValue)

    ### Widgets ###
    header: QLabel = new("Query Parameters:")
    buttons_layout: QHBoxLayout
    table: QTableView = new(bind="record.query_params", columns=["key", "value", DeleteWidget])

    ### Buttons ###
    add_button: QPushButton = new("+ Add", layout="buttons_layout", clicked="_on_add")
    buttons_stretch: Stretch = new(layout="buttons_layout")

    ### Methods ###
    def _on_delete(self, param: KeyValue):
        self.record.query_params.remove(param)

    def _on_add(self):
        self.record.query_params.append(KeyValue())


@widget(title="Headers")
class HeadersTabContent(Widget[Request]):
    _label: QLabel = new(bind="headers")


@widget(title="Auth")
class AuthTabContent(Widget[Request]):
    ### Widgets ###
    _auth_type: QComboBox = new(bind=AuthType, format=AUTH_TYPE_LABELS.get, selectedItem="auth?.type")
    _auth_fields_layout: QFormLayout
    _stretch: Stretch

    ### Auth Fields ###
    _basic_username: QLineEdit = new(
        bind="auth?.username", layout="_auth_fields_layout", label="Username:", visible="{auth?.type == AuthType.BASIC}"
    )


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
    ### Tab Content Widgets ###
    _params_tab: ParamsTabContent = new(layout=False)
    _body_tab: BodyTabContent = new(layout=False)
    _auth_tab: AuthTabContent = new(layout=False)

    ### Widgets ###
    _address_bar: RequestAddressBarWidget
    _tabs: QTabWidget = new(tabs=[_params_tab, _body_tab, _auth_tab])
