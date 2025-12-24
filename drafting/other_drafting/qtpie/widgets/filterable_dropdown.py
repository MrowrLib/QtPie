from typing import override

from PySide6.QtCore import QEvent, QModelIndex, QObject, QPoint, QSortFilterProxyModel, QStringListModel
from PySide6.QtGui import QFocusEvent, QKeyEvent, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QLineEdit,
    QListView,
    QVBoxLayout,
    QWidget,
)

from mrowr import make
from qtpie import Widget, widget


@widget(classes=["filterable-dropdown"])
class FilterableDropdown(QWidget, Widget):
    line_edit: QLineEdit = make(QLineEdit)

    _model: QStringListModel = make(QStringListModel)
    _proxy: QSortFilterProxyModel = make(QSortFilterProxyModel)
    _popup_frame: QFrame = make(QFrame)
    _list_view: QListView = make(QListView)
    _current_index: int = 0

    def set_items(self, items: list[str]) -> None:
        self._model.setStringList(items)

    def set_placeholder_text(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)

    @override
    def setup(self) -> None:
        self.setMinimumWidth(400)

        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._popup_frame = QFrame(self, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self._popup_frame.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._popup_frame.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._popup_frame.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self._list_view = QListView(self._popup_frame)
        self._list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._list_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list_view.setModel(self._proxy)
        self._list_view.clicked.connect(self._on_item_clicked)

        layout = QVBoxLayout(self._popup_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list_view)

        self.line_edit.textEdited.connect(self._on_text_edited)
        self.line_edit.installEventFilter(self)

        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.focusChanged.connect(self._on_focus_changed)

        old_focus_in = self.line_edit.focusInEvent

        def new_focus_in(event: QFocusEvent):
            old_focus_in(event)  # Preserve original behavior
            if self._proxy.rowCount() > 0 and not self._popup_frame.isVisible():
                self._show_popup()

        self.line_edit.focusInEvent = new_focus_in

    def _on_text_edited(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)
        if self._proxy.rowCount() > 0:
            self._show_popup()
        else:
            self._list_view.hide()

    def _on_item_clicked(self, index: QModelIndex) -> None:
        text: str = self._proxy.data(index, Qt.ItemDataRole.DisplayRole)
        self.line_edit.setText(text)
        self._popup_frame.hide()

    def _show_popup(self) -> None:
        if not self._popup_frame.isVisible():
            pos: QPoint = self.line_edit.mapToGlobal(self.line_edit.rect().bottomLeft())
            self._popup_frame.move(pos)
            self._popup_frame.setFixedWidth(self.line_edit.width())
            self._popup_frame.show()
        self._current_index = 0
        self._update_selection()

    def _on_focus_changed(self, old: QWidget | None, now: QWidget | None) -> None:
        if self._popup_frame.isVisible() and now is not None and not self.isAncestorOf(now) and not self._popup_frame.isAncestorOf(now):
            self._popup_frame.hide()

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj == self.line_edit and event.type() == QKeyEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):
                if event.key() == Qt.Key.Key_Escape:
                    self._popup_frame.hide()
                    return True
                elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                    if not self._list_view.isVisible():
                        self._show_popup()
                    direction = 1 if event.key() == Qt.Key.Key_Down else -1
                    self._navigate(direction)
                    return True
                elif event.key() == Qt.Key.Key_Return and self._list_view.isVisible():
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
