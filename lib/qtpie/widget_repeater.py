"""WidgetRepeater - Container that manages repeated widgets bound to list items."""

from __future__ import annotations

from typing import Any

from observant import Observable, ObservableList, ObservableProxy
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .bindings import bind
from .variable import Variable


def _is_primitive_type(t: type | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))


class WidgetRepeater[T](QWidget):
    """Container that manages repeated widgets bound to list items.

    Creates one widget per list item. Uses granular callbacks (on_insert,
    on_remove, on_replace, on_clear) to efficiently sync the widget list
    with the underlying ObservableList.

    Usage:
        # Variable[list[int], QLineEdit] creates this automatically
        # Each QLineEdit is bound to one list item
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
        item_type: type | None,
        widget_type: type,
        widget_args: tuple[Any, ...] = (),
        widget_kwargs: dict[str, Any] | None = None,
        bind_expr: str = "{#self}",
        layout_type: str = "vertical",
    ) -> None:
        """Initialize the widget repeater.

        Args:
            observable_list: The ObservableList to sync with.
            item_type: The type of items in the list (e.g., int, str, Dog).
            widget_type: The widget type to create for each item.
            widget_args: Positional args for widget constructor.
            widget_kwargs: Keyword args for widget constructor.
            bind_expr: Binding expression (default "{#self}").
            layout_type: "vertical" or "horizontal".
        """
        super().__init__()

        self._obs_list = observable_list
        self._item_type = item_type
        self._widget_type = widget_type
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        self._bind_expr = bind_expr
        self._is_primitive = _is_primitive_type(item_type)

        # Track: (widget, item_wrapper, index_holder)
        # item_wrapper is Observable[T] for primitives, ObservableProxy[T] for objects
        # index_holder is [int] so closures can access updated index
        self._items: list[tuple[QWidget, Observable[Any] | ObservableProxy[Any], list[int]]] = []

        # Setup layout
        if layout_type == "horizontal":
            self._layout = QHBoxLayout(self)
        else:
            self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Create initial widgets for existing items
        for i, item in enumerate(observable_list):
            self._create_and_add_widget(i, item)

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

    def _create_item_wrapper(self, item: T) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for an item."""
        if self._is_primitive:
            return Observable(item)
        else:
            return ObservableProxy(item)

    def _create_widget_for_item(self) -> QWidget:
        """Create a new widget instance."""
        return self._widget_type(*self._widget_args, **self._widget_kwargs)

    def _bind_widget_to_item(
        self,
        widget: QWidget,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
    ) -> None:
        """Bind a widget to an item wrapper with two-way sync to the list.

        Args:
            widget: The widget to bind.
            wrapper: Observable or ObservableProxy wrapping the item.
            index_holder: Mutable [int] for tracking index changes.
        """
        # Create a Variable wrapper for the binding system
        var: Variable[Any] = Variable(wrapper)

        # Bind Variable → Widget
        bind(var).to(widget)

        # For primitives, sync wrapper changes back to list
        if isinstance(wrapper, Observable):
            # Prevent infinite loop: track if we're updating
            updating = {"active": False}

            def sync_to_list(new_val: Any, idx: list[int] = index_holder, upd: dict[str, bool] = updating) -> None:
                if upd["active"]:
                    return
                upd["active"] = True
                try:
                    # Update the list item
                    self._obs_list[idx[0]] = new_val
                finally:
                    upd["active"] = False

            wrapper.on_change(sync_to_list)

    def _create_and_add_widget(self, index: int, item: T) -> None:
        """Create a widget for an item and add it to the layout."""
        wrapper = self._create_item_wrapper(item)
        widget = self._create_widget_for_item()
        index_holder = [index]

        self._bind_widget_to_item(widget, wrapper, index_holder)

        # Insert at correct position
        self._items.insert(index, (widget, wrapper, index_holder))
        self._layout.insertWidget(index, widget)

        # Update indices for items after this one
        for i in range(index + 1, len(self._items)):
            self._items[i][2][0] = i

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        self._create_and_add_widget(index, item)

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        if index < len(self._items):
            widget, _, _ = self._items.pop(index)
            self._layout.removeWidget(widget)
            widget.deleteLater()

            # Update indices for remaining items
            for i in range(index, len(self._items)):
                self._items[i][2][0] = i

    def _on_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle item replacement."""
        if index < len(self._items):
            widget, wrapper, index_holder = self._items[index]

            if isinstance(wrapper, Observable):
                # Primitives: just update the Observable
                wrapper.set(new_item)
            else:
                # Complex objects: remove old widget and create new one
                self._layout.removeWidget(widget)
                widget.deleteLater()

                new_wrapper = self._create_item_wrapper(new_item)
                new_widget = self._create_widget_for_item()
                self._bind_widget_to_item(new_widget, new_wrapper, index_holder)

                self._items[index] = (new_widget, new_wrapper, index_holder)
                self._layout.insertWidget(index, new_widget)

    def _on_clear(self, removed_items: list[T]) -> None:
        """Handle list clear."""
        # Remove all widgets
        for widget, _, _ in self._items:
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self._items.clear()

    def widget_at(self, index: int) -> QWidget | None:
        """Get the widget at a specific index."""
        if 0 <= index < len(self._items):
            return self._items[index][0]
        return None

    def widget_count(self) -> int:
        """Get the number of widgets."""
        return len(self._items)
