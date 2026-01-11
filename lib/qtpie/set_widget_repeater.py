"""SetWidgetRepeater - Container that manages repeated widgets bound to set items."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableProxy, ObservableSet
from qtpy.QtWidgets import QWidget

from .bindings import bind
from .repeaters.utils import bind_callable_format, bind_computed_format, connect_child_signals, create_item_wrapper, create_styled_widget, resolve_sort, setup_repeater_layout
from .utils.common import PLACEHOLDER_RE, is_primitive_type
from .variable import Variable

if TYPE_CHECKING:
    from .widget import Widget


class SetWidgetRepeater[T](QWidget):
    """Container that manages repeated widgets bound to set items.

    Creates one widget per set item. Uses granular callbacks (on_add,
    on_remove, on_clear) to efficiently sync the widget list
    with the underlying ObservableSet.

    Key differences from WidgetRepeater:
    - No {#index} placeholder (sets have no indices)
    - Display order: insertion order by default, or sorted if sort= is set
    - Uses widget_for_item(item) instead of widget_at(index)

    Usage:
        # Variable[set[int], QLabel] creates this automatically
        # Each QLabel is bound to one set item
    """

    def __init__(
        self,
        observable_set: ObservableSet[T],
        item_type: type | None,
        widget_type: type,
        widget_args: tuple[Any, ...] = (),
        widget_kwargs: dict[str, Any] | None = None,
        widget_props: dict[str, Any] | None = None,
        bind_expr: str | Callable[[T], str] = "{#self}",
        sort: bool | str | Callable[[T], Any] | None = None,
        layout_type: str = "vertical",
        object_name: str | None = None,
        css_classes: list[str] | None = None,
        signal_connections: dict[str, str | Callable[..., Any]] | None = None,
        parent_widget: Widget[Any] | None = None,
    ) -> None:
        """Initialize the set widget repeater.

        Args:
            observable_set: The ObservableSet to sync with.
            item_type: The type of items in the set (e.g., int, str, Dog).
            widget_type: The widget type to create for each item.
            widget_args: Positional args for widget constructor.
            widget_kwargs: Keyword args for widget constructor.
            widget_props: Widget properties to apply via setXxx() after creation.
            bind_expr: Binding expression or callable formatter (default "{#self}").
            sort: Sorting option - False/None (insertion order), True (sorted()),
                  or callable (key function for sorted()).
            layout_type: "vertical" or "horizontal".
            object_name: objectName to set on each created widget.
            css_classes: CSS classes to apply to each created widget.
            signal_connections: Signal connections from child widget to parent handlers.
            parent_widget: The parent Widget instance for resolving handler methods.
        """
        super().__init__()

        self._obs_set = observable_set
        self._item_type = item_type
        self._widget_type = widget_type
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        self._widget_props = widget_props or {}
        self._bind_expr: str | Callable[[T], str] = bind_expr
        # Resolve sort= string method name to callable
        self._sort: bool | Callable[[T], Any] | None = resolve_sort(sort, parent_widget)
        self._is_primitive = is_primitive_type(item_type)
        self._object_name = object_name
        self._css_classes = css_classes or []
        self._signal_connections = signal_connections or {}
        self._parent_widget = parent_widget

        # Track: item -> (widget, item_wrapper)
        # item_wrapper is Observable[T] for primitives, ObservableProxy[T] for objects
        self._entries: dict[T, tuple[QWidget, Observable[Any] | ObservableProxy[Any]]] = {}
        # Maintain insertion order for layout (like dict's _key_order)
        self._item_order: list[T] = []

        # Setup layout
        self._layout = setup_repeater_layout(self, layout_type)

        # Create initial widgets for existing items (in display order)
        for item in self._get_display_order(list(observable_set)):
            self._item_order.append(item)
            self._create_and_add_widget(item)

        # Subscribe to granular callbacks
        observable_set.on_add(self._on_add)
        observable_set.on_remove(self._on_remove)
        observable_set.on_clear(self._on_clear)

    def _get_display_order(self, items: list[T]) -> list[T]:
        """Get items in display order based on sort= setting.

        Args:
            items: Items to order.

        Returns:
            Items in display order.
        """
        if not self._sort:
            # No sorting - return as-is (insertion order)
            return items

        if self._sort is True:
            # Use default sorted()
            try:
                return sorted(items)  # type: ignore[type-var]
            except TypeError:
                # Items not comparable - fall back to original order
                return items

        # Custom key function
        try:
            return sorted(items, key=self._sort)  # type: ignore[type-var]
        except TypeError:
            return items

    def _find_insert_position(self, item: T) -> int:
        """Find where to insert a new item in the layout based on sort order."""
        if not self._sort:
            # No sorting - append at end
            return len(self._item_order)

        # Get display order including new item
        all_items = list(self._item_order) + [item]
        ordered = self._get_display_order(all_items)

        # Find position of item in ordered list
        try:
            return ordered.index(item)
        except ValueError:
            return len(self._item_order)

    def _create_item_wrapper(self, item: T) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for an item."""
        return create_item_wrapper(item, self._item_type)

    def _create_widget_for_item(self) -> QWidget:
        """Create a new widget instance."""
        return create_styled_widget(
            self._widget_type,
            self._widget_args,
            self._widget_kwargs,
            self._object_name,
            self._css_classes,
            self._widget_props,
        )

    def _bind_widget_to_item(
        self,
        widget: QWidget,
        item: T,
        wrapper: Observable[Any] | ObservableProxy[Any],
    ) -> None:
        """Bind a widget to an item wrapper."""
        bind_expr = self._bind_expr

        # Case 0: Callable formatter - one-way computed binding
        if callable(bind_expr):
            bind_callable_format(widget, wrapper, bind_expr)
            return

        # Find all placeholders in the bind expression
        placeholders = PLACEHOLDER_RE.findall(bind_expr)

        # Case 1: Simple {#self} - bind directly to item value (two-way)
        if bind_expr == "{#self}":
            var: Variable[Any] = Variable(wrapper)
            bind(var).to(widget)
            self._setup_primitive_sync(wrapper, item)
            return

        # Case 2: Single property {name} - bind to that property (two-way for objects)
        if len(placeholders) == 1 and bind_expr == f"{{{placeholders[0]}}}":
            prop_name = placeholders[0]
            if prop_name.startswith("#"):
                # Special placeholder like {#self} - one-way computed
                bind_computed_format(widget, wrapper, bind_expr)
            elif isinstance(wrapper, ObservableProxy):
                # Property on object - get Observable for that property
                prop_obs: Observable[Any] = getattr(wrapper, prop_name)
                var = Variable(prop_obs)
                bind(var).to(widget)
            else:
                # Primitive with property access doesn't make sense, fall back to format
                bind_computed_format(widget, wrapper, bind_expr)
            return

        # Case 3: Format string with multiple placeholders - one-way computed binding
        bind_computed_format(widget, wrapper, bind_expr)

    def _setup_primitive_sync(
        self,
        wrapper: Observable[Any] | ObservableProxy[Any],
        original_item: T,
    ) -> None:
        """Set up sync from primitive Observable back to set.

        For sets, when a primitive value changes, we need to:
        1. Remove the original item from the set
        2. Add the new value to the set
        """
        if isinstance(wrapper, Observable):
            # Prevent infinite loop: track if we're updating
            updating = {"active": False}
            # Track the current item value (may change from original)
            current_item = [original_item]

            def sync_to_set(new_val: Any, upd: dict[str, bool] = updating, cur: list[T] = current_item) -> None:
                if upd["active"]:
                    return
                upd["active"] = True
                try:
                    old_val = cur[0]
                    if old_val != new_val:
                        # Remove old value and add new value
                        self._obs_set.discard(old_val)
                        self._obs_set.add(new_val)
                        cur[0] = new_val
                finally:
                    upd["active"] = False

            wrapper.on_change(sync_to_set)

    def _create_and_add_widget(self, item: T, position: int | None = None) -> None:
        """Create a widget for an item and add it to the layout."""
        wrapper = self._create_item_wrapper(item)
        widget = self._create_widget_for_item()

        self._bind_widget_to_item(widget, item, wrapper)
        connect_child_signals(widget, wrapper, self._signal_connections, self._parent_widget)

        self._entries[item] = (widget, wrapper)

        if position is not None:
            self._layout.insertWidget(position, widget)
        else:
            self._layout.addWidget(widget)

    def _on_add(self, item: T) -> None:
        """Handle item addition."""
        if self._sort:
            # Find correct position based on sort order
            position = self._find_insert_position(item)
            self._item_order.insert(position, item)
            self._create_and_add_widget(item, position)
        else:
            # No sorting - append at end
            self._item_order.append(item)
            self._create_and_add_widget(item)

    def _on_remove(self, item: T) -> None:
        """Handle item removal."""
        if item in self._entries:
            widget, _ = self._entries.pop(item)
            self._item_order.remove(item)
            self._layout.removeWidget(widget)
            widget.deleteLater()

    def _on_clear(self, removed_items: set[T]) -> None:
        """Handle set clear."""
        for widget, _ in self._entries.values():
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self._entries.clear()
        self._item_order.clear()

    def widget_for_item(self, item: T) -> QWidget | None:
        """Get the widget for a specific item."""
        entry = self._entries.get(item)
        return entry[0] if entry else None

    def widget_count(self) -> int:
        """Get the number of widgets."""
        return len(self._entries)

    # Set-like interface
    def __contains__(self, item: T) -> bool:
        """Check if item has a widget."""
        return item in self._entries

    def __len__(self) -> int:
        """Return number of widgets."""
        return len(self._entries)

    def __iter__(self):
        """Iterate over widgets in display order."""
        for item in self._item_order:
            if item in self._entries:
                yield self._entries[item][0]

    def items(self):
        """Iterate over (item, widget) pairs in display order."""
        for item in self._item_order:
            if item in self._entries:
                yield item, self._entries[item][0]
