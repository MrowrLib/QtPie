from qtpy.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

from forc.app.widgets.collections import CollectionsTreeWidget
from forc.app.widgets.cookie_manager import CookieManagerDialog
from forc.app.widgets.environments import EnvironmentSelectorWidget
from forc.services import WorkspaceService
from qtpie import Dialog, DialogButton, Variable, Widget, dialog, new, widget


@dialog(layout="form", size=(400, 100), title="{kind}")
class TextValueDialog(Dialog):
    kind: Variable[str]
    value: Variable[str, QLineEdit] = new()(label="{kind}", placeholderText="Enter {kind} name...")
    _ok: DialogButton = new(enabled="{value != ''}")
    _cancel: DialogButton


@widget
class SidebarWidget(Widget):
    ### Services ###
    workspace_service: Variable[WorkspaceService] = new()

    ### Widgets ###
    _buttons_layout: QHBoxLayout
    collections: CollectionsTreeWidget
    _cookie_manager_button: QPushButton = new("Cookie Manager", clicked="show_cookie_manager")
    _environments: EnvironmentSelectorWidget

    ### Button Widgets ###
    _new_collection_button: QPushButton = new(
        "+ New Collection",
        clicked="_on_new_collection",
        layout="_buttons_layout",
    )
    _new_request_button: QPushButton = new(
        "+ New Request",
        clicked="_on_new_request",
        layout="_buttons_layout",
    )

    ### Methods ###
    def show_cookie_manager(self):
        CookieManagerDialog.show_dialog()

    def _on_new_collection(self):
        dialog = TextValueDialog(kind="Collection")
        if dialog.show_dialog():
            self.workspace_service().add_collection(dialog.value())

    def _on_new_request(self):
        ...
        # dialog = TextValueDialog(kind="Request")
        # if dialog.show_dialog():
        #     self.workspace_service().add_request(
        #         dialog.value()
        #     )
