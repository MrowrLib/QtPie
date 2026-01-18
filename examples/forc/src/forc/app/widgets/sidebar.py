from typing import cast

from qtpy.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeView

from forc.app.helpers import filename_safe_validator
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


@dialog(layout="form", size=(450, 150), title="Add Collection")
class AddCollectionDialog(Dialog):
    name: Variable[str, QLineEdit] = new()(
        label="Collection Name",
        placeholderText="Enter collection name...",
        validator=filename_safe_validator,
    )
    parent_collection: Variable[Collection | None, QLabel] = new(None)(
        bind="{#var.name}", label="Parent Collection", visible="{not make_root_collection}"
    )
    make_root_collection: Variable[bool, QCheckBox] = new(False)(label="Set as Root Collection")
    _ok: DialogButton = new(enabled="{name != ''}")
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
        selected_item = cast(Collection | Request | None, self.var("current_workspace_item"))
        if selected_item is None:
            return
        collection = selected_item if isinstance(selected_item, Collection) else selected_item.collection
        dialog = AddCollectionDialog(parent_collection=collection)
        if dialog.show_dialog():
            collection_name = dialog.name()
            print("Creating new collection with name:", collection_name)
            self.workspace_service().add_collection(name=collection_name)

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
