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


@widget(title="Actions")
class DeleteParamWidget(Widget[KeyValue]):
    delete: QPushButton = new(
        "🗑️", clicked="{on_delete_param(record)}", styleSheet="background: none; border: none; padding: 0;"
    )


@widget(title="Params", on_delete_param="_on_delete")
class ParamsTabContent(Widget[Request]):
    ### Signals ###
    on_delete_param = Signal(KeyValue)

    ### Widgets ###
    header: QLabel = new("Query Parameters:")
    buttons_layout: QHBoxLayout = new()
    table: QTableView = new(bind="record.query_params", columns=["key", "value", DeleteParamWidget])

    ### Buttons ###
    add_button: QPushButton = new("+ Add", layout="buttons_layout", clicked="_on_add")
    buttons_stretch: Stretch = new(layout="buttons_layout")

    ### Methods ###
    def _on_delete(self, param: KeyValue):
        self.record.query_params.remove(param)

    def _on_add(self):
        self.record.query_params.append(KeyValue(key="x", value="y"))


@widget(title="Headers")
class HeadersTabContent(Widget[Request]):
    """Headers tab content showing request headers."""

    _label: QLabel = new(bind="headers")


@widget(title="Auth")
class AuthTabContent(Widget[Request]):
    """Auth tab content showing authentication settings."""

    ### Widgets ###
    _auth_type: QComboBox = new(bind=AuthType, format=AUTH_TYPE_LABELS.get, selectedItem="auth?.type")
    _auth_fields_layout: QFormLayout = new()
    _stretch: Stretch

    ### Auth Fields ###
    _basic_username: QLineEdit = new(
        bind="auth?.username", layout="_auth_fields_layout", label="Username:", visible="{auth?.type == AuthType.BASIC}"
    )


@widget(title="Body")
class BodyTabContent(Widget[Request]):
    """Body tab content showing request body."""

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
    )

    ### Methods ###
    def _on_add_body_field(self) -> None:
        self.record.body_fields.append(KeyValue(key="", value=""))


@widget
class RequestTabsWidget(Widget[Request]):
    ### Tabs ###
    _params_tab: ParamsTabContent = new(layout=False)
    _body_tab: BodyTabContent = new(layout=False)
    _auth_tab: AuthTabContent = new(layout=False)

    ### Widgets ###
    _tabs: QTabWidget = new(tabs=[_params_tab, _body_tab, _auth_tab])
