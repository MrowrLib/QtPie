from qtpy.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QPushButton, QTreeView

from forc2.domain.collection import Collection, TreeItem
from forc2.domain.workspace import Workspace
from qtpie import Dialog, DialogButton, Var, Widget, dialog, new, widget


@dialog(layout="form", size=(400, 100), title="{kind}")
class TextValueDialog(Dialog):
    ### Variables ###
    kind: Var[str]

    ### Widgets ###
    value: Var[str, QLineEdit] = new()(label="{kind}", placeholderText="Enter {kind} name...")

    ### Dialog Buttons ###
    _ok: DialogButton = new(enabled="{value != ''}")
    _cancel: DialogButton


@dialog(layout="form", size=(450, 150), title="Add Collection")
class AddCollectionDialog(Dialog):
    ### Widgets ###
    name: Var[str, QLineEdit] = new()(
        label="Collection Name",
        placeholderText="Enter collection name...",
        # validator=filename_safe_validator,
    )
    parent_collection: Var[Collection | None, QLabel] = new(None)(bind="{#var.name}", label="Parent Collection", visible="{not make_root_collection}")
    make_root_collection: Var[bool, QCheckBox] = new(False)(label="Set as Root Collection")

    ### Dialog Buttons ###
    _ok: DialogButton = new(enabled="{name != ''}")
    _cancel: DialogButton


@dialog(layout="form", size=(450, 150), title="Add Collection")
class DifferentDialog(Dialog):
    name: Var[str, QLineEdit] = new()(
        label="Collection Name",
        placeholderText="Enter collection name...",
    )
    make_root_collection: Var[bool, QCheckBox] = new(False)(label="Set as Root Collection")

    parent_collection: Var[Collection | None, QLabel] = new(None)(
        bind="{#var.name}",
        label="Parent Collection",
        visible="{not make_root_collection}",  # <--- if I comment this out, the mini dialog doesn't appear
    )

    #
    _ok: DialogButton = new(enabled="{name != ''}")
    _cancel: DialogButton


@widget(layout="horizontal")
class WorkspaceActionButtonsWidget(Widget[Workspace | None]):
    ### Widgets ###
    _new_collection_button: QPushButton = new(
        "+ New Collection",
        clicked="_on_new_collection",
        classes=["btn-add"],
    )
    _new_request_button: QPushButton = new(
        "+ New Request",
        # clicked="_on_new_request",
        # enabled="{current_workspace_item is not None}",
        classes=["btn-add"],
    )

    # ### Methods ###
    def _on_new_collection(self) -> None:
        # DifferentDialog()
        AddCollectionDialog()
        # if dialog.show_dialog():
        #     print("YES")
        # else:
        #     print("NO")
        # # d = QDialog()
        # ...
        # if dialog.show_dialog():
        #     ...


@widget(layout="horizontal", margins=0)
class CollectionsTreeWidgetRow(Widget[TreeItem]):
    ### Variables ###
    _is_editing: Var[bool] = new(False)

    # ### Widgets ###
    _method_chip: QLabel = new(
        bind="{method?.value}",
        classes=["method-badge", "method-{method?.value}"],
        visible="{#record?.method is not None}",
        onEnterKey="_start_editing",
    )
    _text_label: QLabel = new(bind="{name}", visible="{not _is_editing}", onMouseDoubleClick="{_start_editing()}")
    _text_edit: QLineEdit = new(
        bind="name",
        visible="{_is_editing}",
        # validator=filename_safe_validator,
        onBlur="_stop_editing",
        onEnterKey="_stop_editing",
    )

    # ### Methods ###
    def _start_editing(self) -> None:
        self._is_editing = True
        self._text_edit.setFocus()

    def _stop_editing(self) -> bool:
        self._text_edit.clearFocus()
        self._is_editing = False
        # self.emit_event("on_rename", self.record_value, self._text_edit.text())
        return True


@widget
class CollectionsTreeWidget(Widget[Collection | None]):
    ### Widgets ###
    _filter_text: Var[str, QLineEdit] = new("")(placeholderText="Filter...")
    _items: QTreeView = new(
        children="items",
        widget=CollectionsTreeWidgetRow,
        expand=True,
        selectedItem="selected_sidebar_item",
        filter="{_filter_text.lower()} in {(name or '').lower()}",
    )

    # The old one:
    #
    #  treeview: QTreeView = new(
    #         validator=filename_safe_validator,
    #         clicked="{on_current_workspace_item_changed()}",
    #         onEnterKey="_on_enter_key",
    #         onDeleteKey="_on_delete_key",
    #         selectedWidget="current_tree_widget_row",
    #     )


@widget
class SidebarWidget(Widget[Workspace | None]):
    ### Widgets ###
    _workspace_name: QLabel = new(bind="Workspace: {name}")
    _action_buttons: WorkspaceActionButtonsWidget
    _collection: CollectionsTreeWidget
    _environment_label: QLabel = new("Environment")
    _environments: QComboBox = new(format="{name}", selectedItem="active_environment")
