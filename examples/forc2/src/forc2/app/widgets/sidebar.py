from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QTreeView

from forc2.domain.collection import TreeItem
from forc2.domain.workspace import Workspace
from qtpie import Var, Widget, new, widget
from qtpie.styles.zoom import set_zoom


@widget(layout="horizontal", margins=0)
class CollectionsTreeWidgetRow(Widget[TreeItem]):
    ### Variables ###
    is_editing: Var[bool] = new(False)

    # ### Widgets ###
    method_chip: QLabel = new(
        bind="{method?.value}",
        classes=["method-badge", "method-{method?.value}"],
        visible="{#record?.method is not None}",
        onEnterKey="start_editing",
    )
    text_label: QLabel = new(bind="{name}", visible="{not is_editing}", onMouseDoubleClick="{start_editing()}")
    text_edit: QLineEdit = new(
        bind="name",
        visible="{is_editing}",
        # validator=filename_safe_validator,
        onBlur="stop_editing",
        onEnterKey="stop_editing",
    )

    # ### Methods ###
    def start_editing(self) -> None:
        self.is_editing = True
        self.text_edit.setFocus()

    def stop_editing(self) -> bool:
        self.text_edit.clearFocus()
        self.is_editing = False
        # self.emit_event("on_rename", self.record_value, self.text_edit.text())
        return True


@widget(layout="horizontal")
class ScaleUpDownButtonsWidget(Widget):
    ### Variables ###
    scale_factor: Var[float] = new(1.0, onChange="_on_scale_factor_changed")

    ### Widgets ###
    scale_up_button: QPushButton = new(text="+", clicked="_on_scale_up")
    scale_down_button: QPushButton = new(text="-", clicked="_on_scale_down")

    ### Methods ###
    def _on_scale_up(self) -> None:
        self.scale_factor *= 1.1

    def _on_scale_down(self) -> None:
        self.scale_factor /= 1.1

    def _on_scale_factor_changed(self, new_value: float) -> None:
        set_zoom(new_value)


@widget
class SidebarWidget(Widget[Workspace | None]):
    scale_buttons: ScaleUpDownButtonsWidget

    collection_name_label: QLabel = new(bind="name")
    collection_tree: QTreeView = new(
        bind="collection?.items",
        children="items",
        headerHidden=True,
        widget=CollectionsTreeWidgetRow,
        expand=True,
        selectedItem="selected_sidebar_item",
    )
    environment_label: QLabel = new("Environment")
    environment_chooser: QComboBox = new(bind="environments", format="{name}", selectedItem="active_environment")

    # The old one:
    #
    #  treeview: QTreeView = new(
    #         selectedItem="current_workspace_item",
    #         headerHidden=True,
    #         validator=filename_safe_validator,
    #         clicked="{on_current_workspace_item_changed()}",
    #         widget=CollectionsTreeWidgetRow,
    #         onEnterKey="_on_enter_key",
    #         onDeleteKey="_on_delete_key",
    #         selectedWidget="current_tree_widget_row",
    #     )
