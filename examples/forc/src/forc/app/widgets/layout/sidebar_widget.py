from typing import cast

from qtpy.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeView

from forc.app.widgets.cookie_manager import CookieManagerDialog
from forc.app.widgets.environments import EnvironmentSelectorWidget
from forc.domain.models import Collection, Request
from forc.services import WorkspaceService
from qtpie import Dialog, DialogButton, Variable, Widget, dialog, new, widget


@dialog(layout="form", size=(400, 100), title="{kind}")
class TextValueDialog(Dialog):
    kind: Variable[str]
    value: Variable[str, QLineEdit] = new()(label="{kind}", placeholderText="Enter {kind} name...")
    _ok: DialogButton = new(enabled="{value != ''}")
    _cancel: DialogButton


@widget
class CollectionsTreeWidget(Widget):
    header: QLabel = new(bind="{workspace?.name}")
    treeview: QTreeView = new(
        bind="workspace.collections",
        children="items",
        format="{name}",
        selectedItem="current_workspace_item",
        expand=True,
        headerHidden=True,
        clicked="{on_current_workspace_item_changed()}",
    )


@widget
class SidebarWidget(Widget):
    ### Services ###
    workspace_service: Variable[WorkspaceService]

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
        enabled="{current_workspace_item is not None}",
    )

    ### Methods ###
    def show_cookie_manager(self):
        CookieManagerDialog.show_dialog()

    def _on_new_collection(self):
        dialog = TextValueDialog(kind="Collection")
        if dialog.show_dialog():
            print("Creating new collection with name:", dialog.value())
            self.workspace_service().add_collection(name=dialog.value())

    def _on_new_request(self):
        selected_item = cast(Collection | Request | None, self.var("current_workspace_item"))
        if selected_item is None:
            return
        collection = selected_item if isinstance(selected_item, Collection) else selected_item.collection
        if collection is None:
            return
        dialog = TextValueDialog(kind="Request")
        if dialog.show_dialog():
            self.workspace_service().add_request(name=dialog.value(), collection=collection)
