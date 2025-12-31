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

    _value_label: QLabel = make(QLabel)
    _description_label: QLabel = make(QLabel)

    def setup(self) -> None:
        # Make transparent to mouse events so list widget receives them
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._value_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._description_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Set spacing between labels
        layout = self.layout()
        if layout is not None:
            layout.setSpacing(2)
        # Style the description as secondary text
        self._description_label.setStyleSheet("color: gray; font-size: 11px;")

    def set_content(self, value: str, description: str) -> None:
        """Set the value and description text."""
        self._value_label.setText(value)
        self._description_label.setText(description)

    def get_value(self) -> str:
        """Get the value text."""
        return self._value_label.text()


@widget(layout="vertical", margins=0)
class _DescriptionDropdownPopup(QFrame):
    """Floating popup containing the filtered list with description items."""

    item_clicked = Signal(QListWidgetItem)
    item_hovered = Signal(int)  # Emits row index when mouse hovers over item

    _list_widget: QListWidget = make(QListWidget, itemClicked="item_clicked")

    def setup(self) -> None:
        # Make it a floating tooltip-style window
        self.setParent(self.parent(), Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)  # type: ignore[arg-type]
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Configure list widget
        self._list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list_widget.setUniformItemSizes(False)
        self._list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Enable mouse tracking for hover
        viewport = self._list_widget.viewport()
        if viewport:
            viewport.setMouseTracking(True)
            viewport.installEventFilter(self)

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            pos = event.position().toPoint()
            item = self._list_widget.itemAt(pos)
            if item:
                row = self._list_widget.row(item)
                self.item_hovered.emit(row)
        return False

    def count(self) -> int:
        """Get the number of items in the list."""
        return self._list_widget.count()

    def clear(self) -> None:
        """Clear all items from the list."""
        self._list_widget.clear()

    def add_item(self, value: str, description: str) -> None:
        """Add an item with value and description."""
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 44))  # Height for two lines

        item_widget = _DescriptionItemWidget()
        item_widget.set_content(value, description)

        self._list_widget.addItem(item)
        self._list_widget.setItemWidget(item, item_widget)

    def get_value_at(self, index: int) -> str | None:
        """Get the value text at the given index."""
        item = self._list_widget.item(index)
        if not item:
            return None
        widget = self._list_widget.itemWidget(item)
        if isinstance(widget, _DescriptionItemWidget):
            return widget.get_value()
        return None

    def select_index(self, index: int) -> None:
        """Select the item at the given index and scroll to it."""
        item = self._list_widget.item(index)
        if item:
            self._list_widget.setCurrentItem(item)
            self._list_widget.scrollToItem(item)


@widget(layout="vertical", margins=0, classes=["filterable-dropdown", "filterable-dropdown-with-description"])
class FilterableDropdownWithDescription(QWidget):
    """A searchable dropdown widget with two-line items (value + description).

    User types in a line edit, and a popup list filters to show matching items.
    Each item displays a primary value and a secondary description.
    Supports keyboard navigation (up/down/enter/escape).
    """

    item_selected = Signal(str)

    _line_edit: QLineEdit = make(QLineEdit, textEdited="_on_text_edited")
    _popup_: _DescriptionDropdownPopup = make(
        _DescriptionDropdownPopup,
        item_clicked="_on_item_clicked",
        item_hovered="_on_item_hovered",
    )
    _app: QApplication = get_app(focusChanged="_on_focus_changed")
    _current_index: int = 0

    def setup(self) -> None:
        self._items: list[tuple[str, str]] = []

        # Install event filter for keyboard navigation and click toggle
        self._line_edit.installEventFilter(self)

    @property
    def filtered_count(self) -> int:
        """Get the number of items currently visible in the list."""
        return self._popup_.count()

    @property
    def current_index(self) -> int:
        """Get the currently selected index in the filtered list."""
        return self._current_index

    @current_index.setter
    def current_index(self, value: int) -> None:
        """Set the currently selected index in the filtered list."""
        self._current_index = value
        self._popup_.select_index(value)

    def set_items(self, items: list[tuple[str, str]]) -> None:
        """Set the list of items to filter from.

        Args:
            items: List of (value, description) tuples.
        """
        self._items = items
        self._update_list()

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
        value = self._popup_.get_value_at(self._current_index)
        if value:
            self._select_value(value)

    @override
    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self._line_edit.setFocus()

    def _on_text_edited(self, text: str) -> None:
        self._update_list(text)
        if self._popup_.count() > 0:
            self._show_popup()
        else:
            self._popup_.hide()

    def _update_list(self, filter_text: str = "") -> None:
        """Update the list widget with filtered items."""
        self._popup_.clear()
        filter_lower = filter_text.lower()

        for value, description in self._items:
            # Filter by both value and description
            if filter_lower and filter_lower not in value.lower() and filter_lower not in description.lower():
                continue
            self._popup_.add_item(value, description)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        # Get value from the popup at the clicked item's index
        value = self._popup_.get_value_at(self._current_index)
        if value:
            self._select_value(value)

    def _on_item_hovered(self, row: int) -> None:
        if row != self._current_index:
            self._current_index = row
            self._popup_.select_index(row)

    def _select_value(self, value: str) -> None:
        """Select a value and emit the signal."""
        self._line_edit.setText(value)
        self._popup_.hide()
        self.item_selected.emit(value)

    def _show_popup(self) -> None:
        if not self._popup_.isVisible():
            pos = self._line_edit.mapToGlobal(self._line_edit.rect().bottomLeft())
            self._popup_.move(pos)
            self._popup_.setFixedWidth(self._line_edit.width())
            self._popup_.show()
        self._current_index = 0
        self._popup_.select_index(0)

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
        if obj is not self._line_edit:
            return super().eventFilter(obj, event)

        event_type = event.type()

        # Handle mouse click on line edit - toggle dropdown
        if event_type == QEvent.Type.MouseButtonPress:
            if self._popup_.isVisible():
                self._popup_.hide()
            elif self._popup_.count() > 0:
                self._show_popup()
            return False

        # Handle keyboard
        if event_type != QEvent.Type.KeyPress:
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
            self.select_current()
            return True

        return super().eventFilter(obj, event)

    def _navigate(self, direction: int) -> None:
        count = self._popup_.count()
        if count == 0:
            return
        self._current_index = (self._current_index + direction) % count
        self._popup_.select_index(self._current_index)
