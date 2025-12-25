from typing import override

from qtpy.QtCore import QEvent, QObject, QSize, Qt, Signal
from qtpy.QtGui import QFocusEvent, QKeyEvent, QMouseEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QWidget,
)

from qtpie import get_app, make, widget


@widget(layout="vertical", margins=(6, 4, 6, 4))
class _DescriptionItemWidget(QWidget):
    """A two-line item widget showing value and description."""

    value_label: QLabel = make(QLabel)
    description_label: QLabel = make(QLabel)

    def setup(self) -> None:
        # Make transparent to mouse events so list widget receives them
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.value_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.description_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Set spacing between labels
        layout = self.layout()
        if layout is not None:
            layout.setSpacing(2)
        # Style the description as secondary text
        self.description_label.setStyleSheet("color: gray; font-size: 11px;")

    def set_content(self, value: str, description: str) -> None:
        """Set the value and description text."""
        self.value_label.setText(value)
        self.description_label.setText(description)

    def get_value(self) -> str:
        """Get the value text."""
        return self.value_label.text()


@widget(layout="vertical", margins=0)
class _DescriptionDropdownPopup(QFrame):
    """Floating popup containing the filtered list with description items."""

    item_clicked = Signal(QListWidgetItem)

    list_widget: QListWidget = make(QListWidget, itemClicked="item_clicked")

    def setup(self) -> None:
        # Make it a floating tooltip-style window
        self.setParent(self.parent(), Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)  # type: ignore[arg-type]
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Configure list widget
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


@widget(layout="vertical", margins=0, classes=["filterable-dropdown", "filterable-dropdown-with-description"])
class FilterableDropdownWithDescription(QWidget):
    """A searchable dropdown widget with two-line items (value + description).

    User types in a line edit, and a popup list filters to show matching items.
    Each item displays a primary value and a secondary description.
    Supports keyboard navigation (up/down/enter/escape).
    """

    item_selected = Signal(str)

    line_edit: QLineEdit = make(QLineEdit, textEdited="_on_text_edited")
    _popup: _DescriptionDropdownPopup = make(_DescriptionDropdownPopup, item_clicked="_on_item_clicked")
    _app: QApplication = get_app(focusChanged="_on_focus_changed")
    _current_index: int = 0

    def setup(self) -> None:
        self._items: list[tuple[str, str]] = []
        self._viewport: QWidget | None = None

        # Install event filter for keyboard navigation
        self.line_edit.installEventFilter(self)

        # Enable mouse tracking for hover highlighting
        self._viewport = self._popup.list_widget.viewport()
        if self._viewport:
            self._viewport.setMouseTracking(True)
            self._viewport.installEventFilter(self)

    @property
    def popup(self) -> _DescriptionDropdownPopup:
        """Access the popup frame widget."""
        return self._popup

    @property
    def list_widget(self) -> QListWidget:
        """Access the list widget inside the popup."""
        return self._popup.list_widget

    @property
    def filtered_count(self) -> int:
        """Get the number of items currently visible in the list."""
        return self._popup.list_widget.count()

    @property
    def current_index(self) -> int:
        """Get the currently selected index in the filtered list."""
        return self._current_index

    @current_index.setter
    def current_index(self, value: int) -> None:
        """Set the currently selected index in the filtered list."""
        self._current_index = value
        self._update_selection()

    def set_items(self, items: list[tuple[str, str]]) -> None:
        """Set the list of items to filter from.

        Args:
            items: List of (value, description) tuples.
        """
        self._items = items
        self._update_list()

    def set_placeholder_text(self, text: str) -> None:
        """Set placeholder text for the line edit."""
        self.line_edit.setPlaceholderText(text)

    def current_text(self) -> str:
        """Get the current text in the line edit."""
        return self.line_edit.text()

    def set_text(self, text: str) -> None:
        """Set the text in the line edit."""
        self.line_edit.setText(text)

    def clear(self) -> None:
        """Clear the line edit text."""
        self.line_edit.clear()

    def show_popup(self) -> None:
        """Show the dropdown popup."""
        self._show_popup()

    def hide_popup(self) -> None:
        """Hide the dropdown popup."""
        self._popup.hide()

    def select_current(self) -> None:
        """Select the currently highlighted item."""
        item = self._popup.list_widget.item(self._current_index)
        if item:
            self._on_item_clicked(item)

    @override
    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.line_edit.setFocus()
        if self._popup.list_widget.count() > 0 and not self._popup.isVisible():
            self._show_popup()

    def _on_text_edited(self, text: str) -> None:
        self._update_list(text)
        if self._popup.list_widget.count() > 0:
            self._show_popup()
        else:
            self._popup.hide()

    def _update_list(self, filter_text: str = "") -> None:
        """Update the list widget with filtered items."""
        self._popup.list_widget.clear()
        filter_lower = filter_text.lower()

        for value, description in self._items:
            # Filter by both value and description
            if filter_lower and filter_lower not in value.lower() and filter_lower not in description.lower():
                continue

            # Create list item with custom widget
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 44))  # Height for two lines

            item_widget = _DescriptionItemWidget()
            item_widget.set_content(value, description)

            self._popup.list_widget.addItem(item)
            self._popup.list_widget.setItemWidget(item, item_widget)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        widget = self._popup.list_widget.itemWidget(item)
        if isinstance(widget, _DescriptionItemWidget):
            text = widget.get_value()
            self.line_edit.setText(text)
            self._popup.hide()
            self.item_selected.emit(text)

    def _show_popup(self) -> None:
        if not self._popup.isVisible():
            pos = self.line_edit.mapToGlobal(self.line_edit.rect().bottomLeft())
            self._popup.move(pos)
            self._popup.setFixedWidth(self.line_edit.width())
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
        event_type = event.type()

        # Handle mouse hover on viewport (check type first for speed)
        if event_type == QEvent.Type.MouseMove and obj is self._viewport:
            if isinstance(event, QMouseEvent):
                pos = event.position().toPoint()
                item = self._popup.list_widget.itemAt(pos)
                if item:
                    row = self._popup.list_widget.row(item)
                    if row != self._current_index:
                        self._current_index = row
                        self._popup.list_widget.setCurrentRow(row)
            return False  # Don't consume, let Qt handle too

        # Handle mouse click on line edit - toggle dropdown
        if obj is self.line_edit and event_type == QEvent.Type.MouseButtonPress:
            if self._popup.isVisible():
                self._popup.hide()
            elif self._popup.list_widget.count() > 0:
                self._show_popup()
            return False

        # Handle keyboard on line edit
        if event_type != QEvent.Type.KeyPress or obj is not self.line_edit:
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
            item = self._popup.list_widget.item(self._current_index)
            if item:
                self._on_item_clicked(item)
            return True

        return super().eventFilter(obj, event)

    def _navigate(self, direction: int) -> None:
        count = self._popup.list_widget.count()
        if count == 0:
            return
        self._current_index = (self._current_index + direction) % count
        self._update_selection()

    def _update_selection(self) -> None:
        item = self._popup.list_widget.item(self._current_index)
        self._popup.list_widget.setCurrentItem(item)
        if item:
            self._popup.list_widget.scrollToItem(item)
