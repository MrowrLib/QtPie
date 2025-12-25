from typing import override

from qtpy.QtCore import (
    QEvent,
    QModelIndex,
    QObject,
    QSortFilterProxyModel,
    QStringListModel,
    Qt,
    Signal,
)
from qtpy.QtGui import QFocusEvent, QKeyEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QLineEdit,
    QListView,
    QWidget,
)

from qtpie import get_app, make, widget


@widget(layout="none")
class _DropdownListView(QListView):
    """List view for dropdown items."""

    def setup(self) -> None:
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)


@widget(layout="vertical", margins=0)
class _DropdownPopup(QFrame):
    """Floating popup containing the filtered list."""

    item_clicked = Signal(QModelIndex)

    _list_view: _DropdownListView = make(_DropdownListView, clicked="item_clicked")

    def setup(self) -> None:
        # Make it a floating tooltip-style window
        self.setParent(self.parent(), Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)  # type: ignore[arg-type]
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

    def set_model(self, model: QSortFilterProxyModel) -> None:
        """Set the model for the list view."""
        self._list_view.setModel(model)

    def update_selection(self, index: QModelIndex) -> None:
        """Update the current selection and scroll to it."""
        self._list_view.setCurrentIndex(index)
        self._list_view.scrollTo(index)


@widget(layout="vertical", margins=0, classes=["filterable-dropdown"])
class FilterableDropdown(QWidget):
    """A searchable dropdown widget (combobox with autocomplete).

    User types in a line edit, and a popup list filters to show matching items.
    Supports keyboard navigation (up/down/enter/escape).
    """

    item_selected = Signal(str)

    _line_edit: QLineEdit = make(QLineEdit, textEdited="_on_text_edited")
    _popup_: _DropdownPopup = make(_DropdownPopup, item_clicked="_on_item_clicked")
    _model: QStringListModel = make(QStringListModel)
    _proxy: QSortFilterProxyModel = make(QSortFilterProxyModel, filterCaseSensitivity=Qt.CaseSensitivity.CaseInsensitive)
    _app: QApplication = get_app(focusChanged="_on_focus_changed")

    _current_index: int = 0

    def setup(self) -> None:
        # Wire up the models
        self._proxy.setSourceModel(self._model)
        self._popup_.set_model(self._proxy)

        # Install event filter for keyboard navigation
        self._line_edit.installEventFilter(self)

    @property
    def filtered_count(self) -> int:
        """Get the number of items currently matching the filter."""
        return self._proxy.rowCount()

    @property
    def current_index(self) -> int:
        """Get the currently selected index in the filtered list."""
        return self._current_index

    @current_index.setter
    def current_index(self, value: int) -> None:
        """Set the currently selected index in the filtered list."""
        self._current_index = value
        self._update_selection()

    def set_items(self, items: list[str]) -> None:
        """Set the list of items to filter from."""
        self._model.setStringList(items)

    def set_placeholder_text(self, text: str) -> None:
        """Set placeholder text for the line edit."""
        self._line_edit.setPlaceholderText(text)

    def placeholder_text(self) -> str:
        """Get placeholder text for the line edit."""
        return self._line_edit.placeholderText()

    def current_text(self) -> str:
        """Get the current text in the line edit."""
        return self._line_edit.text()

    def set_text(self, text: str) -> None:
        """Set the text in the line edit."""
        self._line_edit.setText(text)

    def clear(self) -> None:
        """Clear the line edit text."""
        self._line_edit.clear()

    def show_popup(self) -> None:
        """Show the dropdown popup."""
        self._show_popup()

    def hide_popup(self) -> None:
        """Hide the dropdown popup."""
        self._popup_.hide()

    def is_popup_visible(self) -> bool:
        """Check if the dropdown popup is currently visible."""
        return self._popup_.isVisible()

    def select_current(self) -> None:
        """Select the currently highlighted item."""
        index = self._proxy.index(self._current_index, 0)
        if index.isValid():
            self._on_item_clicked(index)

    @override
    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self._line_edit.setFocus()

    def _on_text_edited(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)
        if self._proxy.rowCount() > 0:
            self._show_popup()
        else:
            self._popup_.hide()

    def _on_item_clicked(self, index: QModelIndex) -> None:
        text: str = self._proxy.data(index, Qt.ItemDataRole.DisplayRole)
        self._line_edit.setText(text)
        self._popup_.hide()
        self.item_selected.emit(text)

    def _show_popup(self) -> None:
        if not self._popup_.isVisible():
            pos = self._line_edit.mapToGlobal(self._line_edit.rect().bottomLeft())
            self._popup_.move(pos)
            self._popup_.setFixedWidth(self._line_edit.width())
            self._popup_.show()
        self._current_index = 0
        self._update_selection()

    def _on_focus_changed(self, old: QWidget | None, now: QWidget | None) -> None:
        if not self._popup_.isVisible():
            return
        if now is None:
            return
        if self.isAncestorOf(now) or self._popup_.isAncestorOf(now):
            return
        self._popup_.hide()

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj != self._line_edit:
            return super().eventFilter(obj, event)

        # Handle mouse click on line edit - toggle dropdown
        if event.type() == QEvent.Type.MouseButtonPress:
            if self._popup_.isVisible():
                self._popup_.hide()
            elif self._proxy.rowCount() > 0:
                self._show_popup()
            return False

        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(obj, event)
        if not isinstance(event, QKeyEvent):
            return super().eventFilter(obj, event)

        key = event.key()

        if key == Qt.Key.Key_Escape:
            self._popup_.hide()
            return True

        if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            if not self._popup_.isVisible():
                self._show_popup()
            direction = 1 if key == Qt.Key.Key_Down else -1
            self._navigate(direction)
            return True

        if key == Qt.Key.Key_Return and self._popup_.isVisible():
            index = self._proxy.index(self._current_index, 0)
            if index.isValid():
                self._on_item_clicked(index)
            return True

        return super().eventFilter(obj, event)

    def _navigate(self, direction: int) -> None:
        row_count = self._proxy.rowCount()
        if row_count == 0:
            return
        self._current_index = (self._current_index + direction) % row_count
        self._update_selection()

    def _update_selection(self) -> None:
        index = self._proxy.index(self._current_index, 0)
        self._popup_.update_selection(index)
