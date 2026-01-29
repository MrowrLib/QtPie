from qtpy.QtWidgets import QCheckBox, QComboBox, QFrame, QLabel, QLineEdit, QListView, QPushButton, QTableView, QToolButton, QTreeView

from forc2.app.helpers import confirm_delete
from forc2.domain.collection import Collection, TreeItem
from forc2.domain.request import Request
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
    ### Variables ###
    selected_collection: Var[Collection | None]

    ### Widgets ###
    name: Var[str, QLineEdit] = new()(
        label="Collection Name",
        placeholderText="Enter collection name...",
        # validator=filename_safe_validator,
    )
    parent_collection: QLabel = new(
        bind="{selected_collection.name}",
        label="Parent Collection",
        visible="{selected_collection is not None and not make_root_collection}",
    )
    make_root_collection: Var[bool, QCheckBox] = new(False)(
        label="Set as Root Collection",
        visible="{selected_collection is not None}",
    )

    ### Dialog Buttons ###
    _ok: DialogButton = new(enabled="{name != ''}")
    _cancel: DialogButton


@widget(layout="horizontal", spacing=10, margins=(10, 10, 10, 0))
class WorkspaceActionButtonsWidget(Widget[Workspace | None]):
    ### Variables ###
    selected_collection: Var[Collection | None]

    ### Widgets ###
    _new_collection_button: QPushButton = new(
        "+ New Collection",
        clicked="_on_new_collection",
        classes=["btn-add"],
    )
    _new_request_button: QPushButton = new(
        "+ New Request",
        # clicked="_on_new_request",
        enabled="{selected_collection is not None}",
        classes=["btn-add"],
    )

    # ### Methods ###
    def _on_new_collection(self) -> None:
        self.open_dialog(AddCollectionDialog)
        ...


@widget(layout="horizontal", margins=0)
class CollectionsTreeWidgetRow(Widget[TreeItem]):
    ### Variables ###
    _is_editing: Var[bool] = new(False)
    _original_name: Var[str] = new("")

    # ### Widgets ###
    _method_chip: QLabel = new(
        bind="{method?.value}",
        classes=["method-badge", "method-{method?.value}"],
        visible="{#record?.method is not None}",
        onEnterKey="start_editing",
    )
    _name_label: QLabel = new(bind="{name}", visible="{not _is_editing}", onMouseDoubleClick="{start_editing()}")
    _name_edit: QLineEdit = new(
        bind="name",
        visible="{_is_editing}",
        # validator=filename_safe_validator,
        onBlur="_stop_editing",
        onEnterKey="_stop_editing",
        onEscapeKey="_cancel_edit",
    )

    # ### Methods ###
    def start_editing(self) -> None:
        self._is_editing = True
        self._original_name = self.record.name  # TODO: should we swap .record and .record_value? to like .record_variable(s) or something?
        print("Starting edit, original name:", self._original_name())
        self._name_edit.setFocus()

    def _stop_editing(self) -> bool:
        self._name_edit.clearFocus()
        self._is_editing = False
        self.record.save()
        return True

    def _cancel_edit(self) -> None:
        self._is_editing = False
        self._name_edit.clearFocus()
        self.record.name = self._original_name()


# (left, top, right, bottom)
@widget(layout="horizontal", margins=(10, 0, 10, 10))
class CollectionsTreeActionsWidget(Widget[Collection | None]):
    ### Widgets ###
    filter_text: Var[str, QLineEdit] = new("")(placeholderText="Filter...")

    # TODO: different buttons based on the theme, use a helper or something? but needs live dynamic too
    _refresh_button: QToolButton = new(icon=":/refresh-dark.svg", clicked="{workspace.refresh() and items.expandAll()}", tooltip="Refresh")
    _expand_all_button: QToolButton = new(icon=":/expand-all-dark.svg", clicked="{items.expandAll()}", tooltip="Expand All")
    _collapse_all_button: QToolButton = new(icon=":/collapse-all-dark.svg", clicked="{items.collapseAll()}", tooltip="Collapse All")


@widget(margins=0)
class CollectionsTreeWidget(Widget[Collection | None]):
    ### Variables ###
    _current_tree_row: Var[CollectionsTreeWidgetRow | None]

    ### Widgets ###
    _actions: CollectionsTreeActionsWidget

    # Someone remind me how the built-in editing works? without a custom widget?
    #
    # I wanna make sure ESCAPE blurs and cancels the edit.
    #
    # _items: QTreeView = new(
    #     children="items",
    #     # widget=CollectionsTreeWidgetRow,
    #     # selectedWidget="_current_tree_row",
    #     format="{name}",
    #     selectedItem="selected_sidebar_item",
    #     filter="{_actions.filter_text.lower()} in {(name or '').lower()}",
    #     expand=True,
    #     # onEnterKey="{_current_tree_row.start_editing()}",
    #     onDeleteKey="_on_delete",
    # )

    # _items: QTreeView = new(
    #     children="items",
    #     widget=CollectionsTreeWidgetRow,
    #     selectedWidget="_current_tree_row",
    #     selectedItem="selected_sidebar_item",
    #     filter="{_actions.filter_text.lower()} in {(name or '').lower()}",
    #     expand=True,
    #     onEnterKey="{_current_tree_row.start_editing()}",
    #     onDeleteKey="_on_delete",
    # )

    # The old one:
    #
    #  treeview: QTreeView = new(
    #         validator=filename_safe_validator,
    #     )

    _item_label: QLabel = new(bind="First Item Name: {items[0].name}")  # works

    # # below do not work, they show nothing in the lists:

    _item_list: QListView = new(bind="{items[0].items}", format="{name}")  # ... doesn't work, should it?!

    _tree: QTreeView = new(bind="{items[0]}", children="items", format="{name}")  # WORKS!

    _table: QTableView = new(bind="{items[0].items}")  # ... doesn't work, should it?!

    _combo: QComboBox = new(bind="{items[0].items}", format="{name}")  # ... doesn't work, should it?!

    ### Methods ###
    def _on_delete(self) -> None:
        item = self.var("selected_sidebar_item", Collection, Request, None)
        if item is not None:
            if confirm_delete():
                item.delete()


@widget
class SidebarWidget(Widget[Workspace | None]):
    ### Widgets ###
    _workspace_name: QLabel = new(bind="Workspace: {name}", classes=["heading-3", "bg-secondary", "p-2"])
    _action_buttons: WorkspaceActionButtonsWidget
    _divider1: QFrame = new(frameShape=QFrame.Shape.HLine)
    _collection: CollectionsTreeWidget
    _environment_label: QLabel = new("Environment", classes=["heading-4", "bg-secondary", "p-2"])
    _environments: QComboBox = new(format="{name}", selectedItem="active_environment")
