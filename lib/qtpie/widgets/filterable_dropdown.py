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
    QVBoxLayout,
    QWidget,
)


class FilterableDropdown(QWidget):
    """A searchable dropdown widget (combobox with autocomplete).

    User types in a line edit, and a popup list filters to show matching items.
    Supports keyboard navigation (up/down/enter/escape).
    """

    item_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_index = 0

        # Main line edit
        self._line_edit = QLineEdit(self)

        # Model and filter proxy
        self._model = QStringListModel(self)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Popup frame (floats above other widgets)
        self._popup = QFrame(self, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self._popup.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._popup.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # List view inside popup
        self._list_view = QListView(self._popup)
        self._list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._list_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list_view.setModel(self._proxy)
        self._list_view.clicked.connect(self._on_item_clicked)

        # Popup layout
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.addWidget(self._list_view)

        # Main widget layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._line_edit)

        # Connect signals
        self._line_edit.textEdited.connect(self._on_text_edited)
        self._line_edit.installEventFilter(self)

        # Watch for focus changes to hide popup
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.focusChanged.connect(self._on_focus_changed)

    @property
    def line_edit(self) -> QLineEdit:
        """Access the underlying line edit widget."""
        return self._line_edit

    @property
    def popup(self) -> QFrame:
        """Access the popup frame widget."""
        return self._popup

    @property
    def list_view(self) -> QListView:
        """Access the list view widget inside the popup."""
        return self._list_view

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
        self._popup.hide()

    def select_current(self) -> None:
        """Select the currently highlighted item."""
        index = self._proxy.index(self._current_index, 0)
        if index.isValid():
            self._on_item_clicked(index)

    @override
    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self._line_edit.setFocus()
        if self._proxy.rowCount() > 0 and not self._popup.isVisible():
            self._show_popup()

    def _on_text_edited(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)
        if self._proxy.rowCount() > 0:
            self._show_popup()
        else:
            self._popup.hide()

    def _on_item_clicked(self, index: QModelIndex) -> None:
        text: str = self._proxy.data(index, Qt.ItemDataRole.DisplayRole)
        self._line_edit.setText(text)
        self._popup.hide()
        self.item_selected.emit(text)

    def _show_popup(self) -> None:
        if not self._popup.isVisible():
            pos = self._line_edit.mapToGlobal(self._line_edit.rect().bottomLeft())
            self._popup.move(pos)
            self._popup.setFixedWidth(self._line_edit.width())
            self._popup.show()
        self._current_index = 0
        self._update_selection()

    def _on_focus_changed(self, old: QWidget | None, now: QWidget | None) -> None:
        if not self._popup.isVisible():
            return
        if now is None:
            return
        if self.isAncestorOf(now) or self._popup.isAncestorOf(now):
            return
        self._popup.hide()

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj != self._line_edit:
            return super().eventFilter(obj, event)
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(obj, event)
        if not isinstance(event, QKeyEvent):
            return super().eventFilter(obj, event)

        key = event.key()

        if key == Qt.Key.Key_Escape:
            self._popup.hide()
            return True

        if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            if not self._popup.isVisible():
                self._show_popup()
            direction = 1 if key == Qt.Key.Key_Down else -1
            self._navigate(direction)
            return True

        if key == Qt.Key.Key_Return and self._popup.isVisible():
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
        self._list_view.setCurrentIndex(index)
        self._list_view.scrollTo(index)
