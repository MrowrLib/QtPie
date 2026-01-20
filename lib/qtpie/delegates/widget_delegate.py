"""Widget delegate for embedding QtPie widgets in model views."""

from typing import Any, cast, override

from qtpy.QtCore import QModelIndex, QPersistentModelIndex, Qt
from qtpy.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

from qtpie.embed import EmbedConfig


class QtPieWidgetDelegate(QStyledItemDelegate):
    """Delegate that creates QtPie Widget instances for each item in a view.

    Uses openPersistentEditor() to keep widgets always visible (not just when editing).

    This delegate:
    - Creates widget instances in createEditor()
    - Injects the item into Widget[T].record if applicable
    - Applies embed() kwargs (variable bindings, signal connections, etc.)
    - Sizes widgets via updateEditorGeometry()
    """

    def __init__(
        self,
        widget_class: type[Any],
        parent_widget: Any,
        embed_config: EmbedConfig | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the delegate.

        Args:
            widget_class: The Widget subclass to instantiate for each item.
            parent_widget: The QtPie Widget that hosts the view (for signal connections).
            embed_config: Optional EmbedConfig with kwargs to apply to each widget.
            parent: Qt parent widget.
        """
        super().__init__(parent)
        self.widget_class = widget_class
        self.parent_widget = parent_widget
        self.embed_config = embed_config
        self._kwargs = embed_config.kwargs if embed_config else {}

    @override
    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        """Create a widget instance for the given index.

        Args:
            parent: The parent widget for the created editor.
            option: Style options (unused, but required by Qt).
            index: The model index being edited.

        Returns:
            A new instance of widget_class, configured with bindings.
        """
        # Get the item from the model
        item = index.data(Qt.ItemDataRole.UserRole)
        row = index.row()

        # Create the widget instance
        widget = self._create_widget_instance(parent, item, row, cast(QModelIndex, index))

        return widget

    def _create_widget_instance(
        self,
        parent: QWidget,
        item: Any,
        row: int,
        index: QModelIndex,
    ) -> QWidget:
        """Create and configure a widget instance.

        Args:
            parent: Qt parent widget.
            item: The data item for this row.
            row: The row index.
            index: The full model index.

        Returns:
            Configured widget instance.
        """
        from observant import Observable

        from qtpie.create import (
            _apply_context_bindings,  # pyright: ignore[reportPrivateUsage]
            _create_instance_internal,  # pyright: ignore[reportPrivateUsage]
        )
        from qtpie.variable import Variable

        # Separate special embed kwargs from regular kwargs
        regular_kwargs: dict[str, Any] = {}
        selected_item_var_name: str | None = None
        selected_index_var_name: str | None = None
        selected_row_var_name: str | None = None

        for key, value in self._kwargs.items():
            if key == "selectedItem":
                selected_item_var_name = value
            elif key == "selectedIndex":
                selected_index_var_name = value
            elif key == "selectedRow":
                selected_row_var_name = value
            else:
                regular_kwargs[key] = value

        # Create the widget using the internal create function
        # This separates QtPie kwargs and returns runtime data for context bindings
        widget, runtime_data = _create_instance_internal(self.widget_class, parent, **regular_kwargs)

        # Inject the record if this is a Widget[T]
        if hasattr(widget, "record") and hasattr(widget, "_qtpie"):
            widget.record = item  # type: ignore[attr-defined]

        # Inject selectedItem as Variable
        if selected_item_var_name:
            item_observable: Observable[Any] = Observable(item)
            item_var: Variable[Any] = Variable(item_observable)
            setattr(widget, selected_item_var_name, item_var)

        # Inject selectedIndex as Variable (for QListView/QTreeView)
        if selected_index_var_name:
            index_observable: Observable[int] = Observable(row)
            index_var: Variable[int] = Variable(index_observable)
            setattr(widget, selected_index_var_name, index_var)

        # Inject selectedRow as Variable (for QTableView)
        if selected_row_var_name:
            row_observable: Observable[int] = Observable(row)
            row_var: Variable[int] = Variable(row_observable)
            setattr(widget, selected_row_var_name, row_var)

        # Apply context bindings (signal connections, property bindings, etc.)
        # The parent_widget is the context for resolving handlers
        _apply_context_bindings(
            self.parent_widget,
            widget,
            runtime_data,
            f"{self.widget_class.__name__}[{row}]",
        )

        return widget

    @override
    def updateEditorGeometry(
        self,
        editor: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """Set the editor geometry to fit the cell.

        Args:
            editor: The editor widget.
            option: Style options containing the rect.
            index: The model index (unused).
        """
        editor.setGeometry(option.rect)  # pyright: ignore[reportUnknownArgumentType,reportUnknownMemberType,reportAttributeAccessIssue]

    @override
    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        """Update the editor with data from the model.

        This is called when the model data changes. We update the injected
        Variables to reflect the new item/index.

        Args:
            editor: The editor widget.
            index: The model index with new data.
        """
        item = index.data(Qt.ItemDataRole.UserRole)
        row = index.row()

        # Update record if Widget[T]
        if hasattr(editor, "record") and hasattr(editor, "_qtpie"):
            editor.record = item  # type: ignore[attr-defined]

        # Update injected Variables
        if self.embed_config:
            kwargs = self.embed_config.kwargs

            if "selectedItem" in kwargs:
                var_name = kwargs["selectedItem"]
                var = getattr(editor, var_name, None)
                if var is not None and hasattr(var, "value"):
                    var.value = item

            if "selectedIndex" in kwargs:
                var_name = kwargs["selectedIndex"]
                var = getattr(editor, var_name, None)
                if var is not None and hasattr(var, "value"):
                    var.value = row

            if "selectedRow" in kwargs:
                var_name = kwargs["selectedRow"]
                var = getattr(editor, var_name, None)
                if var is not None and hasattr(var, "value"):
                    var.value = row

    @override
    def setModelData(
        self,
        editor: QWidget,
        model: Any,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """Write data from editor back to model.

        For Widget[T], the record changes are already synced via ObservableProxy.
        This method is a no-op for our use case.

        Args:
            editor: The editor widget.
            model: The model (unused).
            index: The model index (unused).
        """
        # No-op - Widget[T] record changes sync automatically via ObservableProxy
        pass

    @override
    def paint(
        self,
        painter: Any,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """Don't paint anything - the embedded widget handles all rendering.

        Without this override, Qt draws the DisplayRole text underneath the widget.
        """
        # No-op - widget covers the entire cell
        pass
