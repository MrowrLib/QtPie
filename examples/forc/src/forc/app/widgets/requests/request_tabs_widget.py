from qtpy.QtCore import Signal
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QTableView, QTabWidget

from forc.domain.models import BodyType, KeyValue, Request
from qtpie import Stretch, Variable, Widget, new, widget


@widget
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
        print(f"My objectname is {self.objectName()}")

    def _on_add(self):
        self.record.query_params.append(KeyValue(key="x", value="y"))


@widget(title="Headers")
class HeadersTabContent(Widget[Request]):
    """Headers tab content showing request headers."""

    _label: QLabel = new(bind="{record.headers}")


@widget(title="Auth")
class AuthTabContent(Widget[Request]):
    """Auth tab content showing authentication settings."""

    _label: QLabel = new(bind="{record.auth}")


@widget(title="Body")
class BodyTabContent(Widget[Request]):
    """Body tab content showing request body."""

    ### Variables ###
    _body_type: Variable[BodyType]

    ### Widgets ###
    body_type_chooser: QComboBox = new(
        bind=BodyType, selectedItem="_body_type", currentIndexChanged="_on_body_type_changed"
    )
    test_button: QPushButton = new("Print Body Type", clicked="_on_print_stuff")

    ### Methods ###
    def _on_print_stuff(self) -> None:
        print(f"Current body type is: {self._body_type.value}")

    def _on_body_type_changed(self, index: int) -> None:
        print(f"Body type changed to index: {index}")
        # traceback.print_stack(limit=10)


@widget
class RequestTabsWidget(Widget[Request]):
    params: ParamsTabContent = new(bind="record", layout=False)
    body: BodyTabContent = new(bind="record", layout=False)
    tabs: QTabWidget = new(tabs=[params, body])
