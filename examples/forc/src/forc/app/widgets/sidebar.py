from PySide6.QtCore import Signal
from qtpy.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeView

from forc.app.helpers import confirm_delete, filename_safe_validator
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


@widget(layout="horizontal", margins=0)
class CollectionsTreeWidgetRow(Widget[Collection | Request]):
    ### Variables ###
    is_editing: Variable[bool] = new(False)

    ### Widgets ###
    method_chip: QLabel = new(
        bind="{method?.value}",
        classes=["method-badge", "method-{method?.value}"],
        visible="{record?.method is not None}",
        onEnterKey="start_editing",  # <--- this does not trigger, probably consumed by the qtreeview
    )
    text_label: QLabel = new(bind="{name}", visible="{not is_editing}", onMouseDoubleClick="{start_editing()}")
    text_edit: QLineEdit = new(
        bind="name",
        visible="{is_editing}",
        validator=filename_safe_validator,
        onBlur="stop_editing",
        onEnterKey="stop_editing",
    )

    ### Methods ###
    def __setup__(self) -> None:
        print("My objectName is:", self.objectName())

    def start_editing(self) -> None:
        self.is_editing = True
        self.text_edit.setFocus()

    def stop_editing(self) -> bool:
        self.text_edit.clearFocus()
        self.is_editing = False
        self.emit_signal("on_rename", self.record_value, self.text_edit.text())
        return True


@widget(on_rename="_on_rename")
class CollectionsTreeWidget(Widget):
    on_rename = Signal(object, str)

    ### Services ###
    workspace_service: Variable[WorkspaceService]

    ### Variables ###
    current_tree_widget_row: Variable[CollectionsTreeWidgetRow | None] = new(None)

    ### Widgets ###
    header: QLabel = new(bind="{workspace?.name}")
    treeview: QTreeView = new(
        bind="workspace.collections",
        children="items",
        selectedItem="current_workspace_item",
        expand=True,
        headerHidden=True,
        validator=filename_safe_validator,
        clicked="{on_current_workspace_item_changed()}",
        widget=CollectionsTreeWidgetRow,
        onEnterKey="_on_enter_key",
        onDeleteKey="_on_delete_key",
        selectedWidget="current_tree_widget_row",
    )

    ### Methods ###
    def _on_rename(self, item: Collection | Request, new_name: str) -> None:
        if isinstance(item, Request):
            self.workspace_service().rename_request(item, new_name)
        else:
            self.workspace_service().rename_collection(item, new_name)

    def _on_enter_key(self) -> None:
        widget = self.current_tree_widget_row()
        if widget is not None:
            widget.start_editing()

    def _on_delete_key(self) -> None:
        if confirm_delete():
            item = self.var("current_workspace_item", Collection, Request, None)
            if item is not None:
                self.workspace_service().delete_item(item)


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
        classes=["add-button"],
    )
    _new_request_button: QPushButton = new(
        "+ New Request",
        clicked="_on_new_request",
        layout="_buttons_layout",
        enabled="{current_workspace_item is not None}",
        classes=["add-button"],
    )

    ### Methods ###
    def show_cookie_manager(self):
        CookieManagerDialog.show_dialog()

    def _on_new_collection(self):
        selected_item = self.var("current_workspace_item", Collection, Request, None)
        if selected_item is None:
            return
        collection = selected_item if isinstance(selected_item, Collection) else selected_item.collection
        dialog = AddCollectionDialog(parent_collection=collection)
        if dialog.show_dialog():
            collection_name = dialog.name()
            print("Creating new collection with name:", collection_name)
            self.workspace_service().create_collection(name=collection_name)

    def _on_new_request(self):
        selected_item = self.var("current_workspace_item", Collection, Request, None)
        if selected_item is None:
            return
        collection = selected_item if isinstance(selected_item, Collection) else selected_item.collection
        if collection is None:
            return
        dialog = TextValueDialog(kind="Request")
        if dialog.show_dialog():
            self.workspace_service().create_request(name=dialog.value(), collection=collection)
