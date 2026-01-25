from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QTreeView

from forc2.domain.collection import Collection, TreeItem
from forc2.domain.workspace import Workspace
from qtpie import Var, Widget, new, widget


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
    _workspace_name_label: QLabel = new(bind="Workspace: {name}")
    _collection: CollectionsTreeWidget
    _environment_label: QLabel = new("Environment")
    _environments: QComboBox = new(format="{name}", selectedItem="active_environment")
