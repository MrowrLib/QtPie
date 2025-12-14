from datetime import datetime
from typing import override

from PySide6.QtCore import QEvent, QObject, QPoint, QSize, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QFocusEvent, QKeyEvent, QMouseEvent, QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mrowr import make
from qtpie import Widget, make_widget, widget


@widget
class DescriptionItemWidget(QWidget, Widget):
    id: str
    description: str

    id_label: QLabel = make_widget(QLabel, "Id")
    description_label: QLabel = make_widget(QLabel, "Description")

    @override
    def setup(self) -> None:
        self.id_label.setText(self.id)
        self.description_label.setText(self.description)

    @override
    def setup_box_layout(self, layout: QBoxLayout) -> None:
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)


class MoveResizeWatcher(QObject):
    triggered = Signal()

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Move, QEvent.Type.Resize):
            self.triggered.emit()
        return False


@widget(classes=["filterable-dropdown"])
class FilterableDropdownWithDescription(QWidget, Widget):
    line_edit: QLineEdit = make(QLineEdit)

    _proxy: QSortFilterProxyModel = make(QSortFilterProxyModel)
    _popup_frame: QFrame = make(QFrame)
    _list_widget: QListWidget = make(QListWidget)
    _items: list[tuple[str, str]] = make(list[tuple[str, str]])
    _current_index: int = 0
    _window_watcher: MoveResizeWatcher | None = None
    _clicked_to_hide_at: datetime | None = None

    def set_items(self, items: list[tuple[str, str]]) -> None:
        self._items = items
        self._update_proxy()

    def set_placeholder_text(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)

    @override
    def setup(self) -> None:
        self.setMinimumWidth(400)

        self._popup_frame = QFrame(self, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self._popup_frame.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._popup_frame.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._popup_frame.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self._list_widget = QListWidget(self._popup_frame)
        self._list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list_widget.setUniformItemSizes(False)
        self._list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        self._list_widget.viewport().installEventFilter(self)

        layout = QVBoxLayout(self._popup_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list_widget)

        self.line_edit.textEdited.connect(self._on_text_edited)
        self.line_edit.installEventFilter(self)

        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.focusChanged.connect(self._on_focus_changed)

        old_focus_in = self.line_edit.focusInEvent

        def new_focus_in(event: QFocusEvent):
            old_focus_in(event)
            if self._list_widget.count() > 0 and not self._popup_frame.isVisible():
                if not self._clicked_to_hide_at:
                    self._show_popup()
                else:
                    time_since_clicked_to_hide = datetime.now() - (self._clicked_to_hide_at or datetime.now())
                    if time_since_clicked_to_hide.total_seconds() > 0.5:
                        self._show_popup()

        self.line_edit.focusInEvent = new_focus_in

    @override
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        if self._window_watcher is None:
            top = self.window()
            self._window_watcher = MoveResizeWatcher(self)
            top.installEventFilter(self._window_watcher)
            self._window_watcher.triggered.connect(self._on_parent_moved_or_resized)

    def _on_parent_moved_or_resized(self) -> None:
        self._reposition_popup()

    def _on_text_edited(self, text: str) -> None:
        self._update_proxy(filter_text=text)
        if self._list_widget.count() > 0:
            self._show_popup()
        else:
            self._popup_frame.hide()

    def _update_proxy(self, filter_text: str = "") -> None:
        self._list_widget.clear()
        for agent_id, description in self._items:
            if filter_text.lower() not in agent_id.lower() and filter_text.lower() not in description.lower():
                continue
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 40))
            widget = DescriptionItemWidget(agent_id, description)
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, widget)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        print("----> Item clicked")
        self._clicked_to_hide_at = datetime.now()
        widget = self._list_widget.itemWidget(item)
        if isinstance(widget, DescriptionItemWidget):
            self.line_edit.setText(widget.id_label.text())
        print("Hiding popup")
        print(self._popup_frame)
        self._popup_frame.clearFocus()
        self._popup_frame.hide()

    def _show_popup(self) -> None:
        print("----> Showing popup")
        if not self._popup_frame.isVisible():
            self._reposition_popup()
            self._popup_frame.show()
        self._current_index = 0
        self._update_selection()

    def _on_focus_changed(self, old: QWidget | None, now: QWidget | None) -> None:
        if self._popup_frame.isVisible() and now is not None and not self.isAncestorOf(now) and not self._popup_frame.isAncestorOf(now):
            self._popup_frame.hide()

    def _reposition_popup(self) -> None:
        pos: QPoint = self.line_edit.mapToGlobal(self.line_edit.rect().bottomLeft())
        self._popup_frame.move(pos)
        self._popup_frame.setFixedWidth(self.line_edit.width())

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj == self.line_edit and event.type() == QKeyEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):
                print("---> Key pressed")
                if event.key() == Qt.Key.Key_Escape:
                    self._popup_frame.hide()
                    return True
                elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                    if not self._list_widget.isVisible():
                        self._show_popup()
                    direction = 1 if event.key() == Qt.Key.Key_Down else -1
                    self._navigate(direction)
                    return True
                elif event.key() == Qt.Key.Key_Return and self._list_widget.isVisible():
                    item = self._list_widget.item(self._current_index)
                    self._on_item_clicked(item)
                    return True
        elif obj == self.line_edit and event.type() == QMouseEvent.Type.MouseButtonPress:
            if isinstance(event, QMouseEvent):
                print("---> Mouse event")
                # item = self._list_widget.itemAt(event.pos())
                # self._on_item_clicked(item)
                time_since_clicked_to_hide = datetime.now() - (self._clicked_to_hide_at or datetime.now())
                if time_since_clicked_to_hide.total_seconds() > 0.5:
                    self._show_popup()
                    return True

        return super().eventFilter(obj, event)

    def _navigate(self, direction: int) -> None:
        count = self._list_widget.count()
        if count == 0:
            return
        self._current_index = (self._current_index + direction) % count
        self._update_selection()

    def _update_selection(self) -> None:
        item = self._list_widget.item(self._current_index)
        self._list_widget.setCurrentItem(item)
        self._list_widget.scrollToItem(item)
